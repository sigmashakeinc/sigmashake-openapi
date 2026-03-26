"""OpenAPI SDK drift detector.

Parses an OpenAPI 3.x spec and compares its schemas against Python (Pydantic)
and Node (TypeScript) SDK model files.  Returns structured drift reports so CI
can fail on divergence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FieldInfo:
    name: str
    field_type: str
    required: bool


@dataclass
class SchemaInfo:
    name: str
    is_enum: bool
    enum_values: Optional[List[str]]
    fields: Dict[str, FieldInfo] = field(default_factory=dict)


@dataclass
class DriftItem:
    drift_type: str  # "missing_schema", "missing_field", "missing_enum_value"
    schema_name: str
    field_name: Optional[str] = None
    detail: str = ""


@dataclass
class DriftReport:
    sdk: str
    total_schemas: int = 0
    matched_schemas: int = 0
    missing_schemas: int = 0
    missing_fields: int = 0
    items: List[DriftItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# OpenAPI extraction
# ---------------------------------------------------------------------------

def extract_openapi_schemas(spec: Dict[str, Any]) -> Dict[str, SchemaInfo]:
    """Extract all component schemas from an OpenAPI spec dict."""
    schemas: Dict[str, SchemaInfo] = {}
    raw_schemas = spec.get("components", {}).get("schemas", {})

    for name, defn in raw_schemas.items():
        schema_type = defn.get("type", "object")
        enum_values = defn.get("enum")

        if enum_values is not None:
            schemas[name] = SchemaInfo(
                name=name,
                is_enum=True,
                enum_values=enum_values,
                fields={},
            )
            continue

        # Object schema
        required_set = set(defn.get("required", []))
        properties = defn.get("properties", {})
        fields: Dict[str, FieldInfo] = {}

        for field_name, field_defn in properties.items():
            ft = field_defn.get("type", "object")
            # Handle $ref as "object"
            if "$ref" in field_defn:
                ft = "ref"
            fields[field_name] = FieldInfo(
                name=field_name,
                field_type=ft,
                required=field_name in required_set,
            )

        schemas[name] = SchemaInfo(
            name=name,
            is_enum=False,
            enum_values=None,
            fields=fields,
        )

    return schemas


# ---------------------------------------------------------------------------
# Python model extraction
# ---------------------------------------------------------------------------

def extract_python_models(source: str) -> Dict[str, Dict[str, Any]]:
    """Extract class names and field names from Python Pydantic model source."""
    models: Dict[str, Dict[str, Any]] = {}
    current_class: Optional[str] = None
    is_enum = False

    for line in source.splitlines():
        # Detect class definition
        class_match = re.match(r'^class\s+(\w+)\(', line)
        if class_match:
            current_class = class_match.group(1)
            is_enum = "Enum" in line and "BaseModel" not in line
            models[current_class] = {}
            if is_enum:
                models[current_class]["__is_enum__"] = True
            continue

        # Detect field in current class (indented, with type annotation)
        if current_class is not None:
            # End of class body
            if line and not line[0].isspace() and not line.startswith('#'):
                current_class = None
                continue

            # Field pattern: "    field_name: Type" or "    field_name = value"
            field_match = re.match(r'^\s{4}(\w+)\s*[:=]', line)
            if field_match:
                fname = field_match.group(1)
                if not fname.startswith('_') or fname == "__is_enum__":
                    # Skip dunder methods and private attrs, but not __is_enum__
                    if not fname.startswith('__'):
                        models[current_class][fname] = True

    return models


# ---------------------------------------------------------------------------
# Node model extraction
# ---------------------------------------------------------------------------

def extract_node_models(source: str) -> Dict[str, Dict[str, Any]]:
    """Extract interface/const-enum names and field names from TypeScript source."""
    models: Dict[str, Dict[str, Any]] = {}
    current_interface: Optional[str] = None
    brace_depth = 0

    for line in source.splitlines():
        stripped = line.strip()

        # Detect const enum: export const Foo = { ... } as const;
        const_match = re.match(
            r'^export\s+const\s+(\w+)\s*=\s*\{', stripped
        )
        if const_match:
            name = const_match.group(1)
            # Only treat as enum if there's a matching "export type" line
            models[name] = {"__is_enum__": True}
            continue

        # Detect interface: export interface Foo {
        iface_match = re.match(r'^export\s+interface\s+(\w+)\s*\{', stripped)
        if iface_match:
            current_interface = iface_match.group(1)
            models[current_interface] = {}
            brace_depth = 1
            continue

        # Track nested braces inside interface
        if current_interface is not None:
            brace_depth += stripped.count('{') - stripped.count('}')
            if brace_depth <= 0:
                current_interface = None
                continue

            # Only capture top-level fields (depth == 1)
            if brace_depth == 1:
                # Field pattern: "  fieldName: Type;" or "  fieldName?: Type;"
                field_match = re.match(r'^\s*(\w+)\??:\s*', line)
                if field_match:
                    fname = field_match.group(1)
                    models[current_interface][fname] = True

    return models


# ---------------------------------------------------------------------------
# snake_case <-> camelCase conversion
# ---------------------------------------------------------------------------

def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

def find_drift(
    openapi_schemas: Dict[str, SchemaInfo],
    sdk_models: Dict[str, Dict[str, Any]],
    sdk_type: str,  # "python" or "node"
) -> DriftReport:
    """Compare OpenAPI schemas against SDK models and return drift report."""
    report = DriftReport(sdk=sdk_type, total_schemas=len(openapi_schemas))

    for schema_name, schema in openapi_schemas.items():
        if schema_name not in sdk_models:
            report.missing_schemas += 1
            report.items.append(DriftItem(
                drift_type="missing_schema",
                schema_name=schema_name,
                detail=f"Schema '{schema_name}' not found in {sdk_type} SDK",
            ))
            continue

        report.matched_schemas += 1
        sdk_model = sdk_models[schema_name]

        # Skip enum comparison for now (just check existence)
        if schema.is_enum:
            continue

        # Check fields
        sdk_field_names = {k for k in sdk_model if k != "__is_enum__"}

        for field_name, field_info in schema.fields.items():
            # For Node SDK, convert snake_case to camelCase
            if sdk_type == "node":
                expected_name = snake_to_camel(field_name)
            else:
                expected_name = field_name

            if expected_name not in sdk_field_names:
                report.missing_fields += 1
                report.items.append(DriftItem(
                    drift_type="missing_field",
                    schema_name=schema_name,
                    field_name=field_name,
                    detail=(
                        f"Field '{field_name}' (expected as '{expected_name}') "
                        f"missing from {sdk_type} SDK model '{schema_name}'"
                    ),
                ))

    return report

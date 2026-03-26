"""Tests for the OpenAPI SDK drift detector."""

from __future__ import annotations

import textwrap

import pytest

from drift_detector import (
    extract_openapi_schemas,
    SchemaInfo,
    FieldInfo,
    extract_python_models,
    extract_node_models,
    find_drift,
    DriftReport,
    DriftItem,
)


# ---------------------------------------------------------------------------
# extract_openapi_schemas
# ---------------------------------------------------------------------------

MINIMAL_SPEC = {
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "required": ["error"],
                "properties": {
                    "error": {"type": "string"},
                },
            },
            "Tier": {
                "type": "string",
                "enum": ["Free", "Pro", "Enterprise"],
            },
            "TokenRequest": {
                "type": "object",
                "required": ["agent_id", "scopes"],
                "properties": {
                    "agent_id": {"type": "string", "format": "uuid"},
                    "scopes": {"type": "array", "items": {"type": "string"}},
                    "ttl_secs": {"type": "integer", "minimum": 1},
                },
            },
        }
    }
}


class TestExtractOpenAPISchemas:
    def test_extracts_object_schemas(self) -> None:
        schemas = extract_openapi_schemas(MINIMAL_SPEC)
        assert "Error" in schemas
        assert "TokenRequest" in schemas

    def test_extracts_enum_schemas(self) -> None:
        schemas = extract_openapi_schemas(MINIMAL_SPEC)
        assert "Tier" in schemas
        tier = schemas["Tier"]
        assert tier.is_enum is True
        assert tier.enum_values == ["Free", "Pro", "Enterprise"]

    def test_extracts_required_fields(self) -> None:
        schemas = extract_openapi_schemas(MINIMAL_SPEC)
        tr = schemas["TokenRequest"]
        assert tr.fields["agent_id"].required is True
        assert tr.fields["scopes"].required is True
        assert tr.fields["ttl_secs"].required is False

    def test_extracts_field_types(self) -> None:
        schemas = extract_openapi_schemas(MINIMAL_SPEC)
        tr = schemas["TokenRequest"]
        assert tr.fields["agent_id"].field_type == "string"
        assert tr.fields["scopes"].field_type == "array"
        assert tr.fields["ttl_secs"].field_type == "integer"


# ---------------------------------------------------------------------------
# extract_python_models
# ---------------------------------------------------------------------------

SAMPLE_PYTHON_MODELS = textwrap.dedent("""\
    from pydantic import BaseModel, Field
    from enum import Enum
    from typing import List, Optional

    class Tier(str, Enum):
        free = "free"
        pro = "pro"
        enterprise = "enterprise"

    class TokenRequest(BaseModel):
        agent_id: str
        scopes: List[str] = Field(default_factory=list)

    class TokenResponse(BaseModel):
        token: str
        expires_at: str
""")


class TestExtractPythonModels:
    def test_extracts_class_names(self) -> None:
        models = extract_python_models(SAMPLE_PYTHON_MODELS)
        assert "Tier" in models
        assert "TokenRequest" in models
        assert "TokenResponse" in models

    def test_extracts_field_names(self) -> None:
        models = extract_python_models(SAMPLE_PYTHON_MODELS)
        assert "agent_id" in models["TokenRequest"]
        assert "scopes" in models["TokenRequest"]

    def test_enum_detection(self) -> None:
        models = extract_python_models(SAMPLE_PYTHON_MODELS)
        # Enums are marked with special key
        assert models["Tier"]["__is_enum__"] is True


# ---------------------------------------------------------------------------
# extract_node_models
# ---------------------------------------------------------------------------

SAMPLE_NODE_MODELS = textwrap.dedent("""\
    export const Tier = { Free: 'free', Pro: 'pro', Enterprise: 'enterprise' } as const;
    export type Tier = (typeof Tier)[keyof typeof Tier];

    export interface TokenRequest {
      agentId: string;
      scopes: string[];
      ttlSecs?: number;
    }

    export interface TokenResponse {
      token: string;
      expiresAt: string;
    }
""")


class TestExtractNodeModels:
    def test_extracts_interface_names(self) -> None:
        models = extract_node_models(SAMPLE_NODE_MODELS)
        assert "TokenRequest" in models
        assert "TokenResponse" in models

    def test_extracts_const_enums(self) -> None:
        models = extract_node_models(SAMPLE_NODE_MODELS)
        assert "Tier" in models
        assert models["Tier"]["__is_enum__"] is True

    def test_extracts_field_names(self) -> None:
        models = extract_node_models(SAMPLE_NODE_MODELS)
        assert "agentId" in models["TokenRequest"]
        assert "scopes" in models["TokenRequest"]
        assert "ttlSecs" in models["TokenRequest"]


# ---------------------------------------------------------------------------
# find_drift
# ---------------------------------------------------------------------------

class TestFindDrift:
    def test_missing_schema_detected(self) -> None:
        openapi = {
            "Error": SchemaInfo(
                name="Error",
                is_enum=False,
                enum_values=None,
                fields={"error": FieldInfo(name="error", field_type="string", required=True)},
            ),
            "TokenRequest": SchemaInfo(
                name="TokenRequest",
                is_enum=False,
                enum_values=None,
                fields={"agent_id": FieldInfo(name="agent_id", field_type="string", required=True)},
            ),
        }
        sdk_models = {"Error": {"error": True}}
        report = find_drift(openapi, sdk_models, "python")
        missing = [d for d in report.items if d.drift_type == "missing_schema"]
        assert any(d.schema_name == "TokenRequest" for d in missing)

    def test_missing_field_detected(self) -> None:
        openapi = {
            "TokenRequest": SchemaInfo(
                name="TokenRequest",
                is_enum=False,
                enum_values=None,
                fields={
                    "agent_id": FieldInfo(name="agent_id", field_type="string", required=True),
                    "scopes": FieldInfo(name="scopes", field_type="array", required=True),
                    "ttl_secs": FieldInfo(name="ttl_secs", field_type="integer", required=False),
                },
            ),
        }
        # SDK has agent_id but missing scopes and ttl_secs
        sdk_models = {"TokenRequest": {"agent_id": True}}
        report = find_drift(openapi, sdk_models, "python")
        missing_fields = [d for d in report.items if d.drift_type == "missing_field"]
        field_names = [d.field_name for d in missing_fields]
        assert "scopes" in field_names
        assert "ttl_secs" in field_names

    def test_no_drift_for_matching_schema(self) -> None:
        openapi = {
            "Error": SchemaInfo(
                name="Error",
                is_enum=False,
                enum_values=None,
                fields={"error": FieldInfo(name="error", field_type="string", required=True)},
            ),
        }
        sdk_models = {"Error": {"error": True}}
        report = find_drift(openapi, sdk_models, "python")
        assert len(report.items) == 0

    def test_node_camelcase_mapping(self) -> None:
        openapi = {
            "TokenRequest": SchemaInfo(
                name="TokenRequest",
                is_enum=False,
                enum_values=None,
                fields={
                    "agent_id": FieldInfo(name="agent_id", field_type="string", required=True),
                    "ttl_secs": FieldInfo(name="ttl_secs", field_type="integer", required=False),
                },
            ),
        }
        # Node SDK uses camelCase
        sdk_models = {"TokenRequest": {"agentId": True, "ttlSecs": True}}
        report = find_drift(openapi, sdk_models, "node")
        assert len(report.items) == 0

    def test_report_has_total_and_summary(self) -> None:
        openapi = {
            "Error": SchemaInfo(
                name="Error",
                is_enum=False,
                enum_values=None,
                fields={"error": FieldInfo(name="error", field_type="string", required=True)},
            ),
        }
        sdk_models = {}
        report = find_drift(openapi, sdk_models, "python")
        assert report.total_schemas > 0
        assert report.missing_schemas > 0

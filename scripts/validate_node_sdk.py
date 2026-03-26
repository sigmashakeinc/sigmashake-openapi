#!/usr/bin/env python3
"""Validate Node/TypeScript SDK models against the OpenAPI spec.

Usage:
    python3 validate_node_sdk.py [--spec PATH] [--models PATH] [--json]

Exit codes:
    0 = no drift detected
    1 = drift detected (missing schemas or fields)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from drift_detector import (
    extract_openapi_schemas,
    extract_node_models,
    find_drift,
)

DEFAULT_SPEC = Path(__file__).resolve().parent.parent / "openapi.yaml"
DEFAULT_MODELS = (
    Path(__file__).resolve().parent.parent.parent
    / "sigmashake-sdk-node"
    / "src"
    / "models.ts"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Node SDK types against OpenAPI spec")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC, help="Path to openapi.yaml")
    parser.add_argument("--models", type=Path, default=DEFAULT_MODELS, help="Path to TypeScript models.ts")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.spec.exists():
        print(f"ERROR: Spec not found: {args.spec}", file=sys.stderr)
        return 1
    if not args.models.exists():
        print(f"ERROR: Models not found: {args.models}", file=sys.stderr)
        return 1

    with open(args.spec) as f:
        spec = yaml.safe_load(f)

    openapi_schemas = extract_openapi_schemas(spec)

    models_source = args.models.read_text()
    sdk_models = extract_node_models(models_source)

    report = find_drift(openapi_schemas, sdk_models, "node")

    if args.json:
        output = {
            "sdk": report.sdk,
            "total_schemas": report.total_schemas,
            "matched_schemas": report.matched_schemas,
            "missing_schemas": report.missing_schemas,
            "missing_fields": report.missing_fields,
            "items": [
                {
                    "type": item.drift_type,
                    "schema": item.schema_name,
                    "field": item.field_name,
                    "detail": item.detail,
                }
                for item in report.items
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Node SDK Drift Report")
        print(f"=====================")
        print(f"OpenAPI schemas:  {report.total_schemas}")
        print(f"Matched in SDK:   {report.matched_schemas}")
        print(f"Missing schemas:  {report.missing_schemas}")
        print(f"Missing fields:   {report.missing_fields}")

        if report.items:
            print()
            for item in report.items:
                if item.drift_type == "missing_schema":
                    print(f"  MISSING SCHEMA: {item.schema_name}")
                elif item.drift_type == "missing_field":
                    print(f"  MISSING FIELD:  {item.schema_name}.{item.field_name}")

    has_drift = len(report.items) > 0
    if has_drift:
        if not args.json:
            print(f"\nDRIFT DETECTED: {len(report.items)} issue(s) found")
    else:
        if not args.json:
            print(f"\nNo drift detected.")

    return 1 if has_drift else 0


if __name__ == "__main__":
    sys.exit(main())

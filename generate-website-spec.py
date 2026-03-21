#!/usr/bin/env python3
"""Generate the website-facing OpenAPI subset from the canonical spec + overlay.

Usage:
    python3 generate-website-spec.py                     # writes to stdout
    python3 generate-website-spec.py -o website.yaml     # writes to file
    python3 generate-website-spec.py --check website.yaml  # exits 1 if drift detected

Requires: PyYAML (pip install pyyaml)
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
CANONICAL_PATH = SCRIPT_DIR / "openapi.yaml"
OVERLAY_PATH = SCRIPT_DIR / "website-overlay.yaml"


def load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def collect_refs(node: object, refs: set[str]) -> None:
    """Recursively collect all $ref targets from a schema tree."""
    if isinstance(node, dict):
        if "$ref" in node:
            refs.add(node["$ref"])
        for v in node.values():
            collect_refs(v, refs)
    elif isinstance(node, list):
        for item in node:
            collect_refs(item, refs)


def resolve_schema_refs(schemas: dict, seed_refs: set[str], all_schemas: dict) -> dict:
    """Transitively resolve all referenced schemas starting from seed_refs."""
    resolved: dict = {}
    pending = set()

    for ref in seed_refs:
        # e.g. "#/components/schemas/Error" -> "Error"
        parts = ref.split("/")
        if len(parts) >= 4 and parts[-2] == "schemas":
            pending.add(parts[-1])

    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)

        schema = all_schemas.get(name)
        if schema is None:
            continue

        resolved[name] = copy.deepcopy(schema)

        # Find transitive refs
        child_refs: set[str] = set()
        collect_refs(schema, child_refs)
        for ref in child_refs:
            parts = ref.split("/")
            if len(parts) >= 4 and parts[-2] == "schemas":
                pending.add(parts[-1])

    return resolved


def generate(canonical: dict, overlay: dict) -> dict:
    """Build the website spec from canonical + overlay."""
    # Start with metadata from overlay
    info = overlay.get("info", {})
    website: dict = {
        "openapi": overlay.get("openapi_version", "3.1.0"),
        "info": {
            "title": info.get("title", "SigmaShake API"),
            "version": info.get("version", "1.0.0"),
            "description": info.get("description", ""),
            "contact": info.get("contact", {}),
            "license": canonical.get("info", {}).get("license", {}),
        },
        "servers": [
            {
                "url": overlay.get("server_url", "https://api.sigmashake.com"),
                "description": "Production",
            }
        ],
        "security": [
            {overlay.get("security_scheme", "BearerAuth"): []}
        ],
    }

    canonical_paths = canonical.get("paths", {})
    canonical_schemas = canonical.get("components", {}).get("schemas", {})
    canonical_responses = canonical.get("components", {}).get("responses", {})
    canonical_security = canonical.get("components", {}).get("securitySchemes", {})

    # Collect included paths from canonical
    paths: dict = {}
    include_paths = overlay.get("include_paths", [])
    for path_pattern in include_paths:
        if path_pattern in canonical_paths:
            paths[path_pattern] = copy.deepcopy(canonical_paths[path_pattern])

    # Add website-only paths
    website_only = overlay.get("website_only_paths", {})
    for path_key, path_val in website_only.items():
        paths[path_key] = copy.deepcopy(path_val)

    website["paths"] = paths

    # Collect all $ref targets from included paths
    all_refs: set[str] = set()
    collect_refs(paths, all_refs)

    # Merge canonical schemas with website-only schemas for resolution
    merged_schemas = dict(canonical_schemas)
    website_only_schemas = overlay.get("website_only_schemas", {})
    merged_schemas.update(website_only_schemas)

    # Resolve schemas transitively
    resolved_schemas = resolve_schema_refs(merged_schemas, all_refs, merged_schemas)

    # Resolve response refs — inline them as schemas
    response_refs = {r for r in all_refs if "/responses/" in r}
    resolved_responses: dict = {}
    for ref in response_refs:
        name = ref.split("/")[-1]
        if name in canonical_responses:
            resp = copy.deepcopy(canonical_responses[name])
            resolved_responses[name] = resp
            # Collect any schema refs inside responses
            resp_refs: set[str] = set()
            collect_refs(resp, resp_refs)
            extra = resolve_schema_refs(merged_schemas, resp_refs, merged_schemas)
            resolved_schemas.update(extra)

    # Build security scheme
    scheme_name = overlay.get("security_scheme", "BearerAuth")
    security_schemes = {}
    if scheme_name in canonical_security:
        security_schemes[scheme_name] = copy.deepcopy(canonical_security[scheme_name])

    website["components"] = {
        "securitySchemes": security_schemes,
        "schemas": dict(sorted(resolved_schemas.items())),
    }

    if resolved_responses:
        website["components"]["responses"] = dict(sorted(resolved_responses.items()))

    # Collect tags used in included paths
    used_tags: set[str] = set()
    for path_val in paths.values():
        if isinstance(path_val, dict):
            for method_val in path_val.values():
                if isinstance(method_val, dict):
                    for tag in method_val.get("tags", []):
                        used_tags.add(tag)

    canonical_tags = {t["name"]: t for t in canonical.get("tags", [])}
    website_tags = []
    for tag_name in sorted(used_tags):
        if tag_name in canonical_tags:
            website_tags.append(canonical_tags[tag_name])
        else:
            website_tags.append({"name": tag_name, "description": f"{tag_name} endpoints"})
    if website_tags:
        website["tags"] = website_tags

    return website


def yaml_dump(data: dict) -> str:
    """Dump YAML with consistent formatting."""
    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate website OpenAPI spec from canonical + overlay")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument("--check", metavar="FILE", help="Check if FILE matches generated output; exit 1 if drift")
    parser.add_argument("--canonical", default=str(CANONICAL_PATH), help="Path to canonical openapi.yaml")
    parser.add_argument("--overlay", default=str(OVERLAY_PATH), help="Path to website-overlay.yaml")
    args = parser.parse_args()

    canonical = load_yaml(Path(args.canonical))
    overlay = load_yaml(Path(args.overlay))
    website = generate(canonical, overlay)
    output = yaml_dump(website)

    if args.check:
        check_path = Path(args.check)
        if not check_path.exists():
            print(f"ERROR: {check_path} does not exist", file=sys.stderr)
            sys.exit(1)
        existing = check_path.read_text()
        if existing.strip() != output.strip():
            print(f"DRIFT: {check_path} does not match generated spec", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()

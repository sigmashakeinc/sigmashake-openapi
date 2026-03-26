# SigmaShake Platform OpenAPI Specification

Complete OpenAPI 3.1 specification for the SigmaShake AI-Native platform.

## Services

| Service | Description |
|---------|-------------|
| **Agent API** | Authentication, identity, documents, memory, search |
| **Account API** | Account management, subscriptions, seats, usage |
| **Shield Daemon** | Agent registration, policy scanning, session management |
| **SOC API** | Incidents, alerts, metrics, compliance, logs, correlation, analytics |
| **Gateway** | Pre/post tool call interception and policy enforcement |
| **DB Server** | Table management, columnar queries, vector search, clustering |

## Single Source of Truth

`openapi.yaml` is the **canonical** spec for all SigmaShake platform APIs. The website
(`sigmashake.com`) uses a **generated subset** that exposes only public-facing endpoints.

```
openapi.yaml                    # Canonical OpenAPI 3.1 spec (ALL endpoints)
website-overlay.yaml            # Overlay config defining the website subset
generate-website-spec.py        # Generates website spec from canonical + overlay
schemas/                        # JSON Schema files for key types
  agent-identity-claims.json
  account.json
  scan-result.json
  intercept-result.json
  correlated-session.json
  query-request.json
  error.json
.well-known/sigmashake.json     # Agent discovery manifest
```

### Generate the website spec

```bash
python3 generate-website-spec.py                      # stdout
python3 generate-website-spec.py -o website.yaml      # write to file
python3 generate-website-spec.py --check website.yaml # CI drift check (exit 1 if stale)
```

To add or remove website-visible endpoints, edit `website-overlay.yaml` — not the
website spec directly.

## Usage

### Validate the spec

```bash
npx @redocly/cli lint openapi.yaml
```

### Generate documentation

```bash
npx @redocly/cli build-docs openapi.yaml -o docs/index.html
```

### Generate a client (Rust)

```bash
openapi-generator-cli generate -i openapi.yaml -g rust -o client/
```

### Generate a client (TypeScript)

```bash
openapi-generator-cli generate -i openapi.yaml -g typescript-fetch -o client-ts/
```

## SDK Drift Detection

The SDKs (Python and Node) must stay in sync with this spec. A drift detector
compares the spec schemas against the SDK model files and reports any missing
schemas or fields.

```bash
# Validate both SDKs
./validate-sdks.sh

# Validate one SDK
./validate-sdks.sh --python
./validate-sdks.sh --node

# JSON output for CI pipelines
./validate-sdks.sh --json

# Run unit tests for the drift detector
cd scripts && python3 -m pytest -v
```

Exit code is 0 when SDKs match the spec, 1 when drift is detected.

### Files

```
scripts/
  drift_detector.py          # Core library: schema extraction + comparison
  validate_python_sdk.py     # CLI: validate Python SDK models
  validate_node_sdk.py       # CLI: validate Node SDK types
  test_drift_detector.py     # Unit tests for drift_detector
  test_validate_cli.py       # Integration tests for CLI scripts
validate-sdks.sh             # Top-level entry point for CI
```

### Workflow

1. Edit `openapi.yaml` (the source of truth)
2. Run `./validate-sdks.sh` to see what changed
3. Update SDK model files to match
4. Re-run `./validate-sdks.sh` to confirm zero drift
5. CI runs `./validate-sdks.sh` on every commit to block regressions

## Authentication

All protected endpoints require a JWT Bearer token:

```
Authorization: Bearer <token>
```

JWT claims: `sub`, `roles`, `exp`, `iat`, `iss`, `tenant_id`, `tier`.

Obtain tokens via `POST /auth/token` (unauthenticated).

## Subscription Tiers

| Tier | Seats | Agents/Seat | Cost Units | Price |
|------|-------|-------------|------------|-------|
| Free | 3 | 5 | 1,000 | $0 |
| Pro | 50 | 50 | 50,000 | $29/seat/mo |
| Enterprise | Unlimited | Unlimited | Unlimited | Custom |

## Error Format

All errors return:

```json
{"error": "description"}
```

Status codes: 200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500, 501.

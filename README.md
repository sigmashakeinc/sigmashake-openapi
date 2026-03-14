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

## Files

```
openapi.yaml                    # Full OpenAPI 3.1 spec
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

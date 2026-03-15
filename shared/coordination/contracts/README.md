# Contracts

Contracts define the interface BEFORE implementation. Every workstream must reference
at least one contract. Implementation without a contract is not permitted.

## REST (OpenAPI)

Source of truth: `repos/sigmashake-openapi/openapi.yaml`

When adding new REST endpoints:
1. Define paths and schemas in openapi.yaml FIRST
2. Validate: `cd repos/sigmashake-openapi && npx @redocly/cli lint openapi.yaml`
3. Reference the specific paths in your workstream file
4. Implement backend + frontend against the spec — not ad-hoc

## gRPC (Protobuf)

Source of truth: `shared/coordination/contracts/grpc/*.proto`

When adding new gRPC services:
1. Write the .proto file in this directory FIRST
2. Reference it in your workstream file
3. Use `tonic-build` for Rust server/client codegen

## Adding a New Contract Type

1. Create a subdirectory under `shared/coordination/contracts/`
2. Document the convention in this README
3. Reference from workstream frontmatter using `type: <your-type>`

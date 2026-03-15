# Backlog

Items here are not yet planned. To start work, create a workstream file and add it to BOARD.md.

## Items

### [BL-001] gRPC/HTTP2 Transport Support
**Priority:** high
**Added:** 2026-03-15
**Description:** Add gRPC as an alternative transport to REST for all agent APIs. Requires .proto definitions in `shared/coordination/contracts/grpc/`, tonic integration in sigmashake_inc, and client SDK updates (node, python, terraform provider).
**Depends on:** OpenAPI spec stabilization
**Scope:** api, infra, sdk-node, sdk-python, terraform-provider

### [BL-002] Admin/Dashboard/Governance UI
**Priority:** high
**Added:** 2026-03-15
**Description:** Design and implement admin dashboard for governance controls, account management, and system monitoring. Requires both UI design work and API integration with existing governance crates.
**Depends on:** --
**Scope:** frontend, api, governance

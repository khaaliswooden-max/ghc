# Maintainers

This file lists the people who can review and merge PRs, tag
releases, and act as escalation contacts for the project.

Maintainer addition / removal follows the process documented in
[GOVERNANCE.md](GOVERNANCE.md).

## Active maintainers

| Handle | Areas | Contact |
|--------|-------|---------|
| _vacant_ | _v0.1.0 is maintainer-led-pending. A maintainer slot opens when a steward organization is named (see GOVERNANCE.md §v0.2 roadmap)._ | — |

## Subsystem-area review hints

When you open a PR, tagging one of the area labels below in the PR
title helps the right reviewer find it once active maintainers are
seated:

| Label | Subsystems |
|-------|-----------|
| `proofs/` | `proofs/`, `proofs-mathlib/` Lean theorems |
| `crypto/` | `core/ghc-zk`, `core/ghc-stark`, `integrations/dlt/evm` |
| `core/` | `core/ghc-algebra`, `core/ghc-graph`, `core/ghc-cli` |
| `services/` | `services/ghc_api`, `services/ghc_ml`, `services/ghc_traceability` |
| `dlt/` | `integrations/dlt/fabric`, `integrations/dlt/evm` |
| `certifiers/` | `integrations/certifiers/` |
| `spec/` | `spec/`, JSON Schemas, attestation format |
| `paper/` | `paper/`, bibliography |

## Emeritus

* _none yet_

## Security contact

Security vulnerabilities go through the process in
[SECURITY.md](SECURITY.md), not the issue tracker. Until a project
security alias is provisioned, encrypt disclosures with the
maintainer GPG keys published here (none yet listed; v0.1.0 is
maintainer-led-pending).

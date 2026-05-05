# GHC Protocol — v0.1.0

## 0. Overview

The **GHC Protocol** is an open, authority-parametric specification for
expressing, transmitting, and verifying halal compliance claims across
food, pharmaceutical, cosmetic, financial, and logistics domains.

This document tracks the six contributions defined in the GHC
whitepaper and binds them to on-the-wire data formats, schemas, and
verification procedures. It is **frozen** at v0.1.0; subsequent
changes follow [SemVer](https://semver.org/) and are recorded in the
spec changelog (§0.7) and the top-level [`CHANGELOG.md`](../CHANGELOG.md).

## 0.1 Document set

| File | Purpose |
|------|---------|
| `00-overview.md`            | This file. |
| `01-data-model.md`          | Data model: PROV-O + EPCIS 2.0 extensions. |
| `02-attestation.md`         | zk-Halal credential format and verifier protocol. |
| `03-compliance-lattice.md`  | Authority-parametric compliance lattice. |
| `schemas/*.json`            | JSON Schema + JSON-LD contexts. |

## 0.2 Conformance levels

A GHC implementation **MUST** declare one or more of the following
conformance levels:

- **L1 — Provenance:** Emits and consumes EPCIS 2.0 events extended
  with the GHC `compliance` block (see §1).
- **L2 — Attestation:** Additionally produces and verifies zk-Halal
  Verifiable Credentials (see §2).
- **L3 — Federation:** Additionally implements the multi-authority
  lattice with explicit dissent encoding (see §3).
- **L4 — Anchored:** Additionally anchors attestation hashes to a
  qualifying DLT (Hyperledger Fabric or an EVM L2 with a deployed
  GHC verifier contract).

## 0.3 Terminology (selected)

| Symbol | Term | Definition |
|--------|------|------------|
| 𝐒𝐂 | supply-chain category | symmetric monoidal category of batches and processes |
| 𝐋 | compliance lattice | `{ḥalāl ≺ mashbūh ≺ ḥarām}` |
| H | Halal-Closure Functor | strong monoidal functor `𝐒𝐂 → 𝐋` |
| C_h | contamination capacity | mutual-information bound on haram-bit survival |
| ρ_n | najis density matrix | provenance state, `Tr(ρ²) ∈ (1/dim, 1]` |
| σ(L_G) | provenance fingerprint | normalized-Laplacian spectrum of provenance DAG |

The full glossary (with mappings to fiqh terminology) lives in
`docs/glossary.md`.

## 0.4 Normative references

- W3C PROV-O — *PROV Ontology*, 2013.
- GS1 EPCIS 2.0 — *Electronic Product Code Information Services*, 2022.
- W3C Verifiable Credentials Data Model 2.0, 2024.
- IETF RFC 7515 — *JSON Web Signature*.
- BLS12-381 curve specification (IRTF CFRG).

## 0.5 Versioning

The protocol follows semantic versioning. Breaking schema changes bump
the major version. JSON-LD `@context` URLs are versioned, e.g.
`https://ghc.example/ns/v1`.

## 0.6 Status of this document

**Tagged v0.1.0.** This is the first implementable release. The
reference implementations under `core/`, `services/`, and
`integrations/` conform to this document.

## 0.7 Spec changelog

### v0.1.0 — 2026-05-05

Initial frozen release.

* `ghc:scheme` enum normalized to:
  * `groth16-bls12-381-poseidon` — off-chain default (`core/ghc-zk`).
  * `groth16-bn254-poseidon` — EVM default (`integrations/dlt/evm`).
  * `plonk-bn254-poseidon` — universal-setup variant; reserved.
  * `stark-poseidon` — transparent / post-quantum; reserved.
* §1.3 EPCIS extension: bidirectional mapping for `ObjectEvent`,
  `TransformationEvent`, `AggregationEvent` is implemented in
  `services/ghc_traceability/epcis.py`.
* §2.4 Curve binding: verifiers MUST refuse a proof artifact whose
  `ghc:scheme` tag does not match what their verifier expects.
* §3.3 Dissent encoding: federated verdicts MUST surface
  authority-level disagreement; verifiers MUST NOT silently reduce
  to a single value.

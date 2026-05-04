# GHC Protocol — v0.1 (Draft)

## 0. Overview

The **GHC Protocol** is an open, authority-parametric specification for
expressing, transmitting, and verifying halal compliance claims across
food, pharmaceutical, cosmetic, financial, and logistics domains.

This document is **non-normative** until tagged `v0.1.0`. It tracks the
six contributions defined in the GHC whitepaper and binds them to
on-the-wire data formats, schemas, and verification procedures.

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

Phase A bootstrap. **Do not implement against this draft.** The first
implementable release will be tagged `v0.1.0` after Phase F.

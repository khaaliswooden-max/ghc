---
name: Bug report
about: Something doesn't work the way the spec / docs say it should
title: "[bug] "
labels: bug
assignees: ''
---

## Subsystem

<!-- Pick one. Mirrors the labels in MAINTAINERS.md. -->

- [ ] `proofs/` (Lean kernel)
- [ ] `proofs-mathlib/` (mathlib extensions)
- [ ] `core/ghc-algebra`
- [ ] `core/ghc-graph`
- [ ] `core/ghc-zk` (Groth16 / Poseidon)
- [ ] `core/ghc-stark` (winterfell scaffold)
- [ ] `core/ghc-cli`
- [ ] `services/ghc_api`
- [ ] `services/ghc_ml`
- [ ] `services/ghc_traceability` (EPCIS)
- [ ] `integrations/certifiers`
- [ ] `integrations/dlt/evm` (Circom + Solidity)
- [ ] `integrations/dlt/fabric` (Go chaincode)
- [ ] `spec/`
- [ ] `paper/`
- [ ] Other (please describe)

## Version

* GHC version / tag / commit SHA:
* Rust toolchain (if relevant):
* Python version (if relevant):
* Go version (if relevant):
* Lean toolchain (if relevant):
* OS:

## What did you do?

<!-- Minimal reproducible steps. Paste commands you ran. -->

```
$ ...
```

## What did you expect?

<!-- Reference a spec section, a Lean theorem, a docs paragraph, or
     a test name where possible. -->

## What happened instead?

<!-- Paste output, stack traces, screenshots if a UI is involved. -->

```
...
```

## Is this a security issue?

If your report involves cryptographic soundness, attestation forgery,
supplier-privacy leaks, or any other vulnerability — **stop here**
and follow [`SECURITY.md`](../../SECURITY.md) instead. Do not file
this as a public bug report.

## Additional context

<!-- Anything else that helps the maintainers triage. -->

<!--
Thanks for the PR. The checklist below mirrors what CI enforces;
please tick the boxes that apply.

If your change touches `spec/`, also follow the 7-day public
discussion rule (see GOVERNANCE.md §"Spec changes"). PRs that
modify normative spec language MUST include a `spec/00-overview.md`
§0.7 changelog entry.

Security issues do NOT belong here — see SECURITY.md.
-->

## Summary

<!-- One short paragraph: what problem this PR solves and how. -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (bumps semver-major)
- [ ] Documentation only
- [ ] Spec / protocol change (requires 7-day public discussion)
- [ ] Theorem addition / proof discharge

## Subsystem labels

<!-- Pick what applies; mirrors MAINTAINERS.md. -->

- [ ] `proofs/` (Lean kernel)
- [ ] `proofs-mathlib/` (mathlib extensions)
- [ ] `core/` (Rust workspace)
- [ ] `services/` (Python / API / ML)
- [ ] `integrations/` (adapters, DLT)
- [ ] `spec/` (normative)
- [ ] `paper/` (whitepaper)
- [ ] `.github/` / repo hygiene

## Checklist

- [ ] I have signed off (`git commit -s`).
- [ ] `cargo fmt --check` + `cargo clippy --workspace --all-targets -- -D warnings` (if `core/` touched).
- [ ] `cargo test --workspace` green (if `core/` touched).
- [ ] `pytest` green in `services/` (if `services/` touched).
- [ ] `ruff check .` clean in `services/` (if `services/` touched).
- [ ] `go test ./...` green in `integrations/dlt/fabric/chaincode/` (if Fabric touched).
- [ ] `bash scripts/test.sh` green in `integrations/dlt/evm/` (if EVM touched).
- [ ] `lake build` green in `proofs/` (no new `sorry`s in kernel).
- [ ] `lake build` green in `proofs-mathlib/` (no new `sorry`s).
- [ ] `latexmk -pdf paper/main.tex` builds cleanly (if `paper/` touched).
- [ ] `CHANGELOG.md` updated under the next pending release.
- [ ] `spec/00-overview.md` §0.7 entry added (if `spec/` touched normatively).
- [ ] Theorem additions are `#check`'d in `proofs/Ghc/Smoke.lean`.
- [ ] Tests added or updated to cover the new behavior.

## How to verify

<!-- Reviewer-facing reproduction steps. The smaller the better. -->

```
$ ...
```

## Related issues / theorems / spec sections

<!-- Closes #N, references thm:X.Y, spec §A.B, etc. -->

## Out-of-scope follow-ups

<!-- Anything you noticed but explicitly chose not to address in
     this PR. -->

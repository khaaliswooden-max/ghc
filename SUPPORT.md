# Support

Where to take your question depends on what kind of question it is.

## "How do I use GHC?"

* **Quick start** — [`README.md`](README.md) "Getting started" runs
  every layer's tests + the zk-Halal demo in a few commands.
* **Protocol behavior** — [`spec/`](spec/) is the normative
  reference. Start with `spec/00-overview.md`.
* **API endpoints** — `services/ghc_api/app.py` is the source of
  truth; FastAPI auto-publishes an OpenAPI document at
  `/openapi.json` and a Swagger UI at `/docs` once the server is
  running.
* **CLI** — `cargo run -p ghc-cli -- --help` (subcommands:
  `closure`, `plurality`, `fingerprint`, `prove`, `verify`, `demo`).

## "Something doesn't work"

* First check [`docs/PLAN.md`](docs/PLAN.md) and
  [`CHANGELOG.md`](CHANGELOG.md) "Known gaps tracked for v0.2 / v0.3"
  — your symptom may be a documented limitation, not a bug.
* Then check existing issues:
  <https://github.com/khaaliswooden-max/ghc/issues>.
* If your case isn't covered, file a **Bug Report** using the
  template at `.github/ISSUE_TEMPLATE/bug_report.md`.

## "I think I found a security issue"

**Do not file a public issue.** See
[`SECURITY.md`](SECURITY.md) for the coordinated-disclosure process.
Cryptographic-soundness, attestation-forgery, and supplier-privacy
issues all go through the security alias.

## "I have a question about the math"

Lean kernel theorems live in `proofs/Ghc/`; mathlib extensions in
`proofs-mathlib/GhcMathlib/`. Each theorem in the whitepaper is
indexed in Appendix A to its Lean identifier. If you spot a gap
between the paper and the formalization (a `sorry`, an axiom, or a
proof that doesn't typecheck), file an issue tagged `proofs`.

## "I have a question about juristic interpretation"

GHC formalizes the *propagation* of compliance status — it does not
adjudicate juristic questions. The lattice is **authority-parametric**
by design: where authorities disagree, the protocol records the
disagreement faithfully (§3 of the spec).

* If you represent a Shariah authority and want your published
  position encoded as a `urn:ghc:authority:*` corpus, open an issue
  tagged `authority-binding`.
* If you want to discuss the *substance* of a juristic question, the
  Shariah scholarship and certification bodies are the right
  audience, not the GHC issue tracker.

## "I'd like to integrate GHC with my registry / system"

The integration scaffolds live at:

* `integrations/certifiers/base.py::HttpCertifierAdapter` — for
  HTTP-backed registries. Subclass and provide `_lookup_url`,
  `_search_url`, `_parse_record`.
* `integrations/dlt/evm/` — Circom + Solidity Groth16 verifier
  deployable to any EVM L2.
* `integrations/dlt/fabric/chaincode/` — Hyperledger Fabric (Go).
* `services/ghc_traceability/epcis.py` — bidirectional EPCIS 2.0 ↔
  GHC mapping.

For each, file an issue tagged `integration` describing the target
system and the desired contract.

## Real-time channels

There is no real-time channel (Slack, Discord, IRC) for GHC yet.
The maintainers will announce one when the project's
governance model is ratified (see
[GOVERNANCE.md](GOVERNANCE.md) v0.2 roadmap). Until then, the issue
tracker is the canonical surface.

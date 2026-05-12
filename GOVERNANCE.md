# GHC Governance

## Status

**v0.1.0 — interim, maintainer-led.** A formal multi-stakeholder
governance model is on the v0.2 roadmap (see below).
This document describes how decisions are made *today*; it will be
re-negotiated when the protocol reaches v0.2 and a steward
organization is named.

## Scope

GHC is three coupled artifacts under one roof:

1. **Whitepaper** (`paper/`) — academic monograph; changes follow
   research norms (cite, peer review, revise).
2. **Reference implementation** (`core/`, `services/`,
   `integrations/`, `proofs/`, `proofs-mathlib/`) — versioned OSS
   software; changes follow standard PR review.
3. **Open protocol** (`spec/`) — versioned standard; changes follow
   a public discussion period (below).

Different governance applies to each.

## Decision-making

### Reference implementation

* PRs are reviewed and merged by maintainers (see
  [MAINTAINERS.md](MAINTAINERS.md)).
* Single-maintainer approval suffices for non-breaking changes.
* Two-maintainer approval is required for:
  * Changes to cryptographic primitives or their parameters.
  * Changes to Lean theorems (kernel or mathlib track) — including
    adding or removing `sorry`s.
  * Changes to CI gating that would weaken the test bar.
  * Dependency bumps that cross a major version.

### Spec changes

Any change to `spec/` (Markdown or JSON Schema) follows a **public
discussion period of at least 7 days** before merge, regardless of
maintainer count. The intent is to let downstream implementers
object before the change ships.

* **Editorial** changes (typos, formatting, clarifying prose that
  does not alter normative meaning) bypass the discussion period
  and are merged at maintainer discretion. The PR title prefix
  `spec(editorial):` declares the intent; maintainers may revert
  the prefix and re-open the discussion period if the change is
  judged non-editorial.
* **Normative** changes (scheme tags, verifier behavior,
  data-model semantics) MUST update the §0.7 spec changelog,
  update affected JSON Schemas, and update `CHANGELOG.md`.

### Whitepaper

Substantive changes (new theorems, modified claims, revised
formalization) go through standard PR review and, when a theorem
is involved, require corresponding Lean updates. The whitepaper's
abstract and §1 (Introduction) are stable — changes to those go
through a 14-day discussion period.

## Authority model

GHC's compliance lattice is *authority-parametric*. The project
does not bless any single Shariah authority as canonical. Decisions
about *which authorities the reference registry binds* are made by
the maintainers with input from open issues tagged
`authority-binding`. The protocol itself supports arbitrary
authorities; the v0.1 reference set is a starting point, not a
limit.

When two authorities disagree, the spec REQUIRES verifiers to
surface the disagreement (§3.3 dissent encoding). GHC does not
pick a winner.

## Maintainer addition / removal

* New maintainers are nominated by an existing maintainer in a
  public issue tagged `maintainer-nomination`, with a 14-day
  comment period.
* Two existing maintainers must concur; objections from any
  existing maintainer block addition.
* Maintainers may step down at any time by opening a PR removing
  themselves from [MAINTAINERS.md](MAINTAINERS.md).
* Inactive maintainers (no merges or reviews in 6 months) may be
  moved to "emeritus" status by a 2/3 vote of active maintainers.

## Release authority

Tagging a release (`vX.Y.Z`) requires:

* CI green on `main`.
* `CHANGELOG.md` updated.
* Two-maintainer concurrence on the release notes.

## v0.2 roadmap for governance

When v0.2 ships, the interim model is expected to be replaced by:

1. **Steward organization** — a non-profit foundation or
   consortium that holds the project's domain, signing keys, and
   ceremony outputs. Candidates: a new GHC Foundation; a working
   group under an existing OSS foundation (Apache, Hyperledger,
   IETF); a working group under OIC/SMIIC.
2. **Technical Steering Committee** with seats for: software
   maintainers, formal-methods reviewers, recognized Shariah
   authorities (federated, multi-authority), and downstream
   implementers (certifiers, retailers, regulators).
3. **Trusted-setup ceremony** governance: who runs it, who audits,
   how participants are chosen, how ceremony outputs are
   distributed.
4. **Dispute resolution** between authorities encoded in the
   protocol's federated lattice.

Issues tagged `governance` track the design conversation.

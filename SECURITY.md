# Security Policy

GHC ships cryptographic primitives (Groth16 zk-SNARKs over BLS12-381
and BN254, Poseidon binding commitments, a STARK scaffold over the
Goldilocks field), an authority-attestation chaincode, and an
API gateway that brokers traceability data. A vulnerability in any
of these layers can lead to forged compliance attestations or
inappropriate disclosure of supplier information. We take security
reports seriously.

## Supported versions

| Version | Supported |
|---------|-----------|
| v0.1.x  | ✅ |
| < v0.1  | ❌ pre-release; no security guarantees |

## Reporting a vulnerability

**Please do not file public issues for security reports.** Public
issue threads expose the vulnerability before users can patch.

Email: **security@ghc.example** (replace with the project's real
disclosure address once a foundation/consortium is named — see
[GOVERNANCE.md](GOVERNANCE.md) v0.2 roadmap). Until then, encrypt
disclosures with the maintainer GPG keys listed in
[MAINTAINERS.md](MAINTAINERS.md) and send to the maintainers
directly.

Include:

1. A description of the vulnerability and the component affected
   (`ghc-zk`, `ghc-stark`, `ghc_api`, chaincode, etc.).
2. Steps to reproduce, including any required configuration.
3. Impact assessment (forgery, info leak, DoS, …).
4. Suggested remediation, if any.
5. Whether you intend to publish details, and your preferred
   disclosure timeline.

## Response timeline

| Step | Target |
|------|--------|
| Acknowledge receipt | within **48 hours** |
| Triage + severity assessment | within **7 days** |
| Patch / mitigation in private branch | within **30 days** for high-severity, **90 days** for low |
| Coordinated disclosure | by mutual agreement, typically no later than **90 days** after the initial report |

## Scope

In scope:

* Cryptographic soundness of the zk-Halal Groth16 / STARK pipelines
  and their parameters.
* Constraint-system completeness or soundness bugs that would let a
  hostile prover produce a passing proof for a non-compliant
  witness, or that would let a hostile verifier reject a compliant
  proof.
* Poseidon parameter weaknesses or hash collisions in our chosen
  parameter set.
* Chaincode logic errors that would let a non-issuer mint an
  attestation, or that would corrupt the ledger.
* API gateway vulnerabilities (auth bypass, SQL/JSON-LD injection,
  DoS).
* Spec ambiguities that would let two conformant implementations
  disagree on whether a proof verifies.
* Build-supply-chain compromise (dependency confusion, typosquatting
  on a published artifact name).

Out of scope:

* Findings that depend on the prover being honest (the prover has
  the witness — the proof binds them to it; "the prover knows the
  data" is not a vulnerability).
* Issues in the upstream `vendor/` submodules (report those upstream
  to `karpathy/minGPT`, `karpathy/nanoGPT`, `karpathy/build-nanogpt`).
* Issues in third-party certifier registries; report to the registry
  operator.
* Juristic disagreements about lattice classification of specific
  ingredients (route via the standards process, not security).

## Cryptographic-parameter caveats

The Poseidon parameter set used by `ghc-zk` is the documented
`bls381-fr` research set from `ark-crypto-primitives`. **v0.1 ships
without a multi-party trusted-setup ceremony**; v0.2 freezes
parameters from a real ceremony. Use of v0.1 in adversarial
deployments without an out-of-band ceremony is at your own risk and
is *not* considered a vulnerability of this codebase — it is a
known limitation tracked in
[`docs/PLAN.md`](docs/PLAN.md) and in [`CHANGELOG.md`](CHANGELOG.md)
"Known gaps tracked for v0.2 / v0.3".

The STARK round trip (`ghc-stark`) is currently `#[ignore]`'d; do not
rely on it for production attestation until the v0.2 AIR fix lands.

## Embargo and credit

We follow coordinated disclosure. Reporters who follow this policy:

* Are credited by name (or pseudonym, on request) in the patch's
  commit message, the next `CHANGELOG.md` entry, and any associated
  CVE.
* May request a private patch preview to verify the fix.
* Are not subject to legal action by the project so long as reports
  are in good faith and not used to harm users.

## Non-security conduct reports

For Code-of-Conduct violations, use the address in
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), not the security alias.

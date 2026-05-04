# GHC Protocol — §2 Attestation

## 2.1 The zk-Halal credential

A **zk-Halal credential** is a W3C Verifiable Credential whose
`credentialSubject` carries a zero-knowledge proof attesting that the
issuer's compliant provenance witness commits to compliance lattice
$\geq$ ḥalāl, **without revealing** the witness.

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://ghc.example/ns/v1"
  ],
  "type": ["VerifiableCredential", "ghc:HalalAttestation"],
  "issuer": "did:web:halal.gov.my",
  "validFrom": "2026-05-04T00:00:00Z",
  "credentialSubject": {
    "id": "urn:ghc:product:0123...",
    "ghc:lattice": "halal",
    "ghc:scheme": "groth16-bls12-381-poseidon",
    "ghc:circuit": "ghc-halal-v1",
    "ghc:commitment": "0xabc1...",
    "ghc:proof": "0x9def..."
  },
  "proof": { "...": "Ed25519Signature2020 over the VC envelope" }
}
```

The `ghc:commitment` is a single BLS12-381 `Fr` element — the output
of a Poseidon sponge (width 3, rate 2, capacity 1, `α = 17`, 8 full
rounds, 29 partial rounds) absorbing the salt followed by the
per-step verdict field elements. The native and in-circuit hashers
are byte-identical (enforced by the `native_and_circuit_poseidon_agree`
test in `core/ghc-zk`), so a verifier can independently recompute the
commitment from any disclosed witness.

## 2.2 Verifier protocol

1. Resolve the issuer DID and fetch the public key.
2. Verify the outer Ed25519 signature on the VC envelope.
3. Look up `ghc:circuit` in the GHC circuit registry; fetch the
   verification key.
4. Run the SNARK verifier (`ghc-zk` library) with public input
   `ghc:commitment` and proof `ghc:proof`.
5. Optionally cross-check that `ghc:commitment` appears in the
   anchored DLT root for the issuer (L4 conformance).

## 2.3 Supported schemes

- **`groth16-bls12-381-poseidon`** (default for v0.1) — Groth16 over
  BLS12-381 with a Poseidon binding commitment; smallest proofs
  (192 bytes), per-circuit trusted setup. **Implemented in
  `core/ghc-zk` as of v0.0.x.**
- **`plonk-bn254-poseidon`** — universal trusted setup; planned for
  v0.1.
- **`stark-poseidon`** — transparent / post-quantum; planned for v0.2.

## 2.4 Privacy guarantees

A zk-Halal credential reveals only:

- the issuer's DID and timestamp;
- the compliance lattice level claimed;
- a binding commitment to (provenance DAG, weights, labels);
- the SNARK proof.

It **does not** reveal supplier identities, recipes, batch IDs, audit
logs, or the structure of the upstream supply chain. Indistinguishability
is formalized in §7 of the whitepaper.

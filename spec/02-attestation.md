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
    "ghc:scheme": "groth16-bls12-381",
    "ghc:circuit": "ghc-halal-v1",
    "ghc:commitment": "0xabc1...",
    "ghc:proof": "0x9def..."
  },
  "proof": { "...": "Ed25519Signature2020 over the VC envelope" }
}
```

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

- **`groth16-bls12-381`** (default for v0.1) — smallest proofs,
  per-circuit trusted setup.
- **`plonk-bn254`** — universal trusted setup.
- **`stark-poseidon`** (planned v0.2) — transparent / post-quantum.

## 2.4 Privacy guarantees

A zk-Halal credential reveals only:

- the issuer's DID and timestamp;
- the compliance lattice level claimed;
- a binding commitment to (provenance DAG, weights, labels);
- the SNARK proof.

It **does not** reveal supplier identities, recipes, batch IDs, audit
logs, or the structure of the upstream supply chain. Indistinguishability
is formalized in §7 of the whitepaper.

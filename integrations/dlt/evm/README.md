# GHC EVM Verifier (Phase C+2)

Circom port of the Rust `HalalThresholdCircuit`, plus a snarkjs-generated
Groth16 verifier deployable to any EVM L2.

## What's here

```
circuits/
  halal_threshold.circom    parametric template (N steps, T threshold)
  halal_n3.circom            concrete instantiation: N=3, T=halal-only
contracts/
  halal_n3_Verifier.sol      auto-generated Solidity Groth16 verifier
scripts/
  build.sh                   compile + setup + export verifier
  prove_and_verify.sh        end-to-end prove + verify with snarkjs
  test.sh                    asserts halal-only succeeds and haram fails
build/
  <circuit>/                 build outputs (.r1cs, .wasm, .zkey, etc.)
```

## Curve and trust model

This pipeline targets **BN254 (alt_bn128)** — the curve with native EVM
precompiles at `0x06` / `0x07` / `0x08`, the only ZK-pairing curve
universally available on Ethereum mainnet and most L2s.  The off-chain
Rust pipeline (`core/ghc-zk`) lives over **BLS12-381** for smaller
proofs and faster verification.  The two pipelines prove the **same
statement** (per-step verdicts ≤ threshold, committed via Poseidon)
on parallel curves; they produce **independent proof artifacts**.
v0.1 will document a binding scheme mapping that lets clients choose
which pipeline a given attestation is bound to.

The Poseidon parameters are **`circomlib`'s default BN254 set**, which
is the de-facto industry standard for ZK rollups (Tornado Cash, ZK-EVM
projects, Ethereum L2 verifiers).  The powers-of-tau ceremony output
produced by `build.sh` is a **local single-party ceremony** suitable
for v0.0.x research-grade use; v0.1 will pin a real multi-party
ceremony output (e.g. Hermez `pot28`).

## Build

```bash
npm install                # circomlib + snarkjs + circomlibjs
bash scripts/build.sh halal_n3
```

Outputs (under `build/halal_n3/`):

- `halal_n3.r1cs` — R1CS constraint system
- `halal_n3_js/halal_n3.wasm` — witness generator
- `halal_n3_final.zkey` — Groth16 proving key
- `halal_n3_vkey.json` — verification key
- `contracts/halal_n3_Verifier.sol` — Solidity verifier

## Prove + verify (off-chain test)

```bash
bash scripts/prove_and_verify.sh halal_n3 0,0,0 42        # halal-only — accepted
bash scripts/prove_and_verify.sh halal_n3 0,2,0 42        # haram — REJECTED at witness gen
```

Run the full assertion suite:

```bash
bash scripts/test.sh
```

## Deploy on-chain

```solidity
// Pseudocode for deploying the verifier and gating an attestation:
import "./halal_n3_Verifier.sol";

contract GhcAttestationRegistry {
    Groth16Verifier_halal_n3 public verifier;

    function attest(
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[1] calldata pubSignals  // [commitment]
    ) external {
        require(verifier.verifyProof(a, b, c, pubSignals), "invalid proof");
        // ... record commitment, emit event ...
    }
}
```

The Solidity calldata for an off-chain proof is produced by
`prove_and_verify.sh` (last line of output).

## CI

The `evm` CI job builds the circuit, runs `scripts/test.sh`, and gates
on the auto-generated Solidity verifier compiling cleanly via
`solcjs`. It runs only when `circom` is available; otherwise it is
skipped with a notice.

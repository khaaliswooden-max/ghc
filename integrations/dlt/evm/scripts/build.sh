#!/usr/bin/env bash
# build.sh — compile the Circom circuit, run a test trusted-setup
# ceremony (using snarkjs's powersOfTau28 ceremony output), generate
# the Groth16 proving / verifying keys, and emit the Solidity verifier.
#
# Usage:  bash scripts/build.sh <circuit_basename>
# Example: bash scripts/build.sh halal_n3
#
# The output directory is `build/<circuit>/`.
#
# This script is fully reproducible from a clean checkout:
#   1. `npm install`               (fetches circomlib, snarkjs)
#   2. `bash scripts/build.sh halal_n3`
#   3. `bash scripts/prove_and_verify.sh halal_n3 0,0,0 42`
#
# Trust model: the powers-of-tau (`pot`) file produced here is from a
# local single-party ceremony, suitable for v0.0.x research-grade use.
# v0.1 will swap in a real multi-party ceremony output (e.g. Hermez
# powersOfTau28).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CIRCUIT="${1:-halal_n3}"
OUT="build/${CIRCUIT}"
mkdir -p "$OUT"

PTAU="$OUT/pot12.ptau"

echo "==[ 1/6 ] compiling Circom circuit..."
circom "circuits/${CIRCUIT}.circom" \
  --r1cs --wasm --sym \
  -o "$OUT" \
  -l node_modules

echo "==[ 2/6 ] preparing powers-of-tau (research single-party)..."
if [ ! -f "$PTAU" ]; then
  npx snarkjs powersoftau new bn128 12 "$OUT/pot12_0000.ptau" -v
  npx snarkjs powersoftau contribute "$OUT/pot12_0000.ptau" "$OUT/pot12_0001.ptau" \
    --name="ghc-research-ceremony" -v -e="ghc dev entropy"
  npx snarkjs powersoftau prepare phase2 "$OUT/pot12_0001.ptau" "$PTAU" -v
fi

echo "==[ 3/6 ] generating zkey (groth16 setup)..."
npx snarkjs groth16 setup "$OUT/${CIRCUIT}.r1cs" "$PTAU" "$OUT/${CIRCUIT}_0000.zkey"
npx snarkjs zkey contribute "$OUT/${CIRCUIT}_0000.zkey" "$OUT/${CIRCUIT}_final.zkey" \
  --name="ghc-zkey-ceremony" -v -e="ghc zkey entropy"

echo "==[ 4/6 ] exporting verification key..."
npx snarkjs zkey export verificationkey "$OUT/${CIRCUIT}_final.zkey" \
  "$OUT/${CIRCUIT}_vkey.json"

echo "==[ 5/6 ] exporting Solidity verifier..."
npx snarkjs zkey export solidityverifier "$OUT/${CIRCUIT}_final.zkey" \
  "$OUT/${CIRCUIT}_verifier.sol"

# Copy a stable name into contracts/ so consumers can `import` it.
cp "$OUT/${CIRCUIT}_verifier.sol" "contracts/${CIRCUIT}_Verifier.sol"
sed -i "s/contract Groth16Verifier/contract Groth16Verifier_${CIRCUIT}/" \
  "contracts/${CIRCUIT}_Verifier.sol"

echo "==[ 6/6 ] done."
echo "  r1cs:       $OUT/${CIRCUIT}.r1cs"
echo "  wasm:       $OUT/${CIRCUIT}_js/${CIRCUIT}.wasm"
echo "  zkey:       $OUT/${CIRCUIT}_final.zkey"
echo "  vkey:       $OUT/${CIRCUIT}_vkey.json"
echo "  verifier:   contracts/${CIRCUIT}_Verifier.sol"

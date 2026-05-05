#!/usr/bin/env bash
# test.sh — end-to-end EVM-side tests:
#   1. Halal-only witness produces a verifiable Groth16 proof.
#   2. Haram witness is rejected at witness generation.
#   3. Solidity calldata can be exported.
#
# Run from the integrations/dlt/evm directory after `bash scripts/build.sh halal_n3`.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CIRCUIT="halal_n3"
OUT="build/${CIRCUIT}"

# Test 1: halal-only succeeds.
echo "==[ test 1 ] halal-only proof + verify..."
if ! bash scripts/prove_and_verify.sh "$CIRCUIT" 0,0,0 42 > "$OUT/test1.log" 2>&1; then
  cat "$OUT/test1.log"
  echo "FAIL: halal-only round trip"; exit 1
fi
grep -q "OK!" "$OUT/test1.log" || { echo "FAIL: snarkjs did not say OK!"; exit 1; }
echo "  PASS"

# Test 2: haram is rejected at witness generation.
echo "==[ test 2 ] haram witness should be rejected..."
if bash scripts/prove_and_verify.sh "$CIRCUIT" 0,2,0 7 > "$OUT/test2.log" 2>&1; then
  echo "FAIL: haram witness was accepted"; exit 1
fi
grep -q "Assert Failed" "$OUT/test2.log" || { echo "FAIL: unexpected error"; cat "$OUT/test2.log"; exit 1; }
echo "  PASS"

# Test 3: Solidity calldata is non-empty.
echo "==[ test 3 ] Solidity calldata export..."
bash scripts/prove_and_verify.sh "$CIRCUIT" 0,0,0 99 > "$OUT/test3.log" 2>&1
grep -qE '\[\["0x[0-9a-f]+' "$OUT/test3.log" || { echo "FAIL: no calldata"; exit 1; }
echo "  PASS"

echo
echo "==[ all EVM-side tests passed ]=="

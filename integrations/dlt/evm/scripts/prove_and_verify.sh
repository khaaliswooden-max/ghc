#!/usr/bin/env bash
# prove_and_verify.sh — generate a witness, produce a Groth16 proof,
# and verify it via snarkjs. The Poseidon commitment `c` is computed
# inside the circuit and exposed as a public output, so the input.json
# only carries the private witness.
#
# Usage:
#   bash scripts/prove_and_verify.sh <circuit> <verdicts_csv> <salt>
#
# Example:
#   bash scripts/prove_and_verify.sh halal_n3 0,0,0 42
#
# A non-zero verdict (1=mashbuh, 2=haram) violates the halal-only
# threshold and must cause witness generation or proving to fail.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CIRCUIT="${1:-halal_n3}"
VERDICTS_CSV="${2:-0,0,0}"
SALT="${3:-42}"

OUT="build/${CIRCUIT}"
JSDIR="$OUT/${CIRCUIT}_js"

# Build input.json: private witness only (c is a circuit output).
python3 - "$VERDICTS_CSV" "$SALT" > "$OUT/input.json" <<'PY'
import json, sys
verdicts = [int(x) for x in sys.argv[1].split(",") if x != ""]
print(json.dumps({"salt": int(sys.argv[2]), "w": verdicts}))
PY

GEN="$JSDIR/generate_witness.js"
WASM="$JSDIR/${CIRCUIT}.wasm"

echo "==[ 1/3 ] generating witness..."
node "$GEN" "$WASM" "$OUT/input.json" "$OUT/witness.wtns"

echo "==[ 2/3 ] proving (Groth16)..."
npx snarkjs groth16 prove \
  "$OUT/${CIRCUIT}_final.zkey" \
  "$OUT/witness.wtns" \
  "$OUT/proof.json" \
  "$OUT/public.json"

C=$(python3 -c "import json; print(json.load(open('$OUT/public.json'))[0])")
echo "    commitment c = $C"

echo "==[ 3/3 ] verifying..."
npx snarkjs groth16 verify \
  "$OUT/${CIRCUIT}_vkey.json" \
  "$OUT/public.json" \
  "$OUT/proof.json"

echo
echo "==[ Solidity calldata ]=="
npx snarkjs zkey export soliditycalldata \
  "$OUT/public.json" "$OUT/proof.json"

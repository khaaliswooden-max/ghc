pragma circom 2.1.9;

include "../node_modules/circomlib/circuits/poseidon.circom";

/*
 * HalalThreshold(N, T) — Circom port of the Rust ghc-zk circuit.
 *
 * Public input:
 *   c: Poseidon(salt, w[0], ..., w[N-1])
 *
 * Private inputs:
 *   w[0..N-1]: per-step verdict (0=halal, 1=mashbuh, 2=haram)
 *   salt:      anti-enumeration nonce
 *
 * Constraints:
 *   1. Domain check: each w[i] ∈ {0, 1, 2}.
 *   2. Threshold:
 *        T == 0 (halal)   => each w[i] == 0
 *        T == 1 (mashbuh) => each w[i] ∈ {0, 1}
 *   3. Commitment: Poseidon(salt, w[0], ..., w[N-1]) == c.
 *
 * Curve: BN254 (alt_bn128). Compatible with the Ethereum precompile
 * at 0x06/0x07/0x08 and with snarkjs Groth16. The off-chain
 * arkworks pipeline (`core/ghc-zk`) lives over BLS12-381 and produces
 * a different proof artifact — both pipelines prove the same
 * statement on parallel curves; v0.1 will document a binding scheme
 * mapping that allows clients to choose which artifact they accept.
 */
template HalalThreshold(N, T) {
    signal output c;
    signal input salt;
    signal input w[N];

    // Intermediate signals must be declared at template scope.
    signal d_a[N];
    signal d_b[N];
    signal t_a[N];

    // 1. Domain check: w[i] * (w[i]-1) * (w[i]-2) === 0.
    var i;
    for (i = 0; i < N; i++) {
        d_a[i] <== w[i] * (w[i] - 1);
        d_b[i] <== d_a[i] * (w[i] - 2);
        d_b[i] === 0;
    }

    // 2. Threshold.
    if (T == 0) {
        for (i = 0; i < N; i++) {
            w[i] === 0;
            // unused t_a still needs an assignment to be valid Circom.
            t_a[i] <== 0;
        }
    } else {
        for (i = 0; i < N; i++) {
            t_a[i] <== w[i] * (w[i] - 1);
            t_a[i] === 0;
        }
    }

    // 3. Poseidon commitment over (salt ‖ w). The output `c` is a
    // public output of the circuit (i.e. part of the public input
    // vector that the verifier checks).
    component hasher = Poseidon(N + 1);
    hasher.inputs[0] <== salt;
    for (i = 0; i < N; i++) {
        hasher.inputs[i + 1] <== w[i];
    }
    c <== hasher.out;
}

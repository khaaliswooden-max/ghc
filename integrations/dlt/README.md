# DLT Anchoring

Two reference deployments are tracked:

1. **EVM L2 verifier contract** (`evm/`) — open / consumer-facing
   deployments. **Implemented as of v0.0.x:** Circom port of the
   `ghc-zk` `HalalThresholdCircuit` over BN254 (alt_bn128), snarkjs
   Groth16 setup, auto-generated Solidity verifier, end-to-end
   assertion suite. See `evm/README.md`.

2. **Hyperledger Fabric chaincode** (`fabric/`) — consortium
   deployments where authorities run validating peers. Phase D
   target.

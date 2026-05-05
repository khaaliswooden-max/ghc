// Package main implements the GHC Hyperledger Fabric chaincode for
// anchoring zk-Halal attestations to a consortium ledger.
//
// The chaincode stores immutable records keyed by the binding
// commitment (a single field element from the ZK pipeline). Each
// record carries the issuer DID, the curve+hash+system scheme tag
// (e.g. "groth16-bls12-381-poseidon" or "groth16-bn254-poseidon"),
// and a wall-clock timestamp.
//
// Verification of the underlying SNARK proof is performed off-chain
// before the call (the off-chain verifier produces a Boolean
// `proofValid` that is asserted by the issuer's public key
// signature on the {commitment, scheme, issuer} tuple). v0.1 will
// add an on-chain Groth16 verifier for the BN254 scheme using
// fabric's chaincode interop with a verifier package.
package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// Attestation is the on-ledger record.
type Attestation struct {
	Commitment string `json:"commitment"`         // hex-encoded field element
	Scheme     string `json:"scheme"`             // e.g. "groth16-bls12-381-poseidon"
	Issuer     string `json:"issuer"`             // issuer DID
	Subject    string `json:"subject"`            // GHC subject URN
	Lattice    string `json:"lattice"`            // "halal" | "mashbuh" | "haram"
	Timestamp  string `json:"timestamp"`          // RFC 3339
	ProofRef   string `json:"proofRef,omitempty"` // optional off-chain pointer
}

// SmartContract is the Fabric contract entrypoint.
type SmartContract struct {
	contractapi.Contract
}

// validSchemes is the closed set of recognized ZK schemes per
// `spec/02-attestation.md` §2.3.
var validSchemes = map[string]struct{}{
	"groth16-bls12-381-poseidon": {},
	"groth16-bn254-poseidon":     {},
	"plonk-bn254-poseidon":       {},
	"stark-poseidon":             {},
}

// validLattice is the verdict alphabet (§3 of the spec).
var validLattice = map[string]struct{}{
	"halal":   {},
	"mashbuh": {},
	"haram":   {},
}

// Attest stores a new attestation. Fails if the commitment already
// exists or if any field fails validation.
func (s *SmartContract) Attest(
	ctx contractapi.TransactionContextInterface,
	commitment string,
	scheme string,
	issuer string,
	subject string,
	lattice string,
	timestamp string,
	proofRef string,
) error {
	if err := validate(commitment, scheme, issuer, subject, lattice, timestamp); err != nil {
		return err
	}
	exists, err := s.Exists(ctx, commitment)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("commitment already attested: %s", commitment)
	}
	att := Attestation{
		Commitment: commitment,
		Scheme:     scheme,
		Issuer:     issuer,
		Subject:    subject,
		Lattice:    lattice,
		Timestamp:  timestamp,
		ProofRef:   proofRef,
	}
	bytes, err := json.Marshal(att)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(commitment, bytes)
}

// Get returns the attestation associated with a commitment.
func (s *SmartContract) Get(
	ctx contractapi.TransactionContextInterface,
	commitment string,
) (*Attestation, error) {
	bytes, err := ctx.GetStub().GetState(commitment)
	if err != nil {
		return nil, fmt.Errorf("read state: %w", err)
	}
	if bytes == nil {
		return nil, fmt.Errorf("no attestation for commitment %s", commitment)
	}
	var att Attestation
	if err := json.Unmarshal(bytes, &att); err != nil {
		return nil, err
	}
	return &att, nil
}

// Exists reports whether a commitment has already been attested.
func (s *SmartContract) Exists(
	ctx contractapi.TransactionContextInterface,
	commitment string,
) (bool, error) {
	bytes, err := ctx.GetStub().GetState(commitment)
	if err != nil {
		return false, err
	}
	return bytes != nil, nil
}

// ListByIssuer returns every attestation issued by a given DID. v0.0.x
// scans the full state; v0.1 uses CouchDB indexes for efficiency.
func (s *SmartContract) ListByIssuer(
	ctx contractapi.TransactionContextInterface,
	issuer string,
) ([]*Attestation, error) {
	iter, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer iter.Close()
	out := make([]*Attestation, 0)
	for iter.HasNext() {
		kv, err := iter.Next()
		if err != nil {
			return nil, err
		}
		var att Attestation
		if err := json.Unmarshal(kv.Value, &att); err != nil {
			continue
		}
		if att.Issuer == issuer {
			out = append(out, &att)
		}
	}
	return out, nil
}

func validate(commitment, scheme, issuer, subject, lattice, timestamp string) error {
	if !strings.HasPrefix(commitment, "0x") || len(commitment) < 4 {
		return fmt.Errorf("commitment must be a 0x-hex field element")
	}
	for _, c := range commitment[2:] {
		if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f' || c >= 'A' && c <= 'F') {
			return fmt.Errorf("commitment contains non-hex character: %q", c)
		}
	}
	if _, ok := validSchemes[scheme]; !ok {
		return fmt.Errorf("unrecognized scheme: %s", scheme)
	}
	if !strings.HasPrefix(issuer, "did:") {
		return fmt.Errorf("issuer must be a DID")
	}
	if !strings.HasPrefix(subject, "urn:ghc:") {
		return fmt.Errorf("subject must be a urn:ghc URN")
	}
	if _, ok := validLattice[lattice]; !ok {
		return fmt.Errorf("unrecognized lattice: %s", lattice)
	}
	if _, err := time.Parse(time.RFC3339, timestamp); err != nil {
		return fmt.Errorf("timestamp must be RFC 3339: %w", err)
	}
	return nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		panic(fmt.Sprintf("error creating chaincode: %v", err))
	}
	if err := chaincode.Start(); err != nil {
		panic(fmt.Sprintf("error starting chaincode: %v", err))
	}
}

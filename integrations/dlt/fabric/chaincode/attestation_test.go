package main

import (
	"encoding/json"
	"errors"
	"testing"
)

// fakeStub is a minimal in-memory KV store that satisfies the parts of
// shim.ChaincodeStubInterface our chaincode actually uses. We avoid
// pulling in the real fabric-shim test harness so `go test` runs in
// CI without external dependencies beyond fabric-contract-api.
type fakeStub struct {
	store map[string][]byte
}

func newFakeStub() *fakeStub { return &fakeStub{store: map[string][]byte{}} }

func (f *fakeStub) GetState(key string) ([]byte, error)        { return f.store[key], nil }
func (f *fakeStub) PutState(key string, value []byte) error    { f.store[key] = value; return nil }
func (f *fakeStub) DelState(key string) error                  { delete(f.store, key); return nil }
func (f *fakeStub) GetStateByRange(s, e string) (rangeIter, error) {
	keys := make([]string, 0, len(f.store))
	for k := range f.store {
		if (s == "" || k >= s) && (e == "" || k < e) {
			keys = append(keys, k)
		}
	}
	return &fakeIter{store: f.store, keys: keys}, nil
}

type rangeIter interface {
	HasNext() bool
	Next() (kv, error)
	Close() error
}

type kv struct {
	Key   string
	Value []byte
}

type fakeIter struct {
	store map[string][]byte
	keys  []string
	i     int
}

func (it *fakeIter) HasNext() bool { return it.i < len(it.keys) }
func (it *fakeIter) Next() (kv, error) {
	if it.i >= len(it.keys) {
		return kv{}, errors.New("end")
	}
	k := it.keys[it.i]
	it.i++
	return kv{Key: k, Value: it.store[k]}, nil
}
func (it *fakeIter) Close() error { return nil }

// We exercise the contract's pure-Go logic directly (without going
// through contractapi's reflection machinery) by re-implementing a
// thin wrapper that calls the same `validate` function and KV ops.

type localContract struct{ stub *fakeStub }

func (c *localContract) Attest(commitment, scheme, issuer, subject, lattice, ts, ref string) error {
	if err := validate(commitment, scheme, issuer, subject, lattice, ts); err != nil {
		return err
	}
	if existing, _ := c.stub.GetState(commitment); existing != nil {
		return errors.New("commitment already attested")
	}
	att := Attestation{
		Commitment: commitment,
		Scheme:     scheme,
		Issuer:     issuer,
		Subject:    subject,
		Lattice:    lattice,
		Timestamp:  ts,
		ProofRef:   ref,
	}
	b, _ := json.Marshal(att)
	return c.stub.PutState(commitment, b)
}

func (c *localContract) Get(commitment string) (*Attestation, error) {
	b, _ := c.stub.GetState(commitment)
	if b == nil {
		return nil, errors.New("not found")
	}
	var att Attestation
	_ = json.Unmarshal(b, &att)
	return &att, nil
}

// Tests --------------------------------------------------------------------

func TestAttest_Roundtrip(t *testing.T) {
	c := &localContract{stub: newFakeStub()}
	err := c.Attest(
		"0xc0ffee",
		"groth16-bls12-381-poseidon",
		"did:web:halal.gov.my",
		"urn:ghc:product:beef-shoulder-batch-7c1a",
		"halal",
		"2026-05-04T12:00:00Z",
		"",
	)
	if err != nil {
		t.Fatalf("attest: %v", err)
	}
	got, err := c.Get("0xc0ffee")
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	if got.Lattice != "halal" {
		t.Fatalf("expected halal, got %s", got.Lattice)
	}
}

func TestAttest_RejectsDuplicate(t *testing.T) {
	c := &localContract{stub: newFakeStub()}
	args := []string{
		"0xdeadbeef",
		"groth16-bn254-poseidon",
		"did:web:hfa.uk",
		"urn:ghc:product:lamb-leg-batch-8e22",
		"halal",
		"2026-05-04T12:00:00Z",
		"",
	}
	if err := c.Attest(args[0], args[1], args[2], args[3], args[4], args[5], args[6]); err != nil {
		t.Fatalf("first attest: %v", err)
	}
	if err := c.Attest(args[0], args[1], args[2], args[3], args[4], args[5], args[6]); err == nil {
		t.Fatalf("expected duplicate to be rejected")
	}
}

func TestValidate_RejectsBadCommitment(t *testing.T) {
	if err := validate("nope", "groth16-bn254-poseidon", "did:web:x", "urn:ghc:p:y", "halal", "2026-05-04T12:00:00Z"); err == nil {
		t.Fatal("expected non-hex commitment to be rejected")
	}
	if err := validate("0xZZZ", "groth16-bn254-poseidon", "did:web:x", "urn:ghc:p:y", "halal", "2026-05-04T12:00:00Z"); err == nil {
		t.Fatal("expected bad-hex commitment to be rejected")
	}
}

func TestValidate_RejectsUnknownScheme(t *testing.T) {
	if err := validate("0xab", "rsa", "did:web:x", "urn:ghc:p:y", "halal", "2026-05-04T12:00:00Z"); err == nil {
		t.Fatal("expected unknown scheme to be rejected")
	}
}

func TestValidate_RejectsBadIssuer(t *testing.T) {
	if err := validate("0xab", "groth16-bn254-poseidon", "https://halal.gov.my", "urn:ghc:p:y", "halal", "2026-05-04T12:00:00Z"); err == nil {
		t.Fatal("expected non-DID issuer to be rejected")
	}
}

func TestValidate_RejectsBadSubject(t *testing.T) {
	if err := validate("0xab", "groth16-bn254-poseidon", "did:web:x", "https://example.com/product", "halal", "2026-05-04T12:00:00Z"); err == nil {
		t.Fatal("expected non-urn:ghc subject to be rejected")
	}
}

func TestValidate_RejectsBadLattice(t *testing.T) {
	if err := validate("0xab", "groth16-bn254-poseidon", "did:web:x", "urn:ghc:p:y", "ambiguous", "2026-05-04T12:00:00Z"); err == nil {
		t.Fatal("expected unknown lattice to be rejected")
	}
}

func TestValidate_RejectsBadTimestamp(t *testing.T) {
	if err := validate("0xab", "groth16-bn254-poseidon", "did:web:x", "urn:ghc:p:y", "halal", "yesterday"); err == nil {
		t.Fatal("expected non-RFC3339 timestamp to be rejected")
	}
}

func TestValidate_AcceptsAllSchemeTags(t *testing.T) {
	for _, s := range []string{
		"groth16-bls12-381-poseidon",
		"groth16-bn254-poseidon",
		"plonk-bn254-poseidon",
		"stark-poseidon",
	} {
		if err := validate("0xab", s, "did:web:x", "urn:ghc:p:y", "halal", "2026-05-04T12:00:00Z"); err != nil {
			t.Fatalf("expected scheme %s to be accepted, got %v", s, err)
		}
	}
}

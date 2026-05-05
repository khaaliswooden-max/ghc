# GHC Protocol — §1 Data Model

## 1.1 Foundations

The GHC data model is a profile of:

- **W3C PROV-O** — for the entity / activity / agent vocabulary;
- **GS1 EPCIS 2.0** — for supply-chain event capture;
- **W3C Verifiable Credentials 2.0** — for attestations.

All GHC documents serialize as JSON-LD with the `@context`
`https://ghc.example/ns/v1`.

## 1.2 Core types

### 1.2.1 `Batch`

A `Batch` extends `prov:Entity` with halal-relevant fields:

```json
{
  "@type": "ghc:Batch",
  "@id": "urn:ghc:batch:bf2e...",
  "ingredient": "urn:ghc:ingredient:beef-shoulder",
  "quantity": { "value": 250.0, "unit": "kg" },
  "compliance": {
    "lattice": "halal",
    "authority": "urn:ghc:authority:jakim",
    "evidenceRef": "urn:ghc:vc:9c11..."
  }
}
```

### 1.2.2 `Process`

A `Process` extends `prov:Activity` and `epcis:TransformationEvent`:

```json
{
  "@type": "ghc:Process",
  "@id": "urn:ghc:process:42b9...",
  "operation": "ghc:op/cleaning/CIP-3",
  "inputs":  ["urn:ghc:batch:..."],
  "outputs": ["urn:ghc:batch:..."],
  "channel": {
    "haramBitTransitionMatrix": "urn:ghc:channel:cip3-default",
    "calibration": "urn:ghc:cal:..."
  }
}
```

The `channel` block is what makes the contamination-capacity bound of
§4 of the whitepaper computable.

### 1.2.3 `Authority`

An `Authority` is a Shariah-recognized certifier:

```json
{
  "@type": "ghc:Authority",
  "@id": "urn:ghc:authority:jakim",
  "name": "Jabatan Kemajuan Islam Malaysia (JAKIM)",
  "publicKey": "did:web:halal.gov.my#auth-2026",
  "scope": ["food", "cosmetics"]
}
```

## 1.3 EPCIS extension

GHC defines an EPCIS 2.0 `bizStep` extension namespace
`https://ghc.example/bizstep/` covering halal-specific operations
(slaughter, blessing recitation, washing-cycle, separation-line) and a
`disposition` extension namespace `https://ghc.example/disposition/`
for compliance-lattice membership.

**Bidirectional translation is implemented as of v0.0.x** in
`services/ghc_traceability/epcis.py`. The mapping handles three
EPCIS 2.0 event types:

| EPCIS 2.0 event       | GHC document       |
|-----------------------|--------------------|
| `ObjectEvent`         | `ghc:Batch`        |
| `TransformationEvent` | `ghc:Process`      |
| `AggregationEvent`    | `ghc:Process` (operation `ghc:op/mixing/aggregation`) |

Roundtrip translation `EPCIS → GHC → EPCIS` produces a
semantically-equivalent (though not byte-identical) event;
verifiers MUST treat the two forms as equivalent for the purposes
of provenance reasoning. Pytest assertions covering both directions
ship in `services/tests/test_smoke.py`.

## 1.4 PROV-O alignment

The `Batch` ↔ `prov:Entity`, `Process` ↔ `prov:Activity`, and
`Authority` ↔ `prov:Agent` mappings are documented in
`schemas/prov-alignment.json` so that any standard PROV-O reasoner
(e.g.\ Apache Jena) can query GHC documents directly.

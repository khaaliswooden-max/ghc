# GHC Protocol — §3 Compliance Lattice

## 3.1 The base lattice

The base GHC lattice is the three-element chain

```
ḥalāl  ≺  mashbūh  ≺  ḥarām
```

with meet `⊓` (conjunction of opinion) taking the maximum (i.e. more
restrictive wins) and join `⊔` (disjunction) taking the minimum.

## 3.2 Authority parametrization

Real-world halal compliance is plural: AAOIFI for finance, JAKIM for
food in Malaysia, BPJPH/MUI in Indonesia, ESMA in the UAE, SFDA in
Saudi Arabia, HFA in the UK, and so on. GHC indexes the lattice over
an authority set $\mathcal{A}$ so that

```
L  =  ∏  L_A     for A ∈ 𝒜.
```

A composite verdict is an element of this product. A product element
is **federated-ḥalāl** if every component is ḥalāl, **disputed** if
components disagree, and **federated-ḥarām** if any component is
ḥarām (configurable per deployment).

## 3.3 Dissent encoding

When authorities disagree, GHC records the dissent as a first-class
artifact:

```json
{
  "@type": "ghc:Dissent",
  "subject": "urn:ghc:product:0123...",
  "opinions": [
    { "authority": "urn:ghc:authority:jakim", "verdict": "halal" },
    { "authority": "urn:ghc:authority:mui",   "verdict": "mashbuh" }
  ],
  "evidence": [
    "urn:ghc:vc:f7a1...",
    "urn:ghc:vc:80c2..."
  ]
}
```

Verifiers MUST present the dissent transparently to consumers and MUST
NOT silently reduce a federated verdict to a single value.

## 3.4 Lattice extensions (informative)

Future versions may extend the base lattice to capture finer-grained
distinctions used in the literature (e.g. *makrūh tanzīhī* / *taḥrīmī*
for cosmetics, AAOIFI ratings for sukuk). Extensions MUST refine the
base lattice (i.e. project down to it) and MUST NOT introduce
incomparable elements at the base level.

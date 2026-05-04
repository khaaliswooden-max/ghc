//! `ghc-graph` — provenance DAGs and spectral fingerprints.
//!
//! Runtime mirror of `Ghc/Spectral.lean` (combinatorial kernel) and
//! `GhcMathlib/Spectral.lean` (charpoly/spectrum invariance).
//!
//! Provides:
//! * [`ProvenanceDag`] — a directed weighted graph over `u64` node ids.
//! * [`fingerprint`] — top-`k` eigenvalues of the normalized weighted
//!   Laplacian (the "production" fingerprint cited in §6).
//! * [`weight_seq`] / [`total_weight`] / [`count_weight`] — the
//!   combinatorial fingerprint, provably permutation-invariant.

#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};

use nalgebra::{DMatrix, SymmetricEigen};
use serde::{Deserialize, Serialize};

/// A directed weighted edge.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Edge {
    pub source: u64,
    pub target: u64,
    pub weight: u64,
}

impl Edge {
    pub fn new(source: u64, target: u64, weight: u64) -> Self {
        Self {
            source,
            target,
            weight,
        }
    }
}

/// A provenance DAG.
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ProvenanceDag {
    pub edges: Vec<Edge>,
}

impl ProvenanceDag {
    pub fn new(edges: Vec<Edge>) -> Self {
        Self { edges }
    }

    pub fn nodes(&self) -> BTreeSet<u64> {
        let mut s = BTreeSet::new();
        for e in &self.edges {
            s.insert(e.source);
            s.insert(e.target);
        }
        s
    }

    /// Apply a vertex relabeling (need not be a bijection).
    /// Mirrors `Spectral.Graph.relabel`.
    pub fn relabel(&self, sigma: impl Fn(u64) -> u64) -> ProvenanceDag {
        ProvenanceDag::new(
            self.edges
                .iter()
                .map(|e| Edge::new(sigma(e.source), sigma(e.target), e.weight))
                .collect(),
        )
    }
}

/// The list of edge weights — the combinatorial fingerprint.
/// Mirrors `Spectral.Graph.weightSeq`.
pub fn weight_seq(g: &ProvenanceDag) -> Vec<u64> {
    g.edges.iter().map(|e| e.weight).collect()
}

/// Total edge weight — single-number fingerprint. Mirrors
/// `Spectral.Graph.totalWeight`.
pub fn total_weight(g: &ProvenanceDag) -> u64 {
    g.edges.iter().map(|e| e.weight).sum()
}

/// Count of edges with the given weight. Mirrors
/// `Spectral.Graph.countWeight_relabel`.
pub fn count_weight(g: &ProvenanceDag, w: u64) -> usize {
    g.edges.iter().filter(|e| e.weight == w).count()
}

/// Compute the top-`k` eigenvalues of the normalized weighted
/// Laplacian `L = I - D^{-1/2} W D^{-1/2}` of the symmetrized graph.
/// This is the production fingerprint; the genuinely-spectral
/// invariance under vertex relabeling is mechanized as
/// `GhcMathlib.Spectral.charpoly_relabel`.
pub fn fingerprint(g: &ProvenanceDag, k: usize) -> Vec<f64> {
    let nodes: Vec<u64> = g.nodes().into_iter().collect();
    let n = nodes.len();
    if n == 0 {
        return Vec::new();
    }
    let idx: BTreeMap<u64, usize> = nodes.iter().enumerate().map(|(i, &n)| (n, i)).collect();

    let mut w = DMatrix::<f64>::zeros(n, n);
    for e in &g.edges {
        let (i, j) = (idx[&e.source], idx[&e.target]);
        let weight = e.weight as f64;
        w[(i, j)] += weight;
        w[(j, i)] += weight; // symmetrize
    }
    let mut d_inv_sqrt = DMatrix::<f64>::zeros(n, n);
    for i in 0..n {
        let deg: f64 = (0..n).map(|j| w[(i, j)]).sum();
        d_inv_sqrt[(i, i)] = if deg > 0.0 { deg.sqrt().recip() } else { 0.0 };
    }
    let normalized = &d_inv_sqrt * &w * &d_inv_sqrt;
    let laplacian = DMatrix::<f64>::identity(n, n) - normalized;
    let mut eigs: Vec<f64> = SymmetricEigen::new(laplacian)
        .eigenvalues
        .iter()
        .copied()
        .collect();
    eigs.sort_by(|a, b| b.partial_cmp(a).unwrap());
    eigs.truncate(k.min(n));
    eigs
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    fn arb_edge() -> impl Strategy<Value = Edge> {
        (0u64..32, 0u64..32, 1u64..1000).prop_map(|(s, t, w)| Edge::new(s, t, w))
    }

    proptest! {
        /// Mirrors `Spectral.Graph.weightSeq_relabel`.
        #[test]
        fn weight_seq_invariant_under_relabel(
            edges in prop::collection::vec(arb_edge(), 0..32),
            shift in 1u64..1000
        ) {
            let g = ProvenanceDag::new(edges);
            let g2 = g.relabel(|x| x.wrapping_add(shift));
            prop_assert_eq!(weight_seq(&g), weight_seq(&g2));
        }

        /// Mirrors `Spectral.Graph.totalWeight_relabel`.
        #[test]
        fn total_weight_invariant_under_relabel(
            edges in prop::collection::vec(arb_edge(), 0..32),
            shift in 1u64..1000
        ) {
            let g = ProvenanceDag::new(edges);
            let g2 = g.relabel(|x| x.wrapping_add(shift));
            prop_assert_eq!(total_weight(&g), total_weight(&g2));
        }

        /// Mirrors `Spectral.Graph.countWeight_relabel`.
        #[test]
        fn count_weight_invariant_under_relabel(
            edges in prop::collection::vec(arb_edge(), 0..32),
            shift in 1u64..1000,
            w in 1u64..1000
        ) {
            let g = ProvenanceDag::new(edges);
            let g2 = g.relabel(|x| x.wrapping_add(shift));
            prop_assert_eq!(count_weight(&g, w), count_weight(&g2, w));
        }
    }

    /// Spectral fingerprint is preserved under any *bijective* relabel
    /// (this is the runtime witness of the `GhcMathlib.charpoly_relabel`
    /// theorem: bijective relabel is conjugation by a permutation
    /// matrix, hence the same spectrum).
    #[test]
    fn spectral_fingerprint_relabel_bijection() {
        let edges = vec![Edge::new(0, 1, 1), Edge::new(1, 2, 2), Edge::new(0, 2, 3)];
        let g = ProvenanceDag::new(edges);
        // Bijective relabel: 0↔2 (involution).
        let g2 = g.relabel(|x| {
            if x == 0 {
                2
            } else if x == 2 {
                0
            } else {
                x
            }
        });

        let f1 = fingerprint(&g, 3);
        let f2 = fingerprint(&g2, 3);
        assert_eq!(f1.len(), f2.len());
        for (a, b) in f1.iter().zip(f2.iter()) {
            assert!((a - b).abs() < 1e-9, "{a} vs {b}");
        }
    }

    #[test]
    fn empty_graph_empty_fingerprint() {
        let g = ProvenanceDag::default();
        assert!(fingerprint(&g, 5).is_empty());
        assert_eq!(total_weight(&g), 0);
    }
}

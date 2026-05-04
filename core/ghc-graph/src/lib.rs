//! `ghc-graph` — spectral provenance invariants.
//!
//! Computes the normalized weighted Laplacian spectrum of a provenance
//! DAG. The top-`k` eigenvalues form the GHC provenance fingerprint
//! that v0.1 attestations carry alongside the zk-Halal proof.

#![forbid(unsafe_code)]

use nalgebra::{DMatrix, SymmetricEigen};
use petgraph::graph::DiGraph;

/// A weighted provenance DAG indexed by `usize` node IDs.
pub type ProvenanceGraph = DiGraph<(), f64>;

/// Compute the (real) eigenvalues of the normalized weighted Laplacian
/// `L = I - D^{-1/2} W D^{-1/2}`, where `W` is the symmetrized
/// adjacency matrix and `D` is the weighted degree.
///
/// Empty / disconnected nodes contribute a 0 eigenvalue and are
/// handled gracefully.
pub fn fingerprint(g: &ProvenanceGraph, k: usize) -> Vec<f64> {
    let n = g.node_count();
    if n == 0 {
        return Vec::new();
    }
    let mut w = DMatrix::<f64>::zeros(n, n);
    for e in g.edge_indices() {
        let (a, b) = g.edge_endpoints(e).expect("edge has endpoints");
        let weight = *g.edge_weight(e).expect("weight present");
        let (i, j) = (a.index(), b.index());
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
    let mut eigs: Vec<f64> = SymmetricEigen::new(laplacian).eigenvalues.iter().copied().collect();
    eigs.sort_by(|a, b| b.partial_cmp(a).unwrap());
    eigs.truncate(k.min(n));
    eigs
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_graph_produces_empty_fingerprint() {
        let g = ProvenanceGraph::new();
        assert!(fingerprint(&g, 5).is_empty());
    }

    #[test]
    fn relabel_preserves_spectrum() {
        let mut g1 = ProvenanceGraph::new();
        let a = g1.add_node(());
        let b = g1.add_node(());
        let c = g1.add_node(());
        g1.add_edge(a, b, 1.0);
        g1.add_edge(b, c, 2.0);

        let mut g2 = ProvenanceGraph::new();
        let x = g2.add_node(());
        let y = g2.add_node(());
        let z = g2.add_node(());
        g2.add_edge(z, y, 1.0); // permutation a↔c
        g2.add_edge(y, x, 2.0);

        let f1 = fingerprint(&g1, 3);
        let f2 = fingerprint(&g2, 3);
        for (e1, e2) in f1.iter().zip(f2.iter()) {
            assert!((e1 - e2).abs() < 1e-9, "{e1} vs {e2}");
        }
    }
}

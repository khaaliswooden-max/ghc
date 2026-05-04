//! `ghc` — end-to-end reference CLI.
//!
//! Subcommands:
//! * `closure`     — print the Halal-Closure Functor verdict of a process.
//! * `plurality`   — plurality verdict over an audit log.
//! * `fingerprint` — top-k spectral fingerprint of a provenance DAG.
//! * `prove`       — generate a zk-Halal Groth16 proof.
//! * `verify`      — verify a zk-Halal Groth16 proof.
//! * `demo`        — full farm→retailer demo: build, attest, verify.

use std::path::PathBuf;

use ark_bls12_381::Fr;
use ark_ff::Field;
use ark_serialize::{CanonicalDeserialize, CanonicalSerialize};
use clap::{Parser, Subcommand, ValueEnum};
use ghc_algebra::{halal_closure, plurality, Verdict};
use ghc_graph::{fingerprint, total_weight, Edge, ProvenanceDag};
use ghc_zk::{prove, setup, verify, HalalThresholdCircuit, Threshold};

#[derive(Parser, Debug)]
#[command(version, about = "Global Halal Compliance reference CLI")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand, Debug)]
enum Cmd {
    /// Halal-Closure Functor verdict of a process.
    Closure {
        /// Comma-separated verdict list, e.g. "halal,halal,mashbuh".
        process: String,
    },
    /// Plurality verdict over an audit log.
    Plurality {
        /// Comma-separated verdict list.
        audits: String,
    },
    /// Top-k spectral fingerprint of a provenance DAG.
    Fingerprint {
        /// Path to JSON-encoded ProvenanceDag.
        graph: PathBuf,
        /// Number of eigenvalues to print.
        #[arg(short, long, default_value_t = 5)]
        k: usize,
    },
    /// Generate a zk-Halal Groth16 proof.
    Prove {
        /// Threshold the witness should satisfy.
        #[arg(short, long, value_enum, default_value_t = ThresholdArg::Halal)]
        threshold: ThresholdArg,
        /// Comma-separated witness verdicts.
        witness: String,
        /// Salt (decimal field element).
        #[arg(short, long, default_value_t = 1)]
        salt: u64,
        /// Output base path; writes `.proof` and `.commitment`.
        #[arg(short, long)]
        out: PathBuf,
    },
    /// Verify a zk-Halal Groth16 proof.
    Verify {
        #[arg(short, long, value_enum, default_value_t = ThresholdArg::Halal)]
        threshold: ThresholdArg,
        /// Witness length the proof was generated for (circuit shape).
        #[arg(short, long)]
        n: usize,
        /// Path to a `.proof` file.
        proof: PathBuf,
        /// Path to a `.commitment` file.
        commitment: PathBuf,
    },
    /// End-to-end demo: build a farm→retailer process, attest, verify.
    Demo,
}

#[derive(Copy, Clone, Debug, ValueEnum)]
enum ThresholdArg {
    Halal,
    Mashbuh,
}

impl From<ThresholdArg> for Threshold {
    fn from(t: ThresholdArg) -> Self {
        match t {
            ThresholdArg::Halal => Threshold::Halal,
            ThresholdArg::Mashbuh => Threshold::Mashbuh,
        }
    }
}

fn parse_verdicts(s: &str) -> Result<Vec<Verdict>, String> {
    s.split(',')
        .map(|v| match v.trim().to_lowercase().as_str() {
            "halal" | "h" => Ok(Verdict::Halal),
            "mashbuh" | "m" => Ok(Verdict::Mashbuh),
            "haram" | "x" => Ok(Verdict::Haram),
            other => Err(format!("unknown verdict: {other}")),
        })
        .collect()
}

fn fr_to_string(fr: Fr) -> String {
    let mut bytes = Vec::new();
    fr.serialize_compressed(&mut bytes).unwrap();
    bytes
        .iter()
        .rev()
        .map(|b| format!("{b:02x}"))
        .collect::<String>()
}

fn write_fr(path: &PathBuf, fr: Fr) -> std::io::Result<()> {
    let mut bytes = Vec::new();
    fr.serialize_compressed(&mut bytes).unwrap();
    std::fs::write(path, bytes)
}

fn read_fr(path: &PathBuf) -> std::io::Result<Fr> {
    let bytes = std::fs::read(path)?;
    Ok(Fr::deserialize_compressed(&bytes[..]).expect("valid Fr serialization"))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Closure { process } => {
            let p = parse_verdicts(&process)?;
            println!("{}", halal_closure(&p));
        }
        Cmd::Plurality { audits } => {
            let a = parse_verdicts(&audits)?;
            println!("{}", plurality(&a));
        }
        Cmd::Fingerprint { graph, k } => {
            let s = std::fs::read_to_string(&graph)?;
            let g: ProvenanceDag = serde_json::from_str(&s)?;
            println!("nodes:        {}", g.nodes().len());
            println!("edges:        {}", g.edges.len());
            println!("total_weight: {}", total_weight(&g));
            println!("top-{k} eigenvalues of normalized Laplacian:");
            for (i, e) in fingerprint(&g, k).iter().enumerate() {
                println!("  λ_{i}: {e:.6}");
            }
        }
        Cmd::Prove {
            threshold,
            witness,
            salt,
            out,
        } => {
            let w = parse_verdicts(&witness)?;
            let n = w.len();
            let salt = Fr::from(salt);
            let keys = setup(threshold.into(), n)?;
            let (commitment, proof) = prove(&keys, threshold.into(), w, salt)?;
            let mut proof_bytes = Vec::new();
            proof.serialize_compressed(&mut proof_bytes)?;
            std::fs::write(out.with_extension("proof"), &proof_bytes)?;
            write_fr(&out.with_extension("commitment"), commitment)?;
            println!("commitment = 0x{}", fr_to_string(commitment));
            println!("proof  bytes: {}", proof_bytes.len());
            println!("written: {} (.proof, .commitment)", out.display());
        }
        Cmd::Verify {
            threshold,
            n,
            proof,
            commitment,
        } => {
            let keys = setup(threshold.into(), n)?;
            let proof_bytes = std::fs::read(&proof)?;
            let proof = ark_groth16::Proof::deserialize_compressed(&proof_bytes[..])?;
            let commitment = read_fr(&commitment)?;
            let ok = verify(&keys, commitment, &proof)?;
            if ok {
                println!("VALID  commitment = 0x{}", fr_to_string(commitment));
            } else {
                println!("INVALID");
                std::process::exit(1);
            }
        }
        Cmd::Demo => {
            run_demo()?;
        }
    }
    Ok(())
}

/// End-to-end demo replicating the §10 evaluation beef sample:
/// farm → abattoir → processor → retailer, with a zk-Halal
/// attestation at the end.
fn run_demo() -> Result<(), Box<dyn std::error::Error>> {
    use std::time::Instant;

    println!("== GHC reference demo: farm → abattoir → processor → retailer ==\n");

    // 1. Provenance DAG.
    let dag = ProvenanceDag::new(vec![
        Edge::new(1, 2, 100), // farm → abattoir
        Edge::new(2, 3, 95),  // abattoir → processor (5% loss)
        Edge::new(3, 4, 90),  // processor → retailer
    ]);
    println!(
        "  provenance: {} nodes, {} edges, total_weight = {}",
        dag.nodes().len(),
        dag.edges.len(),
        total_weight(&dag)
    );
    let fp = fingerprint(&dag, 3);
    println!("  fingerprint top-3: {fp:?}");

    // 2. Process verdicts (one per processing step).
    let process = vec![Verdict::Halal, Verdict::Halal, Verdict::Halal];
    let closure = halal_closure(&process);
    println!("  HCF verdict: {closure}");

    // 3. Audit log.
    let audits = vec![
        Verdict::Halal,
        Verdict::Halal,
        Verdict::Halal,
        Verdict::Mashbuh,
    ];
    println!("  audits: {audits:?}  → plurality: {}", plurality(&audits));

    // 4. zk-Halal proof.
    println!("\n  generating zk-Halal Groth16 setup (BLS12-381)...");
    let t0 = Instant::now();
    let keys = setup(Threshold::Halal, process.len())?;
    println!("    setup:     {:?}", t0.elapsed());
    let salt = Fr::from(0xc0ffee_u64);
    let t1 = Instant::now();
    let (commitment, proof) = prove(&keys, Threshold::Halal, process.clone(), salt)?;
    println!("    proving:   {:?}", t1.elapsed());
    let t2 = Instant::now();
    let ok = verify(&keys, commitment, &proof)?;
    println!("    verifying: {:?}", t2.elapsed());

    let mut proof_bytes = Vec::new();
    proof.serialize_compressed(&mut proof_bytes)?;
    println!("    proof: {} bytes", proof_bytes.len());

    println!(
        "\n  zk-Halal attestation: commitment = 0x{}  →  {}",
        fr_to_string(commitment),
        if ok { "VALID" } else { "INVALID" }
    );
    assert!(ok);

    // Sanity: a hostile prover cannot generate a passing proof for a
    // process containing haram (constructor refuses).
    let mut hostile = process.clone();
    hostile[1] = Verdict::Haram;
    let err = HalalThresholdCircuit::new_prover(Threshold::Halal, hostile, salt);
    println!(
        "\n  hostile-witness rejection: {}",
        if err.is_err() { "REJECTED" } else { "FAILED" }
    );
    assert!(err.is_err());

    let _ = Fr::ONE;
    println!("\n== demo complete ==");
    Ok(())
}

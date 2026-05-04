# GHC top-level Makefile.
# Each target delegates to the relevant subsystem; everything is a no-op
# until the corresponding stub is fleshed out, but the wiring is in place
# so CI can invoke a single command per layer.

.PHONY: all proofs core services paper spec demo test clean help

all: proofs core services paper spec

help:
	@echo "GHC build targets:"
	@echo "  make proofs    - lake build (Lean 4 theorems)"
	@echo "  make core      - cargo test --workspace (Rust core)"
	@echo "  make services  - pytest in services/"
	@echo "  make paper     - latexmk -pdf paper/main.tex"
	@echo "  make spec      - validate JSON Schemas in spec/"
	@echo "  make demo      - end-to-end traceability demo"
	@echo "  make test      - run all test suites"
	@echo "  make clean     - remove build artifacts"

proofs:
	cd proofs && lake build

core:
	cd core && cargo test --workspace

services:
	cd services && python -m pytest

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode main.tex

spec:
	cd tools/conformance && python validate_schemas.py ../../spec/schemas

demo:
	@echo "TODO: end-to-end demo (farm -> abattoir -> processor -> retailer)"
	@echo "      will emit a zk-Halal VC and anchor it to a local Fabric net."

test: proofs core services spec

clean:
	cd proofs && rm -rf .lake build || true
	cd core && cargo clean || true
	cd paper && latexmk -C || true
	find services -type d -name __pycache__ -exec rm -rf {} + || true

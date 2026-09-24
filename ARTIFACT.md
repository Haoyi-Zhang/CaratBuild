# Artifact guide

## Scope

This artifact evaluates a bounded claim: accounting-window finality and evidence retention for a fixed, honest source roster under crash-stop endpoint failures and eventual delivery after the final failure. It does **not** implement Byzantine source validation, dynamic membership, cryptographic identity, WAN deployment, general distributed garbage collection, or production build attribution.

## One-command reproduction

```sh
./scripts/reproduce.sh
```

The command is offline, fail-closed, and stage-isolated. It regenerates deterministic correctness results, runs the test suite, executes the independent finite boundary checker, and finishes with `scripts/reviewer_audit.py`. A nonzero status means the reproduction did not pass. Performance fields are descriptive and machine-dependent; semantic acceptance, set, mass, and safety fields are the reproducibility target.

## Fast inspection

```sh
python proofs/boundary_model_check.py
python scripts/reviewer_audit.py
```

The first command checks the indistinguishability witnesses, the general failure-family retention criterion, its cardinality-`f` corollary, the exact-membership state lower bound, and namespace-ablation witnesses without importing the implementation. The second validates the distributable tree, result formats, packaged public-input digests, offline reproduction path, and absence of private absolute paths.

## Public and generated inputs

`inputs/public/pytest/` contains exact upstream diff bytes, the upstream license text, source locations, and SHA-256 digests. It is a narrow reconstructible case, not a representativeness claim. All scale and adversarial families are generated and labeled as such.

## Interpreting performance

Timing and resident-memory values vary with hardware, operating-system scheduling, filesystem state, and co-tenancy. The paper reports repeated clean-run ranges and does not use timing to support a correctness theorem. Counts and semantic decisions should match; timing fields need not.

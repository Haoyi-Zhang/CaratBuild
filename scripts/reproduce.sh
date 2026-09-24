#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${CARAT_PYTHON:-python}"
export PYTHONPATH="$ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON_BIN" "$ROOT/scripts/reproduce_all.py"
# FINAL BOUNDARY MODEL CHECK
echo "[reproduce] independent boundary model check"
python proofs/boundary_model_check.py --output results/boundary_model_check.json
# FINAL ENVIRONMENT AND DEPENDENCY RECORD
echo "[reproduce] dependency and environment records"

# FINAL OFFLINE REVIEWER AUDIT
echo "[reproduce] offline reviewer audit"

# Final fail-closed reviewer checks.
AUDIT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/sanitize_outputs.py"
find "$AUDIT_ROOT" -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
find "$AUDIT_ROOT" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/verify_public_inputs.py"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/dependency_audit.py"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/robustness_audit.py"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/code_quality_audit.py"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/claim_path_audit.py"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/capture_environment.py"
"${PYTHON:-python3}" "$AUDIT_ROOT/scripts/reviewer_audit.py"

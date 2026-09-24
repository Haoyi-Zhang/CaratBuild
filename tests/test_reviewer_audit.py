from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('reviewer_audit',ROOT/'scripts'/'reviewer_audit.py')
mod=module_from_spec(spec);assert spec.loader;spec.loader.exec_module(mod)

def test_distributable_tree_passes_offline_reviewer_audit():
    r=mod.audit(ROOT,require_generated=False)
    assert r['ok'],r['failures']

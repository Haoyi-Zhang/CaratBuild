import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'inputs'/'public'/'pytest'

def test_public_input_bytes_match_provenance_manifest():
    manifest=json.loads((P/'PROVENANCE.json').read_text())
    by_name={x['file']:x for x in manifest['files']}
    for name in ('pr-14018.diff','pr-14074.diff','LICENSE.pytest'):
        b=(P/name).read_bytes()
        assert len(b)==by_name[name]['bytes']
        assert hashlib.sha256(b).hexdigest()==by_name[name]['sha256']

def test_public_diffs_identify_exact_upstream_prs_and_expected_fix():
    a=(P/'pr-14018.diff').read_text(errors='replace')
    b=(P/'pr-14074.diff').read_text(errors='replace')
    for diff in (a,b):
        assert 'conftest.py files are not plugins' in diff
        assert 'Blocking conftest files using -p is not supported' in diff
        assert 'testing/test_config.py' in diff
        assert 'src/_pytest/config/__init__.py' in diff

def test_upstream_license_is_packaged_for_offline_review():
    license_text=(P/'LICENSE.pytest').read_text(errors='replace')
    assert 'MIT License' in license_text or 'Permission is hereby granted' in license_text

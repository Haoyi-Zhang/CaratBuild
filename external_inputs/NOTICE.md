# Input provenance and selection limits

## Fixed inherited size profiles

`public_history_slices.json` is retained unchanged as the exact numeric input to
the generated campaigns. Its eight entries contain counts, source repository
attribution, dates and paraphrased descriptions. Despite its filename it does not
contain repository history, original patch text, build execution, or a
reconstructible extraction record. Except for the pytest example separately
identified below, those historical measurements have not been re-established
from exact upstream changes in this package. They are treated as eight supplied
size constants. No claim about a repository, contributor or natural workload
distribution is based on them.

## Exact public pytest pair

`pytest_pair.json` retains exact unified-diff hunks from pytest pull requests
14018 and 14074. The latter explicitly describes itself as a backport of the
former. Source records were read on 2026-09-10 through their public read-only
interfaces. Stable pull-request URLs and the exact consumed hunks are included;
no upstream execution or test result is imported as evidence.

Selection is all three non-contributor-list changed files:
`changelog/13634.bugfix.rst`, `src/_pytest/config/__init__.py`, and
`testing/test_config.py`. Each source contains respectively five, six and four
added lines in these files and no removed lines. The contributor-list change
is excluded because it is not the software-change relation being illustrated.
Therefore the pair's selected mass is 15 per input, whereas the retained
four-file pytest size profile is 16. The stored diff-hunk headers and whitespace
are unchanged; unrelated diff headers and unselected files are not consumed.

The source fix and backport are not two independent samples. The static adapter
requires an explicit backport relation and equal path-indexed changed-line
payloads. It ignores hunk positions and context for this equality, preserves
changed-line whitespace and order, and rejects malformed or unsupported input
before constructing mints. This is a bounded textual mapping, not a proof of
arbitrary semantic equivalence. Synthetic mutations are negative controls, not
additional public changes.

Pytest is distributed under the MIT license. The exact license notice is in
`pytest-LICENSE.txt` and applies to these retained hunks. The project license
covers the adapter, generated normalized facts and experimental code, and does
not replace upstream attribution.

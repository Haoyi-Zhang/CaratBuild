from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest
from carat.public_pair import extract_pair, payload
from carat.decode import decode
from carat.independent_check import check

ROOT = Path(__file__).resolve().parents[1]

def corpus():
    return json.loads((ROOT/"external_inputs/pytest_pair.json").read_text())

class PublicPairTests(unittest.TestCase):
    def test_exact_payload_and_mass(self):
        data = corpus()
        self.assertEqual([len(payload(item["hunk"])) for item in data["source"]], [5,6,4])
        facts = extract_pair(data)
        self.assertEqual(len(facts), 6)
        self.assertEqual(decode(facts).gross_mass, 15)
        self.assertTrue(check(facts).accepted)

    def test_only_coordinates_may_shift(self):
        data = corpus()
        data["target"][1]["hunk"] = data["target"][1]["hunk"].replace("-814,6 +814,12", "-7,6 +13,12")
        self.assertTrue(check(extract_pair(data)).accepted)
        data["target"][1]["hunk"] = data["target"][1]["hunk"].replace('name.endswith("conftest.py")', 'name.endswith("another.py")')
        with self.assertRaises(ValueError): extract_pair(data)

    def test_path_truncation_and_binary_fail_closed(self):
        original = corpus()
        for field, value in [("path", "different.py"), ("hunk", "Binary files differ\n"),
                             ("hunk", original["target"][2]["hunk"].splitlines(keepends=True)[0])]:
            data = deepcopy(original)
            data["target"][2][field] = value
            with self.assertRaises(ValueError): extract_pair(data)

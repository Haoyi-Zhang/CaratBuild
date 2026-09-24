from __future__ import annotations

import ast
import copy
import inspect
import unittest

import carat.independent_check as independent_check
from carat.baselines import commit_count, presentation_mass
from carat.decode import decode
from carat.facts import FactError, canonical_text, mint, parse_text, presentation, transform
from carat.generate import amplification_history, ambiguity_variant, masses_from_profile, mixed_history
from carat.independent_check import check, verify_witness
from carat.protocol import Replica


class AccountingTests(unittest.TestCase):
    def test_tiny_profile_has_positive_finite_partition(self) -> None:
        masses = masses_from_profile(2, 3, 0)
        self.assertEqual(sum(masses), 4)
        self.assertTrue(all(value >= 1 for value in masses))
        self.assertLessEqual(len(masses), 4)

    def test_all_declared_operations_conserve_mass(self) -> None:
        masses = [1, 2, 3, 5, 8]
        for operation in ("rebase", "cherry_pick", "fork", "squash", "revert"):
            with self.subTest(operation=operation):
                scenario = amplification_history(masses, 4, operation, salt=11)
                result = decode(scenario.facts)
                report = check(scenario.facts)
                self.assertTrue(result.determined, result.witnesses)
                self.assertTrue(report.accepted, report.violations)
                self.assertEqual(result.gross_mass, sum(masses))
                self.assertEqual(result.unique_units, len(masses))
                self.assertGreater(commit_count(scenario.facts), 1)
                self.assertGreater(presentation_mass(scenario.facts), sum(masses))

                # Corrupt one declared output and require both semantic
                # implementations to reject every operation, not merely accept
                # its generated happy path.
                invalid = copy.deepcopy(list(scenario.facts))
                target_transform = next(
                    fact for fact in invalid if fact["kind"] == "transform"
                )
                target_output = target_transform["outputs"][0]
                target_presentation = next(
                    fact
                    for fact in invalid
                    if fact["kind"] == "presentation"
                    and fact["presentation"] == target_output
                )
                target_presentation["atoms"][0][1] *= -1
                invalid_result = decode(invalid)
                invalid_report = check(invalid)
                self.assertFalse(invalid_result.determined)
                self.assertFalse(invalid_report.accepted)
                law_witness = next(
                    item
                    for item in invalid_result.witnesses
                    if item.code == "transform-law-violation"
                )
                self.assertTrue(verify_witness(invalid, law_witness.as_dict())[0])

        # Exercise the non-empty fresh-unit branch directly.  The second rewrite
        # consumes the first output without re-declaring the fresh unit, so its
        # mass must enter once rather than once per presentation.
        fresh_facts = [
            mint("n0:1", "u-base", 2, "n0", "fresh-batch"),
            mint("n1:1", "u-fresh", 7, "n1", "fresh-batch"),
            presentation(
                "n0:2", "p-base", [("u-base", 1)], "main", 0, "fresh-batch"
            ),
            presentation(
                "n1:2",
                "p-fresh",
                [("u-base", 1), ("u-fresh", 1)],
                "topic",
                1,
                "fresh-batch",
            ),
            transform(
                "n1:3",
                "t-fresh",
                "rebase",
                ["p-base"],
                ["p-fresh"],
                ["u-fresh"],
                "fresh-batch",
            ),
            presentation(
                "n2:1",
                "p-replayed",
                [("u-base", 1), ("u-fresh", 1)],
                "release",
                2,
                "fresh-batch",
            ),
            transform(
                "n2:2",
                "t-replayed",
                "rebase",
                ["p-fresh"],
                ["p-replayed"],
                [],
                "fresh-batch",
            ),
        ]
        fresh_result = decode(fresh_facts)
        fresh_report = check(fresh_facts)
        self.assertTrue(fresh_result.determined, fresh_result.witnesses)
        self.assertTrue(fresh_report.accepted, fresh_report.violations)
        self.assertEqual(fresh_result.gross_mass, 9)
        self.assertEqual(fresh_result.unique_units, 2)
        self.assertEqual(fresh_result.presentations, 3)

        # A squash whose inputs assign opposite signs to one unit has no
        # representable sign-consistent union and must be refused.
        sign_conflict = [
            mint("n0:1", "u-sign", 3, "n0", "sign-batch"),
            presentation(
                "n0:2", "p-positive", [("u-sign", 1)], "left", 0, "sign-batch"
            ),
            presentation(
                "n1:1", "p-negative", [("u-sign", -1)], "right", 0, "sign-batch"
            ),
            presentation(
                "n2:1", "p-output", [("u-sign", 1)], "merged", 1, "sign-batch"
            ),
            transform(
                "n2:2",
                "t-sign-conflict",
                "squash",
                ["p-positive", "p-negative"],
                ["p-output"],
                [],
                "sign-batch",
            ),
        ]
        sign_result = decode(sign_conflict)
        sign_report = check(sign_conflict)
        self.assertFalse(sign_result.determined)
        self.assertFalse(sign_report.accepted)
        sign_witness = next(
            item
            for item in sign_result.witnesses
            if item.code == "transform-law-violation"
        )
        self.assertTrue(verify_witness(sign_conflict, sign_witness.as_dict())[0])

        reused_fresh = list(fresh_facts)
        reused_fresh[-1] = transform(
            "n2:2",
            "t-replayed",
            "rebase",
            ["p-fresh"],
            ["p-replayed"],
            ["u-fresh"],
            "fresh-batch",
        )
        self.assertFalse(decode(reused_fresh).determined)
        self.assertFalse(check(reused_fresh).accepted)

    def test_mixed_history(self) -> None:
        scenario = mixed_history(93, 6, 7, rewrite_rounds=3)
        result = decode(scenario.facts)
        report = check(scenario.facts)
        self.assertTrue(result.determined, result.witnesses)
        self.assertTrue(report.accepted, report.violations)
        self.assertEqual(result.gross_mass, scenario.oracle_mass)
        self.assertEqual(result.unique_units, scenario.oracle_units)

    def test_ambiguity_witnesses_are_independently_minimal(self) -> None:
        syntax = ast.parse(inspect.getsource(independent_check))
        imports = [
            node.module or ""
            for node in ast.walk(syntax)
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertFalse(any(module.endswith("decode") for module in imports))

        scenario = mixed_history(71, 5, 9, rewrite_rounds=2)
        for index, variant in enumerate(
            (
                "missing-transform-output",
                "conflicting-presentation",
                "unresolved-effect",
                "conflicting-event",
                "invalid-transform",
            )
        ):
            with self.subTest(variant=variant):
                facts = ambiguity_variant(scenario, variant, index)
                all_texts = [canonical_text(fact) for fact in facts]
                present_unit = next(
                    fact["unit"] for fact in facts if fact["kind"] == "mint"
                )
                result = decode(facts)
                self.assertFalse(result.determined)
                verified = 0
                for witness in result.witnesses:
                    witness_dict = witness.as_dict()
                    ok, reason = verify_witness(facts, witness_dict)
                    self.assertTrue(ok, (witness, reason))

                    removed = dict(witness_dict)
                    removed["facts"] = list(witness_dict["facts"])[1:]
                    self.assertFalse(verify_witness(facts, removed)[0])

                    added = dict(witness_dict)
                    added["facts"] = list(witness_dict["facts"])
                    added["facts"].append(
                        next(text for text in all_texts if text not in added["facts"])
                    )
                    self.assertFalse(verify_witness(facts, added)[0])

                    false_missing = dict(witness_dict)
                    false_missing["missing"] = list(witness_dict["missing"]) + [
                        f"mint:{present_unit}"
                    ]
                    self.assertFalse(verify_witness(facts, false_missing)[0])
                    verified += 1
                self.assertGreater(verified, 0)


    def test_wire_normalization_and_strict_rejection(self) -> None:
        canonical = canonical_text(mint("n0:1", "u0", 3, "n0", "b0"))
        noncanonical = '''{
          "unit": "u0", "mass": 3, "source": "n0",
          "batch": "b0", "kind": "mint", "event": "n0:1"
        }'''
        replica = Replica("n1")
        self.assertTrue(replica.append_text(canonical))
        self.assertFalse(replica.append_text(noncanonical))
        self.assertEqual(replica.facts, {canonical})

        p1 = presentation(
            "n0:2", "p0", [("u-z", 1), ("u-a", -1)], "main", 0, "b0"
        )
        p2 = presentation(
            "n0:2", "p0", [("u-a", -1), ("u-z", 1)], "main", 0, "b0"
        )
        self.assertEqual(canonical_text(p1), canonical_text(p2))
        t1 = transform(
            "n0:3", "t0", "squash", ["p-z", "p-a"], ["p-out"], ["u-z", "u-a"], "b0"
        )
        t2 = transform(
            "n0:3", "t0", "squash", ["p-a", "p-z"], ["p-out"], ["u-a", "u-z"], "b0"
        )
        self.assertEqual(canonical_text(t1), canonical_text(t2))

        invalid_texts = (
            canonical.replace('"n0:1"', '"n0:01"'),
            canonical.replace('"n0:1"', '"n0:+1"'),
            canonical.replace('"mass":3', '"mass":true'),
            canonical.replace('"source":"n0"', '"source":"n1"'),
            '{"event":"n0:1","event":"n0:2","kind":"mint","unit":"u0","mass":1,"source":"n0","batch":"b"}',
            '{"event":"n0:1","kind":"mint","unit":"u0","mass":NaN,"source":"n0","batch":"b"}',
        )
        for text in invalid_texts:
            with self.subTest(text=text):
                with self.assertRaises(FactError):
                    parse_text(text)
        with self.assertRaises(FactError):
            mint("n0:1", "u0", True, "n0", "b0")
        with self.assertRaises(FactError):
            presentation("n0:2", "p0", [("u0", True)], "main", 0, "b0")
        with self.assertRaises(FactError):
            presentation("n0:2", "p0", [("u0", 1)], "main", False, "b0")

    def test_non_degenerate_shapes_and_global_identifiers(self) -> None:
        fork = amplification_history([1, 2, 3, 5], 4, "fork", salt=810)
        fork_transforms = [fact for fact in fork.facts if fact["kind"] == "transform"]
        self.assertEqual(len(fork_transforms), 1)
        self.assertEqual(len(fork_transforms[0]["inputs"]), 1)
        self.assertEqual(len(fork_transforms[0]["outputs"]), 4)

        squash = amplification_history([1, 2, 3, 5], 4, "squash", salt=811)
        squash_transforms = [fact for fact in squash.facts if fact["kind"] == "transform"]
        self.assertEqual(len(squash_transforms), 4)
        self.assertTrue(all(len(fact["inputs"]) == 2 for fact in squash_transforms))
        self.assertTrue(all(len(fact["outputs"]) == 1 for fact in squash_transforms))
        self.assertTrue(decode(fork.facts).determined)
        self.assertTrue(decode(squash.facts).determined)

        base = [
            mint("n0:1", "u0", 2, "n0", "id-batch"),
            presentation("n0:2", "p0", [("u0", 1)], "main", 0, "id-batch"),
            presentation("n1:1", "p1", [("u0", 1)], "topic", 1, "id-batch"),
        ]
        equivocated = base + [
            transform("n1:2", "same-transform", "rebase", ["p0"], ["p1"], [], "id-batch"),
            transform("n2:1", "same-transform", "cherry_pick", ["p0"], ["p1"], [], "id-batch"),
        ]
        result = decode(equivocated)
        self.assertFalse(result.determined)
        witness = next(item for item in result.witnesses if item.code == "transform-equivocation")
        self.assertTrue(verify_witness(equivocated, witness.as_dict())[0])
        self.assertTrue(any(value.startswith("transform-equivocation") for value in check(equivocated).violations))

        fresh_reuse = [
            mint("n0:1", "u0", 2, "n0", "fresh-global"),
            mint("n1:1", "uf", 7, "n1", "fresh-global"),
            presentation("n0:2", "p0", [("u0", 1)], "main", 0, "fresh-global"),
            presentation("n0:3", "p2", [("u0", 1)], "main-2", 0, "fresh-global"),
            presentation("n1:2", "p1", [("u0", 1), ("uf", 1)], "topic", 1, "fresh-global"),
            presentation("n2:1", "p3", [("u0", 1), ("uf", 1)], "release", 1, "fresh-global"),
            transform("n1:3", "t1", "rebase", ["p0"], ["p1"], ["uf"], "fresh-global"),
            transform("n2:2", "t2", "rebase", ["p2"], ["p3"], ["uf"], "fresh-global"),
        ]
        result = decode(fresh_reuse)
        self.assertFalse(result.determined)
        witness = next(item for item in result.witnesses if item.code == "fresh-unit-reused")
        self.assertTrue(verify_witness(fresh_reuse, witness.as_dict())[0])
        self.assertTrue(any(value.startswith("fresh-unit-reused") for value in check(fresh_reuse).violations))

    def test_witness_public_shape_is_enforced(self) -> None:
        scenario = mixed_history(83, 5, 919, rewrite_rounds=2)
        facts = ambiguity_variant(scenario, "missing-transform-output", 3)
        witness = decode(facts).witnesses[0].as_dict()
        self.assertTrue(verify_witness(facts, witness)[0])

        malformed: list[dict[str, object]] = []
        extra = dict(witness)
        extra["extra"] = "not public"
        malformed.append(extra)
        empty_detail = dict(witness)
        empty_detail["detail"] = ""
        malformed.append(empty_detail)
        wrong_category = dict(witness)
        wrong_category["category"] = "unresolved-effect"
        malformed.append(wrong_category)
        duplicated = dict(witness)
        duplicated["facts"] = list(witness["facts"]) + list(witness["facts"])
        malformed.append(duplicated)
        wrong_container = dict(witness)
        wrong_container["missing"] = tuple(witness["missing"])
        malformed.append(wrong_container)
        for value in malformed:
            with self.subTest(value=value):
                self.assertFalse(verify_witness(facts, value)[0])


if __name__ == "__main__":
    unittest.main()

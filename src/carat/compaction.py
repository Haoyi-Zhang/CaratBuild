"""Closure-barrier compaction for sealed history batches."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

from .decode import decode
from .facts import Fact, canonical_pair, canonical_text, parse_text
from .independent_check import check, check_sealed


@dataclass(frozen=True)
class BatchSummary:
    batch: str
    units: tuple[tuple[str, int], ...]
    presentation_ids: tuple[str, ...]
    transform_ids: tuple[str, ...]
    effects: tuple[tuple[str, str, int], ...]
    effect_ids: tuple[str, ...]

    @property
    def presentations(self) -> int:
        return len(self.presentation_ids)

    def as_dict(self) -> dict[str, object]:
        return {
            "batch": self.batch,
            "units": [list(item) for item in self.units],
            "presentation_ids": list(self.presentation_ids),
            "transform_ids": list(self.transform_ids),
            "effects": [list(item) for item in self.effects],
            "effect_ids": list(self.effect_ids),
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "BatchSummary":
        if type(value) is not dict:
            raise ValueError("summary must be an object")
        required = {
            "batch", "units", "presentation_ids", "transform_ids",
            "effects", "effect_ids",
        }
        if set(value) != required or type(value["batch"]) is not str:
            raise ValueError("malformed batch summary")
        units_raw = value["units"]
        presentation_raw = value["presentation_ids"]
        transform_raw = value["transform_ids"]
        effects_raw = value["effects"]
        effect_ids_raw = value["effect_ids"]
        if not all(type(item) is list for item in (units_raw, presentation_raw, transform_raw, effects_raw, effect_ids_raw)):
            raise ValueError("malformed batch summary fields")
        units: list[tuple[str, int]] = []
        for item in units_raw:
            if type(item) is not list or len(item) != 2 or type(item[0]) is not str or type(item[1]) is not int or item[1] <= 0:
                raise ValueError("malformed summarized unit")
            units.append((item[0], item[1]))
        effects: list[tuple[str, str, int]] = []
        for item in effects_raw:
            if (type(item) is not list or len(item) != 3 or type(item[0]) is not str
                    or item[1] not in {"pass", "fail", "skip"}
                    or type(item[2]) is not int or item[2] <= 0):
                raise ValueError("malformed summarized effect")
            effects.append((item[0], item[1], item[2]))
        for values, label in ((presentation_raw, "presentation"), (transform_raw, "transform"), (effect_ids_raw, "effect")):
            if any(type(item) is not str or not item for item in values) or len(values) != len(set(values)):
                raise ValueError(f"malformed summarized {label} identifiers")
        if len(units) != len({unit for unit, _mass in units}):
            raise ValueError("duplicate summarized unit")
        return cls(
            batch=value["batch"],
            units=tuple(sorted(units)),
            presentation_ids=tuple(sorted(presentation_raw)),
            transform_ids=tuple(sorted(transform_raw)),
            effects=tuple(sorted(effects)),
            effect_ids=tuple(sorted(effect_ids_raw)),
        )


@dataclass(frozen=True)
class CompactedLedger:
    summaries: tuple[BatchSummary, ...]
    live_facts: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "summaries": [item.as_dict() for item in self.summaries],
            "live_facts": list(self.live_facts),
        }

    def serialized_bytes(self) -> int:
        return len(json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8"))

    def boundary_valid(self) -> bool:
        """Check namespace separation without requiring live-state completeness."""

        closed = [item.batch for item in self.summaries]
        closed_units = [unit for item in self.summaries for unit, _ in item.units]
        closed_presentations = [identifier for item in self.summaries for identifier in item.presentation_ids]
        closed_transforms = [identifier for item in self.summaries for identifier in item.transform_ids]
        closed_effects = [identifier for item in self.summaries for identifier in item.effect_ids]
        closed_set = set(closed)
        closed_unit_set = set(closed_units)
        closed_presentation_set = set(closed_presentations)
        closed_transform_set = set(closed_transforms)
        closed_effect_set = set(closed_effects)
        live_items = [parse_text(text) for text in self.live_facts]
        return not (
            len(closed) != len(closed_set)
            or len(closed_units) != len(closed_unit_set)
            or len(closed_presentations) != len(closed_presentation_set)
            or len(closed_transforms) != len(closed_transform_set)
            or len(closed_effects) != len(closed_effect_set)
            or any(
                item["batch"] in closed_set and item["kind"] != "seal"
                for item in live_items
            )
            or any(
                (item["kind"] == "mint" and item["unit"] in closed_unit_set)
                or (
                    item["kind"] == "presentation"
                    and item["presentation"] in closed_presentation_set
                )
                or (
                    item["kind"] == "transform"
                    and item["transform"] in closed_transform_set
                )
                or (item["kind"] == "effect" and item["effect"] in closed_effect_set)
                for item in live_items
                if item["kind"] != "seal"
            )
        )

    def accounting(self) -> dict[str, int | bool]:
        live = decode(self.live_facts)
        # Summaries are trusted projections, not independently verifiable
        # history certificates or mergeable replica states. Fail closed on
        # obvious stale replay and identity overlap instead of double counting.
        if not live.determined or not self.boundary_valid():
            return {
                "determined": False,
                "unique_units": live.unique_units,
                "gross_mass": live.gross_mass,
                "presentations": live.presentations,
                "effects": live.effects,
                "passing_effects": live.passing_effects,
                "failing_effects": live.failing_effects,
            }
        units = live.unique_units
        mass = live.gross_mass
        presentations = live.presentations
        effects = live.effects
        passing = live.passing_effects
        failing = live.failing_effects
        for summary in self.summaries:
            units += len(summary.units)
            mass += sum(value for _, value in summary.units)
            presentations += summary.presentations
            for _unit, outcome, count in summary.effects:
                effects += count
                passing += count if outcome == "pass" else 0
                failing += count if outcome == "fail" else 0
        return {
            "determined": True,
            "unique_units": units,
            "gross_mass": mass,
            "presentations": presentations,
            "effects": effects,
            "passing_effects": passing,
            "failing_effects": failing,
        }


def compact_closed_batches(
    values: Iterable[str | Fact], closed_batches: Iterable[str]
) -> CompactedLedger:
    texts = sorted({canonical_pair(value)[0] for value in values})
    report = check(texts)
    decoded = decode(texts)
    if not report.accepted or not decoded.determined:
        raise ValueError("only determined, checker-accepted states may be compacted")
    closed = set(closed_batches)
    facts = [parse_text(text) for text in texts]

    # Every identifier dependency must stay on one side of the closure barrier.
    # These checks run before details are dropped so neither a compacted summary
    # nor the retained live state depends on a definition stored on the other side.
    unit_batch = {
        fact["unit"]: fact["batch"] for fact in facts if fact["kind"] == "mint"
    }
    presentation_batch = {
        fact["presentation"]: fact["batch"]
        for fact in facts
        if fact["kind"] == "presentation"
    }
    for fact in facts:
        fact_is_closed = fact["batch"] in closed
        if fact["kind"] == "presentation":
            reference_batches = [unit_batch[unit] for unit, _sign in fact["atoms"]]
            if any((batch in closed) != fact_is_closed for batch in reference_batches):
                raise ValueError("presentation crosses a closure barrier")
        elif fact["kind"] == "transform":
            reference_batches = [
                presentation_batch[value]
                for value in fact["inputs"] + fact["outputs"]
            ]
            reference_batches.extend(unit_batch[value] for value in fact["fresh"])
            if any((batch in closed) != fact_is_closed for batch in reference_batches):
                raise ValueError("transform crosses a closure barrier")
        elif fact["kind"] == "effect":
            reference_batches = [
                unit_batch[fact["unit"]],
                presentation_batch[fact["presentation"]],
            ]
            if any((batch in closed) != fact_is_closed for batch in reference_batches):
                raise ValueError("effect crosses a closure barrier")

    summaries: list[BatchSummary] = []
    for batch in sorted(closed):
        selected = [fact for fact in facts if fact["batch"] == batch]
        if not selected:
            continue
        units = tuple(
            sorted(
                (fact["unit"], int(fact["mass"]))
                for fact in selected
                if fact["kind"] == "mint"
            )
        )
        presentation_ids = tuple(sorted(
            fact["presentation"] for fact in selected if fact["kind"] == "presentation"
        ))
        transform_ids = tuple(sorted(
            fact["transform"] for fact in selected if fact["kind"] == "transform"
        ))
        effect_ids = tuple(sorted(
            fact["effect"] for fact in selected if fact["kind"] == "effect"
        ))
        effect_counts: dict[tuple[str, str], int] = {}
        for fact in selected:
            if fact["kind"] == "effect":
                key = (fact["unit"], fact["outcome"])
                effect_counts[key] = effect_counts.get(key, 0) + 1
        effects = tuple(sorted((unit, outcome, count) for (unit, outcome), count in effect_counts.items()))
        summaries.append(BatchSummary(
            batch=batch,
            units=units,
            presentation_ids=presentation_ids,
            transform_ids=transform_ids,
            effects=effects,
            effect_ids=effect_ids,
        ))

    # Seal records remain as compact anchor facts.  They carry no accounting
    # mass, but the next window needs the predecessor-seal chain.
    live = tuple(
        text
        for text, fact in zip(texts, facts)
        if fact["batch"] not in closed or fact["kind"] == "seal"
    )
    ledger = CompactedLedger(tuple(summaries), live)

    # Defense in depth: even if the syntactic barrier changes later, never return
    # a ledger that loses determination or changes the declared aggregate tuple.
    after = ledger.accounting()
    aggregate_fields = (
        "unique_units",
        "gross_mass",
        "presentations",
        "effects",
        "passing_effects",
        "failing_effects",
    )
    if not after["determined"] or any(
        getattr(decoded, field) != after[field] for field in aggregate_fields
    ):
        raise ValueError("compaction changed the declared aggregate accounting")
    return ledger


def compact_sealed_batch(
    values: Iterable[str | Fact], batch: str, origins: Iterable[str]
) -> CompactedLedger:
    """Project one self-contained batch only after origin-sealed finality.

    The closure evaluator and separately structured checker must agree on the
    final result.  The projection retains the batch's seal facts as zero-mass
    anchors, so a later window can prove its predecessor chain.  This is still
    a local semantic projection: it does not prove that another replica has a
    surviving copy or authenticate an origin declaration.
    """

    texts = sorted({canonical_pair(value)[0] for value in values})
    from .closure import sealed_query

    closed = sealed_query(texts, batch, origins)
    verified = check_sealed(texts, batch, origins)
    if (
        not closed.final
        or not verified.accepted
        or closed.closure_complete != verified.closure_complete
        or closed.unique_units != verified.unique_units
        or closed.gross_mass != verified.gross_mass
    ):
        raise ValueError("batch is not independently verified as origin-sealed")
    ledger = compact_closed_batches(texts, [batch])
    if len(ledger.summaries) != 1:
        raise ValueError("sealed projection expected exactly one batch summary")
    summary = ledger.summaries[0]
    # `ledger.accounting()` is a whole-replica aggregate and may legitimately
    # include later live batches.  Bind the projected batch result to its own
    # summary instead of confusing that global total with this window's final
    # value.  `compact_closed_batches` already checks whole-replica preservation.
    if (
        len(summary.units) != closed.unique_units
        or sum(mass for _unit, mass in summary.units) != closed.gross_mass
    ):
        raise ValueError("sealed projection changed batch accounting")
    return ledger

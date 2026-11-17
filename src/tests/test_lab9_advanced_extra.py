"""Additional Advanced/Expert tests for Lab 9 (M6/M7 hidden trap coverage)."""

from __future__ import annotations

import copy

import pytest

from lab9 import gate, stats

pytestmark = pytest.mark.student


def _report(rows, metrics, items=4, seeds=(1, 2)):
    return {
        "manifest": {"eval_set_sha": "x", "items": items, "seeds": list(seeds)},
        "rows": rows,
        "metrics": metrics,
        "evaluator_failures": [],
    }


ROWS = [
    {"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i < 2 else []}
    for i in range(4)
    for s in (1, 2)
]
SPEC = {
    "eval_set_version": "v2",
    "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True, "threshold": {"min": 0.8}}],
}


def test_advanced_integrity_flags_duplicate_rows_and_evaluator_failures():
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})

    dup_rows = copy.deepcopy(ROWS)
    dup_rows[-1] = copy.deepcopy(dup_rows[0])
    dup = _report(dup_rows, {"pass_rate": 1.0})
    assert gate.integrity_check(dup, base, SPEC)

    ev_fail = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    ev_fail["evaluator_failures"] = ["E-000@1:TrialPass:boom"]
    assert gate.integrity_check(ev_fail, base, SPEC)

    relabelled = copy.deepcopy(ROWS)
    relabelled[0]["slices"] = []
    assert gate.integrity_check(_report(relabelled, {"pass_rate": 1.0}), base, SPEC)


def test_advanced_pass_hat_k_rejects_bad_args():
    for args in [(5, 6, 1), (5, 2, 0), (3, 1, 4), (0, 0, 1), (5, -1, 1), (True, 1, 1)]:
        with pytest.raises(ValueError):
            stats.pass_hat_k(*args)

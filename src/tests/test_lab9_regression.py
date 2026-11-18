"""Core regression tests for Lab 9 (M3 trace case, FM-08, FM-05)."""

from __future__ import annotations

import pytest
from pydantic_evals.evaluators import EvaluatorContext

from lab9 import graders, trace_case

pytestmark = pytest.mark.student


def _ctx(trial, label):
    return EvaluatorContext(
        name="regression",
        inputs={},
        metadata=None,
        expected_output=label,
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )


def test_trace_case_c002_seed11_ticket_override_caught_and_fixed():
    """Trace case (docs/trace_case.md): seeded_regression C-002@11 overrides DB delay_days at step 3; fixed passes."""
    bad = trace_case.investigate("seeded_regression", "C-002", 11)
    bad_ctx = _ctx(bad["trial"], bad["label"])
    assert graders.TrialPass().evaluate(bad_ctx).value is False
    assert graders.DbFactKept().evaluate(bad_ctx).value is False
    assert graders.RefundAmountCorrect().evaluate(bad_ctx).value is False

    good = trace_case.investigate("fixed", "C-002", 11)
    good_ctx = _ctx(good["trial"], good["label"])
    assert graders.TrialPass().evaluate(good_ctx).value is True
    assert graders.DbFactKept().evaluate(good_ctx).value is True
    assert graders.RefundAmountCorrect().evaluate(good_ctx).value is True


def test_reply_matches_ledger_catches_fm08_and_passes_fixed():
    """FM-08 regression: reply stating 35.000đ when ledger holds 20.000đ (or 0) must fail."""
    case_bad = trace_case.investigate("seeded_regression", "C-008", 11)
    assert graders.ReplyMatchesLedger().evaluate(_ctx(case_bad["trial"], case_bad["label"])).value is False

    case_denied = trace_case.investigate("seeded_regression", "C-007", 11)
    assert graders.ReplyMatchesLedger().evaluate(_ctx(case_denied["trial"], case_denied["label"])).value is False

    case_good = trace_case.investigate("fixed", "C-008", 11)
    assert graders.ReplyMatchesLedger().evaluate(_ctx(case_good["trial"], case_good["label"])).value is True


def test_reply_matches_ledger_handles_alternative_vnd_formats():
    label = {"refund_vnd": 20000, "approval_ok": True}
    trial_bad = {
        "snapshot": {"refund_vnd": 20000, "refund_count": 1},
        "unexpected_rows": 0,
        "blob": "",
        "events": [{"kind": "reply", "payload": {"text": "LogiX đã hoàn 35,000 VNĐ cho bạn."}}],
        "result": {},
        "lab8_pass": True,
        "lab8_reason": "ok",
    }
    assert graders.ReplyMatchesLedger().evaluate(_ctx(trial_bad, label)).value is False

    trial_ok = {
        **trial_bad,
        "events": [{"kind": "reply", "payload": {"text": "LogiX đã hoàn 20000 đồng cho bạn."}}],
    }
    assert graders.ReplyMatchesLedger().evaluate(_ctx(trial_ok, label)).value is True


def test_proposal_matches_quote_catches_pre_deduction_c013():
    """FM-05 regression: seeded_regression C-013@11 pre-deducts proposal_amount to 0 instead of 35000."""
    bad = trace_case.investigate("seeded_regression", "C-013", 11)
    assert graders.ProposalMatchesQuote().evaluate(_ctx(bad["trial"], bad["label"])).value is False

    good = trace_case.investigate("fixed", "C-013", 11)
    assert graders.ProposalMatchesQuote().evaluate(_ctx(good["trial"], good["label"])).value is True

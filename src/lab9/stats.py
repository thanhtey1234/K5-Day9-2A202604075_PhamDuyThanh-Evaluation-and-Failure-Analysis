"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
import math
import numbers

import numpy as np
from scipy.stats import bootstrap

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def _norm(labels: Sequence[str]) -> list[str]:
    return [str(x).strip().upper() for x in labels]


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    h_norm = _norm(human)
    j_norm = _norm(judge)
    if len(h_norm) != len(j_norm):
        raise ValueError(f"length mismatch: human={len(h_norm)} vs judge={len(j_norm)}")
    tp = sum(1 for h, j in zip(h_norm, j_norm) if h == POS and j == POS)
    fp = sum(1 for h, j in zip(h_norm, j_norm) if h != POS and j == POS)
    fn = sum(1 for h, j in zip(h_norm, j_norm) if h == POS and j != POS)
    tn = sum(1 for h, j in zip(h_norm, j_norm) if h != POS and j != POS)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    """Return (precision, recall) with FAIL as positive; return 0.0 when denominator is 0."""
    cm = confusion(human, judge)
    p = cm["tp"] / (cm["tp"] + cm["fp"]) if (cm["tp"] + cm["fp"]) else 0.0
    r = cm["tp"] / (cm["tp"] + cm["fn"]) if (cm["tp"] + cm["fn"]) else 0.0
    return float(p), float(r)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]
    if n == 0:
        raise ValueError("kappa is undefined for empty input")
    p_o = (cm["tp"] + cm["tn"]) / n
    p_h_pos = (cm["tp"] + cm["fn"]) / n
    p_j_pos = (cm["tp"] + cm["fp"]) / n
    p_e = p_h_pos * p_j_pos + (1.0 - p_h_pos) * (1.0 - p_j_pos)
    if abs(1.0 - p_e) <= 1e-12:
        raise ValueError("kappa is undefined when p_e == 1 (constant labels)")
    return float((p_o - p_e) / (1.0 - p_e))


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = float(sensitivity) + float(specificity) - 1.0
    if abs(denom) <= 1e-12:
        return float(min(1.0, max(0.0, observed_rate)))
    corrected = (float(observed_rate) + float(specificity) - 1.0) / denom
    return float(min(1.0, max(0.0, corrected)))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if a_arr.shape != b_arr.shape or a_arr.ndim != 1 or a_arr.size == 0:
        raise ValueError("a and b must be non-empty 1D sequences of equal length")
    if np.array_equal(a_arr, b_arr):
        return (0.0, 0.0, 0.0)
    diff = float(np.mean(a_arr) - np.mean(b_arr))
    res = bootstrap(
        (a_arr, b_arr),
        lambda x, y, axis=-1: np.mean(x, axis=axis) - np.mean(y, axis=axis),
        paired=True,
        method="percentile",
        n_resamples=n_resamples,
        confidence_level=confidence,
        rng=np.random.default_rng(rng),
    )
    return (diff, float(res.confidence_interval.low), float(res.confidence_interval.high))


def _validate_nck(n: int, c: int, k: int) -> tuple[int, int, int]:
    for val in (n, c, k):
        if isinstance(val, bool) or not isinstance(val, numbers.Integral):
            raise ValueError(f"n, c, k must be integers, got {val!r}")
    n_i, c_i, k_i = int(n), int(c), int(k)
    if n_i <= 0 or k_i <= 0 or k_i > n_i or c_i < 0 or c_i > n_i:
        raise ValueError(f"invalid (n={n_i}, c={c_i}, k={k_i})")
    return n_i, c_i, k_i


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    n_i, c_i, k_i = _validate_nck(n, c, k)
    return float(1.0 - math.comb(n_i - c_i, k_i) / math.comb(n_i, k_i))


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    n_i, c_i, k_i = _validate_nck(n, c, k)
    return float(math.comb(c_i, k_i) / math.comb(n_i, k_i))

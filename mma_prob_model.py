
"""
mma_prob_model.py

A generic, explainable model to estimate win probabilities between two MMA fighters
using public per-fighter statistics (e.g., UFC profile metrics).

Designed for academic usage:
- Clear, well-documented feature construction.
- Transparent logistic model with domain-informed default weights.
- Optional calibration on historical fights via L2-regularized logistic regression (no external libs).
- Deterministic and unit-test friendly.

Author: ChatGPT
License: MIT
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, List, Optional
import math
import numpy as np
import random

EPS = 1e-9


# -----------------------------
# Data structures
# -----------------------------

@dataclass
class FighterStats:
    """
    Core statistics per fighter.

    Expected ranges (typical UFC profile ranges in parentheses):
    - slpm: significant strikes landed per minute (0-8)
    - sapm: significant strikes absorbed per minute (0-7)
    - strike_acc: striking accuracy fraction (0-1)      [e.g., 0.49 for 49%]
    - strike_def: striking defense fraction (0-1)
    - td_avg15: takedown attempts landed per 15 min (0-7)
    - td_acc: takedown accuracy fraction (0-1)
    - td_def: takedown defense fraction (0-1)
    - sub_avg15: submission attempts per 15 min (0-5)
    - kd_avg: knockdowns per 15 min (0-2)
    - aft_minutes: average fight time in minutes (0-25)

    Optional metadata fields can be included in the dict and will be ignored by the model.
    """
    slpm: float                    # Significant Strikes Landed per Min
    sapm: float                    # Significant Strikes Absorbed per Min
    strike_acc: float              # e.g., 0.59 for 59%
    strike_def: float              # e.g., 0.42 for 42%
    td_avg15: float                # Takedowns per 15 min
    td_acc: float                  # e.g., 0.47 for 47%
    td_def: float                  # e.g., 1.00 for 100%
    sub_avg15: float               # Submissions per 15 min
    kd_avg: float                  # Knockdowns per 15 min
    aft_minutes: float             # Average fight length

    @staticmethod
    def from_dict(d: Dict) -> "FighterStats":
        # Gracefully accept percentages in [0,100]
        def pct(v):
            if v is None:
                return 0.0
            v = float(v)
            return v/100.0 if v > 1.0 else v

        return FighterStats(
            slpm=float(d.get("slpm", 0.0)),
            sapm=float(d.get("sapm", 0.0)),
            strike_acc=pct(d.get("strike_acc", 0.0)),
            strike_def=pct(d.get("strike_def", 0.0)),
            td_avg15=float(d.get("td_avg15", 0.0)),
            td_acc=pct(d.get("td_acc", 0.0)),
            td_def=pct(d.get("td_def", 0.0)),
            sub_avg15=float(d.get("sub_avg15", 0.0)),
            kd_avg=float(d.get("kd_avg", 0.0)),
            aft_minutes=float(d.get("aft_minutes", 0.0)),
        )


# -----------------------------
# Feature engineering
# -----------------------------

def _clip(v, lo, hi):
    return max(lo, min(hi, v))

def _safe_div(a, b):
    return a / (b + EPS)

def fighter_feature_vector(f: FighterStats) -> Dict[str, float]:
    """
    Compute per-fighter primitive features (scale-stable where possible).

    Returns a dict of interpretable features.
    """
    # Striking efficiency indices
    strike_output = f.slpm
    strike_pressure = f.slpm * (1.0 - _clip(f.aft_minutes/25.0, 0, 1))  # high output + typically shorter avg fights
    strike_efficiency = f.strike_acc * _safe_div(f.slpm, f.sapm + 1.0)  # accuracy weighted by offense/defense ratio
    strike_safety = f.strike_def * _safe_div(1.0, f.sapm + 1.0)         # defense and low absorption

    # Grappling control indices
    td_pressure = f.td_avg15 * f.td_acc                                  # expected landed TDs per 15
    sub_pressure = f.sub_avg15                                           # submissions per 15
    kd_threat = f.kd_avg                                                  # knockdowns per 15

    # Durability / pacing
    durability = _clip(f.aft_minutes/25.0, 0, 1)                          # proxy for cardio/pace tolerance

    return {
        "strike_output": strike_output,
        "strike_pressure": strike_pressure,
        "strike_efficiency": strike_efficiency,
        "strike_safety": strike_safety,
        "td_pressure": td_pressure,
        "sub_pressure": sub_pressure,
        "kd_threat": kd_threat,
        "durability": durability,
        "aft_minutes": f.aft_minutes
    }

def matchup_features(a: FighterStats, b: FighterStats) -> Dict[str, float]:
    """
    Construct matchup-relative features (A vs B) to feed the logistic model.

    We build deltas and interaction terms to reflect offense vs opponent defense.
    """
    fa = fighter_feature_vector(a)
    fb = fighter_feature_vector(b)

    # Striking relative terms
    strike_eff_delta = fa["strike_efficiency"] - fb["strike_efficiency"]
    strike_safety_delta = fa["strike_safety"] - fb["strike_safety"]
    strike_output_delta = fa["strike_output"] - fb["strike_output"]
    kd_delta = fa["kd_threat"] - fb["kd_threat"]

    # Grappling relative terms (offense vs opponent defense)
    a_td_effective = a.td_avg15 * a.td_acc * (1.0 - b.td_def)            # A's TDs vs B's TDD
    b_td_effective = b.td_avg15 * b.td_acc * (1.0 - a.td_def)
    td_control_delta = a_td_effective - b_td_effective

    sub_delta = fa["sub_pressure"] - fb["sub_pressure"]

    # Pacing / durability
    durability_delta = fa["durability"] - fb["durability"]

    # Interaction: if A has strong TDs AND B has poor TDD, boost
    td_vs_tdd_interaction = a.td_avg15 * a.td_acc * (1.0 - b.td_def) - b.td_avg15 * b.td_acc * (1.0 - a.td_def)

    # Compile
    feats = {
        "bias": 1.0,
        "strike_eff_delta": strike_eff_delta,
        "strike_safety_delta": strike_safety_delta,
        "strike_output_delta": strike_output_delta,
        "kd_delta": kd_delta,
        "td_control_delta": td_control_delta,
        "sub_delta": sub_delta,
        "durability_delta": durability_delta,
        "td_vs_tdd_interaction": td_vs_tdd_interaction,
    }
    return feats


# -----------------------------
# Logistic model
# -----------------------------


DEFAULT_WEIGHTS = {
    "bias": 0.0,
    "td_control_delta": 2.2 * 0.115,
    "td_vs_tdd_interaction": 1.6 * 0.115,
    "strike_eff_delta": 1.2 * 0.115,
    "strike_safety_delta": 1.0 * 0.115,
    "strike_output_delta": 0.5 * 0.115,
    "kd_delta": 0.7 * 0.115,
    "sub_delta": 0.8 * 0.115,
    "durability_delta": 0.3 * 0.115,
}


def dot(w: Dict[str, float], x: Dict[str, float]) -> float:
    return sum(w.get(k, 0.0) * x.get(k, 0.0) for k in set(w) | set(x))

def sigmoid(z: float) -> float:
    # Numerically stable
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)

def win_probability(a: FighterStats, b: FighterStats, weights: Dict[str, float]=None) -> Tuple[float, Dict[str,float]]:
    """
    Predict P(A beats B) using logistic function over matchup features.
    Returns (prob, feature_contributions)
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    feats = matchup_features(a, b)
    z = dot(weights, feats)
    p = sigmoid(z)

    # Contribution analysis for explainability
    contrib = {k: feats.get(k,0.0) * weights.get(k,0.0) for k in feats}
    return p, contrib


# -----------------------------
# Optional: Calibration / Training
# -----------------------------

def fit_logistic_regression(X: np.ndarray, y: np.ndarray, l2: float=1.0, lr: float=0.05, epochs: int=1000) -> np.ndarray:
    """
    Simple L2-regularized logistic regression via gradient descent.
    X: [N, D] design matrix
    y: [N] labels 0/1
    Returns weight vector w [D]
    """
    N, D = X.shape
    w = np.zeros(D, dtype=float)
    for _ in range(epochs):
        z = X @ w
        p = 1 / (1 + np.exp(-z))
        # gradient: X^T (p - y) + l2 * w
        grad = X.T @ (p - y) / N + l2 * w / N
        w -= lr * grad
    return w

def build_design_matrix(pairs: List[Tuple[FighterStats, FighterStats]], feature_keys: List[str]) -> np.ndarray:
    rows = []
    for a, b in pairs:
        feats = matchup_features(a, b)
        rows.append([feats.get(k, 0.0) for k in feature_keys])
    return np.array(rows, dtype=float)

def weights_from_vector(vec: np.ndarray, feature_keys: List[str]) -> Dict[str, float]:
    return {k: float(v) for k, v in zip(feature_keys, vec)}


# -----------------------------
# Bootstrap for simple uncertainty
# -----------------------------

def bootstrap_probability(a: FighterStats, b: FighterStats, weights: Dict[str,float]=None, iters: int=1000, noise: float=0.03, seed: int=42) -> Tuple[float, Tuple[float,float]]:
    """
    Perturb inputs by small Gaussian noise and recompute probability to form a pseudo CI.
    noise: stddev proportional perturbation (e.g., 0.03 = 3%)
    Returns (mean_p, (p_low, p_high)) where CI is approx 90% empirical interval.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    rng = random.Random(seed)
    ps = []
    for _ in range(iters):
        def jitter(v): return max(0.0, v * (1.0 + rng.gauss(0.0, noise)))
        aa = FighterStats(
            slpm=jitter(a.slpm), sapm=jitter(a.sapm),
            strike_acc=min(1.0, jitter(a.strike_acc)),
            strike_def=min(1.0, jitter(a.strike_def)),
            td_avg15=jitter(a.td_avg15),
            td_acc=min(1.0, jitter(a.td_acc)),
            td_def=min(1.0, jitter(a.td_def)),
            sub_avg15=jitter(a.sub_avg15),
            kd_avg=jitter(a.kd_avg),
            aft_minutes=min(25.0, jitter(a.aft_minutes)),
        )
        bb = FighterStats(
            slpm=jitter(b.slpm), sapm=jitter(b.sapm),
            strike_acc=min(1.0, jitter(b.strike_acc)),
            strike_def=min(1.0, jitter(b.strike_def)),
            td_avg15=jitter(b.td_avg15),
            td_acc=min(1.0, jitter(b.td_acc)),
            td_def=min(1.0, jitter(b.td_def)),
            sub_avg15=jitter(b.sub_avg15),
            kd_avg=jitter(b.kd_avg),
            aft_minutes=min(25.0, jitter(b.aft_minutes)),
        )
        p, _ = win_probability(aa, bb, weights)
        ps.append(p)
    ps.sort()
    mean_p = sum(ps)/len(ps)
    lo = ps[int(0.05*len(ps))]
    hi = ps[int(0.95*len(ps))-1]
    return mean_p, (lo, hi)


# -----------------------------
# Convenience helpers
# -----------------------------

FEATURE_KEYS = [
    "bias",
    "strike_eff_delta",
    "strike_safety_delta",
    "strike_output_delta",
    "kd_delta",
    "td_control_delta",
    "sub_delta",
    "durability_delta",
    "td_vs_tdd_interaction",
]

def explain(a: FighterStats, b: FighterStats, weights: Dict[str,float]=None) -> Dict[str, float]:
    if weights is None:
        weights = DEFAULT_WEIGHTS
    _, contrib = win_probability(a, b, weights)
    return contrib

def normalize_inputs(d: Dict) -> FighterStats:
    """
    Convenience: accept either 0-1 or 0-100 for percentage-like fields.
    Keys: slpm, sapm, strike_acc, strike_def, td_avg15, td_acc, td_def, sub_avg15, kd_avg, aft_minutes
    """
    return FighterStats.from_dict(d)

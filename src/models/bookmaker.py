from typing import Tuple, Optional

from src.engine.value import implied_prob, remove_overround


def implied_probs(oh: float, od: float, oa: float) -> Optional[Tuple[float, float, float]]:
    """Convert 1x2 odds to fair probabilities after removing overround."""
    try:
        q1 = implied_prob(oh)
        qx = implied_prob(od)
        q2 = implied_prob(oa)
        f1, fx, f2 = remove_overround(q1, qx, q2)
        # return as tuple (home, draw, away)
        return f1, fx, f2
    except Exception:
        return None


def predict_from_odds(odds: Tuple[float, float, float]) -> Optional[Tuple[float, float, float]]:
    """Simple bookmaker model that just returns the implied probabilities."""
    if not odds or len(odds) != 3:
        return None
    return implied_probs(*odds)

from typing import Tuple


def avoid_upset(ph: float, pd: float, pa: float, margin: float = 0.20) -> Tuple[float, float, float]:
    """Modify probabilities to reduce likelihood of big upsets.

    If the favorite probability is very low but the underdog odds are long,
    scale down the underdog probability slightly to "play it safe".
    This is a naive heuristic; in practice one would use model-specific
    upset predictors or draw from historical upset rates.
    """
    probs = [ph, pd, pa]
    fav = max(probs)
    under = min(probs)
    if fav - under > margin:
        # scale underdog probability toward the draw/fav
        factor = 0.9
        if probs[2] == under:
            pa *= factor
        elif probs[0] == under:
            ph *= factor
        else:
            pd *= factor
        s = ph + pd + pa
        return ph/s, pd/s, pa/s
    return ph, pd, pa

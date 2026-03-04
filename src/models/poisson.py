import numpy as np
from scipy.stats import poisson

def predict_poisson(home_attack, away_defense, away_attack, home_defense, home_advantage=0.3):
    lambda_home = home_attack * away_defense * np.exp(home_advantage)
    lambda_away = away_attack * home_defense
    probs = {}
    for h in range(0, 8):
        for a in range(0, 8):
            p = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
            probs[(h, a)] = p
    # 最可能比分
    most_likely = max(probs, key=probs.get)
    win_prob = sum(p for (h,a),p in probs.items() if h > a)
    draw_prob = sum(p for (h,a),p in probs.items() if h == a)
    lose_prob = 1 - win_prob - draw_prob
    return win_prob, draw_prob, lose_prob, most_likely, lambda_home, lambda_away
import math
import pandas as pd
from src.engine.value import implied_prob, remove_overround, calc

def backtest(df: pd.DataFrame, predict_fn, ev_threshold: float = 0.03) -> dict:
    use = df.dropna(subset=["B365H","B365D","B365A","FTHG","FTAG"]).copy()
    if use.empty:
        return {"matches_used":0,"bets":0,"roi":0.0,"hit_rate":0.0,"avg_ev":0.0,"logloss":0.0}

    bets = 0
    hits = 0
    profit = 0.0
    evs = []
    ll = []

    for _, r in use.iterrows():
        home, away = r["HomeTeam"], r["AwayTeam"]
        pred = predict_fn(home, away)
        p1, px, p2 = pred["p_home"], pred["p_draw"], pred["p_away"]

        oh, od, oa = float(r["B365H"]), float(r["B365D"]), float(r["B365A"])
        q1, qx, q2 = implied_prob(oh), implied_prob(od), implied_prob(oa)
        f1, fx, f2 = remove_overround(q1, qx, q2)

        c1 = calc(p1, oh, f1, "H")
        cx = calc(px, od, fx, "D")
        c2 = calc(p2, oa, f2, "A")
        best = max([c1, cx, c2], key=lambda x: x.ev)

        hg, ag = int(r["FTHG"]), int(r["FTAG"])
        if hg > ag:
            ll.append(-math.log(max(p1, 1e-6)))
        elif hg == ag:
            ll.append(-math.log(max(px, 1e-6)))
        else:
            ll.append(-math.log(max(p2, 1e-6)))

        if best.ev < ev_threshold:
            continue

        bets += 1
        evs.append(best.ev)

        win = (best.pick=="H" and hg>ag) or (best.pick=="D" and hg==ag) or (best.pick=="A" and hg<ag)
        if win:
            hits += 1
            profit += (best.odds - 1.0)
        else:
            profit -= 1.0

    roi = profit / bets if bets else 0.0
    hit_rate = hits / bets if bets else 0.0
    avg_ev = sum(evs)/len(evs) if evs else 0.0
    logloss = sum(ll)/len(ll) if ll else 0.0

    return {
        "matches_used": int(len(use)),
        "bets": int(bets),
        "roi": round(roi, 4),
        "hit_rate": round(hit_rate, 4),
        "avg_ev": round(avg_ev, 4),
        "logloss": round(logloss, 4),
    }

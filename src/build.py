import os
import json
import pandas as pd
from datetime import datetime, timezone

from src.data.football_data import season_code_for, prev_season, fetch_league, split_played_future, pick_1x2_odds
from src.models.poisson_elo import run_elo, fit_poisson, FitModels, predict
from src.engine.value import implied_prob, remove_overround, calc, score, label
from src.backtest.backtest import backtest

LEAGUES = {
    "E0": "EPL",
    "SP1": "LaLiga",
    "I1": "SerieA",
    "D1": "Bundesliga",
    "F1": "Ligue1",
}

FUTURE_WINDOW_DAYS = 14
EV_THRESHOLD_BT = 0.03

def main():
    os.makedirs("site/data", exist_ok=True)
    with open("site/.nojekyll", "w", encoding="utf-8") as f:
        f.write("")

    now = datetime.now(timezone.utc)
    sc = season_code_for(now.date())
    sc_prev = prev_season(sc, 1)

    played_parts = []
    future_parts = []

    for div, lname in LEAGUES.items():
        for season in [sc, sc_prev]:
            try:
                df = fetch_league(div, season)
                played, future = split_played_future(df)
                played["Div"] = div
                played["League"] = lname
                future["Div"] = div
                future["League"] = lname
                played_parts.append(played)
                if season == sc:
                    future_parts.append(future)
            except Exception as e:
                print(f"WARN fetch {div} {season} failed:", e)

    if not played_parts:
        raise RuntimeError("No played data fetched. Check network/source.")

    played_df = pd.concat(played_parts, ignore_index=True)

    # 训练（全联赛一起训练，更稳；后续你想拆成分联赛也行）
    elo = run_elo(played_df[["Date","HomeTeam","AwayTeam","FTHG","FTAG"]].copy())
    m_h, m_a = fit_poisson(played_df[["HomeTeam","AwayTeam","FTHG","FTAG"]].copy())
    models = FitModels(home=m_h, away=m_a, elo=elo)

    # 未来赛程
    if future_parts:
        fx = pd.concat(future_parts, ignore_index=True)
        fx = fx.dropna(subset=["Date","HomeTeam","AwayTeam"]).copy()
        fx = fx[fx["Date"] >= pd.Timestamp(now.date())]
        fx = fx[fx["Date"] <= pd.Timestamp(now.date()) + pd.Timedelta(days=FUTURE_WINDOW_DAYS)]
        fx = fx.sort_values(["Date","League","HomeTeam"])
    else:
        fx = pd.DataFrame()

    rows = []
    for _, r in fx.iterrows():
        home, away = str(r["HomeTeam"]), str(r["AwayTeam"])
        pred = predict(models, home, away)

        oh, od, oa, book = pick_1x2_odds(r)

        best = None
        s = None
        lab = "-"
        pick = None
        evv = None
        kellyv = None

        why = f"EloΔ {pred['elo_diff']:.0f} | xG {pred['xg_home']:.2f}-{pred['xg_away']:.2f}"

        if oh and od and oa:
            q1, qx, q2 = implied_prob(oh), implied_prob(od), implied_prob(oa)
            f1, fx_, f2 = remove_overround(q1, qx, q2)

            c1 = calc(pred["p_home"], oh, f1, "主胜")
            cx = calc(pred["p_draw"], od, fx_, "平")
            c2 = calc(pred["p_away"], oa, f2, "客胜")
            best = max([c1, cx, c2], key=lambda x: x.ev)

            s = score(best)
            lab = label(s)
            pick = best.pick
            evv = round(best.ev, 4)
            kellyv = round(min(best.kelly, 0.08), 4)  # 凯利封顶 8%
            why = f"{why} | Odds({book}) {oh}/{od}/{oa} | Gap {best.gap:+.3f}"

        rows.append({
            "date": str(pd.to_datetime(r["Date"]).date()),
            "league": r.get("League",""),
            "div": r.get("Div",""),
            "home": home,
            "away": away,
            "xg_home": round(pred["xg_home"], 2),
            "xg_away": round(pred["xg_away"], 2),
            "p_home": round(pred["p_home"], 4),
            "p_draw": round(pred["p_draw"], 4),
            "p_away": round(pred["p_away"], 4),
            "p_over25": round(pred["p_over25"], 4),
            "p_btts": round(pred["p_btts"], 4),
            "most_likely_score": pred["most_likely_score"],
            "odds_win": oh,
            "odds_draw": od,
            "odds_lose": oa,
            "book": book,
            "pick": pick,
            "ev": evv,
            "kelly": kellyv,
            "score": s,
            "label": lab,
            "why": why,
        })

    # 回测（历史 B365）
    bt = backtest(played_df, lambda h,a: predict(models, h, a), ev_threshold=EV_THRESHOLD_BT)

    top = sorted([x for x in rows if x["score"] is not None], key=lambda z: z["score"], reverse=True)[:50]

    payload = {
        "meta": {
            "generated_at_utc": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "python": "3.12",
            "seasons_used": [sc, sc_prev],
            "window_days": FUTURE_WINDOW_DAYS,
            "note": "Poisson+Elo + scoreline matrix + EV/Kelly + backtest (football-data.co.uk)",
        },
        "stats": {
            "fixtures": len(rows),
            "top": len(top),
            "backtest": bt,
        },
        "top_picks": top,
        "all": rows,
    }

    with open("site/data/picks.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("OK: site/data/picks.json written. fixtures=", len(rows), "top=", len(top))

if __name__ == "__main__":
    main()

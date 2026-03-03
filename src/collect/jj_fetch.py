import json, re
from typing import Any, Dict, List, Optional
from pathlib import Path

import requests
from requests.exceptions import SSLError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JSONP_RE = re.compile(r"^[^(]*\((.*)\)\s*;?\s*$", re.S)

HOME_KEYS = ["home","Home","HomeTeam","homeTeam","host","Host","hostTeam","主队","主","hn","h_cn","hname","home_name","teamHome","team1","t1","hteam"]
AWAY_KEYS = ["away","Away","AwayTeam","awayTeam","guest","Guest","guestTeam","客队","客","an","a_cn","aname","away_name","teamAway","team2","t2","ateam"]

def _get(url: str, headers: Dict[str,str], timeout=20) -> requests.Response:
    try:
        return requests.get(url, headers=headers, timeout=timeout)
    except SSLError:
        return requests.get(url, headers=headers, timeout=timeout, verify=False)

def _parse_json_or_jsonp(text: str) -> Any:
    t = text.strip()
    m = JSONP_RE.match(t)
    if m:
        return json.loads(m.group(1))
    return json.loads(t)

def _walk(obj: Any) -> List[Dict]:
    out = []
    if isinstance(obj, dict):
        keys = set(obj.keys())
        has_home = any(k in keys for k in HOME_KEYS)
        has_away = any(k in keys for k in AWAY_KEYS)
        if has_home and has_away:
            out.append(obj)
        for v in obj.values():
            out.extend(_walk(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_walk(v))
    return out

def _pick(d: Dict, ks: List[str]) -> str:
    for k in ks:
        if k in d and d[k] not in [None,""]:
            return str(d[k])
    return ""

def _f(x) -> Optional[float]:
    try:
        if x is None: return None
        v = float(str(x).strip())
        return v if v > 1 else None
    except:
        return None

def _odds_1x2(d: Dict) -> Dict[str, Optional[float]]:
    for a,b,c in [
        ("sp_3","sp_1","sp_0"),
        ("win","draw","lose"),
        ("h","d","a"),
        ("odds_win","odds_draw","odds_lose"),
        ("homeWin","draw","awayWin"),
        ("W","D","L"),
    ]:
        ow,od,oa=_f(d.get(a)),_f(d.get(b)),_f(d.get(c))
        if ow and od and oa:
            return {"win":ow,"draw":od,"lose":oa}
    for k in ["odds","sp","had","h2h","1x2"]:
        v = d.get(k)
        if isinstance(v,(list,tuple)) and len(v)>=3:
            ow,od,oa=_f(v[0]),_f(v[1]),_f(v[2])
            if ow and od and oa: return {"win":ow,"draw":od,"lose":oa}
        if isinstance(v,dict):
            ow=_f(v.get("win") or v.get("3") or v.get("W"))
            od=_f(v.get("draw") or v.get("1") or v.get("D"))
            oa=_f(v.get("lose") or v.get("0") or v.get("L"))
            if ow and od and oa: return {"win":ow,"draw":od,"lose":oa}
    return {"win":None,"draw":None,"lose":None}

def fetch(api_url: str, headers: Dict[str,str]) -> Dict[str, Any]:
    r = _get(api_url, headers=headers, timeout=25)
    data = _parse_json_or_jsonp(r.text)

    items = []
    for d in _walk(data):
        home = _pick(d, HOME_KEYS)
        away = _pick(d, AWAY_KEYS)
        if not home or not away:
            continue
        league = _pick(d, ["league","League","l_cn","联赛","赛事","competition","matchType","type"])
        time_  = _pick(d, ["time","Time","start_time","bt","开赛","比赛时间","dateTime","kickoff","matchTime"])
        odds = _odds_1x2(d)
        handicap = _pick(d, ["handicap","rq","goalline","让球"])
        items.append({
            "league": league, "time": time_,
            "home": home, "away": away,
            "odds_win": odds["win"], "odds_draw": odds["draw"], "odds_lose": odds["lose"],
            "handicap": handicap
        })

    uniq = {}
    for m in items:
        uniq[(m["home"],m["away"],m["time"])] = m
    return {"raw": data, "matches": list(uniq.values())}


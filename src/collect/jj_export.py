import json
from datetime import datetime, timezone
from pathlib import Path

from src.collect.jj_discover import discover
from src.collect.jj_fetch import fetch

def main():
    cfg_path = Path("data/jj_config.json")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    home_url = cfg.get("home_url","https://jj.shshier.com/#/?tabindex=0")
    api_url = (cfg.get("api_url") or "").strip()
    headers = cfg.get("headers") or {}

    meta = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "jj.shshier.com",
        "home_url": home_url,
        "api_url": api_url
    }

    payload = {"meta": meta, "matches": []}

    try:
        if not api_url:
            api_url, headers2, sample = discover(home_url)
            headers = headers2 or headers
            cfg["api_url"] = api_url
            cfg["headers"] = headers
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
            payload["meta"]["api_url"] = api_url
            payload["meta"]["discover_sample"] = sample

        if not api_url:
            raise RuntimeError("JJ api_url still empty (site may block). Run once in Codespaces: python -m src.collect.jj_export, then check data/jj_config.json")

        res = fetch(api_url=api_url, headers=headers)
        payload["matches"] = res["matches"]
        payload["meta"]["count"] = len(payload["matches"])
        if payload["meta"]["count"] == 0:
            payload["meta"]["note"] = "Fetched JSON but extracted 0 matches (field names changed). Raw saved for debug."
            Path("site/data/jj_raw.json").write_text(json.dumps(res["raw"], ensure_ascii=False)[:200000], encoding="utf-8")

    except Exception as e:
        payload["meta"]["count"] = 0
        payload["meta"]["error"] = str(e)

    Path("site/data").mkdir(parents=True, exist_ok=True)
    Path("site/data/jczq.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK: site/data/jczq.json count=", payload["meta"]["count"])

if __name__ == "__main__":
    main()


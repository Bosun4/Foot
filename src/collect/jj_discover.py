import json, re, time, os, hashlib
from pathlib import Path
from urllib.parse import urljoin
from typing import Dict, List, Optional, Tuple

import requests
from requests.exceptions import SSLError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KEYWORDS = ["match","odds","jczq","lottery","bonus","sp_","home","away","主队","客队","赔率"]

def _get(url: str, headers: Dict[str,str], timeout=20) -> requests.Response:
    try:
        return requests.get(url, headers=headers, timeout=timeout)
    except SSLError:
        return requests.get(url, headers=headers, timeout=timeout, verify=False)

def _cache_path(key: str) -> Path:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    return Path(f"data/cache/jj_{h}.json")

def _load_cache(key: str, ttl: int = 3600) -> Optional[dict]:
    p = _cache_path(key)
    if not p.exists(): return None
    if time.time() - p.stat().st_mtime > ttl: return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return None

def _save_cache(key: str, obj: dict) -> None:
    _cache_path(key).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def _extract_scripts(html: str) -> List[str]:
    # 常见：<script src=/assets/app.xxx.js> / <script defer src="...js">
    return re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)

def _extract_candidates(text: str, base: str) -> List[str]:
    # 1) 绝对 URL
    abs_urls = set(re.findall(r'https?://[^\s"\'<>]+', text))
    # 2) 转义路径：\/api\/xxx
    esc = set(re.findall(r'\\/(?:prod-)?api\\/[A-Za-z0-9_\\/-]+', text))
    esc |= set(re.findall(r'\\/gateway\\/[A-Za-z0-9_\\/-]+', text))
    esc = {s.replace("\\/", "/") for s in esc}
    # 3) 含关键词的相对路径
    rel = set(re.findall(r'/(?:[^\s"\'<>]{0,160})(?:api|match|odds|jczq|lottery|bonus|vote|sp_)[^\s"\'<>]{0,160}', text, flags=re.I))

    def clean(s: str) -> str:
        return s.strip('"\';),> ')

    cands = []
    for u in abs_urls:
        u = clean(u)
        if any(k in u.lower() for k in ["api","match","odds","jczq","lottery","bonus","sp"]):
            cands.append(u)
    for p in list(esc) + list(rel):
        p = clean(p)
        if p.startswith("//"):
            cands.append("https:" + p)
        elif p.startswith("http"):
            cands.append(p)
        else:
            cands.append(urljoin(base, p))

    # 去重限量
    out, seen = [], set()
    for u in cands:
        if u in seen: 
            continue
        seen.add(u)
        out.append(u)
    return out[:260]

def discover(home_url: str) -> Tuple[str, Dict[str,str], str]:
    """
    返回 (api_url, headers, sample)
    找不到就返回 ("", headers, "")
    """
    cache_key = f"discover|{home_url}"
    cached = _load_cache(cache_key, ttl=6*3600)
    if cached and cached.get("api_url"):
        return cached["api_url"], cached.get("headers", {}), cached.get("sample","")

    base = "https://jj.shshier.com/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": base
    }

    html = _get(base, headers=headers, timeout=25).text
    scripts = _extract_scripts(html)
    # 把首页也纳入扫描
    blobs = [html]

    # 下载前 25 个 js（足够覆盖）
    js_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": base
    }
    for s in scripts[:25]:
        url = urljoin(base, s)
        try:
            blobs.append(_get(url, headers=js_headers, timeout=25).text)
        except:
            pass

    big = "\n".join(blobs)
    cands = _extract_candidates(big, base)

    test_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": base,
        "X-Requested-With": "XMLHttpRequest"
    }

    def looks_json(resp_text: str) -> bool:
        t = resp_text.strip()
        return t.startswith("{") or t.startswith("[")

    def looks_data(resp_text: str) -> bool:
        t = resp_text[:3000].lower()
        return any(k in t for k in [x.lower() for x in KEYWORDS])

    best = ""
    sample = ""
    for u in cands:
        try:
            r = _get(u, headers=test_headers, timeout=15)
            txt = r.text
            if looks_json(txt) and looks_data(txt):
                best = u
                sample = txt[:260].replace("\n"," ")
                break
        except:
            continue

    payload = {"api_url": best, "headers": test_headers, "sample": sample}
    _save_cache(cache_key, payload)
    return best, test_headers, sample

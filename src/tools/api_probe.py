"""
用 Playwright 探测网页加载时的 JSON 接口（抓包用）。

使用：
  pip install -r requirements-probe.txt
  python -m playwright install chromium
  python -m src.tools.api_probe "https://example.com"
"""
import sys
from playwright.sync_api import sync_playwright

def main():
    if len(sys.argv) < 2:
        print('Usage: python -m src.tools.api_probe "<url>"')
        raise SystemExit(1)
    url = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def on_response(resp):
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                print("JSON:", resp.status, resp.url)

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        browser.close()

if __name__ == "__main__":
    main()

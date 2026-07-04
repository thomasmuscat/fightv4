from __future__ import annotations
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from fightiq.config import CACHE_DIR, DEBUG_DIR, SLEEP_SECONDS, USE_CACHE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

def safe_name(url: str) -> str:
    return url.replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_").replace(":", "_")

def cache_path_for_url(url: str) -> Path:
    return CACHE_DIR / f"{safe_name(url)}.html"

@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
def fetch_html(url: str, debug_name: str | None = None) -> str:
    CACHE_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)
    path = cache_path_for_url(url)

    if USE_CACHE and path.exists() and path.stat().st_size > 0:
        html = path.read_text(encoding="utf-8", errors="ignore")
        print(f"[http] cache url={url} bytes={len(html)}")
        return html

    time.sleep(SLEEP_SECONDS)
    print(f"[http] GET {url}")
    response = requests.get(url, headers=HEADERS, timeout=60, allow_redirects=True)
    print(f"[http] status={response.status_code} final_url={response.url} bytes={len(response.text)}")
    response.raise_for_status()
    html = response.text

    path.write_text(html, encoding="utf-8")
    if debug_name:
        (DEBUG_DIR / debug_name).write_text(html, encoding="utf-8")
        (DEBUG_DIR / f"{debug_name}.meta.txt").write_text(
            f"url={url}\nfinal_url={response.url}\nstatus={response.status_code}\nbytes={len(html)}\ncontent_type={response.headers.get('content-type')}\n",
            encoding="utf-8"
        )
    return html

def soup_from_url(url: str, debug_name: str | None = None) -> BeautifulSoup:
    return BeautifulSoup(fetch_html(url, debug_name=debug_name), "lxml")

from __future__ import annotations
import pandas as pd
from bs4 import BeautifulSoup

from fightiq.config import EVENTS_URL
from fightiq.scraper.http import soup_from_url
from fightiq.utils.text import clean_text, parse_date, slugify, stable_uuid

def parse_events_page(soup: BeautifulSoup) -> list[dict]:
    rows = soup.select("tr.b-statistics__table-row")
    if not rows:
        rows = [tr for tr in soup.select("tr") if tr.select_one('a[href*="/event-details/"]')]

    events = []
    for row in rows:
        link = row.select_one('a[href*="/event-details/"]') or row.select_one("a")
        if not link:
            continue
        name = clean_text(link.get_text(" ", strip=True))
        if not name:
            continue
        slug = slugify(name)

        date_el = row.select_one(".b-statistics__date")
        date = clean_text(date_el.get_text(" ", strip=True)) if date_el else None
        cols = row.select("td")
        location = clean_text(cols[-1].get_text(" ", strip=True)) if cols else None

        city, country = None, None
        if location and "," in location:
            parts = [p.strip() for p in location.split(",")]
            city = parts[0]
            country = parts[-1]
        elif location:
            country = location

        events.append({
            "id": stable_uuid("event", slug),
            "name": name,
            "slug": slug,
            "event_date": parse_date(date),
            "venue": None,
            "city": city,
            "country": country,
            "ufcstats_url": link.get("href"),
            "data_source": "ufcstats_github_actions_v4",
        })
    return events

def scrape_events() -> pd.DataFrame:
    print("[events] scraping completed events")
    soup = soup_from_url(EVENTS_URL, debug_name="events_debug.html")
    print(f"[events] title={soup.title.get_text(strip=True) if soup.title else 'NO_TITLE'}")
    print(f"[events] table_rows={len(soup.select('tr'))} event_links={len(soup.select('a[href*=\"/event-details/\"]'))}")
    events = parse_events_page(soup)
    df = pd.DataFrame(events)
    if not df.empty:
        df = df.drop_duplicates("slug").reset_index(drop=True)
    print(f"[events] found={len(df)}")
    return df

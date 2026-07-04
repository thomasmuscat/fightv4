from __future__ import annotations

import pandas as pd
from bs4 import BeautifulSoup

from fightiq.config import FIGHTERS_URL, LETTERS, MAX_FIGHTERS
from fightiq.scraper.http import soup_from_url
from fightiq.utils.text import (
    clean_text,
    height_to_cm,
    parse_date,
    reach_to_cm,
    slugify,
    stable_uuid,
    to_float,
    to_int,
)


def parse_fighter_list_page(soup: BeautifulSoup) -> list[dict]:
    rows = soup.select("tr.b-statistics__table-row")

    if not rows:
        rows = [tr for tr in soup.select("tr") if tr.select_one('a[href*="/fighter-details/"]')]

    fighters = []

    for row in rows:
        cols = row.select("td")
        links = row.select('a[href*="/fighter-details/"]')

        if len(cols) < 5 or not links:
            continue

        first = clean_text(links[0].get_text(" ", strip=True)) if len(links) >= 1 else None
        last = clean_text(links[1].get_text(" ", strip=True)) if len(links) >= 2 else None

        if first and last and first != last:
            full_name = f"{first} {last}"
        else:
            cell_texts = [clean_text(td.get_text(" ", strip=True)) for td in cols]
            cell_texts = [x for x in cell_texts if x]
            if len(cell_texts) >= 2:
                full_name = f"{cell_texts[0]} {cell_texts[1]}"
            else:
                continue

        slug = slugify(full_name)

        height = cols[3].get_text(" ", strip=True) if len(cols) > 3 else None
        reach = cols[5].get_text(" ", strip=True) if len(cols) > 5 else None
        stance = cols[6].get_text(" ", strip=True) if len(cols) > 6 else None
        wins = cols[7].get_text(" ", strip=True) if len(cols) > 7 else None
        losses = cols[8].get_text(" ", strip=True) if len(cols) > 8 else None
        draws = cols[9].get_text(" ", strip=True) if len(cols) > 9 else None

        fighters.append(
            {
                "id": stable_uuid("fighter", slug),
                "full_name": full_name,
                "nickname": None,
                "slug": slug,
                "nationality": None,
                "country_code": None,
                "date_of_birth": None,
                "stance": clean_text(stance),
                "height_cm": height_to_cm(height),
                "reach_cm": reach_to_cm(reach),
                "weight_class": None,
                "wins": to_int(wins),
                "losses": to_int(losses),
                "draws": to_int(draws),
                "no_contests": 0,
                "wins_ko": None,
                "wins_sub": None,
                "wins_decision": None,
                "losses_ko": None,
                "losses_sub": None,
                "losses_decision": None,
                "slpm": None,
                "sapm": None,
                "strike_accuracy": None,
                "strike_defense": None,
                "takedown_avg": None,
                "takedown_accuracy": None,
                "takedown_defense": None,
                "submission_avg": None,
                "elo_rating": 1500,
                "current_rank": None,
                "is_champion": False,
                "is_active": True,
                "photo_url": None,
                "ufcstats_url": links[0].get("href") if links else None,
                "data_source": "ufcstats_github_actions_v4",
            }
        )

    return fighters


def parse_fighter_detail(url: str) -> dict:
    soup = soup_from_url(url)
    detail = {}

    nickname = soup.select_one(".b-content__Nickname")
    if nickname:
        detail["nickname"] = clean_text(nickname.get_text(" ", strip=True))

    for item in soup.select(".b-list__box-list-item"):
        text = clean_text(item.get_text(" ", strip=True))

        if not text or ":" not in text:
            continue

        key, value = text.split(":", 1)
        key = key.lower().strip()
        value = clean_text(value)

        if "height" in key:
            detail["height_cm"] = height_to_cm(value)
        elif "reach" in key:
            detail["reach_cm"] = reach_to_cm(value)
        elif "stance" in key:
            detail["stance"] = value
        elif "dob" in key:
            detail["date_of_birth"] = parse_date(value)
        elif "slpm" in key:
            detail["slpm"] = to_float(value)
        elif "sapm" in key:
            detail["sapm"] = to_float(value)
        elif "str. acc" in key:
            detail["strike_accuracy"] = to_float(value)
        elif "str. def" in key:
            detail["strike_defense"] = to_float(value)
        elif "td avg" in key:
            detail["takedown_avg"] = to_float(value)
        elif "td acc" in key:
            detail["takedown_accuracy"] = to_float(value)
        elif "td def" in key:
            detail["takedown_defense"] = to_float(value)
        elif "sub. avg" in key:
            detail["submission_avg"] = to_float(value)

    return detail


def scrape_fighters(include_details: bool = True) -> pd.DataFrame:
    all_fighters = []
    seen = set()

    for letter in LETTERS:
        url = FIGHTERS_URL.format(char=letter)
        print(f"[fighters] list {letter.upper()}")

        soup = soup_from_url(
            url,
            debug_name=f"fighters_{letter}_debug.html" if letter == "a" else None,
        )

        title = soup.title.get_text(strip=True) if soup.title else "NO_TITLE"
        table_rows = len(soup.select("tr"))
        detail_links = len(soup.select('a[href*="/fighter-details/"]'))

        print(f"[fighters] title={title}")
        print(f"[fighters] table_rows={table_rows} detail_links={detail_links}")

        found = parse_fighter_list_page(soup)

        print(f"[fighters] {letter.upper()} found={len(found)}")

        for fighter in found:
            if fighter["slug"] not in seen:
                seen.add(fighter["slug"])
                all_fighters.append(fighter)

    limit = int(MAX_FIGHTERS) if MAX_FIGHTERS else len(all_fighters)

    if include_details:
        for idx, fighter in enumerate(all_fighters[:limit], start=1):
            url = fighter.get("ufcstats_url")

            if not url:
                continue

            print(f"[fighters] detail {idx}/{limit} {fighter['full_name']}")

            try:
                detail = parse_fighter_detail(url)

                for key, value in detail.items():
                    if value is not None:
                        fighter[key] = value

            except Exception as exc:
                print(f"[fighters] detail failed {fighter['full_name']}: {exc}")

    df = pd.DataFrame(all_fighters)

    if not df.empty:
        df = df.drop_duplicates("slug").sort_values("full_name").reset_index(drop=True)

    return df

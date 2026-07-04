from __future__ import annotations
from datetime import datetime
import pandas as pd

from fightiq.config import EXPORT_DIR, DEBUG_DIR, UPLOAD_TO_SUPABASE, MAX_EVENTS, MAX_FIGHTERS, MAX_FIGHTS
from fightiq.scraper.fighters import scrape_fighters
from fightiq.scraper.events import scrape_events
from fightiq.scraper.fights import scrape_fights
from fightiq.database.exporter import write_csv, write_json
from fightiq.database.supabase_client import upsert_dataframe

def main():
    EXPORT_DIR.mkdir(exist_ok=True)
    DEBUG_DIR.mkdir(exist_ok=True)

    report = {
        "started_at": datetime.utcnow().isoformat(),
        "upload_to_supabase": UPLOAD_TO_SUPABASE,
        "limits": {
            "max_events": MAX_EVENTS,
            "max_fighters": MAX_FIGHTERS,
            "max_fights": MAX_FIGHTS,
        }
    }

    fighters = scrape_fighters(include_details=True)
    write_csv("fighters", fighters)
    report["fighters"] = len(fighters)

    fighter_stats_cols = [
        "id", "full_name", "slug", "slpm", "sapm", "strike_accuracy",
        "strike_defense", "takedown_avg", "takedown_accuracy",
        "takedown_defense", "submission_avg", "elo_rating"
    ]
    fighter_stats = fighters[[c for c in fighter_stats_cols if c in fighters.columns]].copy() if not fighters.empty else pd.DataFrame()
    write_csv("fighter_stats", fighter_stats)

    events = scrape_events()
    write_csv("events", events)
    report["events"] = len(events)

    fights, fight_stats = scrape_fights(events, fighters)
    write_csv("fights", fights)
    write_csv("fight_stats", fight_stats)
    report["fights"] = len(fights)
    report["fight_stats"] = len(fight_stats)

    rankings = pd.DataFrame(columns=["id", "fighter_id", "division", "rank", "ranking_date", "data_source"])
    predictions = pd.DataFrame(columns=[
        "id", "fighter_a_id", "fighter_b_id", "fighter_a_win_probability",
        "fighter_b_win_probability", "ko_probability", "submission_probability",
        "decision_probability", "confidence_score", "explanation",
        "engine_version", "data_source"
    ])
    write_csv("rankings", rankings)
    write_csv("predictions", predictions)

    if UPLOAD_TO_SUPABASE:
        upsert_dataframe("fighters", fighters)
        upsert_dataframe("events", events)
        upsert_dataframe("fights", fights)
        upsert_dataframe("fight_stats", fight_stats)

    report["finished_at"] = datetime.utcnow().isoformat()
    write_json("import_report", report)
    print("[done]", report)

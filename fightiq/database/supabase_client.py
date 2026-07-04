from __future__ import annotations
import pandas as pd
from supabase import create_client
from fightiq.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

def get_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def upsert_dataframe(table: str, df: pd.DataFrame, chunk_size: int = 300):
    if df.empty:
        print(f"[supabase] skip empty table={table}")
        return
    client = get_client()
    records = df.where(pd.notnull(df), None).to_dict("records")
    for start in range(0, len(records), chunk_size):
        chunk = records[start:start + chunk_size]
        print(f"[supabase] upsert table={table} rows={len(chunk)}")
        client.table(table).upsert(chunk).execute()

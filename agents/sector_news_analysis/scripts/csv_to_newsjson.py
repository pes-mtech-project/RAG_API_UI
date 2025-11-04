#!/usr/bin/env python3
"""Convert a CSV with news rows to the JSON format consumed by Agent-1.

Expected CSV columns (header row required):
  id, sector, headline, summary, datetime, source, region

- Adds/derives `date_key` = YYYY-MM-DD from `datetime` if missing.
- Outputs a JSON list to the provided output path.

Usage:
  python scripts/csv_to_newsjson.py input.csv out.json
"""

import sys
import csv
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

def iso_to_datekey(iso: str) -> str:
    if not iso:
        raise ValueError("Missing datetime for date_key")
    if iso.endswith('Z'):
        iso = iso.replace('Z', '+00:00')
    return datetime.fromisoformat(iso).date().isoformat()

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/csv_to_newsjson.py <input.csv> <out.json>", file=sys.stderr)
        sys.exit(2)

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if not inp.exists():
        print(f"Error: {inp} not found", file=sys.stderr)
        sys.exit(1)

    rows_out = []
    with inp.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {"id","sector","headline","summary","datetime","source","region"}
        missing = required - set([c.strip() for c in reader.fieldnames or []])
        if missing:
            print(f"Error: CSV missing columns: {sorted(missing)}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            # trim keys
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k,v in row.items()}
            if not row.get("id"):
                # Skip empty lines
                continue
            dk = row.get("date_key") or iso_to_datekey(row["datetime"])
            rows_out.append({
                "id": row["id"],
                "headline": row["headline"],
                "summary": row["summary"],
                "datetime": row["datetime"],
                "source": row["source"],
                "region": row["region"],
                "sector": row.get("sector") or None,
                "date_key": dk,
            })

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(rows_out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(rows_out)} news items → {out}")

if __name__ == "__main__":
    main()

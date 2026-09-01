"""Merge independent discovery outputs while preserving every source row."""

from __future__ import annotations

import argparse
import json

from src.utilities.common import path_for, read_jsonl, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge cached discovery JSONL outputs")
    parser.add_argument("--base", default="data/raw/candidates.jsonl")
    parser.add_argument("--extra", default="data/raw/industrial_estate_candidates.jsonl")
    parser.add_argument("--output", default="data/raw/candidates.jsonl")
    args = parser.parse_args()
    base = read_jsonl(args.base)
    extra = read_jsonl(args.extra)
    rows = []
    seen: set[str] = set()
    for row in base + extra:
        key = row.get("raw_candidate_id") or json.dumps(row, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    write_jsonl(args.output, rows)
    print(f"Merged {len(base)} base + {len(extra)} extra rows into {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

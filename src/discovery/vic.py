"""Fetch the configured Tehran-province industrial-estate indexes only.

This narrow rerunnable stage is useful when the broad discovery sources are
already cached or when a source needs to be refreshed independently.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter

from src.discovery.run import parse_vic_zone
from src.utilities.common import DEFAULT_PROXY, RateLimiter, fetch_url, now_iso, parse_simple_yaml, path_for, write_json, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover public company/activity rows from VIC industrial-estate indexes")
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument("--proxy", default=None)
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    config = parse_simple_yaml(args.config)
    proxy = args.proxy or config.get("direct_proxy") or DEFAULT_PROXY
    if not args.skip_preflight:
        result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy], capture_output=True, text=True, check=False)
        print(result.stdout[-3000:])
        if result.returncode != 0:
            print("VIC discovery stopped: direct-proxy preflight failed.", file=sys.stderr)
            return 2
    vic_cfg = next((item for item in (config.get("discovery") or []) if item.get("name") == "vic_industrial_estates"), {})
    entries = vic_cfg.get("urls") or []
    limiter = RateLimiter(float(config.get("rate_limit_seconds") or 0.35))
    rows: list[dict] = []
    runs: list[dict] = []
    errors: list[dict] = []
    for entry in entries:
        zone = entry.get("name") if isinstance(entry, dict) else "Industrial estate"
        url = entry.get("url") if isinstance(entry, dict) else entry
        response = fetch_url(url, proxy=proxy, limiter=limiter, timeout=35.0, max_bytes=4_000_000)
        parsed = parse_vic_zone(response.get("body", ""), url, zone) if response.get("body") else []
        rows.extend(parsed)
        runs.append({"source": "vic_industrial_estates", "zone": zone, "url": url, "rows": len(parsed), "status": response.get("status"), "elapsed_ms": response.get("elapsed_ms")})
        if response.get("error"):
            errors.append({"url": url, "error": response.get("error")})
        print(f"VIC {zone}: {len(parsed)} rows status={response.get('status')}")
    write_jsonl(path_for("data", "raw", "industrial_estate_candidates.jsonl"), rows)
    write_json(path_for("data", "raw", "industrial_estate_sources.json"), {"generated_at": now_iso(), "runs": runs, "errors": errors, "proxy": proxy})
    summary = {
        "completed_at": now_iso(),
        "candidate_count": len(rows),
        "unique_candidate_count": len({row.get("raw_candidate_id") for row in rows}),
        "source_counts": dict(Counter(row.get("source_type") for row in rows)),
        "zone_counts": dict(Counter(row.get("industrial_zone") for row in rows)),
        "runs": runs,
        "errors": errors,
        "proxy": proxy,
    }
    write_json(path_for("logs", f"vic-discovery-{now_iso().replace(':', '').replace('-', '')}.json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

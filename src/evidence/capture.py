from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.utilities.common import DEFAULT_PROXY, domain_of, now_iso, path_for, read_jsonl, stable_hash, write_json, write_jsonl


CLI = str(Path.home() / ".codex/skills/playwright/scripts/playwright_cli.sh")
CONFIG = "config/playwright.headless.json"
NON_CORPORATE_SITE_DOMAINS = {
    "rubika.ir", "aparat.com", "instagram.com", "facebook.com", "linkedin.com",
    "youtube.com", "telegram.me", "t.me", "x.com", "twitter.com",
}


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:80] or "page"


def corporate_url(url: str | None) -> bool:
    domain = domain_of(url)
    return bool(domain and domain not in NON_CORPORATE_SITE_DOMAINS and not any(domain.endswith("." + item) for item in NON_CORPORATE_SITE_DOMAINS))


def run_cli(session: str, *args: str, timeout: int = 45) -> subprocess.CompletedProcess[str]:
    command = [CLI, f"-s={session}", *args]
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def preflight(proxy: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy], capture_output=True, text=True, check=False)
    return result.returncode == 0


def choose_sources(company: dict[str, Any]) -> list[tuple[str, str, str]]:
    candidates: list[tuple[str, str, str]] = []
    website = company.get("website")
    if website and corporate_url(website) and str(company.get("website_status", "")).isdigit() and 200 <= int(company.get("website_status")) < 400:
        candidates.append((website, "homepage", "Public company homepage is the primary visual evidence surface."))
    if website and corporate_url(website) and website.startswith(("http://", "https://")):
        candidates.append((website, "homepage_candidate", "Public company-site candidate; capture verifies whether it is reachable."))
    if not company.get("website_quality_issue"):
        for candidate in company.get("website_candidates") or []:
            if corporate_url(candidate) and str(candidate).startswith(("http://", "https://")):
                candidates.append((candidate, "homepage_candidate", "Public company-site candidate; capture verifies whether it is reachable."))
    profiles = company.get("profile_urls") or []
    candidates.extend((url, "company_profile", "Public directory profile shows the named company and its listed business footprint.") for url in profiles[:3] if valid_http_url(url))
    candidates.extend((source.get("source_url"), "discovery_listing", "Public discovery source for the canonical company record.") for source in company.get("source_records", [])[:5] if valid_http_url(source.get("source_url")))
    seen: set[str] = set()
    return [item for item in candidates if item[0] not in seen and not seen.add(item[0])]


def valid_http_url(url: str | None) -> bool:
    return bool(url and str(url).startswith(("http://", "https://")))


def actual_screenshots(company_id: str) -> list[Path]:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    if not directory.exists():
        return []
    return [item for item in directory.glob("*.png") if item.is_file() and not item.name.startswith("._")]


def choose_source(company: dict[str, Any]) -> tuple[str | None, str, str]:
    sources = choose_sources(company)
    return sources[0] if sources else (None, "none", "")


def capture_company(company: dict[str, Any], limit_timeout: int = 55) -> dict[str, Any]:
    company_id = company["company_id"]
    package = path_for("evidence", "companies", company_id)
    screenshots = package / "screenshots"
    pages = package / "pages"
    screenshots.mkdir(parents=True, exist_ok=True)
    pages.mkdir(parents=True, exist_ok=True)
    existing_payload: dict[str, Any] = {}
    package_file = package / "sources.json"
    if package_file.exists():
        try:
            existing_payload = json.loads(package_file.read_text(encoding="utf-8"))
        except Exception:
            existing_payload = {}
    for old_file in list(screenshots.glob("*.png")) + list(pages.glob("*.snapshot.txt")):
        if not old_file.name.startswith("._"):
            old_file.unlink()
    candidates = choose_sources(company)
    metadata: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if candidates:
        opened = False
        for index, (source_url, screenshot_type, reason) in enumerate(candidates, 1):
            session = f"luma-b2b-{company_id}-attempt-{index}"
            opened = False
            session_started = False
            try:
                session_started = True
                result = run_cli(session, "open", source_url, "--config", CONFIG, timeout=limit_timeout)
                opened = result.returncode == 0 and "opened" in (result.stdout + result.stderr).lower()
                page_file = pages / f"{safe_name(screenshot_type)}-{index}.snapshot.txt"
                page_file.write_text((result.stdout or "")[-50000:], encoding="utf-8")
                if not opened:
                    errors.append({"stage": "open", "source_url": source_url, "error": (result.stderr or result.stdout)[-1200:]})
                else:
                    snap = run_cli(session, "snapshot", timeout=limit_timeout)
                    page_file.write_text((snap.stdout or "")[-100000:], encoding="utf-8")
                    output_file = screenshots / f"{safe_name(screenshot_type)}-{index}.png"
                    shot = run_cli(session, "screenshot", "--filename", str(output_file), "--full-page", timeout=limit_timeout)
                    if shot.returncode == 0 and output_file.exists() and output_file.stat().st_size > 1000:
                        metadata.append({
                            "company_id": company_id,
                            "source_url": source_url,
                            "page_title": next((line.split(": ", 1)[1] for line in (result.stdout or "").splitlines() if line.startswith("- Page Title:")), None),
                            "captured_at": now_iso(),
                            "screenshot_type": screenshot_type if index == 1 else f"{screenshot_type}_fallback",
                            "reason_this_matters": reason,
                            "path": str(output_file.relative_to(path_for("evidence"))),
                            "bytes": output_file.stat().st_size,
                            "headless": True,
                        })
                        break
                    errors.append({"stage": "screenshot", "source_url": source_url, "error": (shot.stderr or shot.stdout)[-1200:]})
            except subprocess.TimeoutExpired as exc:
                errors.append({"stage": "browser", "source_url": source_url, "error": f"TimeoutExpired: {exc}", "classification": "SOURCE_TIMEOUT"})
            except Exception as exc:
                errors.append({"stage": "browser", "source_url": source_url, "error": f"{type(exc).__name__}: {exc}", "classification": "HEADLESS_BLOCKED"})
            finally:
                if session_started:
                    try:
                        run_cli(session, "close", timeout=min(10, limit_timeout))
                    except Exception:
                        pass
        if not metadata and not errors:
            errors.append({"stage": "selection", "error": "No candidate produced a screenshot", "classification": "NO_PUBLIC_SOURCE"})
    else:
        errors.append({"stage": "selection", "error": "No public URL available", "classification": "NO_PUBLIC_SOURCE"})

    sources = []
    for source in company.get("source_records", []):
        if source.get("source_url"):
            sources.append(source)
    for evidence in company.get("evidence", []):
        if evidence.get("source_url"):
            sources.append(evidence)
    payload = {
        "company_id": company_id,
        "generated_at": now_iso(),
        "sources": sources,
        "screenshots": metadata,
        "errors": errors,
        "headless_policy": {"headless": True, "proxy": DEFAULT_PROXY, "isolated_context": True, "visible_browser_launched": False},
    }
    if existing_payload.get("commercial_audit"):
        payload["commercial_audit"] = existing_payload["commercial_audit"]
    write_json(package_file, payload)
    notes = [f"# {company.get('company_name_fa')}", "", f"Score: {company.get('luma_opportunity_score')}", f"Tier: {company.get('priority_tier')}", "", "Visual evidence is captured from public pages only. Observations remain separate from workflow hypotheses.", ""]
    if metadata:
        notes.append(f"Captured {len(metadata)} headless screenshot(s):")
        notes.extend(f"- `{item['path']}` — {item['screenshot_type']}: {item['reason_this_matters']}" for item in metadata)
    if errors:
        notes.append("\nCapture notes:")
        notes.extend(f"- {item.get('classification', item.get('stage'))}: {item.get('error', '')}" for item in errors)
    (package / "notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    return {"company_id": company_id, "screenshots": len(metadata), "errors": errors, "headless": True}


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture public visual evidence with isolated headless Playwright")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    parser.add_argument("--min-score", type=int, default=65)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--timeout", type=int, default=55, help="Per-browser-command timeout in seconds")
    parser.add_argument("--only-missing-visual", action="store_true", help="Only capture selected records that have no non-sidecar PNG yet")
    parser.add_argument("--top-100-only", action="store_true", help="Restrict selection to the ranked top 100 before applying other filters")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    if not args.skip_preflight and not preflight(args.proxy):
        print("Evidence capture stopped: direct-proxy preflight failed.", file=sys.stderr)
        return 2
    companies = read_jsonl(args.input)
    eligible_targets = sorted([
        company for company in companies
        if company.get("luma_opportunity_score", 0) >= args.min_score
        and company.get("priority_tier") in {"A", "B"}
        and not company.get("hard_disqualifier")
    ], key=lambda item: (-item.get("luma_opportunity_score", 0), item.get("company_name_fa", "")))[: args.limit]
    if args.top_100_only:
        eligible_targets = eligible_targets[:100]
    targets = [
        company for company in eligible_targets
        if not args.only_missing_visual or not any(actual_screenshots(company.get("company_id", "")))
    ]
    print(f"Headless capture targets: {len(targets)}")
    results = []
    for index, company in enumerate(targets, 1):
        result = capture_company(company, limit_timeout=args.timeout)
        results.append(result)
        print(f"[{index}/{len(targets)}] {company.get('company_name_fa')} screenshots={result['screenshots']} errors={len(result['errors'])}")
    summary = {
        "completed_at": now_iso(), "targets": len(targets), "screenshots_captured": sum(item["screenshots"] for item in results),
        "companies_with_screenshot": sum(1 for item in results if item["screenshots"]), "errors": sum(len(item["errors"]) for item in results),
        "headless_blocked": sum(1 for item in results for error in item["errors"] if error.get("classification") == "HEADLESS_BLOCKED"),
        "visible_browser_launched": False, "proxy": args.proxy,
    }
    write_json(path_for("logs", f"evidence-capture-{now_iso().replace(':', '').replace('-', '')}.json"), summary)
    write_jsonl(path_for("data", "normalized", "evidence_capture.jsonl"), results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

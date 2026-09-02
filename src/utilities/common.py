from __future__ import annotations

import hashlib
import html
import json
import re
import threading
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse
from urllib.request import ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROXY = "http://127.0.0.1:1087"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36 "
    "LUMA-B2B-Research/1.0"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def stable_hash(*parts: Any, length: int = 16) -> str:
    value = "\x1f".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(value.encode("utf-8", "ignore")).hexdigest()[:length]


_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_ARABIC_CHARS = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ٱ": "ا",
        "ـ": "",
    }
)


def normalize_digits(value: str | None) -> str:
    return (value or "").translate(_PERSIAN_DIGITS)


def normalize_persian(value: str | None, *, compact: bool = False) -> str:
    text = unicodedata.normalize("NFKC", value or "").translate(_ARABIC_CHARS)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in {"Mn", "Me"})
    text = normalize_digits(text)
    text = text.replace("\u200c", " ").replace("\u200f", " ").replace("\u200e", " ")
    text = re.sub(r"[\u202a-\u202e\u2066-\u2069]", "", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    if compact:
        text = re.sub(r"[^\w\u0600-\u06ff]+", "", text, flags=re.UNICODE)
    return text


def clean_text(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", html.unescape(value or "")).strip()
    return text[:limit] if limit else text


def canonical_url(url: str | None, base: str | None = None) -> str | None:
    if not url:
        return None
    value = urljoin(base or "", html.unescape(url.strip()))
    if value.startswith("//"):
        value = "https:" + value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value.split("#", 1)[0]


def domain_of(url: str | None) -> str | None:
    if not url:
        return None
    host = (urlparse(url).hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def is_external_company_url(url: str | None, *, source_domains: Iterable[str] = ()) -> bool:
    domain = domain_of(url)
    if not domain:
        return False
    excluded = {
        "avval.ir",
        "google.com",
        "googleusercontent.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "telegram.me",
        "t.me",
        "youtube.com",
        "yektanet.com",
        *source_domains,
    }
    return not any(domain == item or domain.endswith("." + item) for item in excluded)


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data.strip():
            self.parts.append(data)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        self._current = {"href": attrs_dict.get("href") or "", "class": attrs_dict.get("class") or ""}
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current is not None:
            self._current["text"] = clean_text(" ".join(self._parts))
            self.links.append(self._current)
            self._current = None
            self._parts = []


def html_to_text(body: str, limit: int | None = None) -> str:
    parser = _TextParser()
    try:
        parser.feed(body or "")
        parser.close()
    except Exception:
        pass
    return clean_text(" ".join(parser.parts), limit)


def extract_links(body: str, base_url: str | None = None) -> list[dict[str, str]]:
    parser = _LinkParser()
    try:
        parser.feed(body or "")
        parser.close()
    except Exception:
        pass
    output: list[dict[str, str]] = []
    for link in parser.links:
        href = canonical_url(link.get("href"), base_url)
        if href:
            item = dict(link)
            item["href"] = href
            output.append(item)
    return output


def extract_title(body: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", body or "", re.I | re.S)
    return clean_text(match.group(1)) if match else ""


def extract_emails(text: str) -> list[str]:
    values = re.findall(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", text or "", re.I)
    return filter_public_emails(values)


def filter_public_emails(values: Iterable[str] | None) -> list[str]:
    """Remove search-provider artifacts before an email enters public contacts."""
    cleaned: set[str] = set()
    for value in values or []:
        email = str(value).lower().strip(" .,;:")
        local, separator, domain = email.partition("@")
        if not separator or not local or not domain:
            continue
        if local.startswith("error-lite") and domain.endswith("duckduckgo.com"):
            continue
        cleaned.add(email)
    return sorted(cleaned)


def normalize_phone(value: str) -> str:
    text = normalize_digits(value).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    text = text.replace("+98", "0", 1) if text.startswith("+98") else text
    return text


def corporate_phones(text: str) -> list[str]:
    candidates = re.findall(r"(?:\+?98|0)?[\s\-()]*9\d[\d\s\-()]{8,}|(?:\+?98|0)?[\s\-()]*2?1[\d\s\-()]{7,}", normalize_digits(text or ""))
    values = []
    for raw in candidates:
        phone = normalize_phone(raw)
        # Deliberately retain public landlines only. Mobile numbers can be personal.
        if phone.startswith("021") and 10 <= len(phone) <= 11:
            values.append(phone)
        elif phone.startswith("98") and phone[2:4] == "21" and 10 <= len(phone) <= 12:
            values.append("0" + phone[2:])
    return sorted(set(values))


def json_ld_objects(body: str) -> list[Any]:
    values: list[Any] = []
    for match in re.finditer(r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", body or "", re.I | re.S):
        raw = html.unescape(match.group(1)).strip()
        if not raw:
            continue
        try:
            values.append(json.loads(raw))
        except json.JSONDecodeError:
            raw = re.sub(r"<!--[\s\S]*?-->", "", raw)
            try:
                values.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return values


def walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


class RateLimiter:
    def __init__(self, interval: float) -> None:
        self.interval = max(0.0, float(interval))
        self.lock = threading.Lock()
        self.last = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        with self.lock:
            now = time.monotonic()
            delay = self.interval - (now - self.last)
            if delay > 0:
                time.sleep(delay)
            self.last = time.monotonic()


def fetch_url(url: str, *, proxy: str | None = DEFAULT_PROXY, timeout: float = 20.0, limiter: RateLimiter | None = None, max_bytes: int = 3_000_000) -> dict[str, Any]:
    started = time.monotonic()
    if limiter:
        limiter.wait()
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.7",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.7,en;q=0.6",
        },
    )
    try:
        handler = ProxyHandler({"http": proxy, "https": proxy} if proxy else {})
        opener = build_opener(handler)
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            truncated = len(raw) > max_bytes
            raw = raw[:max_bytes]
            content_type = response.headers.get("Content-Type", "")
            charset_match = re.search(r"charset=([^;]+)", content_type, re.I)
            charset = charset_match.group(1).strip(" \"") if charset_match else "utf-8"
            if "pdf" in content_type.lower():
                body = raw.decode("latin-1", "ignore")
            else:
                try:
                    body = raw.decode(charset, "replace")
                except LookupError:
                    body = raw.decode("utf-8", "replace")
            return {
                "url": url,
                "final_url": response.geturl(),
                "status": int(response.status),
                "headers": {k.lower(): v for k, v in response.headers.items()},
                "content_type": content_type,
                "body": body,
                "truncated": truncated,
                "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
                "error": None,
            }
    except Exception as exc:  # network diagnostics must retain failure evidence
        return {
            "url": url,
            "final_url": None,
            "status": None,
            "headers": {},
            "content_type": "",
            "body": "",
            "truncated": False,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Parse the intentionally small YAML subset used by config/*.yaml.

    This avoids a runtime dependency while supporting mappings, lists, inline
    scalar lists and list-of-mapping entries. It is not intended as a general
    YAML parser.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    def scalar(raw: str) -> Any:
        text = raw.strip()
        if not text:
            return None
        if text.startswith("[") and text.endswith("]"):
            return [scalar(part) for part in text[1:-1].split(",") if part.strip()]
        if (text.startswith("\"") and text.endswith("\"")) or (text.startswith("'") and text.endswith("'")):
            return text[1:-1]
        if text.lower() in {"true", "false"}:
            return text.lower() == "true"
        try:
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                return text

    meaningful: list[tuple[int, str]] = []
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        meaningful.append((indent, raw_line.strip()))

    for index, (indent, content) in enumerate(meaningful):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if content.startswith("- "):
            if not isinstance(parent, list):
                continue
            item_text = content[2:].strip()
            if "://" not in item_text and re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", item_text):
                key, raw_value = item_text.split(":", 1)
                item: dict[str, Any] = {key.strip(): scalar(raw_value)}
                parent.append(item)
                stack.append((indent, item))
            else:
                parent.append(scalar(item_text))
            continue
        if ":" not in content or not isinstance(parent, dict):
            continue
        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            parent[key] = scalar(raw_value)
            continue
        next_is_list = index + 1 < len(meaningful) and meaningful[index + 1][0] > indent and meaningful[index + 1][1].startswith("- ")
        parent[key] = [] if next_is_list else {}
        stack.append((indent, parent[key]))
    return root


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: str | Path, value: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_url_from_ddg(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        return canonical_url(unquote(target)) if target else None
    return canonical_url(url)


def path_for(*parts: str) -> Path:
    destination = ROOT.joinpath(*parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination

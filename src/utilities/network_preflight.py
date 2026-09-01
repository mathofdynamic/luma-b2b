from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from .common import DEFAULT_PROXY, ROOT, now_iso, path_for, stamp, write_json


def command(args: list[str], timeout: float = 10.0) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return (result.stdout or "") + (result.stderr or "")
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def curl(url: str, proxy: str | None = None) -> dict[str, Any]:
    marker = "__LUMA_META__"
    args = ["curl", "-4", "-sS", "-L", "--max-time", "15"]
    if proxy:
        args += ["-x", proxy]
    else:
        args += ["--noproxy", "*"]
    args += ["-o", "/dev/null", "-w", f"%{{http_code}}|%{{url_effective}}|%{{time_total}}|%{{ssl_verify_result}}|%{{remote_ip}}{marker}", url]
    started = time.monotonic()
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=25, check=False)
        output = (result.stdout or "").strip()
        meta = output.split(marker, 1)[0]
        fields = meta.split("|")
        return {
            "url": url,
            "proxy": proxy,
            "returncode": result.returncode,
            "http_status": int(fields[0]) if fields and fields[0].isdigit() else None,
            "final_url": fields[1] if len(fields) > 1 else None,
            "time_seconds": float(fields[2]) if len(fields) > 2 and fields[2] else round(time.monotonic() - started, 3),
            "tls_verify_result": fields[3] if len(fields) > 3 else None,
            "remote_ip": fields[4] if len(fields) > 4 else None,
            "stderr": (result.stderr or "")[-1000:],
        }
    except Exception as exc:
        return {"url": url, "proxy": proxy, "returncode": None, "http_status": None, "error": f"{type(exc).__name__}: {exc}"}


def curl_text(url: str, proxy: str | None = None) -> dict[str, Any]:
    """Fetch a small text response and retain curl's transport metadata."""
    marker = "__LUMA_META__"
    args = ["curl", "-4", "-sS", "--max-time", "15"]
    if proxy:
        args += ["-x", proxy]
    else:
        args += ["--noproxy", "*"]
    args += ["-w", f"{marker}%{{http_code}}|%{{url_effective}}|%{{time_total}}|%{{ssl_verify_result}}|%{{remote_ip}}", url]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=25, check=False)
        output = result.stdout or ""
        body, _, meta = output.partition(marker)
        fields = meta.strip().split("|")
        return {
            "url": url,
            "proxy": proxy,
            "returncode": result.returncode,
            "body": body.strip(),
            "http_status": int(fields[0]) if fields and fields[0].isdigit() else None,
            "final_url": fields[1] if len(fields) > 1 else None,
            "time_seconds": float(fields[2]) if len(fields) > 2 and fields[2] else None,
            "tls_verify_result": fields[3] if len(fields) > 3 else None,
            "remote_ip": fields[4] if len(fields) > 4 else None,
            "stderr": (result.stderr or "")[-1000:],
        }
    except Exception as exc:
        return {"url": url, "proxy": proxy, "returncode": None, "http_status": None, "body": "", "error": f"{type(exc).__name__}: {exc}"}


def parse_physical_interface(ifconfig: str) -> str | None:
    for match in re.finditer(r"(?m)^([a-zA-Z0-9]+):\s+flags=.*?(?=^\S+:\s+flags=|\Z)", ifconfig, re.S):
        name, block = match.group(1), match.group(0)
        if name in {"en0", "en1", "en2", "en3", "en4"} and re.search(r"\binet\s+\d+\.\d+\.\d+\.\d+", block):
            return name
    return None


def parse_tun_interfaces(ifconfig: str) -> list[str]:
    return sorted(set(re.findall(r"(?m)^(utun\d+):\s+flags=", ifconfig)))


def parse_route_interface(route: str) -> str | None:
    match = re.search(r"(?m)^\s*interface:\s*(\S+)", route)
    return match.group(1) if match else None


def parse_connected_vpn(scutil_nc: str) -> list[str]:
    return [line.strip() for line in scutil_nc.splitlines() if "(Connected)" in line]


def parse_dns(scutil_dns: str) -> list[str]:
    nameservers: list[str] = []
    for line in scutil_dns.splitlines():
        match = re.search(r"nameserver\[\d+\]\s*:\s*(\S+)", line)
        if match and match.group(1) not in nameservers:
            nameservers.append(match.group(1))
    return nameservers


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only LUMA B2B network preflight")
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--target", default="https://didmeet.ir/")
    parser.add_argument("--ip-endpoint", default="https://icanhazip.com")
    args = parser.parse_args()

    ifconfig = command(["ifconfig"])
    route_default = command(["route", "-n", "get", "default"])
    scutil_nc = command(["scutil", "--nc", "list"])
    scutil_dns = command(["scutil", "--dns"])
    physical = parse_physical_interface(ifconfig)
    tun = parse_tun_interfaces(ifconfig)
    connected = parse_connected_vpn(scutil_nc)
    direct_ip = curl_text(args.ip_endpoint, args.proxy)
    normal_ip = curl_text(args.ip_endpoint, None)
    direct_target = curl(args.target, args.proxy)
    normal_target = curl(args.target, None)

    result: dict[str, Any] = {
        "captured_at": now_iso(),
        "proxy": args.proxy,
        "target": args.target,
        "ip_endpoint": args.ip_endpoint,
        "vpn_connected": bool(connected),
        "connected_vpn_services": connected,
        "physical_interface": physical,
        "vpn_tun_interfaces": tun,
        "default_route_interface": parse_route_interface(route_default),
        "dns_nameservers": parse_dns(scutil_dns),
        "direct_ip": direct_ip,
        "normal_ip": normal_ip,
        "direct_target": direct_target,
        "normal_target": normal_target,
        "read_only_diagnostics": {
            "ifconfig": ifconfig,
            "route_default": route_default,
            "scutil_nc": scutil_nc,
            "scutil_dns": scutil_dns,
        },
        "persistent_system_changes": "None",
    }
    output = path_for("logs", f"network_preflight-{stamp()}.json")
    write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    direct_ok = (
        direct_target.get("http_status") is not None
        and direct_target.get("returncode") == 0
        and direct_ip.get("returncode") == 0
        and bool(direct_ip.get("body"))
    )
    return 0 if connected and direct_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

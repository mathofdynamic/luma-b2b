# Networking runbook

## Safety boundary

The macOS VPN remains connected and is not modified by this project. Iranian research traffic is explicitly scoped to the already-verified local direct proxy:

```text
http://127.0.0.1:1087
```

The validated direct egress was `5.238.239.167` on physical interface `en1`. The VPN/TUN interface observed during validation was `utun6`. These values are recorded for audit; the preflight checks the live state again before batches.

## Preflight

```bash
python3 -m src.utilities.network_preflight \
  --proxy http://127.0.0.1:1087 \
  --target https://didmeet.ir/ \
  --ip-endpoint https://api.ipify.org
```

The preflight checks VPN state, physical/TUN interfaces, direct-proxy HTTPS status, direct public egress and didmeet response. A failed direct-proxy check must stop the affected batch. The pipeline never falls back silently to the VPN.

## Runtime

Set only process-local proxy variables when using command-line HTTP clients:

```bash
export LUMA_B2B_DIRECT_PROXY=http://127.0.0.1:1087
python3 -m src.discovery.run --config config/sources.yaml
```

Headless browser launch must set a browser-level proxy, never system proxy settings:

```javascript
{ headless: true, proxy: { server: "http://127.0.0.1:1087" } }
```

No persistent routing change, VPN profile edit, network-service change or browser profile reuse is part of this repository.

# Rerun guide

## Commercial audit only

This pass is intentionally bounded to the existing A/B cohort. It must not be replaced with a broad discovery run when validating rankings:

```bash
python3 -m src.utilities.network_preflight --proxy http://127.0.0.1:1087
python3 -m src.audit.commercial --input data/normalized/companies.jsonl --proxy http://127.0.0.1:1087
python3 -m src.proposals.generate --input data/normalized/companies.jsonl
python3 -m src.exports.generate --input data/normalized/companies.jsonl
node src/exports/build_workbook.mjs
python3 -m src.audit.report --input data/normalized/companies.jsonl
python3 -m src.utilities.qa --input data/normalized/companies.jsonl
```

The audit caches HTTP responses under the ignored `data/raw/http-cache/commercial-audit/` directory. It stops before scoring if the direct-proxy preflight fails. The VPN must remain connected.

All stages are independently runnable and write timestamped artifacts under `data/raw`, `data/normalized`, `evidence`, `proposals`, `reports` and `logs`.

```bash
python3 -m src.utilities.network_preflight
python3 -m src.discovery.run --config config/sources.yaml
python3 -m src.enrichment.enrich --input data/raw/candidates.jsonl
python3 -m src.scoring.score --input data/normalized/companies.jsonl
python3 -m src.evidence.capture --input data/normalized/companies.jsonl
python3 -m src.proposals.generate --input data/normalized/companies.jsonl
python3 -m src.exports.generate --input data/normalized/companies.jsonl
python3 -m src.utilities.qa --input data/normalized/companies.jsonl
```

The runtime uses a direct proxy only for process traffic. Do not add `open`, GUI browser launches, system proxy changes or VPN commands to rerun scripts.

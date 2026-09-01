# Rerun guide

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

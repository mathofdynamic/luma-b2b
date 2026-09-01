# Discovery Report

Generated: 2026-09-01T09:38:12Z

## Scope and method

Persian-first public discovery was run for Tehran city/Tehran Province across the priority industries and the research-defined clusters. The run used Book-e Avval category pages, public official/association references, Persian search results where responsive, and the public VIC industrial-estate company/activity index.

Raw candidate rows: **6,576**; canonical after deterministic normalization/deduplication: **6,084**.

## Source run results

- Book-e Avval / broad directory: 2087 rows in the broad run.
- VIC industrial-estate index: 4461 rows across 6 configured zone requests; final successful zones are retained in `data/raw/industrial_estate_sources.json`.
- Search and official/association rows are retained in the raw candidate file and source table; targeted exact-name search was later stopped after direct-proxy timeout behavior.

## Deduplication

Identity is connected by Avval profile key, external domain, public landline plus normalized name, normalized name/address and finally normalized name. Names are normalized for Arabic/Persian character variants, Persian/Arabic digits and zero-width characters. A canonical record preserves all source rows in `source_records`.

## Qualification boundary

A zone index establishes discovery and an activity label only. It does not establish a strong business, active status, purchasing power or workflow pain. Thin index-only records are retained for future enrichment but capped below B/A by the scoring model.

## Blocked / incomplete

- DuckDuckGo targeted exact-name enrichment: direct-proxy requests timed out; that batch was stopped.
- Avval concurrent profile pass: earlier high-concurrency requests produced HTTP 429s; a later serial prioritized pass returned 220/220 HTTP 200.
- Some public sites returned unreachable/unknown status and remain explicitly marked.

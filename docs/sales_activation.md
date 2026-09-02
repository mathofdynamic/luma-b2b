# Sales activation preparation

This stage is a bounded preparation pass over the 32 records already marked
`READY FOR OUTREACH` by the commercial audit. It must not discover additional
companies, submit a form, call a number, or send an email, LinkedIn message or
WhatsApp message.

## Network and browser boundary

Keep the VPN connected. Iranian research traffic uses the verified process-local
proxy `http://127.0.0.1:1087`; the preflight must succeed before the pass starts.
Browser automation, if needed for a future evidence refresh, must use an
isolated headless Playwright context and must not launch a visible macOS app.
The activation locator uses a bounded public search request only to locate
candidate pages; search engines are not counted as independent evidence
families.

## Bounded rerun

Run from the repository root:

```bash
python3 -m src.utilities.network_preflight --proxy http://127.0.0.1:1087 --target https://didmeet.ir/ --ip-endpoint https://api.ipify.org
python3 -m src.sales.activation --input data/normalized/companies.jsonl --proxy http://127.0.0.1:1087 --max-official-pages 5 --max-external-pages 5
node src/exports/build_outreach_pipeline.mjs
python3 -m src.sales.qa --input data/normalized/companies.jsonl
```

The activation runner aborts if the input does not contain exactly the current
32 READY records. It writes timestamped research logs, caches public responses,
and preserves `UNKNOWN` when a public fact cannot be established. The tracker
always initializes every row to `NOT_CONTACTED`.

## Outputs

- `sales/internal/<company_id>.md`: analytical sales brief.
- `sales/client/<company_id>.md`: polished Persian one-page proposal.
- `sales/outreach/<company_id>.md`: unsent phone, email, LinkedIn and, only
  where explicitly published, WhatsApp copy.
- `sales/visual/<company_id>/README.md`: internal visual-evidence index.
- `reports/first_contact_plan.md`: Wave 1/2/3 ranking and contact plan.
- `data/outreach_pipeline.csv` and `data/outreach_pipeline.xlsx`: review tracker.
- `reports/dossiers/`: current top-30 human sales dossiers.

## First-contact ranking

`first_contact_score` is a preparation priority, not a replacement for the
commercial opportunity score. The implementation combines evidence quality,
workflow clarity, pilot simplicity, measurable KPI potential, public contact
availability, buyer reachability, external-purchasing fit, sales-cycle
reasonableness, demo clarity and LUMA delivery confidence. It penalizes missing
buyer information, weak channels, unclear pilots, heavy integration, regulatory
friction, excessive scale and strong technical sophistication. The score is
documented in each internal brief and in the first-contact plan.

## Human gate

All records remain prepared but uncontacted. A human must validate the company,
process owner, public channel and pilot sample before any sales action. No
activation artifact claims that a company has an internal problem unless a
public source supports the statement; hypotheses are phrased as questions to
validate in discovery.

# Dashboard direction decisions

Date: 2026-09-02
Status: provisional; user confirmation pending

## Working decisions

- Use a local Node server plus static ES modules instead of introducing a frontend framework or database. This keeps the tool reproducible, fast to start, and independent of external services.
- Generate a compact summary index from repository outputs and lazy-load company detail/materials. This protects explorer performance at ۶٬۰۸۴ records while preserving evidence links.
- Use the prior LUMA/Sabah navy/teal/paper direction as provisional visual language. No official LUMA brand palette was found in the repository.
- Keep canonical research immutable in the dashboard. Human status, favorite, and note are stored separately in a local ignored JSON file.
- Treat private dashboard indexing as an internal-tool experience. SEO/discoverability checks are N/A for public indexing, while local server privacy is documented.

## Rejected alternatives

- Full React/Tailwind dependency stack: rejected for this run because the repository had no frontend package and the review tool does not require a large dependency surface.
- Rendering all ۶٬۰۸۴ records and full evidence in the initial DOM: rejected because it would reduce responsiveness and obscure the review task.
- Iframe arbitrary company websites: rejected because it would weaken safety, fail unpredictably on CSP, and blur the line between stored evidence and live external content.
- Storing human review inside canonical JSONL: rejected because it would overwrite or contaminate research facts.

# Typography update — 2026-09-02

## Request

The repository owner requested IRANYekanX as the dashboard-wide Persian typeface and supplied public download URLs for the font files.

## Implementation decision

- Self-host the six supplied WOFF2 weights for `IRANYekanX`.
- Self-host the matching six `IRANYekanXFaNum` weights for numeric/data-heavy roles.
- Map UI text to `--font-ui` and compact scores, timestamps, domains, file paths, and other data labels to `--font-numeric`.
- Serve the allowlisted font filenames from the existing loopback Node server so the dashboard remains local and offline-capable after the assets are present.
- Keep Tahoma/Arial as local fallbacks only; do not add a CDN or runtime external font dependency.

## Boundary

This is a user-provided typography direction applied to the provisional dashboard implementation. The OCD Designer Brand Book, design direction, release acceptance, and font licensing/provenance approval remain pending; no approval is inferred from this implementation change.

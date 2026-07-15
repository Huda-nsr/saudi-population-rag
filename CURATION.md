# Curating datasets into `data/catalog.json`

`data/catalog.json` is the single source of truth the app embeds (for retrieval)
and cites (for provenance). This is how to add or replace a dataset.

## Quickstart vs. real data

- **Quickstart:** `python make_sample_data.py` writes synthetic CSVs into `data/raw/`
  so the whole pipeline runs offline immediately. Entries flagged `"sample_data": true`
  serve these synthetic figures; the UI says so, and the cited `source_url` is still the
  real dataset page.
- **Real data:** replace the sample CSVs with real ones (below) and set
  `"sample_data": false`.

## Why CSVs are downloaded by hand

`open.data.gov.sa` sits behind an F5 WAF: there is no script-usable API, and the CSV
download links are session-bound (they carry a `TSPD_...` token that expires). So you
**download each CSV once through your browser and cache it in `data/raw/`** — the app
only ever reads local files. This is also better for a demo: offline, fast, reproducible.

## The loop (per dataset)

1. Open the dataset on `open.data.gov.sa` (both `/en/` and `/ar/`), copy the real
   **title** and **description** in each language into a catalog entry.
2. **Resources** tab → download the CSV → save it into `data/raw/`.
3. Fill the entry (schema below): set `file` to the CSV's filename, list its `columns`,
   set `content_type` to `numeric` (has figures to look up) or `descriptive` (text only).
4. Rebuild + check: `python scripts/build_index.py` then `python -m eval.run_eval --routing`.

## Entry schema (what the code reads)

```json
{
  "id": "unique-slug",                 // used for citation + eval routing
  "title_en": "...", "title_ar": "...",
  "description_en": "...", "description_ar": "...",
  "source_org": "Ministry of Education",
  "source_url": "https://open.data.gov.sa/en/datasets/view/<uuid>",
  "file": "my-dataset.csv",            // in data/raw/ ; "" for descriptive-only
  "columns": ["region", "gender", "year", "population"],
  "content_type": "numeric",           // "numeric" | "descriptive"
  "language": "bilingual",
  "sample_data": false                 // true = synthetic demo figures
}
```

## Retrieval tips (learned from the eval)

- Keep the **embedded description about the data**, not disclaimers — shared boilerplate
  across entries blurs them together in vector space. Caveats belong on `sample_data`/UI.
- Put terms users will actually type into the description — e.g. region *values*
  ("Riyadh, Makkah") not just the column name "region". `ingest.py` embeds the
  description, so a question mentioning "Riyadh" then matches.

## Population/census sources to curate

The real figures come from GASTAT's Saudi Census 2022. To attach real CSVs:
- Browse the **Saudi Census 2022** portal: https://portal.saudicensus.sa/  (population by
  region, age, nationality, households) and **GASTAT**: https://www.stats.gov.sa/
- On `open.data.gov.sa`, find GASTAT's population datasets (filter publisher = General
  Authority for Statistics), grab each dataset-view UUID, download the CSV into
  `data/raw/`, and set `sample_data: false`. (The platform's search index is thin and
  WAF-protected, so browse it in a logged-in browser rather than scripting it.)

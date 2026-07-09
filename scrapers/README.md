# Scrapers Framework

This package provides reusable scraper classes for collecting AP-style educational material only from sources that explicitly allow redistribution or educational reuse.

## Compliance Rules

- `robots.txt` is checked before each fetch.
- Source terms must explicitly permit redistribution (`allows_redistribution=True`).
- Records always include:
  - `source_url`
  - `license`
  - `retrieval_date`
- College Board domains are explicitly blocked.

## Main Classes

- `BaseScraper`: policy-aware abstract base class.
- `StaticHTMLScraper`: scrapes static HTML pages and extracts text.
- `JSONListScraper`: scrapes JSON endpoints that return list records.
- `write_jsonl`: saves normalized records to JSONL.

## Output Record

```json
{
  "id": "...",
  "text": "...",
  "source_url": "...",
  "license": "...",
  "retrieval_date": "2026-07-08T12:00:00+00:00",
  "metadata": {}
}
```

## Important

Do not add sources unless license and Terms of Service are verified.

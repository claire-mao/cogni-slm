# Source Collection Run - 2026-07-11

## Completed

- Cloned public fallacy sources:
  - `datasets/raw/fallacy/source_files/argotario`
  - `datasets/raw/fallacy/source_files/logical-fallacy`
  - `datasets/raw/fallacy/source_files/MAFALDA`
- Built consolidated corpus:
  - `datasets/raw/fallacy/normalized/fallacy_corpus_v1.jsonl`
  - `outputs/data_ingestion/fallacy_corpus_report.json`
  - `outputs/data_ingestion/fallacy_corpus_report.md`
- Built non-placeholder held-out benchmark (30 examples):
  - `datasets/eval/heldout_benchmark_public_v1.jsonl`
  - `outputs/data_ingestion/heldout_public_v1_report.json`
- Checked AP ingestion folder:
  - `datasets/raw/ap_lang/source_files` (currently empty)
  - `outputs/data_ingestion/ap_lang_ingestion_report.md`

## Current Counts

- Consolidated fallacy corpus rows: 4,946
- Held-out benchmark rows: 30
- AP source files ingested: 0

## Next Action (After Adding AP Files)

Place AP FRQ PDFs/scoring guides/sample responses under:
- `datasets/raw/ap_lang/source_files`

Then run:

```bash
cd /Users/clairemao/Documents/cogni-slm
python3 -m src.data.ingest_private_documents \
  --input-dir datasets/raw/ap_lang/source_files \
  --output-jsonl datasets/raw/ap_lang/normalized/ap_lang_private_docs.jsonl \
  --report-path outputs/data_ingestion/ap_lang_ingestion_report.md \
  --min-words 40
```

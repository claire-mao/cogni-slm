# Schema Validation Audit

This report inspects dataset artifacts under:
- `datasets/raw/`
- `datasets/processed/`
- `datasets/final/`
- `datasets/training/`

Artifacts profiled: `99`

## Stage Summary

| stage | artifacts | total_rows (sum) | distinct_schema_signatures |
|---|---:|---:|---:|
| raw | 12 | 40744 | 7 |
| processed | 76 | 1841916 | 5 |
| final | 10 | 1185968 | 4 |
| training | 1 | 12413 | 1 |

## Schema Drift Highlights

- `raw` has schema drift: `7` distinct schema signatures.
- `processed` has schema drift: `5` distinct schema signatures.
- `final` has schema drift: `4` distinct schema signatures.
- `training` has one schema signature in profiled artifacts.

### Canonical Pipeline Schema Changes
- raw -> processed: +11 / -28 columns
- processed -> final: +2 / -5 columns
- final -> training: +2 / -7 columns

## Dataset Inventory (Columns, Types, Nullability, Missing, Schema Change)

| artifact | kind | rows | columns | nullable_fields | missing_total | schema_change |
|---|---|---:|---:|---:|---:|---|
| `datasets/final/dataset_dict` | hf_disk | 12960 | 8 | 0 | 0 | +0/-0 vs final_baseline |
| `datasets/final/merged_all.jsonl` | jsonl | 12413 | 8 | 0 | 0 | +0/-0 vs final_baseline |
| `datasets/final/provenance.parquet` | parquet | 12413 | 8 | 0 | 0 | +7/-7 vs final_baseline |
| `datasets/final/quality_deduped.jsonl` | jsonl | 12413 | 12 | 2 | 24826 | +6/-2 vs final_baseline |
| `datasets/final/quality_filtered.jsonl` | jsonl | 433906 | 12 | 3 | 938345 | +6/-2 vs final_baseline |
| `datasets/final/quality_removed.jsonl` | jsonl | 127772 | 4 | 0 | 0 | +2/-6 vs final_baseline |
| `datasets/final/quality_scored.jsonl` | jsonl | 561678 | 12 | 5 | 1479840 | +6/-2 vs final_baseline |
| `datasets/final/test.jsonl` | jsonl | 1232 | 8 | 0 | 0 | +0/-0 vs final_baseline |
| `datasets/final/train.jsonl` | jsonl | 9940 | 8 | 0 | 0 | +0/-0 vs final_baseline |
| `datasets/final/validation.jsonl` | jsonl | 1241 | 8 | 0 | 0 | +0/-0 vs final_baseline |
| `datasets/processed/golden/golden-20260708T183049Z/audit_traces.jsonl` | jsonl | 50 | 8 | 2 | 56 | +7/-10 vs processed_baseline |
| `datasets/processed/golden/golden-20260708T183049Z/dataset.jsonl` | jsonl | 50 | 35 | 4 | 136 | +34/-10 vs processed_baseline |
| `datasets/processed/golden/golden-20260708T202613Z/audit_traces.jsonl` | jsonl | 50 | 8 | 2 | 56 | +7/-10 vs processed_baseline |
| `datasets/processed/golden/golden-20260708T202613Z/dataset.jsonl` | jsonl | 50 | 35 | 4 | 136 | +34/-10 vs processed_baseline |
| `datasets/processed/normalized/all_datasets.jsonl` | jsonl | 22326 | 7 | 7 | 16608 | +2/-6 vs processed_baseline |
| `datasets/processed/normalized/asap2.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/normalized/asap_aes.jsonl` | jsonl | 22326 | 7 | 7 | 16608 | +2/-6 vs processed_baseline |
| `datasets/processed/normalized/persuade2.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/raw_essays.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/eval__heldout_benchmark.jsonl` | jsonl | 18 | 11 | 2 | 36 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/eval__heldout_benchmark.jsonl.jsonl` | jsonl | 18 | 11 | 2 | 36 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final.jsonl` | jsonl | 12413 | 11 | 2 | 24826 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__dataset_dict.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__test__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__test__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__train__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__train__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__validation__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict__validation__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict_hf.jsonl` | jsonl | 12960 | 11 | 2 | 25920 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__dataset_dict_hf_hf.jsonl` | jsonl | 12960 | 11 | 2 | 25920 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__merged_all.jsonl` | jsonl | 12413 | 11 | 2 | 24826 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__merged_all.jsonl.jsonl` | jsonl | 12960 | 11 | 2 | 25920 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_deduped.jsonl` | jsonl | 12413 | 11 | 2 | 24826 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_filtered.jsonl` | jsonl | 149598 | 11 | 3 | 322707 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_filtered.jsonl.jsonl` | jsonl | 12959 | 11 | 2 | 25918 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_removed.jsonl` | jsonl | 44591 | 11 | 5 | 222955 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_removed.jsonl.jsonl` | jsonl | 1 | 11 | 2 | 2 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_scored.jsonl` | jsonl | 194189 | 11 | 5 | 489550 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/final__quality_scored.jsonl.jsonl` | jsonl | 12960 | 11 | 2 | 25920 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/hf__build_summary.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/hf__dataset_dict__dataset_dict.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/hf__dataset_dict__train__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/hf__dataset_dict__train__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/hf__dataset_dict_hf.jsonl` | jsonl | 12964 | 11 | 2 | 25928 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/hf__dataset_dict_hf_hf.jsonl` | jsonl | 12964 | 11 | 2 | 25928 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl` | jsonl | 50 | 11 | 5 | 250 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl.jsonl` | jsonl | 50 | 11 | 5 | 250 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl` | jsonl | 50 | 11 | 3 | 150 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl.jsonl` | jsonl | 50 | 11 | 3 | 150 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T183049Z__manifest.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl` | jsonl | 50 | 11 | 5 | 250 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl.jsonl` | jsonl | 50 | 11 | 5 | 250 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl` | jsonl | 50 | 11 | 3 | 150 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl.jsonl` | jsonl | 50 | 11 | 3 | 150 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__golden__golden-20260708T202613Z__manifest.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__all_datasets.jsonl` | jsonl | 22326 | 11 | 5 | 56548 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__all_datasets.jsonl.jsonl` | jsonl | 22326 | 11 | 5 | 56548 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__asap2.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__asap2.jsonl.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__asap_aes.jsonl` | jsonl | 22326 | 11 | 5 | 56548 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__asap_aes.jsonl.jsonl` | jsonl | 22326 | 11 | 5 | 56548 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__persuade2.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__persuade2.jsonl.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/processed__normalized__summary.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/processed__raw_essays.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/processed__raw_essays.jsonl.jsonl` | jsonl | 0 | 0 | 0 | 0 | +0/-11 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__.cache__huggingface__trees__a46733395585b56c3bbe88f1957360a632ac3e9e.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__test_set.jsonl` | jsonl | 4404 | 11 | 11 | 14860 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__training_set_rel3.jsonl` | jsonl | 13566 | 11 | 11 | 34152 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column.jsonl` | jsonl | 4818 | 11 | 5 | 24090 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column_no_header.jsonl` | jsonl | 4817 | 11 | 5 | 24085 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__valid_sample_submission_2_column.jsonl` | jsonl | 4818 | 11 | 5 | 24090 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__valid_sample_submission_5_column.jsonl` | jsonl | 4818 | 11 | 4 | 19272 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/raw__asap_aes__valid_set.jsonl` | jsonl | 4356 | 11 | 11 | 14604 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__dataset_dict.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__test__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__test__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__train__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__train__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__validation__dataset_info.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training__validation__state.jsonl` | jsonl | 1 | 11 | 5 | 5 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training_hf_hf.jsonl` | jsonl | 12413 | 11 | 2 | 24826 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/training_provenance.jsonl` | jsonl | 12413 | 11 | 3 | 37239 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/unified_all.jsonl` | jsonl | 562856 | 11 | 11 | 1492798 | +0/-0 vs processed_baseline |
| `datasets/processed/unified/unified_all.sanitized.jsonl` | jsonl | 561678 | 11 | 5 | 1479840 | +0/-0 vs processed_baseline |
| `datasets/raw/asap_aes/Essay_Set_Descriptions/essay_set_descriptions.xlsx` | xlsx | 0 | 0 | 0 | 0 | +0/-28 vs raw_baseline |
| `datasets/raw/asap_aes/test_set.tsv` | tsv | 4261 | 5 | 4 | 3682 | +2/-25 vs raw_baseline |
| `datasets/raw/asap_aes/training_set_rel3.tsv` | tsv | 12991 | 28 | 28 | 258354 | baseline_raw |
| `datasets/raw/asap_aes/training_set_rel3.xls` | xls | 0 | 0 | 0 | 0 | +0/-28 vs raw_baseline |
| `datasets/raw/asap_aes/training_set_rel3.xlsx` | xlsx | 0 | 0 | 0 | 0 | +0/-28 vs raw_baseline |
| `datasets/raw/asap_aes/valid_sample_submission_1_column.csv` | csv | 4818 | 1 | 0 | 0 | +1/-28 vs raw_baseline |
| `datasets/raw/asap_aes/valid_sample_submission_1_column_no_header.csv` | csv | 4817 | 1 | 0 | 0 | +1/-28 vs raw_baseline |
| `datasets/raw/asap_aes/valid_sample_submission_2_column.csv` | csv | 4818 | 2 | 0 | 0 | +2/-28 vs raw_baseline |
| `datasets/raw/asap_aes/valid_sample_submission_5_column.csv` | csv | 4818 | 5 | 0 | 0 | +3/-26 vs raw_baseline |
| `datasets/raw/asap_aes/valid_set.tsv` | tsv | 4221 | 5 | 3 | 3630 | +2/-25 vs raw_baseline |
| `datasets/raw/asap_aes/valid_set.xls` | xls | 0 | 0 | 0 | 0 | +0/-28 vs raw_baseline |
| `datasets/raw/asap_aes/valid_set.xlsx` | xlsx | 0 | 0 | 0 | 0 | +0/-28 vs raw_baseline |
| `datasets/training` | hf_disk | 12413 | 3 | 0 | 0 | +0/-0 vs training_baseline |

## Per-Dataset Details

### `datasets/final/dataset_dict`
- Stage: `final`
- Kind: `hf_disk`
- Rows: `12960`
- Schema change: `+0/-0 vs final_baseline`
- Columns (8): `id, label, metadata, prompt, source, split, task, text`
- Datatypes:
  - `id`: `Value('string')`
  - `label`: `Value('float64')`
  - `metadata`: `{'source_split': Value('string'), 'source_row_index': Value('int64')}`
  - `prompt`: `Value('string')`
  - `source`: `Value('string')`
  - `split`: `Value('string')`
  - `task`: `Value('string')`
  - `text`: `Value('string')`
- Nullable fields (0): `none`
- Missing values (per column):
  - `id`: `0`
  - `label`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
  - `text`: `0`
- Notes: `splits=test,train,validation`

### `datasets/final/merged_all.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+0/-0 vs final_baseline`
- Columns (8): `id, label, metadata, prompt, source, split, task, text`
- Datatypes:
  - `id`: `str`
  - `label`: `float`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
  - `text`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `id`: `0`
  - `label`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
  - `text`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/provenance.parquet`
- Stage: `final`
- Kind: `parquet`
- Rows: `12413`
- Schema change: `+7/-7 vs final_baseline`
- Columns (8): `example_id, dataset, original_url, license, retrieval_date, hash, split, source_filename`
- Datatypes:
  - `example_id`: `large_string`
  - `dataset`: `large_string`
  - `original_url`: `large_string`
  - `license`: `large_string`
  - `retrieval_date`: `large_string`
  - `hash`: `large_string`
  - `split`: `large_string`
  - `source_filename`: `large_string`
- Nullable fields (0): `none`
- Missing values (per column):
  - `example_id`: `0`
  - `dataset`: `0`
  - `original_url`: `0`
  - `license`: `0`
  - `retrieval_date`: `0`
  - `hash`: `0`
  - `split`: `0`
  - `source_filename`: `0`

### `datasets/final/quality_deduped.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+6/-2 vs final_baseline`
- Columns (12): `id, input, license, metadata, prompt, quality, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `quality`: `dict`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `quality`: `0`
  - `response`: `12413`
  - `rubric`: `12413`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/quality_filtered.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `433906`
- Schema change: `+6/-2 vs final_baseline`
- Columns (12): `id, input, license, metadata, prompt, quality, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `quality`: `dict`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `quality`: `0`
  - `response`: `433906`
  - `rubric`: `433906`
  - `score`: `70533`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/quality_removed.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `127772`
- Schema change: `+2/-6 vs final_baseline`
- Columns (4): `id, overall_quality_score, reason, source`
- Datatypes:
  - `id`: `str`
  - `overall_quality_score`: `float`
  - `reason`: `str`
  - `source`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `id`: `0`
  - `overall_quality_score`: `0`
  - `reason`: `0`
  - `source`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/quality_scored.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `561678`
- Schema change: `+6/-2 vs final_baseline`
- Columns (12): `id, input, license, metadata, prompt, quality, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `quality`: `dict`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `116059`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `78653`
  - `quality`: `0`
  - `response`: `561678`
  - `rubric`: `561442`
  - `score`: `162008`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/test.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `1232`
- Schema change: `+0/-0 vs final_baseline`
- Columns (8): `id, label, metadata, prompt, source, split, task, text`
- Datatypes:
  - `id`: `str`
  - `label`: `float`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
  - `text`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `id`: `0`
  - `label`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
  - `text`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/train.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `9940`
- Schema change: `+0/-0 vs final_baseline`
- Columns (8): `id, label, metadata, prompt, source, split, task, text`
- Datatypes:
  - `id`: `str`
  - `label`: `float`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
  - `text`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `id`: `0`
  - `label`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
  - `text`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/final/validation.jsonl`
- Stage: `final`
- Kind: `jsonl`
- Rows: `1241`
- Schema change: `+0/-0 vs final_baseline`
- Columns (8): `id, label, metadata, prompt, source, split, task, text`
- Datatypes:
  - `id`: `str`
  - `label`: `float`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
  - `text`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `id`: `0`
  - `label`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
  - `text`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/golden/golden-20260708T183049Z/audit_traces.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+7/-10 vs processed_baseline`
- Columns (8): `critique_scores, dedup_cluster_id, example_id, filter_decisions, is_adversarial, is_no_fallacy, metadata, primary_fallacy_label`
- Datatypes:
  - `critique_scores`: `dict`
  - `dedup_cluster_id`: `null`
  - `example_id`: `str`
  - `filter_decisions`: `list`
  - `is_adversarial`: `bool`
  - `is_no_fallacy`: `bool`
  - `metadata`: `dict`
  - `primary_fallacy_label`: `null|str`
- Nullable fields (2): `dedup_cluster_id, primary_fallacy_label`
- Missing values (per column):
  - `critique_scores`: `0`
  - `dedup_cluster_id`: `50`
  - `example_id`: `0`
  - `filter_decisions`: `0`
  - `is_adversarial`: `0`
  - `is_no_fallacy`: `0`
  - `metadata`: `0`
  - `primary_fallacy_label`: `6`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/golden/golden-20260708T183049Z/dataset.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+34/-10 vs processed_baseline`
- Columns (35): `acceptable_alternative_labels, adversarial_type, analogy_source_domain, analogy_target_domain, argument_text, attack_target, created_at, critic_model_id, critique_scores, dataset_version, decoding_config, dedup_cluster_id, difficulty_level, domain_tag, example_id, expected_sections, filter_decisions, generator_model_id, is_adversarial, is_no_fallacy, metadata, primary_fallacy_label, prohibited_behaviors, prompt_seed, reflection_style_tag, required_behaviors, rubric_hooks, source_id, split_hint, task_mode, taxonomy_version, template_id, template_version, updated_at, validation_status`
- Datatypes:
  - `acceptable_alternative_labels`: `list`
  - `adversarial_type`: `null|str`
  - `analogy_source_domain`: `str`
  - `analogy_target_domain`: `str`
  - `argument_text`: `str`
  - `attack_target`: `null|str`
  - `created_at`: `str`
  - `critic_model_id`: `str`
  - `critique_scores`: `dict`
  - `dataset_version`: `str`
  - `decoding_config`: `dict`
  - `dedup_cluster_id`: `null`
  - `difficulty_level`: `str`
  - `domain_tag`: `str`
  - `example_id`: `str`
  - `expected_sections`: `list`
  - `filter_decisions`: `list`
  - `generator_model_id`: `str`
  - `is_adversarial`: `bool`
  - `is_no_fallacy`: `bool`
  - `metadata`: `dict`
  - `primary_fallacy_label`: `null|str`
  - `prohibited_behaviors`: `list`
  - `prompt_seed`: `int`
  - `reflection_style_tag`: `str`
  - `required_behaviors`: `list`
  - `rubric_hooks`: `list`
  - `source_id`: `str`
  - `split_hint`: `str`
  - `task_mode`: `str`
  - `taxonomy_version`: `str`
  - `template_id`: `str`
  - `template_version`: `str`
  - `updated_at`: `str`
  - `validation_status`: `str`
- Nullable fields (4): `adversarial_type, attack_target, dedup_cluster_id, primary_fallacy_label`
- Missing values (per column):
  - `acceptable_alternative_labels`: `0`
  - `adversarial_type`: `40`
  - `analogy_source_domain`: `0`
  - `analogy_target_domain`: `0`
  - `argument_text`: `0`
  - `attack_target`: `40`
  - `created_at`: `0`
  - `critic_model_id`: `0`
  - `critique_scores`: `0`
  - `dataset_version`: `0`
  - `decoding_config`: `0`
  - `dedup_cluster_id`: `50`
  - `difficulty_level`: `0`
  - `domain_tag`: `0`
  - `example_id`: `0`
  - `expected_sections`: `0`
  - `filter_decisions`: `0`
  - `generator_model_id`: `0`
  - `is_adversarial`: `0`
  - `is_no_fallacy`: `0`
  - `metadata`: `0`
  - `primary_fallacy_label`: `6`
  - `prohibited_behaviors`: `0`
  - `prompt_seed`: `0`
  - `reflection_style_tag`: `0`
  - `required_behaviors`: `0`
  - `rubric_hooks`: `0`
  - `source_id`: `0`
  - `split_hint`: `0`
  - `task_mode`: `0`
  - `taxonomy_version`: `0`
  - `template_id`: `0`
  - `template_version`: `0`
  - `updated_at`: `0`
  - `validation_status`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/golden/golden-20260708T202613Z/audit_traces.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+7/-10 vs processed_baseline`
- Columns (8): `critique_scores, dedup_cluster_id, example_id, filter_decisions, is_adversarial, is_no_fallacy, metadata, primary_fallacy_label`
- Datatypes:
  - `critique_scores`: `dict`
  - `dedup_cluster_id`: `null`
  - `example_id`: `str`
  - `filter_decisions`: `list`
  - `is_adversarial`: `bool`
  - `is_no_fallacy`: `bool`
  - `metadata`: `dict`
  - `primary_fallacy_label`: `null|str`
- Nullable fields (2): `dedup_cluster_id, primary_fallacy_label`
- Missing values (per column):
  - `critique_scores`: `0`
  - `dedup_cluster_id`: `50`
  - `example_id`: `0`
  - `filter_decisions`: `0`
  - `is_adversarial`: `0`
  - `is_no_fallacy`: `0`
  - `metadata`: `0`
  - `primary_fallacy_label`: `6`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/golden/golden-20260708T202613Z/dataset.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+34/-10 vs processed_baseline`
- Columns (35): `acceptable_alternative_labels, adversarial_type, analogy_source_domain, analogy_target_domain, argument_text, attack_target, created_at, critic_model_id, critique_scores, dataset_version, decoding_config, dedup_cluster_id, difficulty_level, domain_tag, example_id, expected_sections, filter_decisions, generator_model_id, is_adversarial, is_no_fallacy, metadata, primary_fallacy_label, prohibited_behaviors, prompt_seed, reflection_style_tag, required_behaviors, rubric_hooks, source_id, split_hint, task_mode, taxonomy_version, template_id, template_version, updated_at, validation_status`
- Datatypes:
  - `acceptable_alternative_labels`: `list`
  - `adversarial_type`: `null|str`
  - `analogy_source_domain`: `str`
  - `analogy_target_domain`: `str`
  - `argument_text`: `str`
  - `attack_target`: `null|str`
  - `created_at`: `str`
  - `critic_model_id`: `str`
  - `critique_scores`: `dict`
  - `dataset_version`: `str`
  - `decoding_config`: `dict`
  - `dedup_cluster_id`: `null`
  - `difficulty_level`: `str`
  - `domain_tag`: `str`
  - `example_id`: `str`
  - `expected_sections`: `list`
  - `filter_decisions`: `list`
  - `generator_model_id`: `str`
  - `is_adversarial`: `bool`
  - `is_no_fallacy`: `bool`
  - `metadata`: `dict`
  - `primary_fallacy_label`: `null|str`
  - `prohibited_behaviors`: `list`
  - `prompt_seed`: `int`
  - `reflection_style_tag`: `str`
  - `required_behaviors`: `list`
  - `rubric_hooks`: `list`
  - `source_id`: `str`
  - `split_hint`: `str`
  - `task_mode`: `str`
  - `taxonomy_version`: `str`
  - `template_id`: `str`
  - `template_version`: `str`
  - `updated_at`: `str`
  - `validation_status`: `str`
- Nullable fields (4): `adversarial_type, attack_target, dedup_cluster_id, primary_fallacy_label`
- Missing values (per column):
  - `acceptable_alternative_labels`: `0`
  - `adversarial_type`: `40`
  - `analogy_source_domain`: `0`
  - `analogy_target_domain`: `0`
  - `argument_text`: `0`
  - `attack_target`: `40`
  - `created_at`: `0`
  - `critic_model_id`: `0`
  - `critique_scores`: `0`
  - `dataset_version`: `0`
  - `decoding_config`: `0`
  - `dedup_cluster_id`: `50`
  - `difficulty_level`: `0`
  - `domain_tag`: `0`
  - `example_id`: `0`
  - `expected_sections`: `0`
  - `filter_decisions`: `0`
  - `generator_model_id`: `0`
  - `is_adversarial`: `0`
  - `is_no_fallacy`: `0`
  - `metadata`: `0`
  - `primary_fallacy_label`: `6`
  - `prohibited_behaviors`: `0`
  - `prompt_seed`: `0`
  - `reflection_style_tag`: `0`
  - `required_behaviors`: `0`
  - `rubric_hooks`: `0`
  - `source_id`: `0`
  - `split_hint`: `0`
  - `task_mode`: `0`
  - `taxonomy_version`: `0`
  - `template_id`: `0`
  - `template_version`: `0`
  - `updated_at`: `0`
  - `validation_status`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/normalized/all_datasets.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `22326`
- Schema change: `+2/-6 vs processed_baseline`
- Columns (7): `id, label, metadata, prompt, source, task, text`
- Datatypes:
  - `id`: `str`
  - `label`: `float|null`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `source`: `str`
  - `task`: `str`
  - `text`: `str`
- Nullable fields (7): `id, label, metadata, prompt, source, task, text`
- Missing values (per column):
  - `id`: `1178`
  - `label`: `9540`
  - `metadata`: `1178`
  - `prompt`: `1178`
  - `source`: `1178`
  - `task`: `1178`
  - `text`: `1178`
- Notes: `encoding=utf-8-sig; json_error_line_33:Unterminated string starting at; json_error_line_34:Expecting value; json_error_line_35:Expecting value; json_error_line_373:Unterminated string starting at; json_error_line_374:Expecting value; json_error_line_375:Expecting value; json_error_line_467:Unterminated string starting at; json_error_line_468:Expecting value; json_error_line_469:Expecting value; json_error_line_483:Unterminated string starting at; json_error_line_484:Expecting value; json_error_line_485:Expecting value; json_error_line_1282:Unterminated string starting at; json_error_line_1283:Expecting value; json_error_line_1284:Expecting value; json_error_line_1297:Unterminated string starting at; json_error_line_1298:Expecting value; json_error_line_1299:Expecting value; json_error_line_1300:Expecting value; json_error_line_1301:Expecting value; json_error_line_1307:Unterminated string starting at; json_error_line_1308:Expecting value; json_error_line_1309:Expecting value; json_error_line_1310:Expecting value; json_error_line_1311:Expecting value; json_error_line_1316:Unterminated string starting at; json_error_line_1317:Expecting value; json_error_line_1318:Expecting value; json_error_line_1321:Unterminated string starting at; json_error_line_1322:Expecting value; json_error_line_1323:Expecting value; json_error_line_1409:Unterminated string starting at; json_error_line_1410:Expecting value; json_error_line_1411:Expecting value; json_error_line_1456:Unterminated string starting at; json_error_line_1457:Expecting value; json_error_line_1458:Expecting value; json_error_line_1489:Unterminated string starting at; json_error_line_1490:Expecting value; json_error_line_1491:Expecting value; json_error_line_1553:Unterminated string starting at; json_error_line_1554:Expecting value; json_error_line_1555:Expecting value; json_error_line_1556:Expecting value; json_error_line_1557:Expecting value; json_error_line_1587:Unterminated string starting at; json_error_line_1588:Expecting value; json_error_line_1589:Expecting value; json_error_line_1601:Unterminated string starting at; json_error_line_1602:Expecting value; json_error_line_1603:Expecting value; json_error_line_1604:Expecting value; json_error_line_1605:Expecting value; json_error_line_1613:Unterminated string starting at; json_error_line_1614:Expecting value; json_error_line_1615:Expecting value; json_error_line_1618:Unterminated string starting at; json_error_line_1619:Expecting value; json_error_line_1620:Expecting value; json_error_line_1626:Unterminated string starting at; json_error_line_1627:Expecting value; json_error_line_1628:Expecting value; json_error_line_1629:Expecting value; json_error_line_1630:Expecting value; json_error_line_1690:Unterminated string starting at; json_error_line_1691:Expecting value; json_error_line_1692:Expecting value; json_error_line_1693:Expecting value; json_error_line_1694:Expecting value; json_error_line_1708:Unterminated string starting at; json_error_line_1709:Expecting value; json_error_line_1710:Expecting value; json_error_line_1711:Expecting value; json_error_line_1712:Expecting value; json_error_line_1713:Expecting value; json_error_line_1714:Expecting value; json_error_line_1715:Expecting value; json_error_line_1716:Expecting value; json_error_line_1792:Unterminated string starting at; json_error_line_1793:Expecting value; json_error_line_1794:Expecting value; json_error_line_1813:Unterminated string starting at; json_error_line_1814:Expecting value; json_error_line_1815:Expecting value; json_error_line_1845:Unterminated string starting at; json_error_line_1846:Expecting value; json_error_line_1847:Expecting value; json_error_line_1854:Unterminated string starting at; json_error_line_1855:Expecting value; json_error_line_1856:Expecting value; json_error_line_1857:Expecting value; json_error_line_1858:Expecting value; json_error_line_1895:Unterminated string starting at; json_error_line_1896:Expecting value; json_error_line_1897:Expecting value; json_error_line_1898:Expecting value; json_error_line_1899:Expecting value; json_error_line_1914:Unterminated string starting at; json_error_line_1915:Expecting value; json_error_line_1916:Expecting value; json_error_line_1969:Unterminated string starting at; json_error_line_1970:Expecting value; json_error_line_1971:Expecting value; json_error_line_1985:Unterminated string starting at; json_error_line_1986:Expecting value; json_error_line_1987:Expecting value; json_error_line_2014:Unterminated string starting at; json_error_line_2015:Expecting value; json_error_line_2016:Expecting value; json_error_line_2131:Unterminated string starting at; json_error_line_2132:Expecting value; json_error_line_2133:Expecting value; json_error_line_2170:Unterminated string starting at; json_error_line_2171:Expecting value; json_error_line_2172:Expecting value; json_error_line_2173:Expecting value; json_error_line_2174:Expecting value; json_error_line_2175:Expecting value; json_error_line_2176:Expecting value; json_error_line_2193:Unterminated string starting at; json_error_line_2194:Expecting value; json_error_line_2195:Expecting value; json_error_line_2203:Unterminated string starting at; json_error_line_2204:Expecting value; json_error_line_2205:Expecting value; json_error_line_2220:Unterminated string starting at; json_error_line_2221:Expecting value; json_error_line_2222:Expecting value; json_error_line_2223:Unterminated string starting at; json_error_line_2224:Expecting value; json_error_line_2225:Expecting value; json_error_line_2226:Expecting value; json_error_line_2227:Expecting value; json_error_line_2253:Unterminated string starting at; json_error_line_2254:Expecting value; json_error_line_2255:Expecting value; json_error_line_2256:Expecting value; json_error_line_2257:Expecting value; json_error_line_2278:Unterminated string starting at; json_error_line_2279:Expecting value; json_error_line_2280:Expecting value; json_error_line_2356:Unterminated string starting at; json_error_line_2357:Expecting value; json_error_line_2358:Expecting value; json_error_line_2397:Unterminated string starting at; json_error_line_2398:Expecting value; json_error_line_2399:Expecting value; json_error_line_2400:Expecting value; json_error_line_2401:Expecting value; json_error_line_2419:Unterminated string starting at; json_error_line_2420:Expecting value; json_error_line_2421:Expecting value; json_error_line_2422:Expecting value; json_error_line_2423:Expecting value; json_error_line_2540:Unterminated string starting at; json_error_line_2541:Expecting value; json_error_line_2542:Expecting value; json_error_line_3002:Unterminated string starting at; json_error_line_3003:Expecting value; json_error_line_3004:Expecting value; json_error_line_3626:Unterminated string starting at; json_error_line_3627:Expecting value; json_error_line_3628:Expecting value; json_error_line_3775:Unterminated string starting at; json_error_line_3776:Expecting value; json_error_line_3777:Expecting value; json_error_line_3785:Unterminated string starting at; json_error_line_3786:Expecting value; json_error_line_3787:Expecting value; json_error_line_3844:Unterminated string starting at; json_error_line_3845:Expecting value; json_error_line_3846:Expecting value; json_error_line_3860:Unterminated string starting at; json_error_line_3861:Expecting value; json_error_line_3862:Expecting value; json_error_line_3863:Unterminated string starting at; json_error_line_3864:Expecting value; json_error_line_3865:Expecting value; json_error_line_3872:Unterminated string starting at; json_error_line_3873:Expecting value; json_error_line_3874:Expecting value; json_error_line_3905:Unterminated string starting at; json_error_line_3906:Expecting value; json_error_line_3907:Expecting value; json_error_line_3951:Unterminated string starting at; json_error_line_3952:Expecting value; json_error_line_3953:Expecting value; json_error_line_3998:Unterminated string starting at; json_error_line_3999:Expecting value; json_error_line_4000:Expecting value; json_error_line_4001:Expecting value; json_error_line_4002:Expecting value; json_error_line_4003:Expecting value; json_error_line_4004:Expecting value; json_error_line_4008:Unterminated string starting at; json_error_line_4009:Expecting value; json_error_line_4010:Expecting value; json_error_line_4023:Unterminated string starting at; json_error_line_4024:Expecting value; json_error_line_4025:Expecting value; json_error_line_4132:Unterminated string starting at; json_error_line_4133:Expecting value; json_error_line_4134:Expecting value; json_error_line_4138:Unterminated string starting at; json_error_line_4139:Expecting value; json_error_line_4140:Expecting value; json_error_line_4629:Unterminated string starting at; json_error_line_4630:Expecting value; json_error_line_4631:Expecting value; json_error_line_5023:Unterminated string starting at; json_error_line_5024:Expecting value; json_error_line_5025:Expecting value; json_error_line_6062:Unterminated string starting at; json_error_line_6063:Expecting value; json_error_line_6064:Expecting value; json_error_line_6092:Unterminated string starting at; json_error_line_6093:Expecting value; json_error_line_6094:Expecting value; json_error_line_8059:Unterminated string starting at; json_error_line_8060:Expecting value; json_error_line_8061:Expecting value; json_error_line_8070:Unterminated string starting at; json_error_line_8071:Expecting value; json_error_line_8072:Expecting value; json_error_line_8089:Unterminated string starting at; json_error_line_8090:Expecting value; json_error_line_8091:Expecting value; json_error_line_8112:Unterminated string starting at; json_error_line_8113:Expecting value; json_error_line_8114:Expecting value; json_error_line_8121:Unterminated string starting at; json_error_line_8122:Expecting value; json_error_line_8123:Expecting value; json_error_line_8138:Unterminated string starting at; json_error_line_8139:Expecting value; json_error_line_8140:Expecting value; json_error_line_8145:Unterminated string starting at; json_error_line_8146:Expecting value; json_error_line_8147:Expecting value; json_error_line_8176:Unterminated string starting at; json_error_line_8177:Expecting value; json_error_line_8178:Expecting value; json_error_line_8179:Expecting value; json_error_line_8180:Expecting value; json_error_line_8181:Expecting value; json_error_line_8182:Expecting value; json_error_line_8188:Unterminated string starting at; json_error_line_8189:Expecting value; json_error_line_8190:Expecting value; json_error_line_8211:Unterminated string starting at; json_error_line_8212:Expecting value; json_error_line_8213:Expecting value; json_error_line_8236:Unterminated string starting at; json_error_line_8237:Expecting value; json_error_line_8238:Expecting value; json_error_line_8271:Unterminated string starting at; json_error_line_8272:Expecting value; json_error_line_8273:Expecting value; json_error_line_8277:Unterminated string starting at; json_error_line_8278:Expecting value; json_error_line_8279:Expecting value; json_error_line_8280:Expecting value; json_error_line_8281:Expecting value; json_error_line_8282:Expecting value; json_error_line_8283:Expecting value; json_error_line_8291:Unterminated string starting at; json_error_line_8292:Expecting value; json_error_line_8293:Expecting value; json_error_line_8294:Expecting value; json_error_line_8295:Expecting value; json_error_line_8296:Expecting value; json_error_line_8297:Expecting value; json_error_line_8328:Unterminated string starting at; json_error_line_8329:Expecting value; json_error_line_8330:Expecting value; json_error_line_8337:Unterminated string starting at; json_error_line_8338:Expecting value; json_error_line_8339:Expecting value; json_error_line_8347:Unterminated string starting at; json_error_line_8348:Expecting value; json_error_line_8349:Expecting value; json_error_line_8415:Unterminated string starting at; json_error_line_8416:Expecting value; json_error_line_8417:Expecting value; json_error_line_8483:Unterminated string starting at; json_error_line_8484:Expecting value; json_error_line_8485:Expecting value; json_error_line_8486:Expecting value; json_error_line_8487:Expecting value; json_error_line_8488:Expecting value; json_error_line_8489:Expecting value; json_error_line_8505:Unterminated string starting at; json_error_line_8506:Expecting value; json_error_line_8507:Expecting value; json_error_line_8516:Unterminated string starting at; json_error_line_8517:Expecting value; json_error_line_8518:Expecting value; json_error_line_8519:Expecting value; json_error_line_8520:Expecting value; json_error_line_8521:Unterminated string starting at; json_error_line_8522:Expecting value; json_error_line_8523:Expecting value; json_error_line_8524:Expecting value; json_error_line_8525:Expecting value; json_error_line_8544:Unterminated string starting at; json_error_line_8545:Expecting value; json_error_line_8546:Expecting value; json_error_line_8547:Expecting value; json_error_line_8548:Expecting value; json_error_line_8549:Expecting value; json_error_line_8550:Expecting value; json_error_line_8551:Expecting value; json_error_line_8552:Expecting value; json_error_line_8574:Unterminated string starting at; json_error_line_8575:Expecting value; json_error_line_8576:Expecting value; json_error_line_8577:Expecting value; json_error_line_8578:Expecting value; json_error_line_8626:Unterminated string starting at; json_error_line_8627:Expecting value; json_error_line_8628:Expecting value; json_error_line_8636:Unterminated string starting at; json_error_line_8637:Expecting value; json_error_line_8638:Expecting value; json_error_line_8639:Expecting value; json_error_line_8640:Expecting value; json_error_line_8641:Expecting value; json_error_line_8642:Expecting value; json_error_line_8647:Unterminated string starting at; json_error_line_8648:Expecting value; json_error_line_8649:Expecting value; json_error_line_8669:Unterminated string starting at; json_error_line_8670:Expecting value; json_error_line_8671:Expecting value; json_error_line_8672:Expecting value; json_error_line_8673:Expecting value; json_error_line_8693:Unterminated string starting at; json_error_line_8694:Expecting value; json_error_line_8695:Expecting value; json_error_line_8696:Expecting value; json_error_line_8697:Expecting value; json_error_line_8701:Unterminated string starting at; json_error_line_8702:Expecting value; json_error_line_8703:Expecting value; json_error_line_8790:Unterminated string starting at; json_error_line_8791:Expecting value; json_error_line_8792:Expecting value; json_error_line_8858:Unterminated string starting at; json_error_line_8859:Expecting value; json_error_line_8860:Expecting value; json_error_line_8871:Unterminated string starting at; json_error_line_8872:Expecting value; json_error_line_8873:Expecting value; json_error_line_8874:Unterminated string starting at; json_error_line_8875:Expecting value; json_error_line_8876:Expecting value; json_error_line_8877:Expecting value; json_error_line_8878:Expecting value; json_error_line_8902:Unterminated string starting at; json_error_line_8903:Expecting value; json_error_line_8904:Expecting value; json_error_line_8926:Unterminated string starting at; json_error_line_8927:Expecting value; json_error_line_8928:Expecting value; json_error_line_8936:Unterminated string starting at; json_error_line_8937:Expecting value; json_error_line_8938:Expecting value; json_error_line_8953:Unterminated string starting at; json_error_line_8954:Expecting value; json_error_line_8955:Expecting value; json_error_line_8998:Unterminated string starting at; json_error_line_8999:Expecting value; json_error_line_9000:Expecting value; json_error_line_9001:Expecting value; json_error_line_9002:Expecting value; json_error_line_9003:Expecting value; json_error_line_9004:Expecting value; json_error_line_9045:Unterminated string starting at; json_error_line_9046:Expecting value; json_error_line_9047:Expecting value; json_error_line_9067:Unterminated string starting at; json_error_line_9068:Expecting value; json_error_line_9069:Expecting value; json_error_line_9125:Unterminated string starting at; json_error_line_9126:Expecting value; json_error_line_9127:Expecting value; json_error_line_9132:Unterminated string starting at; json_error_line_9133:Expecting value; json_error_line_9134:Expecting value; json_error_line_9135:Expecting value; json_error_line_9136:Expecting value; json_error_line_9244:Unterminated string starting at; json_error_line_9245:Expecting value; json_error_line_9246:Expecting value; json_error_line_9247:Expecting value; json_error_line_9248:Expecting value; json_error_line_9249:Expecting value; json_error_line_9250:Expecting value; json_error_line_9261:Unterminated string starting at; json_error_line_9262:Expecting value; json_error_line_9263:Expecting value; json_error_line_9264:Expecting value; json_error_line_9265:Expecting value; json_error_line_9266:Expecting value; json_error_line_9267:Expecting value; json_error_line_9343:Unterminated string starting at; json_error_line_9344:Expecting value; json_error_line_9345:Expecting value; json_error_line_9346:Expecting value; json_error_line_9347:Expecting value; json_error_line_9377:Unterminated string starting at; json_error_line_9378:Expecting value; json_error_line_9379:Expecting value; json_error_line_9427:Unterminated string starting at; json_error_line_9428:Expecting value; json_error_line_9429:Expecting value; json_error_line_9430:Expecting value; json_error_line_9431:Expecting value; json_error_line_9461:Unterminated string starting at; json_error_line_9462:Expecting value; json_error_line_9463:Expecting value; json_error_line_9482:Unterminated string starting at; json_error_line_9483:Expecting value; json_error_line_9484:Expecting value; json_error_line_9491:Unterminated string starting at; json_error_line_9492:Expecting value; json_error_line_9493:Expecting value; json_error_line_9568:Unterminated string starting at; json_error_line_9569:Expecting value; json_error_line_9570:Expecting value; json_error_line_9589:Unterminated string starting at; json_error_line_9590:Expecting value; json_error_line_9591:Expecting value; json_error_line_9605:Unterminated string starting at; json_error_line_9606:Expecting value; json_error_line_9607:Expecting value; json_error_line_9608:Expecting value; json_error_line_9609:Expecting value; json_error_line_9655:Unterminated string starting at; json_error_line_9656:Expecting value; json_error_line_9657:Expecting value; json_error_line_9691:Unterminated string starting at; json_error_line_9692:Expecting value; json_error_line_9693:Expecting value; json_error_line_9694:Expecting value; json_error_line_9695:Expecting value; json_error_line_9739:Unterminated string starting at; json_error_line_9740:Expecting value; json_error_line_9741:Expecting value; json_error_line_9778:Unterminated string starting at; json_error_line_9779:Expecting value; json_error_line_9780:Expecting value; json_error_line_9781:Unterminated string starting at; json_error_line_9782:Expecting value; json_error_line_9783:Expecting value; json_error_line_9800:Unterminated string starting at; json_error_line_9801:Expecting value; json_error_line_9802:Expecting value; json_error_line_9803:Expecting value; json_error_line_9804:Expecting value; json_error_line_9814:Unterminated string starting at; json_error_line_9815:Expecting value; json_error_line_9816:Expecting value; json_error_line_9826:Unterminated string starting at; json_error_line_9827:Extra data; json_error_line_9852:Unterminated string starting at; json_error_line_9853:Expecting value; json_error_line_9854:Expecting value; json_error_line_9855:Expecting value; json_error_line_9856:Expecting value; json_error_line_9857:Expecting value; json_error_line_9858:Expecting value; json_error_line_9873:Unterminated string starting at; json_error_line_9874:Expecting value; json_error_line_9875:Expecting value; json_error_line_9902:Unterminated string starting at; json_error_line_9903:Expecting value; json_error_line_9904:Expecting value; json_error_line_9911:Unterminated string starting at; json_error_line_9912:Expecting value; json_error_line_9913:Expecting value; json_error_line_9914:Expecting value; json_error_line_9915:Expecting value; json_error_line_9916:Expecting value; json_error_line_9917:Expecting value; json_error_line_9918:Expecting value; json_error_line_9919:Expecting value; json_error_line_9923:Unterminated string starting at; json_error_line_9924:Expecting value; json_error_line_9925:Expecting value; json_error_line_9952:Unterminated string starting at; json_error_line_9953:Expecting value; json_error_line_9954:Expecting value; json_error_line_9970:Unterminated string starting at; json_error_line_9971:Expecting value; json_error_line_9972:Expecting value; json_error_line_9982:Unterminated string starting at; json_error_line_9983:Expecting value; json_error_line_9984:Expecting value; json_error_line_10011:Unterminated string starting at; json_error_line_10012:Expecting value; json_error_line_10013:Expecting value; json_error_line_10014:Expecting value; json_error_line_10015:Expecting value; json_error_line_10022:Unterminated string starting at; json_error_line_10023:Expecting value; json_error_line_10024:Expecting value; json_error_line_10025:Expecting value; json_error_line_10026:Expecting value; json_error_line_10043:Unterminated string starting at; json_error_line_10044:Expecting value; json_error_line_10045:Expecting value; json_error_line_10046:Expecting value; json_error_line_10047:Expecting value; json_error_line_10048:Expecting value; json_error_line_10049:Expecting value; json_error_line_10079:Unterminated string starting at; json_error_line_10080:Expecting value; json_error_line_10081:Expecting value; json_error_line_10089:Unterminated string starting at; json_error_line_10090:Expecting value; json_error_line_10091:Expecting value; json_error_line_10095:Unterminated string starting at; json_error_line_10096:Expecting value; json_error_line_10097:Expecting value; json_error_line_10167:Unterminated string starting at; json_error_line_10168:Expecting value; json_error_line_10169:Expecting value; json_error_line_10242:Unterminated string starting at; json_error_line_10243:Expecting value; json_error_line_10244:Expecting value; json_error_line_10308:Unterminated string starting at; json_error_line_10309:Expecting value; json_error_line_10310:Expecting value; json_error_line_10312:Unterminated string starting at; json_error_line_10313:Expecting value; json_error_line_10314:Expecting value; json_error_line_10315:Expecting value; json_error_line_10316:Expecting value; json_error_line_10317:Expecting value; json_error_line_10318:Expecting value; json_error_line_10319:Expecting value; json_error_line_10320:Expecting value; json_error_line_10321:Expecting value; json_error_line_10322:Expecting value; json_error_line_10323:Expecting value; json_error_line_10324:Expecting value; json_error_line_10326:Unterminated string starting at; json_error_line_10327:Expecting value; json_error_line_10328:Expecting value; json_error_line_10363:Unterminated string starting at; json_error_line_10364:Expecting value; json_error_line_10365:Expecting value; json_error_line_10412:Unterminated string starting at; json_error_line_10413:Expecting value; json_error_line_10414:Expecting value; json_error_line_10459:Unterminated string starting at; json_error_line_10460:Expecting value; json_error_line_10461:Expecting value; json_error_line_10462:Expecting value; json_error_line_10463:Expecting value; json_error_line_10523:Unterminated string starting at; json_error_line_10524:Expecting value; json_error_line_10525:Expecting value; json_error_line_10549:Unterminated string starting at; json_error_line_10550:Expecting value; json_error_line_10551:Expecting value; json_error_line_10552:Expecting value; json_error_line_10553:Expecting value; json_error_line_10594:Unterminated string starting at; json_error_line_10595:Expecting value; json_error_line_10596:Expecting value; json_error_line_10597:Expecting value; json_error_line_10598:Expecting value; json_error_line_10602:Unterminated string starting at; json_error_line_10603:Expecting value; json_error_line_10604:Expecting value; json_error_line_10641:Unterminated string starting at; json_error_line_10642:Expecting value; json_error_line_10643:Expecting value; json_error_line_10645:Unterminated string starting at; json_error_line_10646:Expecting value; json_error_line_10647:Expecting value; json_error_line_10666:Unterminated string starting at; json_error_line_10667:Expecting value; json_error_line_10668:Expecting value; json_error_line_10684:Unterminated string starting at; json_error_line_10685:Expecting value; json_error_line_10686:Expecting value; json_error_line_10697:Unterminated string starting at; json_error_line_10698:Expecting value; json_error_line_10699:Expecting value; json_error_line_10736:Unterminated string starting at; json_error_line_10737:Expecting value; json_error_line_10738:Expecting value; json_error_line_10747:Unterminated string starting at; json_error_line_10748:Expecting value; json_error_line_10749:Expecting value; json_error_line_10757:Unterminated string starting at; json_error_line_10758:Expecting value; json_error_line_10759:Expecting value; json_error_line_10768:Unterminated string starting at; json_error_line_10769:Expecting value; json_error_line_10770:Expecting value; json_error_line_10804:Unterminated string starting at; json_error_line_10805:Expecting value; json_error_line_10806:Expecting value; json_error_line_10818:Unterminated string starting at; json_error_line_10819:Expecting value; json_error_line_10820:Expecting value; json_error_line_10823:Unterminated string starting at; json_error_line_10824:Expecting value; json_error_line_10825:Expecting value; json_error_line_10826:Expecting value; json_error_line_10827:Expecting value; json_error_line_10828:Expecting value; json_error_line_10829:Expecting value; json_error_line_10862:Unterminated string starting at; json_error_line_10863:Expecting value; json_error_line_10864:Expecting value; json_error_line_10868:Unterminated string starting at; json_error_line_10869:Expecting value; json_error_line_10870:Expecting value; json_error_line_10886:Unterminated string starting at; json_error_line_10887:Expecting value; json_error_line_10888:Expecting value; json_error_line_10900:Unterminated string starting at; json_error_line_10901:Expecting value; json_error_line_10902:Expecting value; json_error_line_10918:Unterminated string starting at; json_error_line_10919:Expecting value; json_error_line_10920:Expecting value; json_error_line_10923:Unterminated string starting at; json_error_line_10924:Expecting value; json_error_line_10925:Expecting value; json_error_line_10965:Unterminated string starting at; json_error_line_10966:Expecting value; json_error_line_10967:Expecting value; json_error_line_10968:Unterminated string starting at; json_error_line_10969:Expecting value; json_error_line_10970:Expecting value; json_error_line_10971:Expecting value; json_error_line_10972:Expecting value; json_error_line_10993:Unterminated string starting at; json_error_line_10994:Expecting value; json_error_line_10995:Expecting value; json_error_line_11005:Unterminated string starting at; json_error_line_11006:Expecting value; json_error_line_11007:Expecting value; json_error_line_11008:Unterminated string starting at; json_error_line_11009:Expecting value; json_error_line_11010:Expecting value; json_error_line_11011:Expecting value; json_error_line_11012:Expecting value; json_error_line_11013:Expecting value; json_error_line_11014:Expecting value; json_error_line_11018:Unterminated string starting at; json_error_line_11019:Expecting value; json_error_line_11020:Expecting value; json_error_line_11032:Unterminated string starting at; json_error_line_11033:Expecting value; json_error_line_11034:Expecting value; json_error_line_11039:Unterminated string starting at; json_error_line_11040:Expecting value; json_error_line_11041:Expecting value; json_error_line_11049:Unterminated string starting at; json_error_line_11050:Extra data; json_error_line_11189:Unterminated string starting at; json_error_line_11190:Expecting value; json_error_line_11191:Expecting value; json_error_line_11205:Unterminated string starting at; json_error_line_11206:Expecting value; json_error_line_11207:Expecting value; json_error_line_11241:Unterminated string starting at; json_error_line_11242:Expecting value; json_error_line_11243:Expecting value; json_error_line_11313:Unterminated string starting at; json_error_line_11314:Expecting value; json_error_line_11315:Expecting value; json_error_line_11316:Expecting value; json_error_line_11317:Expecting value; json_error_line_11355:Unterminated string starting at; json_error_line_11356:Expecting value; json_error_line_11357:Expecting value; json_error_line_11358:Expecting value; json_error_line_11359:Expecting value; json_error_line_11481:Unterminated string starting at; json_error_line_11482:Expecting value; json_error_line_11483:Expecting value; json_error_line_11523:Unterminated string starting at; json_error_line_11524:Expecting value; json_error_line_11525:Expecting value; json_error_line_11544:Unterminated string starting at; json_error_line_11545:Expecting value; json_error_line_11546:Expecting value; json_error_line_11562:Unterminated string starting at; json_error_line_11563:Expecting value; json_error_line_11564:Expecting value; json_error_line_11658:Unterminated string starting at; json_error_line_11659:Expecting value; json_error_line_11660:Expecting value; json_error_line_11715:Unterminated string starting at; json_error_line_11716:Expecting value; json_error_line_11717:Expecting value; json_error_line_11730:Unterminated string starting at; json_error_line_11731:Expecting value; json_error_line_11732:Expecting value; json_error_line_11737:Unterminated string starting at; json_error_line_11738:Expecting value; json_error_line_11739:Expecting value; json_error_line_11759:Unterminated string starting at; json_error_line_11760:Expecting value; json_error_line_11761:Expecting value; json_error_line_11762:Expecting value; json_error_line_11763:Expecting value; json_error_line_11764:Expecting value; json_error_line_11765:Expecting value; json_error_line_11778:Unterminated string starting at; json_error_line_11779:Expecting value; json_error_line_11780:Expecting value; json_error_line_11813:Unterminated string starting at; json_error_line_11814:Expecting value; json_error_line_11815:Expecting value; json_error_line_11816:Expecting value; json_error_line_11817:Expecting value; json_error_line_11818:Expecting value; json_error_line_11819:Expecting value; json_error_line_11820:Expecting value; json_error_line_11821:Expecting value; json_error_line_11831:Unterminated string starting at; json_error_line_11832:Expecting value; json_error_line_11833:Expecting value; json_error_line_11861:Unterminated string starting at; json_error_line_11862:Expecting value; json_error_line_11863:Expecting value; json_error_line_11927:Unterminated string starting at; json_error_line_11928:Expecting value; json_error_line_11929:Expecting value; json_error_line_11930:Expecting value; json_error_line_11931:Expecting value; json_error_line_11968:Unterminated string starting at; json_error_line_11969:Expecting value; json_error_line_11970:Expecting value; json_error_line_12009:Unterminated string starting at; json_error_line_12010:Expecting value; json_error_line_12011:Expecting value; json_error_line_12012:Expecting value; json_error_line_12013:Expecting value; json_error_line_12185:Unterminated string starting at; json_error_line_12186:Expecting value; json_error_line_12187:Expecting value; json_error_line_12331:Unterminated string starting at; json_error_line_12332:Expecting value; json_error_line_12333:Expecting value; json_error_line_12334:Expecting value; json_error_line_12335:Expecting value; json_error_line_12336:Expecting value; json_error_line_12337:Expecting value; json_error_line_12338:Expecting value; json_error_line_12339:Expecting value; json_error_line_12563:Unterminated string starting at; json_error_line_12564:Expecting value; json_error_line_12565:Expecting value; json_error_line_12937:Unterminated string starting at; json_error_line_12938:Expecting value; json_error_line_12939:Expecting value; json_error_line_13220:Unterminated string starting at; json_error_line_13221:Expecting value; json_error_line_13222:Expecting value; json_error_line_13235:Unterminated string starting at; json_error_line_13236:Expecting value; json_error_line_13237:Expecting value; json_error_line_13238:Expecting value; json_error_line_13239:Expecting value; json_error_line_13240:Expecting value; json_error_line_13241:Expecting value; json_error_line_13242:Expecting value; json_error_line_13243:Expecting value; json_error_line_13244:Expecting value; json_error_line_13245:Expecting value; json_error_line_13246:Expecting value; json_error_line_13247:Expecting value; json_error_line_13248:Expecting value; json_error_line_13249:Expecting value; json_error_line_13250:Expecting value; json_error_line_13251:Expecting value; json_error_line_13428:Unterminated string starting at; json_error_line_13429:Expecting value; json_error_line_13430:Expecting value; json_error_line_13448:Unterminated string starting at; json_error_line_13449:Expecting value; json_error_line_13450:Expecting value; json_error_line_13451:Expecting value; json_error_line_13452:Expecting value; json_error_line_13560:Unterminated string starting at; json_error_line_13561:Expecting value; json_error_line_13562:Expecting value; json_error_line_13563:Expecting value; json_error_line_13564:Expecting value; json_error_line_13565:Expecting value; json_error_line_13566:Expecting value; json_error_line_13567:Expecting value; json_error_line_13568:Expecting value; json_error_line_13569:Expecting value; json_error_line_13570:Expecting value; json_error_line_13733:Unterminated string starting at; json_error_line_13734:Expecting value; json_error_line_13735:Expecting value; json_error_line_13866:Unterminated string starting at; json_error_line_13867:Expecting value; json_error_line_13868:Expecting value; json_error_line_15564:Unterminated string starting at; json_error_line_15565:Expecting value; json_error_line_15566:Expecting value; json_error_line_15567:Expecting value; json_error_line_15568:Expecting value; json_error_line_15570:Unterminated string starting at; json_error_line_15571:Expecting value; json_error_line_15572:Expecting value; json_error_line_15593:Unterminated string starting at; json_error_line_15594:Expecting value; json_error_line_15595:Expecting value; json_error_line_15658:Unterminated string starting at; json_error_line_15659:Expecting value; json_error_line_15660:Expecting value; json_error_line_15679:Unterminated string starting at; json_error_line_15680:Expecting value; json_error_line_15681:Expecting value; json_error_line_15759:Unterminated string starting at; json_error_line_15760:Expecting value; json_error_line_15761:Expecting value; json_error_line_15764:Unterminated string starting at; json_error_line_15765:Expecting value; json_error_line_15766:Expecting value; json_error_line_15769:Unterminated string starting at; json_error_line_15770:Expecting value; json_error_line_15771:Expecting value; json_error_line_15801:Unterminated string starting at; json_error_line_15802:Expecting value; json_error_line_15803:Expecting value; json_error_line_15804:Expecting value; json_error_line_15805:Expecting value; json_error_line_15828:Unterminated string starting at; json_error_line_15829:Expecting value; json_error_line_15830:Expecting value; json_error_line_15863:Unterminated string starting at; json_error_line_15864:Expecting value; json_error_line_15865:Expecting value; json_error_line_15893:Unterminated string starting at; json_error_line_15894:Expecting value; json_error_line_15895:Expecting value; json_error_line_15896:Expecting value; json_error_line_15897:Expecting value; json_error_line_15898:Expecting value; json_error_line_15899:Expecting value; json_error_line_15900:Unterminated string starting at; json_error_line_15901:Expecting value; json_error_line_15902:Expecting value; json_error_line_15903:Expecting value; json_error_line_15904:Expecting value; json_error_line_15912:Unterminated string starting at; json_error_line_15913:Expecting value; json_error_line_15914:Expecting value; json_error_line_15942:Unterminated string starting at; json_error_line_15943:Expecting value; json_error_line_15944:Expecting value; json_error_line_16020:Unterminated string starting at; json_error_line_16021:Expecting value; json_error_line_16022:Expecting value; json_error_line_16055:Unterminated string starting at; json_error_line_16056:Expecting value; json_error_line_16057:Expecting value; json_error_line_16058:Expecting value; json_error_line_16059:Expecting value; json_error_line_16073:Unterminated string starting at; json_error_line_16074:Expecting value; json_error_line_16075:Expecting value; json_error_line_16166:Unterminated string starting at; json_error_line_16167:Expecting value; json_error_line_16168:Expecting value; json_error_line_16307:Unterminated string starting at; json_error_line_16308:Expecting value; json_error_line_16309:Expecting value; json_error_line_16330:Unterminated string starting at; json_error_line_16331:Expecting value; json_error_line_16332:Expecting value; json_error_line_16333:Expecting value; json_error_line_16334:Expecting value; json_error_line_16335:Expecting value; json_error_line_16336:Expecting value; json_error_line_16337:Expecting value; json_error_line_16338:Expecting value; json_error_line_16339:Expecting value; json_error_line_16340:Expecting value; json_error_line_16343:Unterminated string starting at; json_error_line_16344:Expecting value; json_error_line_16345:Expecting value; json_error_line_16364:Unterminated string starting at; json_error_line_16365:Expecting value; json_error_line_16366:Expecting value; json_error_line_16405:Unterminated string starting at; json_error_line_16406:Expecting value; json_error_line_16407:Expecting value; json_error_line_16424:Unterminated string starting at; json_error_line_16425:Expecting value; json_error_line_16426:Expecting value; json_error_line_16427:Expecting value; json_error_line_16428:Expecting value; json_error_line_16442:Unterminated string starting at; json_error_line_16443:Expecting value; json_error_line_16444:Expecting value; json_error_line_16445:Expecting value; json_error_line_16446:Expecting value; json_error_line_16466:Unterminated string starting at; json_error_line_16467:Expecting value; json_error_line_16468:Expecting value; json_error_line_16482:Unterminated string starting at; json_error_line_16483:Expecting value; json_error_line_16484:Expecting value; json_error_line_16531:Unterminated string starting at; json_error_line_16532:Expecting value; json_error_line_16533:Expecting value; json_error_line_16558:Unterminated string starting at; json_error_line_16559:Expecting value; json_error_line_16560:Expecting value; json_error_line_16561:Expecting value; json_error_line_16562:Expecting value; json_error_line_16563:Expecting value; json_error_line_16564:Expecting value; json_error_line_16565:Expecting value; json_error_line_16566:Expecting value; json_error_line_16567:Expecting value; json_error_line_16568:Expecting value; json_error_line_16569:Expecting value; json_error_line_16570:Expecting value; json_error_line_16571:Expecting value; json_error_line_16572:Expecting value; json_error_line_16573:Expecting value; json_error_line_16574:Expecting value; json_error_line_16575:Expecting value; json_error_line_16576:Expecting value; json_error_line_16577:Expecting value; json_error_line_16578:Expecting value; json_error_line_16579:Expecting value; json_error_line_16580:Expecting value; json_error_line_16581:Expecting value; json_error_line_16582:Expecting value; json_error_line_16583:Expecting value; json_error_line_16584:Expecting value; json_error_line_16585:Expecting value; json_error_line_16586:Expecting value; json_error_line_16653:Unterminated string starting at; json_error_line_16654:Expecting value; json_error_line_16655:Expecting value; json_error_line_16656:Expecting value; json_error_line_16657:Expecting value; json_error_line_16658:Expecting value; json_error_line_16659:Expecting value; json_error_line_16660:Expecting value; json_error_line_16661:Expecting value; json_error_line_16675:Unterminated string starting at; json_error_line_16676:Expecting value; json_error_line_16677:Expecting value; json_error_line_16680:Unterminated string starting at; json_error_line_16681:Expecting value; json_error_line_16682:Expecting value; json_error_line_16709:Unterminated string starting at; json_error_line_16710:Expecting value; json_error_line_16711:Expecting value; json_error_line_16712:Expecting value; json_error_line_16713:Expecting value; json_error_line_16742:Unterminated string starting at; json_error_line_16743:Expecting value; json_error_line_16744:Expecting value; json_error_line_16771:Unterminated string starting at; json_error_line_16772:Expecting value; json_error_line_16773:Expecting value; json_error_line_16908:Unterminated string starting at; json_error_line_16909:Expecting value; json_error_line_16910:Expecting value; json_error_line_17161:Unterminated string starting at; json_error_line_17162:Expecting value; json_error_line_17163:Expecting value; json_error_line_17193:Unterminated string starting at; json_error_line_17194:Expecting value; json_error_line_17195:Expecting value; json_error_line_18103:Unterminated string starting at; json_error_line_18104:Expecting value; json_error_line_18105:Expecting value; json_error_line_19168:Unterminated string starting at; json_error_line_19169:Expecting value; json_error_line_19170:Expecting value; json_error_line_19185:Unterminated string starting at; json_error_line_19186:Expecting value; json_error_line_19187:Expecting value; json_error_line_19208:Unterminated string starting at; json_error_line_19209:Expecting value; json_error_line_19210:Expecting value; json_error_line_19268:Unterminated string starting at; json_error_line_19269:Expecting value; json_error_line_19270:Expecting value; json_error_line_19281:Unterminated string starting at; json_error_line_19282:Expecting value; json_error_line_19283:Expecting value; json_error_line_19284:Expecting value; json_error_line_19285:Expecting value; json_error_line_19290:Unterminated string starting at; json_error_line_19291:Expecting value; json_error_line_19292:Expecting value; json_error_line_19311:Unterminated string starting at; json_error_line_19312:Expecting value; json_error_line_19313:Expecting value; json_error_line_19380:Unterminated string starting at; json_error_line_19381:Expecting value; json_error_line_19382:Expecting value; json_error_line_19405:Unterminated string starting at; json_error_line_19406:Expecting value; json_error_line_19407:Expecting value; json_error_line_19438:Unterminated string starting at; json_error_line_19439:Expecting value; json_error_line_19440:Expecting value; json_error_line_19441:Expecting value; json_error_line_19442:Expecting value; json_error_line_19460:Unterminated string starting at; json_error_line_19461:Expecting value; json_error_line_19462:Expecting value; json_error_line_19466:Unterminated string starting at; json_error_line_19467:Expecting value; json_error_line_19468:Expecting value; json_error_line_19470:Unterminated string starting at; json_error_line_19471:Expecting value; json_error_line_19472:Expecting value; json_error_line_19473:Expecting value; json_error_line_19474:Expecting value; json_error_line_19508:Unterminated string starting at; json_error_line_19509:Expecting value; json_error_line_19510:Expecting value; json_error_line_19519:Unterminated string starting at; json_error_line_19520:Expecting value; json_error_line_19521:Expecting value; json_error_line_19522:Expecting value; json_error_line_19523:Expecting value; json_error_line_19549:Unterminated string starting at; json_error_line_19550:Expecting value; json_error_line_19551:Expecting value; json_error_line_19552:Expecting value; json_error_line_19553:Expecting value; json_error_line_19564:Unterminated string starting at; json_error_line_19565:Expecting value; json_error_line_19566:Expecting value; json_error_line_19602:Unterminated string starting at; json_error_line_19603:Expecting value; json_error_line_19604:Expecting value; json_error_line_19625:Unterminated string starting at; json_error_line_19626:Expecting value; json_error_line_19627:Expecting value; json_error_line_19644:Unterminated string starting at; json_error_line_19645:Expecting value; json_error_line_19646:Expecting value; json_error_line_19647:Expecting value; json_error_line_19648:Expecting value; json_error_line_19649:Expecting value; json_error_line_19650:Expecting value; json_error_line_19683:Unterminated string starting at; json_error_line_19684:Expecting value; json_error_line_19685:Expecting value; json_error_line_19710:Unterminated string starting at; json_error_line_19711:Expecting value; json_error_line_19712:Expecting value; json_error_line_19733:Unterminated string starting at; json_error_line_19734:Expecting value; json_error_line_19735:Expecting value; json_error_line_19739:Unterminated string starting at; json_error_line_19740:Expecting value; json_error_line_19741:Expecting value; json_error_line_19757:Unterminated string starting at; json_error_line_19758:Expecting value; json_error_line_19759:Expecting value; json_error_line_19760:Expecting value; json_error_line_19761:Expecting value; json_error_line_19793:Unterminated string starting at; json_error_line_19794:Expecting value; json_error_line_19795:Expecting value; json_error_line_19806:Unterminated string starting at; json_error_line_19807:Expecting value; json_error_line_19808:Expecting value; json_error_line_19814:Unterminated string starting at; json_error_line_19815:Expecting value; json_error_line_19816:Expecting value; json_error_line_19931:Unterminated string starting at; json_error_line_19932:Expecting value; json_error_line_19933:Expecting value; json_error_line_19965:Unterminated string starting at; json_error_line_19966:Expecting value; json_error_line_19967:Expecting value; json_error_line_19980:Unterminated string starting at; json_error_line_19981:Expecting value; json_error_line_19982:Expecting value; json_error_line_20007:Unterminated string starting at; json_error_line_20008:Expecting value; json_error_line_20009:Expecting value; json_error_line_20010:Expecting value; json_error_line_20011:Expecting value; json_error_line_20024:Unterminated string starting at; json_error_line_20025:Expecting value; json_error_line_20026:Expecting value; json_error_line_20060:Unterminated string starting at; json_error_line_20061:Expecting value; json_error_line_20062:Expecting value; json_error_line_20089:Unterminated string starting at; json_error_line_20090:Expecting value; json_error_line_20091:Expecting value; json_error_line_20092:Expecting value; json_error_line_20093:Expecting value; json_error_line_20109:Unterminated string starting at; json_error_line_20110:Expecting value; json_error_line_20111:Expecting value; json_error_line_20112:Expecting value; json_error_line_20113:Expecting value; json_error_line_20237:Unterminated string starting at; json_error_line_20238:Expecting value; json_error_line_20239:Expecting value; json_error_line_20257:Unterminated string starting at; json_error_line_20258:Expecting value; json_error_line_20259:Expecting value; json_error_line_20262:Unterminated string starting at; json_error_line_20263:Expecting value; json_error_line_20264:Expecting value; json_error_line_20282:Unterminated string starting at; json_error_line_20283:Expecting value; json_error_line_20284:Expecting value; json_error_line_20302:Unterminated string starting at; json_error_line_20303:Expecting value; json_error_line_20304:Expecting value; json_error_line_20347:Unterminated string starting at; json_error_line_20348:Expecting value; json_error_line_20349:Expecting value; json_error_line_20417:Unterminated string starting at; json_error_line_20418:Expecting value; json_error_line_20419:Expecting value; json_error_line_20679:Unterminated string starting at; json_error_line_20680:Expecting value; json_error_line_20681:Expecting value; json_error_line_20763:Unterminated string starting at; json_error_line_20764:Expecting value; json_error_line_20765:Expecting value; json_error_line_20972:Unterminated string starting at; json_error_line_20973:Expecting value; json_error_line_20974:Expecting value; json_error_line_21004:Unterminated string starting at; json_error_line_21005:Expecting value; json_error_line_21006:Expecting value; json_error_line_21007:Expecting value; json_error_line_21008:Expecting value; json_error_line_21009:Expecting value; json_error_line_21010:Expecting value; json_error_line_21386:Unterminated string starting at; json_error_line_21387:Expecting value; json_error_line_21388:Expecting value; json_error_line_21573:Unterminated string starting at; json_error_line_21574:Expecting value; json_error_line_21575:Expecting value; json_error_line_21576:Expecting value; json_error_line_21577:Expecting value; json_error_line_21578:Expecting value; json_error_line_21579:Expecting value; json_error_line_21723:Unterminated string starting at; json_error_line_21724:Expecting value; json_error_line_21725:Expecting value; json_error_line_21771:Unterminated string starting at; json_error_line_21772:Expecting value; json_error_line_21773:Expecting value; json_error_line_22056:Unterminated string starting at; json_error_line_22057:Expecting value; json_error_line_22058:Expecting value; json_error_line_22079:Unterminated string starting at; json_error_line_22080:Expecting value; json_error_line_22081:Expecting value`

### `datasets/processed/normalized/asap2.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/normalized/asap_aes.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `22326`
- Schema change: `+2/-6 vs processed_baseline`
- Columns (7): `id, label, metadata, prompt, source, task, text`
- Datatypes:
  - `id`: `str`
  - `label`: `float|null`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `source`: `str`
  - `task`: `str`
  - `text`: `str`
- Nullable fields (7): `id, label, metadata, prompt, source, task, text`
- Missing values (per column):
  - `id`: `1178`
  - `label`: `9540`
  - `metadata`: `1178`
  - `prompt`: `1178`
  - `source`: `1178`
  - `task`: `1178`
  - `text`: `1178`
- Notes: `encoding=utf-8-sig; json_error_line_33:Unterminated string starting at; json_error_line_34:Expecting value; json_error_line_35:Expecting value; json_error_line_373:Unterminated string starting at; json_error_line_374:Expecting value; json_error_line_375:Expecting value; json_error_line_467:Unterminated string starting at; json_error_line_468:Expecting value; json_error_line_469:Expecting value; json_error_line_483:Unterminated string starting at; json_error_line_484:Expecting value; json_error_line_485:Expecting value; json_error_line_1282:Unterminated string starting at; json_error_line_1283:Expecting value; json_error_line_1284:Expecting value; json_error_line_1297:Unterminated string starting at; json_error_line_1298:Expecting value; json_error_line_1299:Expecting value; json_error_line_1300:Expecting value; json_error_line_1301:Expecting value; json_error_line_1307:Unterminated string starting at; json_error_line_1308:Expecting value; json_error_line_1309:Expecting value; json_error_line_1310:Expecting value; json_error_line_1311:Expecting value; json_error_line_1316:Unterminated string starting at; json_error_line_1317:Expecting value; json_error_line_1318:Expecting value; json_error_line_1321:Unterminated string starting at; json_error_line_1322:Expecting value; json_error_line_1323:Expecting value; json_error_line_1409:Unterminated string starting at; json_error_line_1410:Expecting value; json_error_line_1411:Expecting value; json_error_line_1456:Unterminated string starting at; json_error_line_1457:Expecting value; json_error_line_1458:Expecting value; json_error_line_1489:Unterminated string starting at; json_error_line_1490:Expecting value; json_error_line_1491:Expecting value; json_error_line_1553:Unterminated string starting at; json_error_line_1554:Expecting value; json_error_line_1555:Expecting value; json_error_line_1556:Expecting value; json_error_line_1557:Expecting value; json_error_line_1587:Unterminated string starting at; json_error_line_1588:Expecting value; json_error_line_1589:Expecting value; json_error_line_1601:Unterminated string starting at; json_error_line_1602:Expecting value; json_error_line_1603:Expecting value; json_error_line_1604:Expecting value; json_error_line_1605:Expecting value; json_error_line_1613:Unterminated string starting at; json_error_line_1614:Expecting value; json_error_line_1615:Expecting value; json_error_line_1618:Unterminated string starting at; json_error_line_1619:Expecting value; json_error_line_1620:Expecting value; json_error_line_1626:Unterminated string starting at; json_error_line_1627:Expecting value; json_error_line_1628:Expecting value; json_error_line_1629:Expecting value; json_error_line_1630:Expecting value; json_error_line_1690:Unterminated string starting at; json_error_line_1691:Expecting value; json_error_line_1692:Expecting value; json_error_line_1693:Expecting value; json_error_line_1694:Expecting value; json_error_line_1708:Unterminated string starting at; json_error_line_1709:Expecting value; json_error_line_1710:Expecting value; json_error_line_1711:Expecting value; json_error_line_1712:Expecting value; json_error_line_1713:Expecting value; json_error_line_1714:Expecting value; json_error_line_1715:Expecting value; json_error_line_1716:Expecting value; json_error_line_1792:Unterminated string starting at; json_error_line_1793:Expecting value; json_error_line_1794:Expecting value; json_error_line_1813:Unterminated string starting at; json_error_line_1814:Expecting value; json_error_line_1815:Expecting value; json_error_line_1845:Unterminated string starting at; json_error_line_1846:Expecting value; json_error_line_1847:Expecting value; json_error_line_1854:Unterminated string starting at; json_error_line_1855:Expecting value; json_error_line_1856:Expecting value; json_error_line_1857:Expecting value; json_error_line_1858:Expecting value; json_error_line_1895:Unterminated string starting at; json_error_line_1896:Expecting value; json_error_line_1897:Expecting value; json_error_line_1898:Expecting value; json_error_line_1899:Expecting value; json_error_line_1914:Unterminated string starting at; json_error_line_1915:Expecting value; json_error_line_1916:Expecting value; json_error_line_1969:Unterminated string starting at; json_error_line_1971:Expecting value; json_error_line_1973:Expecting value; json_error_line_1987:Unterminated string starting at; json_error_line_1988:Expecting value; json_error_line_1989:Expecting value; json_error_line_2016:Unterminated string starting at; json_error_line_2017:Expecting value; json_error_line_2018:Expecting value; json_error_line_2133:Unterminated string starting at; json_error_line_2134:Expecting value; json_error_line_2135:Expecting value; json_error_line_2172:Unterminated string starting at; json_error_line_2173:Expecting value; json_error_line_2174:Expecting value; json_error_line_2176:Expecting value; json_error_line_2177:Expecting value; json_error_line_2178:Expecting value; json_error_line_2180:Expecting value; json_error_line_2197:Unterminated string starting at; json_error_line_2198:Expecting value; json_error_line_2199:Expecting value; json_error_line_2207:Unterminated string starting at; json_error_line_2208:Expecting value; json_error_line_2209:Expecting value; json_error_line_2224:Unterminated string starting at; json_error_line_2225:Expecting value; json_error_line_2226:Expecting value; json_error_line_2227:Unterminated string starting at; json_error_line_2228:Expecting value; json_error_line_2229:Expecting value; json_error_line_2230:Expecting value; json_error_line_2231:Expecting value; json_error_line_2257:Unterminated string starting at; json_error_line_2258:Expecting value; json_error_line_2259:Expecting value; json_error_line_2260:Expecting value; json_error_line_2261:Expecting value; json_error_line_2282:Unterminated string starting at; json_error_line_2283:Expecting value; json_error_line_2284:Expecting value; json_error_line_2360:Unterminated string starting at; json_error_line_2361:Expecting value; json_error_line_2362:Expecting value; json_error_line_2401:Unterminated string starting at; json_error_line_2402:Expecting value; json_error_line_2403:Expecting value; json_error_line_2404:Expecting value; json_error_line_2405:Expecting value; json_error_line_2423:Unterminated string starting at; json_error_line_2424:Expecting value; json_error_line_2425:Expecting value; json_error_line_2426:Expecting value; json_error_line_2427:Expecting value; json_error_line_2544:Unterminated string starting at; json_error_line_2545:Expecting value; json_error_line_2546:Expecting value; json_error_line_3006:Unterminated string starting at; json_error_line_3007:Expecting value; json_error_line_3008:Expecting value; json_error_line_3630:Unterminated string starting at; json_error_line_3631:Expecting value; json_error_line_3632:Expecting value; json_error_line_3779:Unterminated string starting at; json_error_line_3780:Expecting value; json_error_line_3781:Expecting value; json_error_line_3789:Unterminated string starting at; json_error_line_3791:Expecting value; json_error_line_3793:Expecting value; json_error_line_3850:Unterminated string starting at; json_error_line_3851:Expecting value; json_error_line_3852:Expecting value; json_error_line_3866:Unterminated string starting at; json_error_line_3867:Expecting value; json_error_line_3868:Expecting value; json_error_line_3869:Unterminated string starting at; json_error_line_3870:Expecting value; json_error_line_3871:Expecting value; json_error_line_3878:Unterminated string starting at; json_error_line_3879:Expecting value; json_error_line_3880:Expecting value; json_error_line_3911:Unterminated string starting at; json_error_line_3912:Expecting value; json_error_line_3913:Expecting value; json_error_line_3957:Unterminated string starting at; json_error_line_3958:Expecting value; json_error_line_3959:Expecting value; json_error_line_4004:Unterminated string starting at; json_error_line_4005:Expecting value; json_error_line_4006:Expecting value; json_error_line_4007:Expecting value; json_error_line_4008:Expecting value; json_error_line_4009:Expecting value; json_error_line_4010:Expecting value; json_error_line_4014:Unterminated string starting at; json_error_line_4015:Expecting value; json_error_line_4016:Expecting value; json_error_line_4029:Unterminated string starting at; json_error_line_4031:Expecting value; json_error_line_4033:Expecting value; json_error_line_4140:Unterminated string starting at; json_error_line_4141:Expecting value; json_error_line_4142:Expecting value; json_error_line_4146:Unterminated string starting at; json_error_line_4147:Expecting value; json_error_line_4148:Expecting value; json_error_line_4637:Unterminated string starting at; json_error_line_4638:Expecting value; json_error_line_4639:Expecting value; json_error_line_5031:Unterminated string starting at; json_error_line_5032:Expecting value; json_error_line_5033:Expecting value; json_error_line_6070:Unterminated string starting at; json_error_line_6071:Expecting value; json_error_line_6072:Expecting value; json_error_line_6100:Unterminated string starting at; json_error_line_6101:Expecting value; json_error_line_6102:Expecting value; json_error_line_8067:Unterminated string starting at; json_error_line_8068:Expecting value; json_error_line_8069:Expecting value; json_error_line_8078:Unterminated string starting at; json_error_line_8079:Expecting value; json_error_line_8080:Expecting value; json_error_line_8097:Unterminated string starting at; json_error_line_8098:Expecting value; json_error_line_8099:Expecting value; json_error_line_8120:Unterminated string starting at; json_error_line_8121:Expecting value; json_error_line_8122:Expecting value; json_error_line_8129:Unterminated string starting at; json_error_line_8130:Expecting value; json_error_line_8131:Expecting value; json_error_line_8146:Unterminated string starting at; json_error_line_8147:Expecting value; json_error_line_8148:Expecting value; json_error_line_8153:Unterminated string starting at; json_error_line_8154:Expecting value; json_error_line_8155:Expecting value; json_error_line_8184:Unterminated string starting at; json_error_line_8185:Expecting value; json_error_line_8186:Expecting value; json_error_line_8187:Expecting value; json_error_line_8188:Expecting value; json_error_line_8189:Expecting value; json_error_line_8190:Expecting value; json_error_line_8196:Unterminated string starting at; json_error_line_8197:Expecting value; json_error_line_8198:Expecting value; json_error_line_8219:Unterminated string starting at; json_error_line_8220:Expecting value; json_error_line_8221:Expecting value; json_error_line_8244:Unterminated string starting at; json_error_line_8245:Expecting value; json_error_line_8246:Expecting value; json_error_line_8279:Unterminated string starting at; json_error_line_8280:Expecting value; json_error_line_8281:Expecting value; json_error_line_8285:Unterminated string starting at; json_error_line_8286:Expecting value; json_error_line_8287:Expecting value; json_error_line_8288:Expecting value; json_error_line_8289:Expecting value; json_error_line_8290:Expecting value; json_error_line_8291:Expecting value; json_error_line_8299:Unterminated string starting at; json_error_line_8300:Expecting value; json_error_line_8301:Expecting value; json_error_line_8302:Expecting value; json_error_line_8303:Expecting value; json_error_line_8304:Expecting value; json_error_line_8305:Expecting value; json_error_line_8336:Unterminated string starting at; json_error_line_8337:Expecting value; json_error_line_8338:Expecting value; json_error_line_8345:Unterminated string starting at; json_error_line_8346:Expecting value; json_error_line_8347:Expecting value; json_error_line_8355:Unterminated string starting at; json_error_line_8356:Expecting value; json_error_line_8357:Expecting value; json_error_line_8423:Unterminated string starting at; json_error_line_8424:Expecting value; json_error_line_8425:Expecting value; json_error_line_8491:Unterminated string starting at; json_error_line_8492:Expecting value; json_error_line_8493:Expecting value; json_error_line_8494:Expecting value; json_error_line_8495:Expecting value; json_error_line_8496:Expecting value; json_error_line_8497:Expecting value; json_error_line_8513:Unterminated string starting at; json_error_line_8514:Expecting value; json_error_line_8515:Expecting value; json_error_line_8524:Unterminated string starting at; json_error_line_8525:Expecting value; json_error_line_8526:Expecting value; json_error_line_8527:Expecting value; json_error_line_8528:Expecting value; json_error_line_8529:Unterminated string starting at; json_error_line_8530:Expecting value; json_error_line_8531:Expecting value; json_error_line_8532:Expecting value; json_error_line_8533:Expecting value; json_error_line_8552:Unterminated string starting at; json_error_line_8553:Expecting value; json_error_line_8554:Expecting value; json_error_line_8555:Expecting value; json_error_line_8556:Expecting value; json_error_line_8557:Expecting value; json_error_line_8558:Expecting value; json_error_line_8559:Expecting value; json_error_line_8560:Expecting value; json_error_line_8582:Unterminated string starting at; json_error_line_8583:Expecting value; json_error_line_8584:Expecting value; json_error_line_8585:Expecting value; json_error_line_8586:Expecting value; json_error_line_8634:Unterminated string starting at; json_error_line_8635:Expecting value; json_error_line_8636:Expecting value; json_error_line_8644:Unterminated string starting at; json_error_line_8645:Expecting value; json_error_line_8646:Expecting value; json_error_line_8647:Expecting value; json_error_line_8648:Expecting value; json_error_line_8649:Expecting value; json_error_line_8650:Expecting value; json_error_line_8655:Unterminated string starting at; json_error_line_8656:Expecting value; json_error_line_8657:Expecting value; json_error_line_8677:Unterminated string starting at; json_error_line_8678:Expecting value; json_error_line_8679:Expecting value; json_error_line_8680:Expecting value; json_error_line_8681:Expecting value; json_error_line_8701:Unterminated string starting at; json_error_line_8702:Expecting value; json_error_line_8703:Expecting value; json_error_line_8704:Expecting value; json_error_line_8705:Expecting value; json_error_line_8709:Unterminated string starting at; json_error_line_8710:Expecting value; json_error_line_8711:Expecting value; json_error_line_8798:Unterminated string starting at; json_error_line_8799:Expecting value; json_error_line_8800:Expecting value; json_error_line_8866:Unterminated string starting at; json_error_line_8867:Expecting value; json_error_line_8868:Expecting value; json_error_line_8879:Unterminated string starting at; json_error_line_8880:Expecting value; json_error_line_8881:Expecting value; json_error_line_8882:Unterminated string starting at; json_error_line_8883:Expecting value; json_error_line_8884:Expecting value; json_error_line_8885:Expecting value; json_error_line_8886:Expecting value; json_error_line_8910:Unterminated string starting at; json_error_line_8911:Expecting value; json_error_line_8912:Expecting value; json_error_line_8934:Unterminated string starting at; json_error_line_8935:Expecting value; json_error_line_8936:Expecting value; json_error_line_8944:Unterminated string starting at; json_error_line_8945:Expecting value; json_error_line_8946:Expecting value; json_error_line_8961:Unterminated string starting at; json_error_line_8962:Expecting value; json_error_line_8963:Expecting value; json_error_line_9006:Unterminated string starting at; json_error_line_9007:Expecting value; json_error_line_9008:Expecting value; json_error_line_9009:Expecting value; json_error_line_9010:Expecting value; json_error_line_9011:Expecting value; json_error_line_9012:Expecting value; json_error_line_9053:Unterminated string starting at; json_error_line_9054:Expecting value; json_error_line_9055:Expecting value; json_error_line_9075:Unterminated string starting at; json_error_line_9076:Expecting value; json_error_line_9077:Expecting value; json_error_line_9133:Unterminated string starting at; json_error_line_9134:Expecting value; json_error_line_9135:Expecting value; json_error_line_9140:Unterminated string starting at; json_error_line_9141:Expecting value; json_error_line_9142:Expecting value; json_error_line_9143:Expecting value; json_error_line_9144:Expecting value; json_error_line_9252:Unterminated string starting at; json_error_line_9253:Expecting value; json_error_line_9254:Expecting value; json_error_line_9255:Expecting value; json_error_line_9256:Expecting value; json_error_line_9257:Expecting value; json_error_line_9258:Expecting value; json_error_line_9269:Unterminated string starting at; json_error_line_9270:Expecting value; json_error_line_9271:Expecting value; json_error_line_9272:Expecting value; json_error_line_9273:Expecting value; json_error_line_9274:Expecting value; json_error_line_9275:Expecting value; json_error_line_9351:Unterminated string starting at; json_error_line_9352:Expecting value; json_error_line_9353:Expecting value; json_error_line_9354:Expecting value; json_error_line_9355:Expecting value; json_error_line_9385:Unterminated string starting at; json_error_line_9386:Expecting value; json_error_line_9387:Expecting value; json_error_line_9435:Unterminated string starting at; json_error_line_9436:Expecting value; json_error_line_9437:Expecting value; json_error_line_9438:Expecting value; json_error_line_9439:Expecting value; json_error_line_9469:Unterminated string starting at; json_error_line_9470:Expecting value; json_error_line_9471:Expecting value; json_error_line_9490:Unterminated string starting at; json_error_line_9491:Expecting value; json_error_line_9492:Expecting value; json_error_line_9499:Unterminated string starting at; json_error_line_9500:Expecting value; json_error_line_9501:Expecting value; json_error_line_9576:Unterminated string starting at; json_error_line_9577:Expecting value; json_error_line_9578:Expecting value; json_error_line_9597:Unterminated string starting at; json_error_line_9598:Expecting value; json_error_line_9599:Expecting value; json_error_line_9613:Unterminated string starting at; json_error_line_9614:Expecting value; json_error_line_9615:Expecting value; json_error_line_9616:Expecting value; json_error_line_9617:Expecting value; json_error_line_9663:Unterminated string starting at; json_error_line_9664:Expecting value; json_error_line_9665:Expecting value; json_error_line_9699:Unterminated string starting at; json_error_line_9700:Expecting value; json_error_line_9701:Expecting value; json_error_line_9702:Expecting value; json_error_line_9703:Expecting value; json_error_line_9747:Unterminated string starting at; json_error_line_9748:Expecting value; json_error_line_9749:Expecting value; json_error_line_9786:Unterminated string starting at; json_error_line_9787:Expecting value; json_error_line_9788:Expecting value; json_error_line_9789:Unterminated string starting at; json_error_line_9790:Expecting value; json_error_line_9791:Expecting value; json_error_line_9808:Unterminated string starting at; json_error_line_9809:Expecting value; json_error_line_9810:Expecting value; json_error_line_9811:Expecting value; json_error_line_9812:Expecting value; json_error_line_9822:Unterminated string starting at; json_error_line_9823:Expecting value; json_error_line_9824:Expecting value; json_error_line_9834:Unterminated string starting at; json_error_line_9835:Extra data; json_error_line_9860:Unterminated string starting at; json_error_line_9861:Expecting value; json_error_line_9862:Expecting value; json_error_line_9863:Expecting value; json_error_line_9864:Expecting value; json_error_line_9865:Expecting value; json_error_line_9866:Expecting value; json_error_line_9881:Unterminated string starting at; json_error_line_9882:Expecting value; json_error_line_9883:Expecting value; json_error_line_9910:Unterminated string starting at; json_error_line_9911:Expecting value; json_error_line_9912:Expecting value; json_error_line_9919:Unterminated string starting at; json_error_line_9920:Expecting value; json_error_line_9921:Expecting value; json_error_line_9922:Expecting value; json_error_line_9923:Expecting value; json_error_line_9924:Expecting value; json_error_line_9925:Expecting value; json_error_line_9926:Expecting value; json_error_line_9927:Expecting value; json_error_line_9931:Unterminated string starting at; json_error_line_9932:Expecting value; json_error_line_9933:Expecting value; json_error_line_9960:Unterminated string starting at; json_error_line_9961:Expecting value; json_error_line_9962:Expecting value; json_error_line_9978:Unterminated string starting at; json_error_line_9979:Expecting value; json_error_line_9980:Expecting value; json_error_line_9990:Unterminated string starting at; json_error_line_9991:Expecting value; json_error_line_9992:Expecting value; json_error_line_10019:Unterminated string starting at; json_error_line_10020:Expecting value; json_error_line_10021:Expecting value; json_error_line_10022:Expecting value; json_error_line_10023:Expecting value; json_error_line_10030:Unterminated string starting at; json_error_line_10031:Expecting value; json_error_line_10032:Expecting value; json_error_line_10033:Expecting value; json_error_line_10034:Expecting value; json_error_line_10051:Unterminated string starting at; json_error_line_10052:Expecting value; json_error_line_10053:Expecting value; json_error_line_10054:Expecting value; json_error_line_10055:Expecting value; json_error_line_10056:Expecting value; json_error_line_10057:Expecting value; json_error_line_10087:Unterminated string starting at; json_error_line_10088:Expecting value; json_error_line_10089:Expecting value; json_error_line_10097:Unterminated string starting at; json_error_line_10098:Expecting value; json_error_line_10099:Expecting value; json_error_line_10103:Unterminated string starting at; json_error_line_10104:Expecting value; json_error_line_10105:Expecting value; json_error_line_10175:Unterminated string starting at; json_error_line_10179:Expecting value; json_error_line_10183:Expecting value; json_error_line_10256:Unterminated string starting at; json_error_line_10257:Expecting value; json_error_line_10258:Expecting value; json_error_line_10322:Unterminated string starting at; json_error_line_10323:Expecting value; json_error_line_10324:Expecting value; json_error_line_10326:Unterminated string starting at; json_error_line_10327:Expecting value; json_error_line_10328:Expecting value; json_error_line_10329:Expecting value; json_error_line_10330:Expecting value; json_error_line_10331:Expecting value; json_error_line_10332:Expecting value; json_error_line_10333:Expecting value; json_error_line_10334:Expecting value; json_error_line_10335:Expecting value; json_error_line_10336:Expecting value; json_error_line_10337:Expecting value; json_error_line_10338:Expecting value; json_error_line_10340:Unterminated string starting at; json_error_line_10341:Expecting value; json_error_line_10342:Expecting value; json_error_line_10377:Unterminated string starting at; json_error_line_10378:Expecting value; json_error_line_10379:Expecting value; json_error_line_10426:Unterminated string starting at; json_error_line_10427:Expecting value; json_error_line_10428:Expecting value; json_error_line_10473:Unterminated string starting at; json_error_line_10474:Expecting value; json_error_line_10475:Expecting value; json_error_line_10476:Expecting value; json_error_line_10477:Expecting value; json_error_line_10537:Unterminated string starting at; json_error_line_10538:Expecting value; json_error_line_10539:Expecting value; json_error_line_10563:Unterminated string starting at; json_error_line_10564:Expecting value; json_error_line_10565:Expecting value; json_error_line_10566:Expecting value; json_error_line_10567:Expecting value; json_error_line_10608:Unterminated string starting at; json_error_line_10609:Expecting value; json_error_line_10610:Expecting value; json_error_line_10611:Expecting value; json_error_line_10612:Expecting value; json_error_line_10616:Unterminated string starting at; json_error_line_10617:Expecting value; json_error_line_10618:Expecting value; json_error_line_10655:Unterminated string starting at; json_error_line_10656:Expecting value; json_error_line_10657:Expecting value; json_error_line_10659:Unterminated string starting at; json_error_line_10660:Expecting value; json_error_line_10661:Expecting value; json_error_line_10680:Unterminated string starting at; json_error_line_10681:Expecting value; json_error_line_10682:Expecting value; json_error_line_10698:Unterminated string starting at; json_error_line_10699:Expecting value; json_error_line_10700:Expecting value; json_error_line_10711:Unterminated string starting at; json_error_line_10712:Expecting value; json_error_line_10713:Expecting value; json_error_line_10750:Unterminated string starting at; json_error_line_10751:Expecting value; json_error_line_10752:Expecting value; json_error_line_10761:Unterminated string starting at; json_error_line_10762:Expecting value; json_error_line_10763:Expecting value; json_error_line_10771:Unterminated string starting at; json_error_line_10772:Expecting value; json_error_line_10773:Expecting value; json_error_line_10782:Unterminated string starting at; json_error_line_10783:Expecting value; json_error_line_10784:Expecting value; json_error_line_10818:Unterminated string starting at; json_error_line_10819:Expecting value; json_error_line_10820:Expecting value; json_error_line_10832:Unterminated string starting at; json_error_line_10833:Expecting value; json_error_line_10834:Expecting value; json_error_line_10837:Unterminated string starting at; json_error_line_10838:Expecting value; json_error_line_10839:Expecting value; json_error_line_10840:Expecting value; json_error_line_10841:Expecting value; json_error_line_10842:Expecting value; json_error_line_10843:Expecting value; json_error_line_10876:Unterminated string starting at; json_error_line_10877:Expecting value; json_error_line_10878:Expecting value; json_error_line_10882:Unterminated string starting at; json_error_line_10883:Expecting value; json_error_line_10884:Expecting value; json_error_line_10900:Unterminated string starting at; json_error_line_10901:Expecting value; json_error_line_10902:Expecting value; json_error_line_10914:Unterminated string starting at; json_error_line_10915:Expecting value; json_error_line_10916:Expecting value; json_error_line_10932:Unterminated string starting at; json_error_line_10933:Expecting value; json_error_line_10934:Expecting value; json_error_line_10937:Unterminated string starting at; json_error_line_10938:Expecting value; json_error_line_10939:Expecting value; json_error_line_10979:Unterminated string starting at; json_error_line_10980:Expecting value; json_error_line_10981:Expecting value; json_error_line_10982:Unterminated string starting at; json_error_line_10983:Expecting value; json_error_line_10984:Expecting value; json_error_line_10985:Expecting value; json_error_line_10986:Expecting value; json_error_line_11007:Unterminated string starting at; json_error_line_11008:Expecting value; json_error_line_11009:Expecting value; json_error_line_11019:Unterminated string starting at; json_error_line_11020:Expecting value; json_error_line_11021:Expecting value; json_error_line_11022:Unterminated string starting at; json_error_line_11023:Expecting value; json_error_line_11024:Expecting value; json_error_line_11025:Expecting value; json_error_line_11026:Expecting value; json_error_line_11027:Expecting value; json_error_line_11028:Expecting value; json_error_line_11032:Unterminated string starting at; json_error_line_11033:Expecting value; json_error_line_11034:Expecting value; json_error_line_11046:Unterminated string starting at; json_error_line_11047:Expecting value; json_error_line_11048:Expecting value; json_error_line_11053:Unterminated string starting at; json_error_line_11054:Expecting value; json_error_line_11055:Expecting value; json_error_line_11063:Unterminated string starting at; json_error_line_11064:Extra data; json_error_line_11203:Unterminated string starting at; json_error_line_11204:Expecting value; json_error_line_11205:Expecting value; json_error_line_11219:Unterminated string starting at; json_error_line_11220:Expecting value; json_error_line_11221:Expecting value; json_error_line_11255:Unterminated string starting at; json_error_line_11256:Expecting value; json_error_line_11257:Expecting value; json_error_line_11327:Unterminated string starting at; json_error_line_11328:Expecting value; json_error_line_11329:Expecting value; json_error_line_11330:Expecting value; json_error_line_11331:Expecting value; json_error_line_11369:Unterminated string starting at; json_error_line_11370:Expecting value; json_error_line_11371:Expecting value; json_error_line_11372:Expecting value; json_error_line_11373:Expecting value; json_error_line_11495:Unterminated string starting at; json_error_line_11496:Expecting value; json_error_line_11497:Expecting value; json_error_line_11537:Unterminated string starting at; json_error_line_11538:Expecting value; json_error_line_11539:Expecting value; json_error_line_11558:Unterminated string starting at; json_error_line_11559:Expecting value; json_error_line_11560:Expecting value; json_error_line_11576:Unterminated string starting at; json_error_line_11577:Expecting value; json_error_line_11578:Expecting value; json_error_line_11672:Unterminated string starting at; json_error_line_11673:Expecting value; json_error_line_11674:Expecting value; json_error_line_11729:Unterminated string starting at; json_error_line_11730:Expecting value; json_error_line_11731:Expecting value; json_error_line_11744:Unterminated string starting at; json_error_line_11745:Expecting value; json_error_line_11746:Expecting value; json_error_line_11751:Unterminated string starting at; json_error_line_11752:Expecting value; json_error_line_11753:Expecting value; json_error_line_11773:Unterminated string starting at; json_error_line_11774:Expecting value; json_error_line_11775:Expecting value; json_error_line_11776:Expecting value; json_error_line_11777:Expecting value; json_error_line_11778:Expecting value; json_error_line_11779:Expecting value; json_error_line_11792:Unterminated string starting at; json_error_line_11793:Expecting value; json_error_line_11794:Expecting value; json_error_line_11827:Unterminated string starting at; json_error_line_11828:Expecting value; json_error_line_11829:Expecting value; json_error_line_11830:Expecting value; json_error_line_11831:Expecting value; json_error_line_11832:Expecting value; json_error_line_11833:Expecting value; json_error_line_11834:Expecting value; json_error_line_11835:Expecting value; json_error_line_11845:Unterminated string starting at; json_error_line_11846:Expecting value; json_error_line_11847:Expecting value; json_error_line_11875:Unterminated string starting at; json_error_line_11876:Expecting value; json_error_line_11877:Expecting value; json_error_line_11941:Unterminated string starting at; json_error_line_11942:Expecting value; json_error_line_11943:Expecting value; json_error_line_11944:Expecting value; json_error_line_11945:Expecting value; json_error_line_11982:Unterminated string starting at; json_error_line_11983:Expecting value; json_error_line_11984:Expecting value; json_error_line_12023:Unterminated string starting at; json_error_line_12024:Expecting value; json_error_line_12025:Expecting value; json_error_line_12026:Expecting value; json_error_line_12027:Expecting value; json_error_line_12199:Unterminated string starting at; json_error_line_12200:Expecting value; json_error_line_12201:Expecting value; json_error_line_12345:Unterminated string starting at; json_error_line_12346:Expecting value; json_error_line_12347:Expecting value; json_error_line_12348:Expecting value; json_error_line_12349:Expecting value; json_error_line_12350:Expecting value; json_error_line_12351:Expecting value; json_error_line_12352:Expecting value; json_error_line_12353:Expecting value; json_error_line_12577:Unterminated string starting at; json_error_line_12578:Expecting value; json_error_line_12579:Expecting value; json_error_line_12951:Unterminated string starting at; json_error_line_12952:Expecting value; json_error_line_12953:Expecting value; json_error_line_13234:Unterminated string starting at; json_error_line_13235:Expecting value; json_error_line_13236:Expecting value; json_error_line_13249:Unterminated string starting at; json_error_line_13250:Expecting value; json_error_line_13251:Expecting value; json_error_line_13252:Expecting value; json_error_line_13253:Expecting value; json_error_line_13254:Expecting value; json_error_line_13255:Expecting value; json_error_line_13256:Expecting value; json_error_line_13257:Expecting value; json_error_line_13258:Expecting value; json_error_line_13259:Expecting value; json_error_line_13260:Expecting value; json_error_line_13261:Expecting value; json_error_line_13262:Expecting value; json_error_line_13263:Expecting value; json_error_line_13264:Expecting value; json_error_line_13265:Expecting value; json_error_line_13442:Unterminated string starting at; json_error_line_13443:Expecting value; json_error_line_13444:Expecting value; json_error_line_13462:Unterminated string starting at; json_error_line_13463:Expecting value; json_error_line_13464:Expecting value; json_error_line_13465:Expecting value; json_error_line_13466:Expecting value; json_error_line_13574:Unterminated string starting at; json_error_line_13575:Expecting value; json_error_line_13576:Expecting value; json_error_line_13577:Expecting value; json_error_line_13578:Expecting value; json_error_line_13579:Expecting value; json_error_line_13580:Expecting value; json_error_line_13581:Expecting value; json_error_line_13582:Expecting value; json_error_line_13583:Expecting value; json_error_line_13584:Expecting value; json_error_line_13747:Unterminated string starting at; json_error_line_13748:Expecting value; json_error_line_13749:Expecting value; json_error_line_13880:Unterminated string starting at; json_error_line_13881:Expecting value; json_error_line_13882:Expecting value; json_error_line_15578:Unterminated string starting at; json_error_line_15579:Expecting value; json_error_line_15580:Expecting value; json_error_line_15581:Expecting value; json_error_line_15582:Expecting value; json_error_line_15584:Unterminated string starting at; json_error_line_15585:Expecting value; json_error_line_15586:Expecting value; json_error_line_15607:Unterminated string starting at; json_error_line_15608:Expecting value; json_error_line_15609:Expecting value; json_error_line_15672:Unterminated string starting at; json_error_line_15673:Expecting value; json_error_line_15674:Expecting value; json_error_line_15693:Unterminated string starting at; json_error_line_15694:Expecting value; json_error_line_15695:Expecting value; json_error_line_15773:Unterminated string starting at; json_error_line_15774:Expecting value; json_error_line_15775:Expecting value; json_error_line_15778:Unterminated string starting at; json_error_line_15779:Expecting value; json_error_line_15780:Expecting value; json_error_line_15783:Unterminated string starting at; json_error_line_15784:Expecting value; json_error_line_15785:Expecting value; json_error_line_15815:Unterminated string starting at; json_error_line_15816:Expecting value; json_error_line_15817:Expecting value; json_error_line_15818:Expecting value; json_error_line_15819:Expecting value; json_error_line_15842:Unterminated string starting at; json_error_line_15843:Expecting value; json_error_line_15844:Expecting value; json_error_line_15877:Unterminated string starting at; json_error_line_15878:Expecting value; json_error_line_15879:Expecting value; json_error_line_15907:Unterminated string starting at; json_error_line_15908:Expecting value; json_error_line_15909:Expecting value; json_error_line_15910:Expecting value; json_error_line_15911:Expecting value; json_error_line_15912:Expecting value; json_error_line_15913:Expecting value; json_error_line_15914:Unterminated string starting at; json_error_line_15915:Expecting value; json_error_line_15916:Expecting value; json_error_line_15917:Expecting value; json_error_line_15918:Expecting value; json_error_line_15926:Unterminated string starting at; json_error_line_15927:Expecting value; json_error_line_15928:Expecting value; json_error_line_15956:Unterminated string starting at; json_error_line_15957:Expecting value; json_error_line_15958:Expecting value; json_error_line_16034:Unterminated string starting at; json_error_line_16037:Expecting value; json_error_line_16040:Expecting value; json_error_line_16073:Unterminated string starting at; json_error_line_16074:Expecting value; json_error_line_16075:Expecting value; json_error_line_16076:Expecting value; json_error_line_16077:Expecting value; json_error_line_16091:Unterminated string starting at; json_error_line_16092:Expecting value; json_error_line_16093:Expecting value; json_error_line_16184:Unterminated string starting at; json_error_line_16185:Expecting value; json_error_line_16186:Expecting value; json_error_line_16325:Unterminated string starting at; json_error_line_16326:Expecting value; json_error_line_16327:Expecting value; json_error_line_16348:Unterminated string starting at; json_error_line_16349:Expecting value; json_error_line_16350:Expecting value; json_error_line_16351:Expecting value; json_error_line_16352:Expecting value; json_error_line_16353:Expecting value; json_error_line_16354:Expecting value; json_error_line_16355:Expecting value; json_error_line_16356:Expecting value; json_error_line_16357:Expecting value; json_error_line_16358:Expecting value; json_error_line_16361:Unterminated string starting at; json_error_line_16362:Expecting value; json_error_line_16363:Expecting value; json_error_line_16382:Unterminated string starting at; json_error_line_16383:Expecting value; json_error_line_16384:Expecting value; json_error_line_16423:Unterminated string starting at; json_error_line_16424:Expecting value; json_error_line_16425:Expecting value; json_error_line_16442:Unterminated string starting at; json_error_line_16443:Expecting value; json_error_line_16444:Expecting value; json_error_line_16445:Expecting value; json_error_line_16446:Expecting value; json_error_line_16460:Unterminated string starting at; json_error_line_16461:Expecting value; json_error_line_16462:Expecting value; json_error_line_16463:Expecting value; json_error_line_16464:Expecting value; json_error_line_16484:Unterminated string starting at; json_error_line_16485:Expecting value; json_error_line_16486:Expecting value; json_error_line_16500:Unterminated string starting at; json_error_line_16501:Expecting value; json_error_line_16502:Expecting value; json_error_line_16549:Unterminated string starting at; json_error_line_16550:Expecting value; json_error_line_16551:Expecting value; json_error_line_16576:Unterminated string starting at; json_error_line_16577:Expecting value; json_error_line_16578:Expecting value; json_error_line_16579:Expecting value; json_error_line_16580:Expecting value; json_error_line_16581:Expecting value; json_error_line_16582:Expecting value; json_error_line_16583:Expecting value; json_error_line_16584:Expecting value; json_error_line_16585:Expecting value; json_error_line_16586:Expecting value; json_error_line_16587:Expecting value; json_error_line_16588:Expecting value; json_error_line_16589:Expecting value; json_error_line_16590:Expecting value; json_error_line_16591:Expecting value; json_error_line_16592:Expecting value; json_error_line_16593:Expecting value; json_error_line_16594:Expecting value; json_error_line_16595:Expecting value; json_error_line_16596:Expecting value; json_error_line_16597:Expecting value; json_error_line_16598:Expecting value; json_error_line_16599:Expecting value; json_error_line_16600:Expecting value; json_error_line_16601:Expecting value; json_error_line_16602:Expecting value; json_error_line_16603:Expecting value; json_error_line_16604:Expecting value; json_error_line_16671:Unterminated string starting at; json_error_line_16672:Expecting value; json_error_line_16673:Expecting value; json_error_line_16674:Expecting value; json_error_line_16675:Expecting value; json_error_line_16676:Expecting value; json_error_line_16677:Expecting value; json_error_line_16678:Expecting value; json_error_line_16679:Expecting value; json_error_line_16693:Unterminated string starting at; json_error_line_16694:Expecting value; json_error_line_16695:Expecting value; json_error_line_16698:Unterminated string starting at; json_error_line_16700:Expecting value; json_error_line_16702:Expecting value; json_error_line_16729:Unterminated string starting at; json_error_line_16730:Expecting value; json_error_line_16731:Expecting value; json_error_line_16732:Expecting value; json_error_line_16733:Expecting value; json_error_line_16762:Unterminated string starting at; json_error_line_16763:Expecting value; json_error_line_16764:Expecting value; json_error_line_16791:Unterminated string starting at; json_error_line_16792:Expecting value; json_error_line_16793:Expecting value; json_error_line_16928:Unterminated string starting at; json_error_line_16929:Expecting value; json_error_line_16930:Expecting value; json_error_line_17181:Unterminated string starting at; json_error_line_17182:Expecting value; json_error_line_17183:Expecting value; json_error_line_17213:Unterminated string starting at; json_error_line_17214:Expecting value; json_error_line_17215:Expecting value; json_error_line_18123:Unterminated string starting at; json_error_line_18124:Expecting value; json_error_line_18125:Expecting value; json_error_line_19188:Unterminated string starting at; json_error_line_19189:Expecting value; json_error_line_19190:Expecting value; json_error_line_19205:Unterminated string starting at; json_error_line_19206:Expecting value; json_error_line_19207:Expecting value; json_error_line_19228:Unterminated string starting at; json_error_line_19229:Expecting value; json_error_line_19230:Expecting value; json_error_line_19288:Unterminated string starting at; json_error_line_19289:Expecting value; json_error_line_19290:Expecting value; json_error_line_19301:Unterminated string starting at; json_error_line_19302:Expecting value; json_error_line_19303:Expecting value; json_error_line_19304:Expecting value; json_error_line_19305:Expecting value; json_error_line_19310:Unterminated string starting at; json_error_line_19311:Expecting value; json_error_line_19312:Expecting value; json_error_line_19331:Unterminated string starting at; json_error_line_19332:Expecting value; json_error_line_19333:Expecting value; json_error_line_19400:Unterminated string starting at; json_error_line_19401:Expecting value; json_error_line_19402:Expecting value; json_error_line_19425:Unterminated string starting at; json_error_line_19426:Expecting value; json_error_line_19427:Expecting value; json_error_line_19458:Unterminated string starting at; json_error_line_19459:Expecting value; json_error_line_19460:Expecting value; json_error_line_19461:Expecting value; json_error_line_19462:Expecting value; json_error_line_19480:Unterminated string starting at; json_error_line_19481:Expecting value; json_error_line_19482:Expecting value; json_error_line_19486:Unterminated string starting at; json_error_line_19487:Expecting value; json_error_line_19488:Expecting value; json_error_line_19490:Unterminated string starting at; json_error_line_19491:Expecting value; json_error_line_19492:Expecting value; json_error_line_19493:Expecting value; json_error_line_19494:Expecting value; json_error_line_19528:Unterminated string starting at; json_error_line_19529:Expecting value; json_error_line_19530:Expecting value; json_error_line_19539:Unterminated string starting at; json_error_line_19540:Expecting value; json_error_line_19541:Expecting value; json_error_line_19542:Expecting value; json_error_line_19543:Expecting value; json_error_line_19569:Unterminated string starting at; json_error_line_19570:Expecting value; json_error_line_19571:Expecting value; json_error_line_19572:Expecting value; json_error_line_19573:Expecting value; json_error_line_19584:Unterminated string starting at; json_error_line_19585:Expecting value; json_error_line_19586:Expecting value; json_error_line_19622:Unterminated string starting at; json_error_line_19623:Expecting value; json_error_line_19624:Expecting value; json_error_line_19645:Unterminated string starting at; json_error_line_19646:Expecting value; json_error_line_19647:Expecting value; json_error_line_19664:Unterminated string starting at; json_error_line_19665:Expecting value; json_error_line_19666:Expecting value; json_error_line_19667:Expecting value; json_error_line_19668:Expecting value; json_error_line_19669:Expecting value; json_error_line_19670:Expecting value; json_error_line_19703:Unterminated string starting at; json_error_line_19704:Expecting value; json_error_line_19705:Expecting value; json_error_line_19730:Unterminated string starting at; json_error_line_19731:Expecting value; json_error_line_19732:Expecting value; json_error_line_19753:Unterminated string starting at; json_error_line_19754:Expecting value; json_error_line_19755:Expecting value; json_error_line_19759:Unterminated string starting at; json_error_line_19760:Expecting value; json_error_line_19761:Expecting value; json_error_line_19777:Unterminated string starting at; json_error_line_19778:Expecting value; json_error_line_19779:Expecting value; json_error_line_19780:Expecting value; json_error_line_19781:Expecting value; json_error_line_19813:Unterminated string starting at; json_error_line_19814:Expecting value; json_error_line_19815:Expecting value; json_error_line_19826:Unterminated string starting at; json_error_line_19827:Expecting value; json_error_line_19828:Expecting value; json_error_line_19834:Unterminated string starting at; json_error_line_19835:Expecting value; json_error_line_19836:Expecting value; json_error_line_19951:Unterminated string starting at; json_error_line_19952:Expecting value; json_error_line_19953:Expecting value; json_error_line_19985:Unterminated string starting at; json_error_line_19986:Expecting value; json_error_line_19987:Expecting value; json_error_line_20000:Unterminated string starting at; json_error_line_20001:Expecting value; json_error_line_20002:Expecting value; json_error_line_20027:Unterminated string starting at; json_error_line_20028:Expecting value; json_error_line_20029:Expecting value; json_error_line_20030:Expecting value; json_error_line_20031:Expecting value; json_error_line_20044:Unterminated string starting at; json_error_line_20045:Expecting value; json_error_line_20046:Expecting value; json_error_line_20080:Unterminated string starting at; json_error_line_20081:Expecting value; json_error_line_20082:Expecting value; json_error_line_20109:Unterminated string starting at; json_error_line_20110:Expecting value; json_error_line_20111:Expecting value; json_error_line_20112:Expecting value; json_error_line_20113:Expecting value; json_error_line_20129:Unterminated string starting at; json_error_line_20130:Expecting value; json_error_line_20131:Expecting value; json_error_line_20132:Expecting value; json_error_line_20133:Expecting value; json_error_line_20257:Unterminated string starting at; json_error_line_20258:Expecting value; json_error_line_20259:Expecting value; json_error_line_20277:Unterminated string starting at; json_error_line_20278:Expecting value; json_error_line_20279:Expecting value; json_error_line_20282:Unterminated string starting at; json_error_line_20283:Expecting value; json_error_line_20284:Expecting value; json_error_line_20302:Unterminated string starting at; json_error_line_20303:Expecting value; json_error_line_20304:Expecting value; json_error_line_20322:Unterminated string starting at; json_error_line_20323:Expecting value; json_error_line_20324:Expecting value; json_error_line_20367:Unterminated string starting at; json_error_line_20368:Expecting value; json_error_line_20369:Expecting value; json_error_line_20437:Unterminated string starting at; json_error_line_20438:Expecting value; json_error_line_20439:Expecting value; json_error_line_20699:Unterminated string starting at; json_error_line_20700:Expecting value; json_error_line_20701:Expecting value; json_error_line_20783:Unterminated string starting at; json_error_line_20784:Expecting value; json_error_line_20785:Expecting value; json_error_line_20992:Unterminated string starting at; json_error_line_20993:Expecting value; json_error_line_20994:Expecting value; json_error_line_21024:Unterminated string starting at; json_error_line_21025:Expecting value; json_error_line_21026:Expecting value; json_error_line_21027:Expecting value; json_error_line_21028:Expecting value; json_error_line_21029:Expecting value; json_error_line_21030:Expecting value; json_error_line_21406:Unterminated string starting at; json_error_line_21407:Expecting value; json_error_line_21408:Expecting value; json_error_line_21593:Unterminated string starting at; json_error_line_21594:Expecting value; json_error_line_21595:Expecting value; json_error_line_21596:Expecting value; json_error_line_21597:Expecting value; json_error_line_21598:Expecting value; json_error_line_21599:Expecting value; json_error_line_21743:Unterminated string starting at; json_error_line_21744:Expecting value; json_error_line_21745:Expecting value; json_error_line_21791:Unterminated string starting at; json_error_line_21792:Expecting value; json_error_line_21793:Expecting value; json_error_line_22076:Unterminated string starting at; json_error_line_22077:Expecting value; json_error_line_22078:Expecting value; json_error_line_22099:Unterminated string starting at; json_error_line_22100:Expecting value; json_error_line_22101:Expecting value`

### `datasets/processed/normalized/persuade2.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/raw_essays.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/eval__heldout_benchmark.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `18`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `18`
  - `rubric`: `0`
  - `score`: `18`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/eval__heldout_benchmark.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `18`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `18`
  - `rubric`: `0`
  - `score`: `18`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12413`
  - `rubric`: `12413`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__dataset_dict.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__test__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__test__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__train__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__train__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__validation__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict__validation__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict_hf.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12960`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12960`
  - `rubric`: `12960`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__dataset_dict_hf_hf.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12960`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12960`
  - `rubric`: `12960`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__merged_all.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12413`
  - `rubric`: `12413`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__merged_all.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12960`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12960`
  - `rubric`: `12960`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_deduped.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12413`
  - `rubric`: `12413`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_filtered.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `149598`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `149598`
  - `rubric`: `149598`
  - `score`: `23511`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_filtered.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12959`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12959`
  - `rubric`: `12959`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_removed.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `44591`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `44591`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `44591`
  - `response`: `44591`
  - `rubric`: `44591`
  - `score`: `44591`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_removed.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_scored.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `194189`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `37306`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `17031`
  - `response`: `194189`
  - `rubric`: `194071`
  - `score`: `46953`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/final__quality_scored.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12960`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12960`
  - `rubric`: `12960`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/hf__build_summary.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/hf__dataset_dict__dataset_dict.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/hf__dataset_dict__train__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/hf__dataset_dict__train__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/hf__dataset_dict_hf.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12964`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12964`
  - `rubric`: `12964`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/hf__dataset_dict_hf_hf.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12964`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12964`
  - `rubric`: `12964`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `50`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `50`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `50`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `50`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `prompt, response, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `0`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `prompt, response, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `0`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T183049Z__manifest.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `50`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `50`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `50`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `50`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `prompt, response, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `0`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `50`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `prompt, response, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `50`
  - `response`: `50`
  - `rubric`: `0`
  - `score`: `50`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__golden__golden-20260708T202613Z__manifest.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__all_datasets.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `22326`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1178`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1178`
  - `response`: `22326`
  - `rubric`: `22326`
  - `score`: `9540`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__all_datasets.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `22326`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1178`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1178`
  - `response`: `22326`
  - `rubric`: `22326`
  - `score`: `9540`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__asap2.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__asap2.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__asap_aes.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `22326`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1178`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1178`
  - `response`: `22326`
  - `rubric`: `22326`
  - `score`: `9540`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__asap_aes.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `22326`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1178`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1178`
  - `response`: `22326`
  - `rubric`: `22326`
  - `score`: `9540`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__persuade2.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__persuade2.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__normalized__summary.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__raw_essays.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/processed__raw_essays.jsonl.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `0`
- Schema change: `+0/-11 vs processed_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/raw__asap_aes__.cache__huggingface__trees__a46733395585b56c3bbe88f1957360a632ac3e9e.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/raw__asap_aes__test_set.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `4404`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Missing values (per column):
  - `id`: `206`
  - `input`: `206`
  - `license`: `206`
  - `metadata`: `206`
  - `prompt`: `206`
  - `response`: `4404`
  - `rubric`: `4404`
  - `score`: `4404`
  - `source`: `206`
  - `split`: `206`
  - `task`: `206`
- Notes: `encoding=utf-8-sig; json_error_line_33:Unterminated string starting at; json_error_line_34:Expecting value; json_error_line_35:Expecting value; json_error_line_373:Unterminated string starting at; json_error_line_374:Expecting value; json_error_line_375:Expecting value; json_error_line_467:Unterminated string starting at; json_error_line_468:Expecting value; json_error_line_469:Expecting value; json_error_line_483:Unterminated string starting at; json_error_line_484:Expecting value; json_error_line_485:Expecting value; json_error_line_1282:Unterminated string starting at; json_error_line_1283:Expecting value; json_error_line_1284:Expecting value; json_error_line_1297:Unterminated string starting at; json_error_line_1298:Expecting value; json_error_line_1299:Expecting value; json_error_line_1300:Expecting value; json_error_line_1301:Expecting value; json_error_line_1307:Unterminated string starting at; json_error_line_1308:Expecting value; json_error_line_1309:Expecting value; json_error_line_1310:Expecting value; json_error_line_1311:Expecting value; json_error_line_1316:Unterminated string starting at; json_error_line_1317:Expecting value; json_error_line_1318:Expecting value; json_error_line_1321:Unterminated string starting at; json_error_line_1322:Expecting value; json_error_line_1323:Expecting value; json_error_line_1409:Unterminated string starting at; json_error_line_1410:Expecting value; json_error_line_1411:Expecting value; json_error_line_1456:Unterminated string starting at; json_error_line_1457:Expecting value; json_error_line_1458:Expecting value; json_error_line_1489:Unterminated string starting at; json_error_line_1490:Expecting value; json_error_line_1491:Expecting value; json_error_line_1553:Unterminated string starting at; json_error_line_1554:Expecting value; json_error_line_1555:Expecting value; json_error_line_1556:Expecting value; json_error_line_1557:Expecting value; json_error_line_1587:Unterminated string starting at; json_error_line_1588:Expecting value; json_error_line_1589:Expecting value; json_error_line_1601:Unterminated string starting at; json_error_line_1602:Expecting value; json_error_line_1603:Expecting value; json_error_line_1604:Expecting value; json_error_line_1605:Expecting value; json_error_line_1613:Unterminated string starting at; json_error_line_1614:Expecting value; json_error_line_1615:Expecting value; json_error_line_1618:Unterminated string starting at; json_error_line_1619:Expecting value; json_error_line_1620:Expecting value; json_error_line_1626:Unterminated string starting at; json_error_line_1627:Expecting value; json_error_line_1628:Expecting value; json_error_line_1629:Expecting value; json_error_line_1630:Expecting value; json_error_line_1690:Unterminated string starting at; json_error_line_1691:Expecting value; json_error_line_1692:Expecting value; json_error_line_1693:Expecting value; json_error_line_1694:Expecting value; json_error_line_1708:Unterminated string starting at; json_error_line_1709:Expecting value; json_error_line_1710:Expecting value; json_error_line_1711:Expecting value; json_error_line_1712:Expecting value; json_error_line_1713:Expecting value; json_error_line_1714:Expecting value; json_error_line_1715:Expecting value; json_error_line_1716:Expecting value; json_error_line_1792:Unterminated string starting at; json_error_line_1793:Expecting value; json_error_line_1794:Expecting value; json_error_line_1813:Unterminated string starting at; json_error_line_1814:Expecting value; json_error_line_1815:Expecting value; json_error_line_1845:Unterminated string starting at; json_error_line_1846:Expecting value; json_error_line_1847:Expecting value; json_error_line_1854:Unterminated string starting at; json_error_line_1855:Expecting value; json_error_line_1856:Expecting value; json_error_line_1857:Expecting value; json_error_line_1858:Expecting value; json_error_line_1895:Unterminated string starting at; json_error_line_1896:Expecting value; json_error_line_1897:Expecting value; json_error_line_1898:Expecting value; json_error_line_1899:Expecting value; json_error_line_1914:Unterminated string starting at; json_error_line_1915:Expecting value; json_error_line_1916:Expecting value; json_error_line_1969:Unterminated string starting at; json_error_line_1971:Expecting value; json_error_line_1973:Expecting value; json_error_line_1987:Unterminated string starting at; json_error_line_1988:Expecting value; json_error_line_1989:Expecting value; json_error_line_2016:Unterminated string starting at; json_error_line_2017:Expecting value; json_error_line_2018:Expecting value; json_error_line_2133:Unterminated string starting at; json_error_line_2134:Expecting value; json_error_line_2135:Expecting value; json_error_line_2172:Unterminated string starting at; json_error_line_2173:Expecting value; json_error_line_2174:Expecting value; json_error_line_2176:Expecting value; json_error_line_2177:Expecting value; json_error_line_2178:Expecting value; json_error_line_2180:Expecting value; json_error_line_2197:Unterminated string starting at; json_error_line_2198:Expecting value; json_error_line_2199:Expecting value; json_error_line_2207:Unterminated string starting at; json_error_line_2208:Expecting value; json_error_line_2209:Expecting value; json_error_line_2224:Unterminated string starting at; json_error_line_2225:Expecting value; json_error_line_2226:Expecting value; json_error_line_2227:Unterminated string starting at; json_error_line_2228:Expecting value; json_error_line_2229:Expecting value; json_error_line_2230:Expecting value; json_error_line_2231:Expecting value; json_error_line_2257:Unterminated string starting at; json_error_line_2258:Expecting value; json_error_line_2259:Expecting value; json_error_line_2260:Expecting value; json_error_line_2261:Expecting value; json_error_line_2282:Unterminated string starting at; json_error_line_2283:Expecting value; json_error_line_2284:Expecting value; json_error_line_2360:Unterminated string starting at; json_error_line_2361:Expecting value; json_error_line_2362:Expecting value; json_error_line_2401:Unterminated string starting at; json_error_line_2402:Expecting value; json_error_line_2403:Expecting value; json_error_line_2404:Expecting value; json_error_line_2405:Expecting value; json_error_line_2423:Unterminated string starting at; json_error_line_2424:Expecting value; json_error_line_2425:Expecting value; json_error_line_2426:Expecting value; json_error_line_2427:Expecting value; json_error_line_2544:Unterminated string starting at; json_error_line_2545:Expecting value; json_error_line_2546:Expecting value; json_error_line_3006:Unterminated string starting at; json_error_line_3007:Expecting value; json_error_line_3008:Expecting value; json_error_line_3630:Unterminated string starting at; json_error_line_3631:Expecting value; json_error_line_3632:Expecting value; json_error_line_3779:Unterminated string starting at; json_error_line_3780:Expecting value; json_error_line_3781:Expecting value; json_error_line_3789:Unterminated string starting at; json_error_line_3791:Expecting value; json_error_line_3793:Expecting value; json_error_line_3850:Unterminated string starting at; json_error_line_3851:Expecting value; json_error_line_3852:Expecting value; json_error_line_3866:Unterminated string starting at; json_error_line_3867:Expecting value; json_error_line_3868:Expecting value; json_error_line_3869:Unterminated string starting at; json_error_line_3870:Expecting value; json_error_line_3871:Expecting value; json_error_line_3878:Unterminated string starting at; json_error_line_3879:Expecting value; json_error_line_3880:Expecting value; json_error_line_3911:Unterminated string starting at; json_error_line_3912:Expecting value; json_error_line_3913:Expecting value; json_error_line_3957:Unterminated string starting at; json_error_line_3958:Expecting value; json_error_line_3959:Expecting value; json_error_line_4004:Unterminated string starting at; json_error_line_4005:Expecting value; json_error_line_4006:Expecting value; json_error_line_4007:Expecting value; json_error_line_4008:Expecting value; json_error_line_4009:Expecting value; json_error_line_4010:Expecting value; json_error_line_4014:Unterminated string starting at; json_error_line_4015:Expecting value; json_error_line_4016:Expecting value; json_error_line_4029:Unterminated string starting at; json_error_line_4031:Expecting value; json_error_line_4033:Expecting value; json_error_line_4140:Unterminated string starting at; json_error_line_4141:Expecting value; json_error_line_4142:Expecting value; json_error_line_4146:Unterminated string starting at; json_error_line_4147:Expecting value; json_error_line_4148:Expecting value`

### `datasets/processed/unified/raw__asap_aes__training_set_rel3.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `13566`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Missing values (per column):
  - `id`: `780`
  - `input`: `780`
  - `license`: `780`
  - `metadata`: `780`
  - `prompt`: `780`
  - `response`: `13566`
  - `rubric`: `13566`
  - `score`: `780`
  - `source`: `780`
  - `split`: `780`
  - `task`: `780`
- Notes: `encoding=utf-8-sig; json_error_line_225:Unterminated string starting at; json_error_line_226:Expecting value; json_error_line_227:Expecting value; json_error_line_619:Unterminated string starting at; json_error_line_620:Expecting value; json_error_line_621:Expecting value; json_error_line_1658:Unterminated string starting at; json_error_line_1659:Expecting value; json_error_line_1660:Expecting value; json_error_line_1688:Unterminated string starting at; json_error_line_1689:Expecting value; json_error_line_1690:Expecting value; json_error_line_3655:Unterminated string starting at; json_error_line_3656:Expecting value; json_error_line_3657:Expecting value; json_error_line_3666:Unterminated string starting at; json_error_line_3667:Expecting value; json_error_line_3668:Expecting value; json_error_line_3685:Unterminated string starting at; json_error_line_3686:Expecting value; json_error_line_3687:Expecting value; json_error_line_3708:Unterminated string starting at; json_error_line_3709:Expecting value; json_error_line_3710:Expecting value; json_error_line_3717:Unterminated string starting at; json_error_line_3718:Expecting value; json_error_line_3719:Expecting value; json_error_line_3734:Unterminated string starting at; json_error_line_3735:Expecting value; json_error_line_3736:Expecting value; json_error_line_3741:Unterminated string starting at; json_error_line_3742:Expecting value; json_error_line_3743:Expecting value; json_error_line_3772:Unterminated string starting at; json_error_line_3773:Expecting value; json_error_line_3774:Expecting value; json_error_line_3775:Expecting value; json_error_line_3776:Expecting value; json_error_line_3777:Expecting value; json_error_line_3778:Expecting value; json_error_line_3784:Unterminated string starting at; json_error_line_3785:Expecting value; json_error_line_3786:Expecting value; json_error_line_3807:Unterminated string starting at; json_error_line_3808:Expecting value; json_error_line_3809:Expecting value; json_error_line_3832:Unterminated string starting at; json_error_line_3833:Expecting value; json_error_line_3834:Expecting value; json_error_line_3867:Unterminated string starting at; json_error_line_3868:Expecting value; json_error_line_3869:Expecting value; json_error_line_3873:Unterminated string starting at; json_error_line_3874:Expecting value; json_error_line_3875:Expecting value; json_error_line_3876:Expecting value; json_error_line_3877:Expecting value; json_error_line_3878:Expecting value; json_error_line_3879:Expecting value; json_error_line_3887:Unterminated string starting at; json_error_line_3888:Expecting value; json_error_line_3889:Expecting value; json_error_line_3890:Expecting value; json_error_line_3891:Expecting value; json_error_line_3892:Expecting value; json_error_line_3893:Expecting value; json_error_line_3924:Unterminated string starting at; json_error_line_3925:Expecting value; json_error_line_3926:Expecting value; json_error_line_3933:Unterminated string starting at; json_error_line_3934:Expecting value; json_error_line_3935:Expecting value; json_error_line_3943:Unterminated string starting at; json_error_line_3944:Expecting value; json_error_line_3945:Expecting value; json_error_line_4011:Unterminated string starting at; json_error_line_4012:Expecting value; json_error_line_4013:Expecting value; json_error_line_4079:Unterminated string starting at; json_error_line_4080:Expecting value; json_error_line_4081:Expecting value; json_error_line_4082:Expecting value; json_error_line_4083:Expecting value; json_error_line_4084:Expecting value; json_error_line_4085:Expecting value; json_error_line_4101:Unterminated string starting at; json_error_line_4102:Expecting value; json_error_line_4103:Expecting value; json_error_line_4112:Unterminated string starting at; json_error_line_4113:Expecting value; json_error_line_4114:Expecting value; json_error_line_4115:Expecting value; json_error_line_4116:Expecting value; json_error_line_4117:Unterminated string starting at; json_error_line_4118:Expecting value; json_error_line_4119:Expecting value; json_error_line_4120:Expecting value; json_error_line_4121:Expecting value; json_error_line_4140:Unterminated string starting at; json_error_line_4141:Expecting value; json_error_line_4142:Expecting value; json_error_line_4143:Expecting value; json_error_line_4144:Expecting value; json_error_line_4145:Expecting value; json_error_line_4146:Expecting value; json_error_line_4147:Expecting value; json_error_line_4148:Expecting value; json_error_line_4170:Unterminated string starting at; json_error_line_4171:Expecting value; json_error_line_4172:Expecting value; json_error_line_4173:Expecting value; json_error_line_4174:Expecting value; json_error_line_4222:Unterminated string starting at; json_error_line_4223:Expecting value; json_error_line_4224:Expecting value; json_error_line_4232:Unterminated string starting at; json_error_line_4233:Expecting value; json_error_line_4234:Expecting value; json_error_line_4235:Expecting value; json_error_line_4236:Expecting value; json_error_line_4237:Expecting value; json_error_line_4238:Expecting value; json_error_line_4243:Unterminated string starting at; json_error_line_4244:Expecting value; json_error_line_4245:Expecting value; json_error_line_4265:Unterminated string starting at; json_error_line_4266:Expecting value; json_error_line_4267:Expecting value; json_error_line_4268:Expecting value; json_error_line_4269:Expecting value; json_error_line_4289:Unterminated string starting at; json_error_line_4290:Expecting value; json_error_line_4291:Expecting value; json_error_line_4292:Expecting value; json_error_line_4293:Expecting value; json_error_line_4297:Unterminated string starting at; json_error_line_4298:Expecting value; json_error_line_4299:Expecting value; json_error_line_4386:Unterminated string starting at; json_error_line_4387:Expecting value; json_error_line_4388:Expecting value; json_error_line_4454:Unterminated string starting at; json_error_line_4455:Expecting value; json_error_line_4456:Expecting value; json_error_line_4467:Unterminated string starting at; json_error_line_4468:Expecting value; json_error_line_4469:Expecting value; json_error_line_4470:Unterminated string starting at; json_error_line_4471:Expecting value; json_error_line_4472:Expecting value; json_error_line_4473:Expecting value; json_error_line_4474:Expecting value; json_error_line_4498:Unterminated string starting at; json_error_line_4499:Expecting value; json_error_line_4500:Expecting value; json_error_line_4522:Unterminated string starting at; json_error_line_4523:Expecting value; json_error_line_4524:Expecting value; json_error_line_4532:Unterminated string starting at; json_error_line_4533:Expecting value; json_error_line_4534:Expecting value; json_error_line_4549:Unterminated string starting at; json_error_line_4550:Expecting value; json_error_line_4551:Expecting value; json_error_line_4594:Unterminated string starting at; json_error_line_4595:Expecting value; json_error_line_4596:Expecting value; json_error_line_4597:Expecting value; json_error_line_4598:Expecting value; json_error_line_4599:Expecting value; json_error_line_4600:Expecting value; json_error_line_4641:Unterminated string starting at; json_error_line_4642:Expecting value; json_error_line_4643:Expecting value; json_error_line_4663:Unterminated string starting at; json_error_line_4664:Expecting value; json_error_line_4665:Expecting value; json_error_line_4721:Unterminated string starting at; json_error_line_4722:Expecting value; json_error_line_4723:Expecting value; json_error_line_4728:Unterminated string starting at; json_error_line_4729:Expecting value; json_error_line_4730:Expecting value; json_error_line_4731:Expecting value; json_error_line_4732:Expecting value; json_error_line_4840:Unterminated string starting at; json_error_line_4841:Expecting value; json_error_line_4842:Expecting value; json_error_line_4843:Expecting value; json_error_line_4844:Expecting value; json_error_line_4845:Expecting value; json_error_line_4846:Expecting value; json_error_line_4857:Unterminated string starting at; json_error_line_4858:Expecting value; json_error_line_4859:Expecting value; json_error_line_4860:Expecting value; json_error_line_4861:Expecting value; json_error_line_4862:Expecting value; json_error_line_4863:Expecting value; json_error_line_4939:Unterminated string starting at; json_error_line_4940:Expecting value; json_error_line_4941:Expecting value; json_error_line_4942:Expecting value; json_error_line_4943:Expecting value; json_error_line_4973:Unterminated string starting at; json_error_line_4974:Expecting value; json_error_line_4975:Expecting value; json_error_line_5023:Unterminated string starting at; json_error_line_5024:Expecting value; json_error_line_5025:Expecting value; json_error_line_5026:Expecting value; json_error_line_5027:Expecting value; json_error_line_5057:Unterminated string starting at; json_error_line_5058:Expecting value; json_error_line_5059:Expecting value; json_error_line_5078:Unterminated string starting at; json_error_line_5079:Expecting value; json_error_line_5080:Expecting value; json_error_line_5087:Unterminated string starting at; json_error_line_5088:Expecting value; json_error_line_5089:Expecting value; json_error_line_5164:Unterminated string starting at; json_error_line_5165:Expecting value; json_error_line_5166:Expecting value; json_error_line_5185:Unterminated string starting at; json_error_line_5186:Expecting value; json_error_line_5187:Expecting value; json_error_line_5201:Unterminated string starting at; json_error_line_5202:Expecting value; json_error_line_5203:Expecting value; json_error_line_5204:Expecting value; json_error_line_5205:Expecting value; json_error_line_5251:Unterminated string starting at; json_error_line_5252:Expecting value; json_error_line_5253:Expecting value; json_error_line_5287:Unterminated string starting at; json_error_line_5288:Expecting value; json_error_line_5289:Expecting value; json_error_line_5290:Expecting value; json_error_line_5291:Expecting value; json_error_line_5335:Unterminated string starting at; json_error_line_5336:Expecting value; json_error_line_5337:Expecting value; json_error_line_5374:Unterminated string starting at; json_error_line_5375:Expecting value; json_error_line_5376:Expecting value; json_error_line_5377:Unterminated string starting at; json_error_line_5378:Expecting value; json_error_line_5379:Expecting value; json_error_line_5396:Unterminated string starting at; json_error_line_5397:Expecting value; json_error_line_5398:Expecting value; json_error_line_5399:Expecting value; json_error_line_5400:Expecting value; json_error_line_5410:Unterminated string starting at; json_error_line_5411:Expecting value; json_error_line_5412:Expecting value; json_error_line_5422:Unterminated string starting at; json_error_line_5423:Extra data; json_error_line_5448:Unterminated string starting at; json_error_line_5449:Expecting value; json_error_line_5450:Expecting value; json_error_line_5451:Expecting value; json_error_line_5452:Expecting value; json_error_line_5453:Expecting value; json_error_line_5454:Expecting value; json_error_line_5469:Unterminated string starting at; json_error_line_5470:Expecting value; json_error_line_5471:Expecting value; json_error_line_5498:Unterminated string starting at; json_error_line_5499:Expecting value; json_error_line_5500:Expecting value; json_error_line_5507:Unterminated string starting at; json_error_line_5508:Expecting value; json_error_line_5509:Expecting value; json_error_line_5510:Expecting value; json_error_line_5511:Expecting value; json_error_line_5512:Expecting value; json_error_line_5513:Expecting value; json_error_line_5514:Expecting value; json_error_line_5515:Expecting value; json_error_line_5519:Unterminated string starting at; json_error_line_5520:Expecting value; json_error_line_5521:Expecting value; json_error_line_5548:Unterminated string starting at; json_error_line_5549:Expecting value; json_error_line_5550:Expecting value; json_error_line_5566:Unterminated string starting at; json_error_line_5567:Expecting value; json_error_line_5568:Expecting value; json_error_line_5578:Unterminated string starting at; json_error_line_5579:Expecting value; json_error_line_5580:Expecting value; json_error_line_5607:Unterminated string starting at; json_error_line_5608:Expecting value; json_error_line_5609:Expecting value; json_error_line_5610:Expecting value; json_error_line_5611:Expecting value; json_error_line_5618:Unterminated string starting at; json_error_line_5619:Expecting value; json_error_line_5620:Expecting value; json_error_line_5621:Expecting value; json_error_line_5622:Expecting value; json_error_line_5639:Unterminated string starting at; json_error_line_5640:Expecting value; json_error_line_5641:Expecting value; json_error_line_5642:Expecting value; json_error_line_5643:Expecting value; json_error_line_5644:Expecting value; json_error_line_5645:Expecting value; json_error_line_5675:Unterminated string starting at; json_error_line_5676:Expecting value; json_error_line_5677:Expecting value; json_error_line_5685:Unterminated string starting at; json_error_line_5686:Expecting value; json_error_line_5687:Expecting value; json_error_line_5691:Unterminated string starting at; json_error_line_5692:Expecting value; json_error_line_5693:Expecting value; json_error_line_5763:Unterminated string starting at; json_error_line_5767:Expecting value; json_error_line_5771:Expecting value; json_error_line_5844:Unterminated string starting at; json_error_line_5845:Expecting value; json_error_line_5846:Expecting value; json_error_line_5910:Unterminated string starting at; json_error_line_5911:Expecting value; json_error_line_5912:Expecting value; json_error_line_5914:Unterminated string starting at; json_error_line_5915:Expecting value; json_error_line_5916:Expecting value; json_error_line_5917:Expecting value; json_error_line_5918:Expecting value; json_error_line_5919:Expecting value; json_error_line_5920:Expecting value; json_error_line_5921:Expecting value; json_error_line_5922:Expecting value; json_error_line_5923:Expecting value; json_error_line_5924:Expecting value; json_error_line_5925:Expecting value; json_error_line_5926:Expecting value; json_error_line_5928:Unterminated string starting at; json_error_line_5929:Expecting value; json_error_line_5930:Expecting value; json_error_line_5965:Unterminated string starting at; json_error_line_5966:Expecting value; json_error_line_5967:Expecting value; json_error_line_6014:Unterminated string starting at; json_error_line_6015:Expecting value; json_error_line_6016:Expecting value; json_error_line_6061:Unterminated string starting at; json_error_line_6062:Expecting value; json_error_line_6063:Expecting value; json_error_line_6064:Expecting value; json_error_line_6065:Expecting value; json_error_line_6125:Unterminated string starting at; json_error_line_6126:Expecting value; json_error_line_6127:Expecting value; json_error_line_6151:Unterminated string starting at; json_error_line_6152:Expecting value; json_error_line_6153:Expecting value; json_error_line_6154:Expecting value; json_error_line_6155:Expecting value; json_error_line_6196:Unterminated string starting at; json_error_line_6197:Expecting value; json_error_line_6198:Expecting value; json_error_line_6199:Expecting value; json_error_line_6200:Expecting value; json_error_line_6204:Unterminated string starting at; json_error_line_6205:Expecting value; json_error_line_6206:Expecting value; json_error_line_6243:Unterminated string starting at; json_error_line_6244:Expecting value; json_error_line_6245:Expecting value; json_error_line_6247:Unterminated string starting at; json_error_line_6248:Expecting value; json_error_line_6249:Expecting value; json_error_line_6268:Unterminated string starting at; json_error_line_6269:Expecting value; json_error_line_6270:Expecting value; json_error_line_6286:Unterminated string starting at; json_error_line_6287:Expecting value; json_error_line_6288:Expecting value; json_error_line_6299:Unterminated string starting at; json_error_line_6300:Expecting value; json_error_line_6301:Expecting value; json_error_line_6338:Unterminated string starting at; json_error_line_6339:Expecting value; json_error_line_6340:Expecting value; json_error_line_6349:Unterminated string starting at; json_error_line_6350:Expecting value; json_error_line_6351:Expecting value; json_error_line_6359:Unterminated string starting at; json_error_line_6360:Expecting value; json_error_line_6361:Expecting value; json_error_line_6370:Unterminated string starting at; json_error_line_6371:Expecting value; json_error_line_6372:Expecting value; json_error_line_6406:Unterminated string starting at; json_error_line_6407:Expecting value; json_error_line_6408:Expecting value; json_error_line_6420:Unterminated string starting at; json_error_line_6421:Expecting value; json_error_line_6422:Expecting value; json_error_line_6425:Unterminated string starting at; json_error_line_6426:Expecting value; json_error_line_6427:Expecting value; json_error_line_6428:Expecting value; json_error_line_6429:Expecting value; json_error_line_6430:Expecting value; json_error_line_6431:Expecting value; json_error_line_6464:Unterminated string starting at; json_error_line_6465:Expecting value; json_error_line_6466:Expecting value; json_error_line_6470:Unterminated string starting at; json_error_line_6471:Expecting value; json_error_line_6472:Expecting value; json_error_line_6488:Unterminated string starting at; json_error_line_6489:Expecting value; json_error_line_6490:Expecting value; json_error_line_6502:Unterminated string starting at; json_error_line_6503:Expecting value; json_error_line_6504:Expecting value; json_error_line_6520:Unterminated string starting at; json_error_line_6521:Expecting value; json_error_line_6522:Expecting value; json_error_line_6525:Unterminated string starting at; json_error_line_6526:Expecting value; json_error_line_6527:Expecting value; json_error_line_6567:Unterminated string starting at; json_error_line_6568:Expecting value; json_error_line_6569:Expecting value; json_error_line_6570:Unterminated string starting at; json_error_line_6571:Expecting value; json_error_line_6572:Expecting value; json_error_line_6573:Expecting value; json_error_line_6574:Expecting value; json_error_line_6595:Unterminated string starting at; json_error_line_6596:Expecting value; json_error_line_6597:Expecting value; json_error_line_6607:Unterminated string starting at; json_error_line_6608:Expecting value; json_error_line_6609:Expecting value; json_error_line_6610:Unterminated string starting at; json_error_line_6611:Expecting value; json_error_line_6612:Expecting value; json_error_line_6613:Expecting value; json_error_line_6614:Expecting value; json_error_line_6615:Expecting value; json_error_line_6616:Expecting value; json_error_line_6620:Unterminated string starting at; json_error_line_6621:Expecting value; json_error_line_6622:Expecting value; json_error_line_6634:Unterminated string starting at; json_error_line_6635:Expecting value; json_error_line_6636:Expecting value; json_error_line_6641:Unterminated string starting at; json_error_line_6642:Expecting value; json_error_line_6643:Expecting value; json_error_line_6651:Unterminated string starting at; json_error_line_6652:Extra data; json_error_line_6791:Unterminated string starting at; json_error_line_6792:Expecting value; json_error_line_6793:Expecting value; json_error_line_6807:Unterminated string starting at; json_error_line_6808:Expecting value; json_error_line_6809:Expecting value; json_error_line_6843:Unterminated string starting at; json_error_line_6844:Expecting value; json_error_line_6845:Expecting value; json_error_line_6915:Unterminated string starting at; json_error_line_6916:Expecting value; json_error_line_6917:Expecting value; json_error_line_6918:Expecting value; json_error_line_6919:Expecting value; json_error_line_6957:Unterminated string starting at; json_error_line_6958:Expecting value; json_error_line_6959:Expecting value; json_error_line_6960:Expecting value; json_error_line_6961:Expecting value; json_error_line_7083:Unterminated string starting at; json_error_line_7084:Expecting value; json_error_line_7085:Expecting value; json_error_line_7125:Unterminated string starting at; json_error_line_7126:Expecting value; json_error_line_7127:Expecting value; json_error_line_7146:Unterminated string starting at; json_error_line_7147:Expecting value; json_error_line_7148:Expecting value; json_error_line_7164:Unterminated string starting at; json_error_line_7165:Expecting value; json_error_line_7166:Expecting value; json_error_line_7260:Unterminated string starting at; json_error_line_7261:Expecting value; json_error_line_7262:Expecting value; json_error_line_7317:Unterminated string starting at; json_error_line_7318:Expecting value; json_error_line_7319:Expecting value; json_error_line_7332:Unterminated string starting at; json_error_line_7333:Expecting value; json_error_line_7334:Expecting value; json_error_line_7339:Unterminated string starting at; json_error_line_7340:Expecting value; json_error_line_7341:Expecting value; json_error_line_7361:Unterminated string starting at; json_error_line_7362:Expecting value; json_error_line_7363:Expecting value; json_error_line_7364:Expecting value; json_error_line_7365:Expecting value; json_error_line_7366:Expecting value; json_error_line_7367:Expecting value; json_error_line_7380:Unterminated string starting at; json_error_line_7381:Expecting value; json_error_line_7382:Expecting value; json_error_line_7415:Unterminated string starting at; json_error_line_7416:Expecting value; json_error_line_7417:Expecting value; json_error_line_7418:Expecting value; json_error_line_7419:Expecting value; json_error_line_7420:Expecting value; json_error_line_7421:Expecting value; json_error_line_7422:Expecting value; json_error_line_7423:Expecting value; json_error_line_7433:Unterminated string starting at; json_error_line_7434:Expecting value; json_error_line_7435:Expecting value; json_error_line_7463:Unterminated string starting at; json_error_line_7464:Expecting value; json_error_line_7465:Expecting value; json_error_line_7529:Unterminated string starting at; json_error_line_7530:Expecting value; json_error_line_7531:Expecting value; json_error_line_7532:Expecting value; json_error_line_7533:Expecting value; json_error_line_7570:Unterminated string starting at; json_error_line_7571:Expecting value; json_error_line_7572:Expecting value; json_error_line_7611:Unterminated string starting at; json_error_line_7612:Expecting value; json_error_line_7613:Expecting value; json_error_line_7614:Expecting value; json_error_line_7615:Expecting value; json_error_line_7787:Unterminated string starting at; json_error_line_7788:Expecting value; json_error_line_7789:Expecting value; json_error_line_7933:Unterminated string starting at; json_error_line_7934:Expecting value; json_error_line_7935:Expecting value; json_error_line_7936:Expecting value; json_error_line_7937:Expecting value; json_error_line_7938:Expecting value; json_error_line_7939:Expecting value; json_error_line_7940:Expecting value; json_error_line_7941:Expecting value; json_error_line_8165:Unterminated string starting at; json_error_line_8166:Expecting value; json_error_line_8167:Expecting value; json_error_line_8539:Unterminated string starting at; json_error_line_8540:Expecting value; json_error_line_8541:Expecting value; json_error_line_8822:Unterminated string starting at; json_error_line_8823:Expecting value; json_error_line_8824:Expecting value; json_error_line_8837:Unterminated string starting at; json_error_line_8838:Expecting value; json_error_line_8839:Expecting value; json_error_line_8840:Expecting value; json_error_line_8841:Expecting value; json_error_line_8842:Expecting value; json_error_line_8843:Expecting value; json_error_line_8844:Expecting value; json_error_line_8845:Expecting value; json_error_line_8846:Expecting value; json_error_line_8847:Expecting value; json_error_line_8848:Expecting value; json_error_line_8849:Expecting value; json_error_line_8850:Expecting value; json_error_line_8851:Expecting value; json_error_line_8852:Expecting value; json_error_line_8853:Expecting value; json_error_line_9030:Unterminated string starting at; json_error_line_9031:Expecting value; json_error_line_9032:Expecting value; json_error_line_9050:Unterminated string starting at; json_error_line_9051:Expecting value; json_error_line_9052:Expecting value; json_error_line_9053:Expecting value; json_error_line_9054:Expecting value; json_error_line_9162:Unterminated string starting at; json_error_line_9163:Expecting value; json_error_line_9164:Expecting value; json_error_line_9165:Expecting value; json_error_line_9166:Expecting value; json_error_line_9167:Expecting value; json_error_line_9168:Expecting value; json_error_line_9169:Expecting value; json_error_line_9170:Expecting value; json_error_line_9171:Expecting value; json_error_line_9172:Expecting value; json_error_line_9335:Unterminated string starting at; json_error_line_9336:Expecting value; json_error_line_9337:Expecting value; json_error_line_9468:Unterminated string starting at; json_error_line_9469:Expecting value; json_error_line_9470:Expecting value; json_error_line_11166:Unterminated string starting at; json_error_line_11167:Expecting value; json_error_line_11168:Expecting value; json_error_line_11169:Expecting value; json_error_line_11170:Expecting value; json_error_line_11172:Unterminated string starting at; json_error_line_11173:Expecting value; json_error_line_11174:Expecting value; json_error_line_11195:Unterminated string starting at; json_error_line_11196:Expecting value; json_error_line_11197:Expecting value; json_error_line_11260:Unterminated string starting at; json_error_line_11261:Expecting value; json_error_line_11262:Expecting value; json_error_line_11281:Unterminated string starting at; json_error_line_11282:Expecting value; json_error_line_11283:Expecting value; json_error_line_11361:Unterminated string starting at; json_error_line_11362:Expecting value; json_error_line_11363:Expecting value; json_error_line_11366:Unterminated string starting at; json_error_line_11367:Expecting value; json_error_line_11368:Expecting value; json_error_line_11371:Unterminated string starting at; json_error_line_11372:Expecting value; json_error_line_11373:Expecting value; json_error_line_11403:Unterminated string starting at; json_error_line_11404:Expecting value; json_error_line_11405:Expecting value; json_error_line_11406:Expecting value; json_error_line_11407:Expecting value; json_error_line_11430:Unterminated string starting at; json_error_line_11431:Expecting value; json_error_line_11432:Expecting value; json_error_line_11465:Unterminated string starting at; json_error_line_11466:Expecting value; json_error_line_11467:Expecting value; json_error_line_11495:Unterminated string starting at; json_error_line_11496:Expecting value; json_error_line_11497:Expecting value; json_error_line_11498:Expecting value; json_error_line_11499:Expecting value; json_error_line_11500:Expecting value; json_error_line_11501:Expecting value; json_error_line_11502:Unterminated string starting at; json_error_line_11503:Expecting value; json_error_line_11504:Expecting value; json_error_line_11505:Expecting value; json_error_line_11506:Expecting value; json_error_line_11514:Unterminated string starting at; json_error_line_11515:Expecting value; json_error_line_11516:Expecting value; json_error_line_11544:Unterminated string starting at; json_error_line_11545:Expecting value; json_error_line_11546:Expecting value; json_error_line_11622:Unterminated string starting at; json_error_line_11625:Expecting value; json_error_line_11628:Expecting value; json_error_line_11661:Unterminated string starting at; json_error_line_11662:Expecting value; json_error_line_11663:Expecting value; json_error_line_11664:Expecting value; json_error_line_11665:Expecting value; json_error_line_11679:Unterminated string starting at; json_error_line_11680:Expecting value; json_error_line_11681:Expecting value; json_error_line_11772:Unterminated string starting at; json_error_line_11773:Expecting value; json_error_line_11774:Expecting value; json_error_line_11913:Unterminated string starting at; json_error_line_11914:Expecting value; json_error_line_11915:Expecting value; json_error_line_11936:Unterminated string starting at; json_error_line_11937:Expecting value; json_error_line_11938:Expecting value; json_error_line_11939:Expecting value; json_error_line_11940:Expecting value; json_error_line_11941:Expecting value; json_error_line_11942:Expecting value; json_error_line_11943:Expecting value; json_error_line_11944:Expecting value; json_error_line_11945:Expecting value; json_error_line_11946:Expecting value; json_error_line_11949:Unterminated string starting at; json_error_line_11950:Expecting value; json_error_line_11951:Expecting value; json_error_line_11970:Unterminated string starting at; json_error_line_11971:Expecting value; json_error_line_11972:Expecting value; json_error_line_12011:Unterminated string starting at; json_error_line_12012:Expecting value; json_error_line_12013:Expecting value; json_error_line_12030:Unterminated string starting at; json_error_line_12031:Expecting value; json_error_line_12032:Expecting value; json_error_line_12033:Expecting value; json_error_line_12034:Expecting value; json_error_line_12048:Unterminated string starting at; json_error_line_12049:Expecting value; json_error_line_12050:Expecting value; json_error_line_12051:Expecting value; json_error_line_12052:Expecting value; json_error_line_12072:Unterminated string starting at; json_error_line_12073:Expecting value; json_error_line_12074:Expecting value; json_error_line_12088:Unterminated string starting at; json_error_line_12089:Expecting value; json_error_line_12090:Expecting value; json_error_line_12137:Unterminated string starting at; json_error_line_12138:Expecting value; json_error_line_12139:Expecting value; json_error_line_12164:Unterminated string starting at; json_error_line_12165:Expecting value; json_error_line_12166:Expecting value; json_error_line_12167:Expecting value; json_error_line_12168:Expecting value; json_error_line_12169:Expecting value; json_error_line_12170:Expecting value; json_error_line_12171:Expecting value; json_error_line_12172:Expecting value; json_error_line_12173:Expecting value; json_error_line_12174:Expecting value; json_error_line_12175:Expecting value; json_error_line_12176:Expecting value; json_error_line_12177:Expecting value; json_error_line_12178:Expecting value; json_error_line_12179:Expecting value; json_error_line_12180:Expecting value; json_error_line_12181:Expecting value; json_error_line_12182:Expecting value; json_error_line_12183:Expecting value; json_error_line_12184:Expecting value; json_error_line_12185:Expecting value; json_error_line_12186:Expecting value; json_error_line_12187:Expecting value; json_error_line_12188:Expecting value; json_error_line_12189:Expecting value; json_error_line_12190:Expecting value; json_error_line_12191:Expecting value; json_error_line_12192:Expecting value; json_error_line_12259:Unterminated string starting at; json_error_line_12260:Expecting value; json_error_line_12261:Expecting value; json_error_line_12262:Expecting value; json_error_line_12263:Expecting value; json_error_line_12264:Expecting value; json_error_line_12265:Expecting value; json_error_line_12266:Expecting value; json_error_line_12267:Expecting value; json_error_line_12281:Unterminated string starting at; json_error_line_12282:Expecting value; json_error_line_12283:Expecting value; json_error_line_12286:Unterminated string starting at; json_error_line_12288:Expecting value; json_error_line_12290:Expecting value; json_error_line_12317:Unterminated string starting at; json_error_line_12318:Expecting value; json_error_line_12319:Expecting value; json_error_line_12320:Expecting value; json_error_line_12321:Expecting value; json_error_line_12350:Unterminated string starting at; json_error_line_12351:Expecting value; json_error_line_12352:Expecting value; json_error_line_12379:Unterminated string starting at; json_error_line_12380:Expecting value; json_error_line_12381:Expecting value; json_error_line_12516:Unterminated string starting at; json_error_line_12517:Expecting value; json_error_line_12518:Expecting value; json_error_line_12769:Unterminated string starting at; json_error_line_12770:Expecting value; json_error_line_12771:Expecting value; json_error_line_12801:Unterminated string starting at; json_error_line_12802:Expecting value; json_error_line_12803:Expecting value`

### `datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `4818`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `4818`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `4818`
  - `response`: `4818`
  - `rubric`: `4818`
  - `score`: `4818`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column_no_header.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `4817`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `4817`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `4817`
  - `response`: `4817`
  - `rubric`: `4817`
  - `score`: `4817`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/raw__asap_aes__valid_sample_submission_2_column.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `4818`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `4818`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `4818`
  - `response`: `4818`
  - `rubric`: `4818`
  - `score`: `4818`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/raw__asap_aes__valid_sample_submission_5_column.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `4818`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (4): `input, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `4818`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `4818`
  - `rubric`: `4818`
  - `score`: `4818`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/raw__asap_aes__valid_set.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `4356`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Missing values (per column):
  - `id`: `192`
  - `input`: `192`
  - `license`: `192`
  - `metadata`: `192`
  - `prompt`: `192`
  - `response`: `4356`
  - `rubric`: `4356`
  - `score`: `4356`
  - `source`: `192`
  - `split`: `192`
  - `task`: `192`
- Notes: `encoding=utf-8-sig; json_error_line_133:Unterminated string starting at; json_error_line_134:Expecting value; json_error_line_135:Expecting value; json_error_line_1198:Unterminated string starting at; json_error_line_1199:Expecting value; json_error_line_1200:Expecting value; json_error_line_1215:Unterminated string starting at; json_error_line_1216:Expecting value; json_error_line_1217:Expecting value; json_error_line_1238:Unterminated string starting at; json_error_line_1239:Expecting value; json_error_line_1240:Expecting value; json_error_line_1298:Unterminated string starting at; json_error_line_1299:Expecting value; json_error_line_1300:Expecting value; json_error_line_1311:Unterminated string starting at; json_error_line_1312:Expecting value; json_error_line_1313:Expecting value; json_error_line_1314:Expecting value; json_error_line_1315:Expecting value; json_error_line_1320:Unterminated string starting at; json_error_line_1321:Expecting value; json_error_line_1322:Expecting value; json_error_line_1341:Unterminated string starting at; json_error_line_1342:Expecting value; json_error_line_1343:Expecting value; json_error_line_1410:Unterminated string starting at; json_error_line_1411:Expecting value; json_error_line_1412:Expecting value; json_error_line_1435:Unterminated string starting at; json_error_line_1436:Expecting value; json_error_line_1437:Expecting value; json_error_line_1468:Unterminated string starting at; json_error_line_1469:Expecting value; json_error_line_1470:Expecting value; json_error_line_1471:Expecting value; json_error_line_1472:Expecting value; json_error_line_1490:Unterminated string starting at; json_error_line_1491:Expecting value; json_error_line_1492:Expecting value; json_error_line_1496:Unterminated string starting at; json_error_line_1497:Expecting value; json_error_line_1498:Expecting value; json_error_line_1500:Unterminated string starting at; json_error_line_1501:Expecting value; json_error_line_1502:Expecting value; json_error_line_1503:Expecting value; json_error_line_1504:Expecting value; json_error_line_1538:Unterminated string starting at; json_error_line_1539:Expecting value; json_error_line_1540:Expecting value; json_error_line_1549:Unterminated string starting at; json_error_line_1550:Expecting value; json_error_line_1551:Expecting value; json_error_line_1552:Expecting value; json_error_line_1553:Expecting value; json_error_line_1579:Unterminated string starting at; json_error_line_1580:Expecting value; json_error_line_1581:Expecting value; json_error_line_1582:Expecting value; json_error_line_1583:Expecting value; json_error_line_1594:Unterminated string starting at; json_error_line_1595:Expecting value; json_error_line_1596:Expecting value; json_error_line_1632:Unterminated string starting at; json_error_line_1633:Expecting value; json_error_line_1634:Expecting value; json_error_line_1655:Unterminated string starting at; json_error_line_1656:Expecting value; json_error_line_1657:Expecting value; json_error_line_1674:Unterminated string starting at; json_error_line_1675:Expecting value; json_error_line_1676:Expecting value; json_error_line_1677:Expecting value; json_error_line_1678:Expecting value; json_error_line_1679:Expecting value; json_error_line_1680:Expecting value; json_error_line_1713:Unterminated string starting at; json_error_line_1714:Expecting value; json_error_line_1715:Expecting value; json_error_line_1740:Unterminated string starting at; json_error_line_1741:Expecting value; json_error_line_1742:Expecting value; json_error_line_1763:Unterminated string starting at; json_error_line_1764:Expecting value; json_error_line_1765:Expecting value; json_error_line_1769:Unterminated string starting at; json_error_line_1770:Expecting value; json_error_line_1771:Expecting value; json_error_line_1787:Unterminated string starting at; json_error_line_1788:Expecting value; json_error_line_1789:Expecting value; json_error_line_1790:Expecting value; json_error_line_1791:Expecting value; json_error_line_1823:Unterminated string starting at; json_error_line_1824:Expecting value; json_error_line_1825:Expecting value; json_error_line_1836:Unterminated string starting at; json_error_line_1837:Expecting value; json_error_line_1838:Expecting value; json_error_line_1844:Unterminated string starting at; json_error_line_1845:Expecting value; json_error_line_1846:Expecting value; json_error_line_1961:Unterminated string starting at; json_error_line_1962:Expecting value; json_error_line_1963:Expecting value; json_error_line_1995:Unterminated string starting at; json_error_line_1996:Expecting value; json_error_line_1997:Expecting value; json_error_line_2010:Unterminated string starting at; json_error_line_2011:Expecting value; json_error_line_2012:Expecting value; json_error_line_2037:Unterminated string starting at; json_error_line_2038:Expecting value; json_error_line_2039:Expecting value; json_error_line_2040:Expecting value; json_error_line_2041:Expecting value; json_error_line_2054:Unterminated string starting at; json_error_line_2055:Expecting value; json_error_line_2056:Expecting value; json_error_line_2090:Unterminated string starting at; json_error_line_2091:Expecting value; json_error_line_2092:Expecting value; json_error_line_2119:Unterminated string starting at; json_error_line_2120:Expecting value; json_error_line_2121:Expecting value; json_error_line_2122:Expecting value; json_error_line_2123:Expecting value; json_error_line_2139:Unterminated string starting at; json_error_line_2140:Expecting value; json_error_line_2141:Expecting value; json_error_line_2142:Expecting value; json_error_line_2143:Expecting value; json_error_line_2267:Unterminated string starting at; json_error_line_2268:Expecting value; json_error_line_2269:Expecting value; json_error_line_2287:Unterminated string starting at; json_error_line_2288:Expecting value; json_error_line_2289:Expecting value; json_error_line_2292:Unterminated string starting at; json_error_line_2293:Expecting value; json_error_line_2294:Expecting value; json_error_line_2312:Unterminated string starting at; json_error_line_2313:Expecting value; json_error_line_2314:Expecting value; json_error_line_2332:Unterminated string starting at; json_error_line_2333:Expecting value; json_error_line_2334:Expecting value; json_error_line_2377:Unterminated string starting at; json_error_line_2378:Expecting value; json_error_line_2379:Expecting value; json_error_line_2447:Unterminated string starting at; json_error_line_2448:Expecting value; json_error_line_2449:Expecting value; json_error_line_2709:Unterminated string starting at; json_error_line_2710:Expecting value; json_error_line_2711:Expecting value; json_error_line_2793:Unterminated string starting at; json_error_line_2794:Expecting value; json_error_line_2795:Expecting value; json_error_line_3002:Unterminated string starting at; json_error_line_3003:Expecting value; json_error_line_3004:Expecting value; json_error_line_3034:Unterminated string starting at; json_error_line_3035:Expecting value; json_error_line_3036:Expecting value; json_error_line_3037:Expecting value; json_error_line_3038:Expecting value; json_error_line_3039:Expecting value; json_error_line_3040:Expecting value; json_error_line_3416:Unterminated string starting at; json_error_line_3417:Expecting value; json_error_line_3418:Expecting value; json_error_line_3603:Unterminated string starting at; json_error_line_3604:Expecting value; json_error_line_3605:Expecting value; json_error_line_3606:Expecting value; json_error_line_3607:Expecting value; json_error_line_3608:Expecting value; json_error_line_3609:Expecting value; json_error_line_3753:Unterminated string starting at; json_error_line_3754:Expecting value; json_error_line_3755:Expecting value; json_error_line_3801:Unterminated string starting at; json_error_line_3802:Expecting value; json_error_line_3803:Expecting value; json_error_line_4086:Unterminated string starting at; json_error_line_4087:Expecting value; json_error_line_4088:Expecting value; json_error_line_4109:Unterminated string starting at; json_error_line_4110:Expecting value; json_error_line_4111:Expecting value`

### `datasets/processed/unified/training__dataset_dict.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training__test__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training__test__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training__train__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training__train__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training__validation__dataset_info.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training__validation__state.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `1`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `1`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `1`
  - `response`: `1`
  - `rubric`: `1`
  - `score`: `1`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training_hf_hf.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (2): `response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `0`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12413`
  - `rubric`: `12413`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/training_provenance.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `12413`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (3): `input, response, rubric`
- Missing values (per column):
  - `id`: `0`
  - `input`: `12413`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `0`
  - `response`: `12413`
  - `rubric`: `12413`
  - `score`: `0`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/processed/unified/unified_all.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `562856`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Missing values (per column):
  - `id`: `1178`
  - `input`: `117237`
  - `license`: `1178`
  - `metadata`: `1178`
  - `prompt`: `79831`
  - `response`: `562856`
  - `rubric`: `562620`
  - `score`: `163186`
  - `source`: `1178`
  - `split`: `1178`
  - `task`: `1178`
- Notes: `encoding=utf-8-sig; json_error_line_496459:Unterminated string starting at; json_error_line_496460:Expecting value; json_error_line_496461:Expecting value; json_error_line_496799:Unterminated string starting at; json_error_line_496800:Expecting value; json_error_line_496801:Expecting value; json_error_line_496893:Unterminated string starting at; json_error_line_496894:Expecting value; json_error_line_496895:Expecting value; json_error_line_496909:Unterminated string starting at; json_error_line_496910:Expecting value; json_error_line_496911:Expecting value; json_error_line_497708:Unterminated string starting at; json_error_line_497709:Expecting value; json_error_line_497710:Expecting value; json_error_line_497723:Unterminated string starting at; json_error_line_497724:Expecting value; json_error_line_497725:Expecting value; json_error_line_497726:Expecting value; json_error_line_497727:Expecting value; json_error_line_497733:Unterminated string starting at; json_error_line_497734:Expecting value; json_error_line_497735:Expecting value; json_error_line_497736:Expecting value; json_error_line_497737:Expecting value; json_error_line_497742:Unterminated string starting at; json_error_line_497743:Expecting value; json_error_line_497744:Expecting value; json_error_line_497747:Unterminated string starting at; json_error_line_497748:Expecting value; json_error_line_497749:Expecting value; json_error_line_497835:Unterminated string starting at; json_error_line_497836:Expecting value; json_error_line_497837:Expecting value; json_error_line_497882:Unterminated string starting at; json_error_line_497883:Expecting value; json_error_line_497884:Expecting value; json_error_line_497915:Unterminated string starting at; json_error_line_497916:Expecting value; json_error_line_497917:Expecting value; json_error_line_497979:Unterminated string starting at; json_error_line_497980:Expecting value; json_error_line_497981:Expecting value; json_error_line_497982:Expecting value; json_error_line_497983:Expecting value; json_error_line_498013:Unterminated string starting at; json_error_line_498014:Expecting value; json_error_line_498015:Expecting value; json_error_line_498027:Unterminated string starting at; json_error_line_498028:Expecting value; json_error_line_498029:Expecting value; json_error_line_498030:Expecting value; json_error_line_498031:Expecting value; json_error_line_498039:Unterminated string starting at; json_error_line_498040:Expecting value; json_error_line_498041:Expecting value; json_error_line_498044:Unterminated string starting at; json_error_line_498045:Expecting value; json_error_line_498046:Expecting value; json_error_line_498052:Unterminated string starting at; json_error_line_498053:Expecting value; json_error_line_498054:Expecting value; json_error_line_498055:Expecting value; json_error_line_498056:Expecting value; json_error_line_498116:Unterminated string starting at; json_error_line_498117:Expecting value; json_error_line_498118:Expecting value; json_error_line_498119:Expecting value; json_error_line_498120:Expecting value; json_error_line_498134:Unterminated string starting at; json_error_line_498135:Expecting value; json_error_line_498136:Expecting value; json_error_line_498137:Expecting value; json_error_line_498138:Expecting value; json_error_line_498139:Expecting value; json_error_line_498140:Expecting value; json_error_line_498141:Expecting value; json_error_line_498142:Expecting value; json_error_line_498218:Unterminated string starting at; json_error_line_498219:Expecting value; json_error_line_498220:Expecting value; json_error_line_498239:Unterminated string starting at; json_error_line_498240:Expecting value; json_error_line_498241:Expecting value; json_error_line_498271:Unterminated string starting at; json_error_line_498272:Expecting value; json_error_line_498273:Expecting value; json_error_line_498280:Unterminated string starting at; json_error_line_498281:Expecting value; json_error_line_498282:Expecting value; json_error_line_498283:Expecting value; json_error_line_498284:Expecting value; json_error_line_498321:Unterminated string starting at; json_error_line_498322:Expecting value; json_error_line_498323:Expecting value; json_error_line_498324:Expecting value; json_error_line_498325:Expecting value; json_error_line_498340:Unterminated string starting at; json_error_line_498341:Expecting value; json_error_line_498342:Expecting value; json_error_line_498395:Unterminated string starting at; json_error_line_498396:Expecting value; json_error_line_498397:Expecting value; json_error_line_498411:Unterminated string starting at; json_error_line_498412:Expecting value; json_error_line_498413:Expecting value; json_error_line_498440:Unterminated string starting at; json_error_line_498441:Expecting value; json_error_line_498442:Expecting value; json_error_line_498557:Unterminated string starting at; json_error_line_498558:Expecting value; json_error_line_498559:Expecting value; json_error_line_498596:Unterminated string starting at; json_error_line_498597:Expecting value; json_error_line_498598:Expecting value; json_error_line_498599:Expecting value; json_error_line_498600:Expecting value; json_error_line_498601:Expecting value; json_error_line_498602:Expecting value; json_error_line_498619:Unterminated string starting at; json_error_line_498620:Expecting value; json_error_line_498621:Expecting value; json_error_line_498629:Unterminated string starting at; json_error_line_498630:Expecting value; json_error_line_498631:Expecting value; json_error_line_498646:Unterminated string starting at; json_error_line_498647:Expecting value; json_error_line_498648:Expecting value; json_error_line_498649:Unterminated string starting at; json_error_line_498650:Expecting value; json_error_line_498651:Expecting value; json_error_line_498652:Expecting value; json_error_line_498653:Expecting value; json_error_line_498679:Unterminated string starting at; json_error_line_498680:Expecting value; json_error_line_498681:Expecting value; json_error_line_498682:Expecting value; json_error_line_498683:Expecting value; json_error_line_498704:Unterminated string starting at; json_error_line_498705:Expecting value; json_error_line_498706:Expecting value; json_error_line_498782:Unterminated string starting at; json_error_line_498783:Expecting value; json_error_line_498784:Expecting value; json_error_line_498823:Unterminated string starting at; json_error_line_498824:Expecting value; json_error_line_498825:Expecting value; json_error_line_498826:Expecting value; json_error_line_498827:Expecting value; json_error_line_498845:Unterminated string starting at; json_error_line_498846:Expecting value; json_error_line_498847:Expecting value; json_error_line_498848:Expecting value; json_error_line_498849:Expecting value; json_error_line_498966:Unterminated string starting at; json_error_line_498967:Expecting value; json_error_line_498968:Expecting value; json_error_line_499428:Unterminated string starting at; json_error_line_499429:Expecting value; json_error_line_499430:Expecting value; json_error_line_500052:Unterminated string starting at; json_error_line_500053:Expecting value; json_error_line_500054:Expecting value; json_error_line_500201:Unterminated string starting at; json_error_line_500202:Expecting value; json_error_line_500203:Expecting value; json_error_line_500211:Unterminated string starting at; json_error_line_500212:Expecting value; json_error_line_500213:Expecting value; json_error_line_500270:Unterminated string starting at; json_error_line_500271:Expecting value; json_error_line_500272:Expecting value; json_error_line_500286:Unterminated string starting at; json_error_line_500287:Expecting value; json_error_line_500288:Expecting value; json_error_line_500289:Unterminated string starting at; json_error_line_500290:Expecting value; json_error_line_500291:Expecting value; json_error_line_500298:Unterminated string starting at; json_error_line_500299:Expecting value; json_error_line_500300:Expecting value; json_error_line_500331:Unterminated string starting at; json_error_line_500332:Expecting value; json_error_line_500333:Expecting value; json_error_line_500377:Unterminated string starting at; json_error_line_500378:Expecting value; json_error_line_500379:Expecting value; json_error_line_500424:Unterminated string starting at; json_error_line_500425:Expecting value; json_error_line_500426:Expecting value; json_error_line_500427:Expecting value; json_error_line_500428:Expecting value; json_error_line_500429:Expecting value; json_error_line_500430:Expecting value; json_error_line_500434:Unterminated string starting at; json_error_line_500435:Expecting value; json_error_line_500436:Expecting value; json_error_line_500449:Unterminated string starting at; json_error_line_500450:Expecting value; json_error_line_500451:Expecting value; json_error_line_500558:Unterminated string starting at; json_error_line_500559:Expecting value; json_error_line_500560:Expecting value; json_error_line_500564:Unterminated string starting at; json_error_line_500565:Expecting value; json_error_line_500566:Expecting value; json_error_line_501055:Unterminated string starting at; json_error_line_501056:Expecting value; json_error_line_501057:Expecting value; json_error_line_501449:Unterminated string starting at; json_error_line_501450:Expecting value; json_error_line_501451:Expecting value; json_error_line_502488:Unterminated string starting at; json_error_line_502489:Expecting value; json_error_line_502490:Expecting value; json_error_line_502518:Unterminated string starting at; json_error_line_502519:Expecting value; json_error_line_502520:Expecting value; json_error_line_504485:Unterminated string starting at; json_error_line_504486:Expecting value; json_error_line_504487:Expecting value; json_error_line_504496:Unterminated string starting at; json_error_line_504497:Expecting value; json_error_line_504498:Expecting value; json_error_line_504515:Unterminated string starting at; json_error_line_504516:Expecting value; json_error_line_504517:Expecting value; json_error_line_504538:Unterminated string starting at; json_error_line_504539:Expecting value; json_error_line_504540:Expecting value; json_error_line_504547:Unterminated string starting at; json_error_line_504548:Expecting value; json_error_line_504549:Expecting value; json_error_line_504564:Unterminated string starting at; json_error_line_504565:Expecting value; json_error_line_504566:Expecting value; json_error_line_504571:Unterminated string starting at; json_error_line_504572:Expecting value; json_error_line_504573:Expecting value; json_error_line_504602:Unterminated string starting at; json_error_line_504603:Expecting value; json_error_line_504604:Expecting value; json_error_line_504605:Expecting value; json_error_line_504606:Expecting value; json_error_line_504607:Expecting value; json_error_line_504608:Expecting value; json_error_line_504614:Unterminated string starting at; json_error_line_504615:Expecting value; json_error_line_504616:Expecting value; json_error_line_504637:Unterminated string starting at; json_error_line_504638:Expecting value; json_error_line_504639:Expecting value; json_error_line_504662:Unterminated string starting at; json_error_line_504663:Expecting value; json_error_line_504664:Expecting value; json_error_line_504697:Unterminated string starting at; json_error_line_504698:Expecting value; json_error_line_504699:Expecting value; json_error_line_504703:Unterminated string starting at; json_error_line_504704:Expecting value; json_error_line_504705:Expecting value; json_error_line_504706:Expecting value; json_error_line_504707:Expecting value; json_error_line_504708:Expecting value; json_error_line_504709:Expecting value; json_error_line_504717:Unterminated string starting at; json_error_line_504718:Expecting value; json_error_line_504719:Expecting value; json_error_line_504720:Expecting value; json_error_line_504721:Expecting value; json_error_line_504722:Expecting value; json_error_line_504723:Expecting value; json_error_line_504754:Unterminated string starting at; json_error_line_504755:Expecting value; json_error_line_504756:Expecting value; json_error_line_504763:Unterminated string starting at; json_error_line_504764:Expecting value; json_error_line_504765:Expecting value; json_error_line_504773:Unterminated string starting at; json_error_line_504774:Expecting value; json_error_line_504775:Expecting value; json_error_line_504841:Unterminated string starting at; json_error_line_504842:Expecting value; json_error_line_504843:Expecting value; json_error_line_504909:Unterminated string starting at; json_error_line_504910:Expecting value; json_error_line_504911:Expecting value; json_error_line_504912:Expecting value; json_error_line_504913:Expecting value; json_error_line_504914:Expecting value; json_error_line_504915:Expecting value; json_error_line_504931:Unterminated string starting at; json_error_line_504932:Expecting value; json_error_line_504933:Expecting value; json_error_line_504942:Unterminated string starting at; json_error_line_504943:Expecting value; json_error_line_504944:Expecting value; json_error_line_504945:Expecting value; json_error_line_504946:Expecting value; json_error_line_504947:Unterminated string starting at; json_error_line_504948:Expecting value; json_error_line_504949:Expecting value; json_error_line_504950:Expecting value; json_error_line_504951:Expecting value; json_error_line_504970:Unterminated string starting at; json_error_line_504971:Expecting value; json_error_line_504972:Expecting value; json_error_line_504973:Expecting value; json_error_line_504974:Expecting value; json_error_line_504975:Expecting value; json_error_line_504976:Expecting value; json_error_line_504977:Expecting value; json_error_line_504978:Expecting value; json_error_line_505000:Unterminated string starting at; json_error_line_505001:Expecting value; json_error_line_505002:Expecting value; json_error_line_505003:Expecting value; json_error_line_505004:Expecting value; json_error_line_505052:Unterminated string starting at; json_error_line_505053:Expecting value; json_error_line_505054:Expecting value; json_error_line_505062:Unterminated string starting at; json_error_line_505063:Expecting value; json_error_line_505064:Expecting value; json_error_line_505065:Expecting value; json_error_line_505066:Expecting value; json_error_line_505067:Expecting value; json_error_line_505068:Expecting value; json_error_line_505073:Unterminated string starting at; json_error_line_505074:Expecting value; json_error_line_505075:Expecting value; json_error_line_505095:Unterminated string starting at; json_error_line_505096:Expecting value; json_error_line_505097:Expecting value; json_error_line_505098:Expecting value; json_error_line_505099:Expecting value; json_error_line_505119:Unterminated string starting at; json_error_line_505120:Expecting value; json_error_line_505121:Expecting value; json_error_line_505122:Expecting value; json_error_line_505123:Expecting value; json_error_line_505127:Unterminated string starting at; json_error_line_505128:Expecting value; json_error_line_505129:Expecting value; json_error_line_505216:Unterminated string starting at; json_error_line_505217:Expecting value; json_error_line_505218:Expecting value; json_error_line_505284:Unterminated string starting at; json_error_line_505285:Expecting value; json_error_line_505286:Expecting value; json_error_line_505297:Unterminated string starting at; json_error_line_505298:Expecting value; json_error_line_505299:Expecting value; json_error_line_505300:Unterminated string starting at; json_error_line_505301:Expecting value; json_error_line_505302:Expecting value; json_error_line_505303:Expecting value; json_error_line_505304:Expecting value; json_error_line_505328:Unterminated string starting at; json_error_line_505329:Expecting value; json_error_line_505330:Expecting value; json_error_line_505352:Unterminated string starting at; json_error_line_505353:Expecting value; json_error_line_505354:Expecting value; json_error_line_505362:Unterminated string starting at; json_error_line_505363:Expecting value; json_error_line_505364:Expecting value; json_error_line_505379:Unterminated string starting at; json_error_line_505380:Expecting value; json_error_line_505381:Expecting value; json_error_line_505424:Unterminated string starting at; json_error_line_505425:Expecting value; json_error_line_505426:Expecting value; json_error_line_505427:Expecting value; json_error_line_505428:Expecting value; json_error_line_505429:Expecting value; json_error_line_505430:Expecting value; json_error_line_505471:Unterminated string starting at; json_error_line_505472:Expecting value; json_error_line_505473:Expecting value; json_error_line_505493:Unterminated string starting at; json_error_line_505494:Expecting value; json_error_line_505495:Expecting value; json_error_line_505551:Unterminated string starting at; json_error_line_505552:Expecting value; json_error_line_505553:Expecting value; json_error_line_505558:Unterminated string starting at; json_error_line_505559:Expecting value; json_error_line_505560:Expecting value; json_error_line_505561:Expecting value; json_error_line_505562:Expecting value; json_error_line_505670:Unterminated string starting at; json_error_line_505671:Expecting value; json_error_line_505672:Expecting value; json_error_line_505673:Expecting value; json_error_line_505674:Expecting value; json_error_line_505675:Expecting value; json_error_line_505676:Expecting value; json_error_line_505687:Unterminated string starting at; json_error_line_505688:Expecting value; json_error_line_505689:Expecting value; json_error_line_505690:Expecting value; json_error_line_505691:Expecting value; json_error_line_505692:Expecting value; json_error_line_505693:Expecting value; json_error_line_505769:Unterminated string starting at; json_error_line_505770:Expecting value; json_error_line_505771:Expecting value; json_error_line_505772:Expecting value; json_error_line_505773:Expecting value; json_error_line_505803:Unterminated string starting at; json_error_line_505804:Expecting value; json_error_line_505805:Expecting value; json_error_line_505853:Unterminated string starting at; json_error_line_505854:Expecting value; json_error_line_505855:Expecting value; json_error_line_505856:Expecting value; json_error_line_505857:Expecting value; json_error_line_505887:Unterminated string starting at; json_error_line_505888:Expecting value; json_error_line_505889:Expecting value; json_error_line_505908:Unterminated string starting at; json_error_line_505909:Expecting value; json_error_line_505910:Expecting value; json_error_line_505917:Unterminated string starting at; json_error_line_505918:Expecting value; json_error_line_505919:Expecting value; json_error_line_505994:Unterminated string starting at; json_error_line_505995:Expecting value; json_error_line_505996:Expecting value; json_error_line_506015:Unterminated string starting at; json_error_line_506016:Expecting value; json_error_line_506017:Expecting value; json_error_line_506031:Unterminated string starting at; json_error_line_506032:Expecting value; json_error_line_506033:Expecting value; json_error_line_506034:Expecting value; json_error_line_506035:Expecting value; json_error_line_506081:Unterminated string starting at; json_error_line_506082:Expecting value; json_error_line_506083:Expecting value; json_error_line_506117:Unterminated string starting at; json_error_line_506118:Expecting value; json_error_line_506119:Expecting value; json_error_line_506120:Expecting value; json_error_line_506121:Expecting value; json_error_line_506165:Unterminated string starting at; json_error_line_506166:Expecting value; json_error_line_506167:Expecting value; json_error_line_506204:Unterminated string starting at; json_error_line_506205:Expecting value; json_error_line_506206:Expecting value; json_error_line_506207:Unterminated string starting at; json_error_line_506208:Expecting value; json_error_line_506209:Expecting value; json_error_line_506226:Unterminated string starting at; json_error_line_506227:Expecting value; json_error_line_506228:Expecting value; json_error_line_506229:Expecting value; json_error_line_506230:Expecting value; json_error_line_506240:Unterminated string starting at; json_error_line_506241:Expecting value; json_error_line_506242:Expecting value; json_error_line_506252:Unterminated string starting at; json_error_line_506253:Extra data; json_error_line_506278:Unterminated string starting at; json_error_line_506279:Expecting value; json_error_line_506280:Expecting value; json_error_line_506281:Expecting value; json_error_line_506282:Expecting value; json_error_line_506283:Expecting value; json_error_line_506284:Expecting value; json_error_line_506299:Unterminated string starting at; json_error_line_506300:Expecting value; json_error_line_506301:Expecting value; json_error_line_506328:Unterminated string starting at; json_error_line_506329:Expecting value; json_error_line_506330:Expecting value; json_error_line_506337:Unterminated string starting at; json_error_line_506338:Expecting value; json_error_line_506339:Expecting value; json_error_line_506340:Expecting value; json_error_line_506341:Expecting value; json_error_line_506342:Expecting value; json_error_line_506343:Expecting value; json_error_line_506344:Expecting value; json_error_line_506345:Expecting value; json_error_line_506349:Unterminated string starting at; json_error_line_506350:Expecting value; json_error_line_506351:Expecting value; json_error_line_506378:Unterminated string starting at; json_error_line_506379:Expecting value; json_error_line_506380:Expecting value; json_error_line_506396:Unterminated string starting at; json_error_line_506397:Expecting value; json_error_line_506398:Expecting value; json_error_line_506408:Unterminated string starting at; json_error_line_506409:Expecting value; json_error_line_506410:Expecting value; json_error_line_506437:Unterminated string starting at; json_error_line_506438:Expecting value; json_error_line_506439:Expecting value; json_error_line_506440:Expecting value; json_error_line_506441:Expecting value; json_error_line_506448:Unterminated string starting at; json_error_line_506449:Expecting value; json_error_line_506450:Expecting value; json_error_line_506451:Expecting value; json_error_line_506452:Expecting value; json_error_line_506469:Unterminated string starting at; json_error_line_506470:Expecting value; json_error_line_506471:Expecting value; json_error_line_506472:Expecting value; json_error_line_506473:Expecting value; json_error_line_506474:Expecting value; json_error_line_506475:Expecting value; json_error_line_506505:Unterminated string starting at; json_error_line_506506:Expecting value; json_error_line_506507:Expecting value; json_error_line_506515:Unterminated string starting at; json_error_line_506516:Expecting value; json_error_line_506517:Expecting value; json_error_line_506521:Unterminated string starting at; json_error_line_506522:Expecting value; json_error_line_506523:Expecting value; json_error_line_506593:Unterminated string starting at; json_error_line_506594:Expecting value; json_error_line_506595:Expecting value; json_error_line_506668:Unterminated string starting at; json_error_line_506669:Expecting value; json_error_line_506670:Expecting value; json_error_line_506734:Unterminated string starting at; json_error_line_506735:Expecting value; json_error_line_506736:Expecting value; json_error_line_506738:Unterminated string starting at; json_error_line_506739:Expecting value; json_error_line_506740:Expecting value; json_error_line_506741:Expecting value; json_error_line_506742:Expecting value; json_error_line_506743:Expecting value; json_error_line_506744:Expecting value; json_error_line_506745:Expecting value; json_error_line_506746:Expecting value; json_error_line_506747:Expecting value; json_error_line_506748:Expecting value; json_error_line_506749:Expecting value; json_error_line_506750:Expecting value; json_error_line_506752:Unterminated string starting at; json_error_line_506753:Expecting value; json_error_line_506754:Expecting value; json_error_line_506789:Unterminated string starting at; json_error_line_506790:Expecting value; json_error_line_506791:Expecting value; json_error_line_506838:Unterminated string starting at; json_error_line_506839:Expecting value; json_error_line_506840:Expecting value; json_error_line_506885:Unterminated string starting at; json_error_line_506886:Expecting value; json_error_line_506887:Expecting value; json_error_line_506888:Expecting value; json_error_line_506889:Expecting value; json_error_line_506949:Unterminated string starting at; json_error_line_506950:Expecting value; json_error_line_506951:Expecting value; json_error_line_506975:Unterminated string starting at; json_error_line_506976:Expecting value; json_error_line_506977:Expecting value; json_error_line_506978:Expecting value; json_error_line_506979:Expecting value; json_error_line_507020:Unterminated string starting at; json_error_line_507021:Expecting value; json_error_line_507022:Expecting value; json_error_line_507023:Expecting value; json_error_line_507024:Expecting value; json_error_line_507028:Unterminated string starting at; json_error_line_507029:Expecting value; json_error_line_507030:Expecting value; json_error_line_507067:Unterminated string starting at; json_error_line_507068:Expecting value; json_error_line_507069:Expecting value; json_error_line_507071:Unterminated string starting at; json_error_line_507072:Expecting value; json_error_line_507073:Expecting value; json_error_line_507092:Unterminated string starting at; json_error_line_507093:Expecting value; json_error_line_507094:Expecting value; json_error_line_507110:Unterminated string starting at; json_error_line_507111:Expecting value; json_error_line_507112:Expecting value; json_error_line_507123:Unterminated string starting at; json_error_line_507124:Expecting value; json_error_line_507125:Expecting value; json_error_line_507162:Unterminated string starting at; json_error_line_507163:Expecting value; json_error_line_507164:Expecting value; json_error_line_507173:Unterminated string starting at; json_error_line_507174:Expecting value; json_error_line_507175:Expecting value; json_error_line_507183:Unterminated string starting at; json_error_line_507184:Expecting value; json_error_line_507185:Expecting value; json_error_line_507194:Unterminated string starting at; json_error_line_507195:Expecting value; json_error_line_507196:Expecting value; json_error_line_507230:Unterminated string starting at; json_error_line_507231:Expecting value; json_error_line_507232:Expecting value; json_error_line_507244:Unterminated string starting at; json_error_line_507245:Expecting value; json_error_line_507246:Expecting value; json_error_line_507249:Unterminated string starting at; json_error_line_507250:Expecting value; json_error_line_507251:Expecting value; json_error_line_507252:Expecting value; json_error_line_507253:Expecting value; json_error_line_507254:Expecting value; json_error_line_507255:Expecting value; json_error_line_507288:Unterminated string starting at; json_error_line_507289:Expecting value; json_error_line_507290:Expecting value; json_error_line_507294:Unterminated string starting at; json_error_line_507295:Expecting value; json_error_line_507296:Expecting value; json_error_line_507312:Unterminated string starting at; json_error_line_507313:Expecting value; json_error_line_507314:Expecting value; json_error_line_507326:Unterminated string starting at; json_error_line_507327:Expecting value; json_error_line_507328:Expecting value; json_error_line_507344:Unterminated string starting at; json_error_line_507345:Expecting value; json_error_line_507346:Expecting value; json_error_line_507349:Unterminated string starting at; json_error_line_507350:Expecting value; json_error_line_507351:Expecting value; json_error_line_507391:Unterminated string starting at; json_error_line_507392:Expecting value; json_error_line_507393:Expecting value; json_error_line_507394:Unterminated string starting at; json_error_line_507395:Expecting value; json_error_line_507396:Expecting value; json_error_line_507397:Expecting value; json_error_line_507398:Expecting value; json_error_line_507419:Unterminated string starting at; json_error_line_507420:Expecting value; json_error_line_507421:Expecting value; json_error_line_507431:Unterminated string starting at; json_error_line_507432:Expecting value; json_error_line_507433:Expecting value; json_error_line_507434:Unterminated string starting at; json_error_line_507435:Expecting value; json_error_line_507436:Expecting value; json_error_line_507437:Expecting value; json_error_line_507438:Expecting value; json_error_line_507439:Expecting value; json_error_line_507440:Expecting value; json_error_line_507444:Unterminated string starting at; json_error_line_507445:Expecting value; json_error_line_507446:Expecting value; json_error_line_507458:Unterminated string starting at; json_error_line_507459:Expecting value; json_error_line_507460:Expecting value; json_error_line_507465:Unterminated string starting at; json_error_line_507466:Expecting value; json_error_line_507467:Expecting value; json_error_line_507475:Unterminated string starting at; json_error_line_507476:Extra data; json_error_line_507615:Unterminated string starting at; json_error_line_507616:Expecting value; json_error_line_507617:Expecting value; json_error_line_507631:Unterminated string starting at; json_error_line_507632:Expecting value; json_error_line_507633:Expecting value; json_error_line_507667:Unterminated string starting at; json_error_line_507668:Expecting value; json_error_line_507669:Expecting value; json_error_line_507739:Unterminated string starting at; json_error_line_507740:Expecting value; json_error_line_507741:Expecting value; json_error_line_507742:Expecting value; json_error_line_507743:Expecting value; json_error_line_507781:Unterminated string starting at; json_error_line_507782:Expecting value; json_error_line_507783:Expecting value; json_error_line_507784:Expecting value; json_error_line_507785:Expecting value; json_error_line_507907:Unterminated string starting at; json_error_line_507908:Expecting value; json_error_line_507909:Expecting value; json_error_line_507949:Unterminated string starting at; json_error_line_507950:Expecting value; json_error_line_507951:Expecting value; json_error_line_507970:Unterminated string starting at; json_error_line_507971:Expecting value; json_error_line_507972:Expecting value; json_error_line_507988:Unterminated string starting at; json_error_line_507989:Expecting value; json_error_line_507990:Expecting value; json_error_line_508084:Unterminated string starting at; json_error_line_508085:Expecting value; json_error_line_508086:Expecting value; json_error_line_508141:Unterminated string starting at; json_error_line_508142:Expecting value; json_error_line_508143:Expecting value; json_error_line_508156:Unterminated string starting at; json_error_line_508157:Expecting value; json_error_line_508158:Expecting value; json_error_line_508163:Unterminated string starting at; json_error_line_508164:Expecting value; json_error_line_508165:Expecting value; json_error_line_508185:Unterminated string starting at; json_error_line_508186:Expecting value; json_error_line_508187:Expecting value; json_error_line_508188:Expecting value; json_error_line_508189:Expecting value; json_error_line_508190:Expecting value; json_error_line_508191:Expecting value; json_error_line_508204:Unterminated string starting at; json_error_line_508205:Expecting value; json_error_line_508206:Expecting value; json_error_line_508239:Unterminated string starting at; json_error_line_508240:Expecting value; json_error_line_508241:Expecting value; json_error_line_508242:Expecting value; json_error_line_508243:Expecting value; json_error_line_508244:Expecting value; json_error_line_508245:Expecting value; json_error_line_508246:Expecting value; json_error_line_508247:Expecting value; json_error_line_508257:Unterminated string starting at; json_error_line_508258:Expecting value; json_error_line_508259:Expecting value; json_error_line_508287:Unterminated string starting at; json_error_line_508288:Expecting value; json_error_line_508289:Expecting value; json_error_line_508353:Unterminated string starting at; json_error_line_508354:Expecting value; json_error_line_508355:Expecting value; json_error_line_508356:Expecting value; json_error_line_508357:Expecting value; json_error_line_508394:Unterminated string starting at; json_error_line_508395:Expecting value; json_error_line_508396:Expecting value; json_error_line_508435:Unterminated string starting at; json_error_line_508436:Expecting value; json_error_line_508437:Expecting value; json_error_line_508438:Expecting value; json_error_line_508439:Expecting value; json_error_line_508611:Unterminated string starting at; json_error_line_508612:Expecting value; json_error_line_508613:Expecting value; json_error_line_508757:Unterminated string starting at; json_error_line_508758:Expecting value; json_error_line_508759:Expecting value; json_error_line_508760:Expecting value; json_error_line_508761:Expecting value; json_error_line_508762:Expecting value; json_error_line_508763:Expecting value; json_error_line_508764:Expecting value; json_error_line_508765:Expecting value; json_error_line_508989:Unterminated string starting at; json_error_line_508990:Expecting value; json_error_line_508991:Expecting value; json_error_line_509363:Unterminated string starting at; json_error_line_509364:Expecting value; json_error_line_509365:Expecting value; json_error_line_509646:Unterminated string starting at; json_error_line_509647:Expecting value; json_error_line_509648:Expecting value; json_error_line_509661:Unterminated string starting at; json_error_line_509662:Expecting value; json_error_line_509663:Expecting value; json_error_line_509664:Expecting value; json_error_line_509665:Expecting value; json_error_line_509666:Expecting value; json_error_line_509667:Expecting value; json_error_line_509668:Expecting value; json_error_line_509669:Expecting value; json_error_line_509670:Expecting value; json_error_line_509671:Expecting value; json_error_line_509672:Expecting value; json_error_line_509673:Expecting value; json_error_line_509674:Expecting value; json_error_line_509675:Expecting value; json_error_line_509676:Expecting value; json_error_line_509677:Expecting value; json_error_line_509854:Unterminated string starting at; json_error_line_509855:Expecting value; json_error_line_509856:Expecting value; json_error_line_509874:Unterminated string starting at; json_error_line_509875:Expecting value; json_error_line_509876:Expecting value; json_error_line_509877:Expecting value; json_error_line_509878:Expecting value; json_error_line_509986:Unterminated string starting at; json_error_line_509987:Expecting value; json_error_line_509988:Expecting value; json_error_line_509989:Expecting value; json_error_line_509990:Expecting value; json_error_line_509991:Expecting value; json_error_line_509992:Expecting value; json_error_line_509993:Expecting value; json_error_line_509994:Expecting value; json_error_line_509995:Expecting value; json_error_line_509996:Expecting value; json_error_line_510159:Unterminated string starting at; json_error_line_510160:Expecting value; json_error_line_510161:Expecting value; json_error_line_510292:Unterminated string starting at; json_error_line_510293:Expecting value; json_error_line_510294:Expecting value; json_error_line_511990:Unterminated string starting at; json_error_line_511991:Expecting value; json_error_line_511992:Expecting value; json_error_line_511993:Expecting value; json_error_line_511994:Expecting value; json_error_line_511996:Unterminated string starting at; json_error_line_511997:Expecting value; json_error_line_511998:Expecting value; json_error_line_512019:Unterminated string starting at; json_error_line_512020:Expecting value; json_error_line_512021:Expecting value; json_error_line_512084:Unterminated string starting at; json_error_line_512085:Expecting value; json_error_line_512086:Expecting value; json_error_line_512105:Unterminated string starting at; json_error_line_512106:Expecting value; json_error_line_512107:Expecting value; json_error_line_512185:Unterminated string starting at; json_error_line_512186:Expecting value; json_error_line_512187:Expecting value; json_error_line_512190:Unterminated string starting at; json_error_line_512191:Expecting value; json_error_line_512192:Expecting value; json_error_line_512195:Unterminated string starting at; json_error_line_512196:Expecting value; json_error_line_512197:Expecting value; json_error_line_512227:Unterminated string starting at; json_error_line_512228:Expecting value; json_error_line_512229:Expecting value; json_error_line_512230:Expecting value; json_error_line_512231:Expecting value; json_error_line_512254:Unterminated string starting at; json_error_line_512255:Expecting value; json_error_line_512256:Expecting value; json_error_line_512289:Unterminated string starting at; json_error_line_512290:Expecting value; json_error_line_512291:Expecting value; json_error_line_512319:Unterminated string starting at; json_error_line_512320:Expecting value; json_error_line_512321:Expecting value; json_error_line_512322:Expecting value; json_error_line_512323:Expecting value; json_error_line_512324:Expecting value; json_error_line_512325:Expecting value; json_error_line_512326:Unterminated string starting at; json_error_line_512327:Expecting value; json_error_line_512328:Expecting value; json_error_line_512329:Expecting value; json_error_line_512330:Expecting value; json_error_line_512338:Unterminated string starting at; json_error_line_512339:Expecting value; json_error_line_512340:Expecting value; json_error_line_512368:Unterminated string starting at; json_error_line_512369:Expecting value; json_error_line_512370:Expecting value; json_error_line_512446:Unterminated string starting at; json_error_line_512447:Expecting value; json_error_line_512448:Expecting value; json_error_line_512481:Unterminated string starting at; json_error_line_512482:Expecting value; json_error_line_512483:Expecting value; json_error_line_512484:Expecting value; json_error_line_512485:Expecting value; json_error_line_512499:Unterminated string starting at; json_error_line_512500:Expecting value; json_error_line_512501:Expecting value; json_error_line_512592:Unterminated string starting at; json_error_line_512593:Expecting value; json_error_line_512594:Expecting value; json_error_line_512733:Unterminated string starting at; json_error_line_512734:Expecting value; json_error_line_512735:Expecting value; json_error_line_512756:Unterminated string starting at; json_error_line_512757:Expecting value; json_error_line_512758:Expecting value; json_error_line_512759:Expecting value; json_error_line_512760:Expecting value; json_error_line_512761:Expecting value; json_error_line_512762:Expecting value; json_error_line_512763:Expecting value; json_error_line_512764:Expecting value; json_error_line_512765:Expecting value; json_error_line_512766:Expecting value; json_error_line_512769:Unterminated string starting at; json_error_line_512770:Expecting value; json_error_line_512771:Expecting value; json_error_line_512790:Unterminated string starting at; json_error_line_512791:Expecting value; json_error_line_512792:Expecting value; json_error_line_512831:Unterminated string starting at; json_error_line_512832:Expecting value; json_error_line_512833:Expecting value; json_error_line_512850:Unterminated string starting at; json_error_line_512851:Expecting value; json_error_line_512852:Expecting value; json_error_line_512853:Expecting value; json_error_line_512854:Expecting value; json_error_line_512868:Unterminated string starting at; json_error_line_512869:Expecting value; json_error_line_512870:Expecting value; json_error_line_512871:Expecting value; json_error_line_512872:Expecting value; json_error_line_512892:Unterminated string starting at; json_error_line_512893:Expecting value; json_error_line_512894:Expecting value; json_error_line_512908:Unterminated string starting at; json_error_line_512909:Expecting value; json_error_line_512910:Expecting value; json_error_line_512957:Unterminated string starting at; json_error_line_512958:Expecting value; json_error_line_512959:Expecting value; json_error_line_512984:Unterminated string starting at; json_error_line_512985:Expecting value; json_error_line_512986:Expecting value; json_error_line_512987:Expecting value; json_error_line_512988:Expecting value; json_error_line_512989:Expecting value; json_error_line_512990:Expecting value; json_error_line_512991:Expecting value; json_error_line_512992:Expecting value; json_error_line_512993:Expecting value; json_error_line_512994:Expecting value; json_error_line_512995:Expecting value; json_error_line_512996:Expecting value; json_error_line_512997:Expecting value; json_error_line_512998:Expecting value; json_error_line_512999:Expecting value; json_error_line_513000:Expecting value; json_error_line_513001:Expecting value; json_error_line_513002:Expecting value; json_error_line_513003:Expecting value; json_error_line_513004:Expecting value; json_error_line_513005:Expecting value; json_error_line_513006:Expecting value; json_error_line_513007:Expecting value; json_error_line_513008:Expecting value; json_error_line_513009:Expecting value; json_error_line_513010:Expecting value; json_error_line_513011:Expecting value; json_error_line_513012:Expecting value; json_error_line_513079:Unterminated string starting at; json_error_line_513080:Expecting value; json_error_line_513081:Expecting value; json_error_line_513082:Expecting value; json_error_line_513083:Expecting value; json_error_line_513084:Expecting value; json_error_line_513085:Expecting value; json_error_line_513086:Expecting value; json_error_line_513087:Expecting value; json_error_line_513101:Unterminated string starting at; json_error_line_513102:Expecting value; json_error_line_513103:Expecting value; json_error_line_513106:Unterminated string starting at; json_error_line_513107:Expecting value; json_error_line_513108:Expecting value; json_error_line_513135:Unterminated string starting at; json_error_line_513136:Expecting value; json_error_line_513137:Expecting value; json_error_line_513138:Expecting value; json_error_line_513139:Expecting value; json_error_line_513168:Unterminated string starting at; json_error_line_513169:Expecting value; json_error_line_513170:Expecting value; json_error_line_513197:Unterminated string starting at; json_error_line_513198:Expecting value; json_error_line_513199:Expecting value; json_error_line_513334:Unterminated string starting at; json_error_line_513335:Expecting value; json_error_line_513336:Expecting value; json_error_line_513587:Unterminated string starting at; json_error_line_513588:Expecting value; json_error_line_513589:Expecting value; json_error_line_513619:Unterminated string starting at; json_error_line_513620:Expecting value; json_error_line_513621:Expecting value; json_error_line_533800:Unterminated string starting at; json_error_line_533801:Expecting value; json_error_line_533802:Expecting value; json_error_line_534865:Unterminated string starting at; json_error_line_534866:Expecting value; json_error_line_534867:Expecting value; json_error_line_534882:Unterminated string starting at; json_error_line_534883:Expecting value; json_error_line_534884:Expecting value; json_error_line_534905:Unterminated string starting at; json_error_line_534906:Expecting value; json_error_line_534907:Expecting value; json_error_line_534965:Unterminated string starting at; json_error_line_534966:Expecting value; json_error_line_534967:Expecting value; json_error_line_534978:Unterminated string starting at; json_error_line_534979:Expecting value; json_error_line_534980:Expecting value; json_error_line_534981:Expecting value; json_error_line_534982:Expecting value; json_error_line_534987:Unterminated string starting at; json_error_line_534988:Expecting value; json_error_line_534989:Expecting value; json_error_line_535008:Unterminated string starting at; json_error_line_535009:Expecting value; json_error_line_535010:Expecting value; json_error_line_535077:Unterminated string starting at; json_error_line_535078:Expecting value; json_error_line_535079:Expecting value; json_error_line_535102:Unterminated string starting at; json_error_line_535103:Expecting value; json_error_line_535104:Expecting value; json_error_line_535135:Unterminated string starting at; json_error_line_535136:Expecting value; json_error_line_535137:Expecting value; json_error_line_535138:Expecting value; json_error_line_535139:Expecting value; json_error_line_535157:Unterminated string starting at; json_error_line_535158:Expecting value; json_error_line_535159:Expecting value; json_error_line_535163:Unterminated string starting at; json_error_line_535164:Expecting value; json_error_line_535165:Expecting value; json_error_line_535167:Unterminated string starting at; json_error_line_535168:Expecting value; json_error_line_535169:Expecting value; json_error_line_535170:Expecting value; json_error_line_535171:Expecting value; json_error_line_535205:Unterminated string starting at; json_error_line_535206:Expecting value; json_error_line_535207:Expecting value; json_error_line_535216:Unterminated string starting at; json_error_line_535217:Expecting value; json_error_line_535218:Expecting value; json_error_line_535219:Expecting value; json_error_line_535220:Expecting value; json_error_line_535246:Unterminated string starting at; json_error_line_535247:Expecting value; json_error_line_535248:Expecting value; json_error_line_535249:Expecting value; json_error_line_535250:Expecting value; json_error_line_535261:Unterminated string starting at; json_error_line_535262:Expecting value; json_error_line_535263:Expecting value; json_error_line_535299:Unterminated string starting at; json_error_line_535300:Expecting value; json_error_line_535301:Expecting value; json_error_line_535322:Unterminated string starting at; json_error_line_535323:Expecting value; json_error_line_535324:Expecting value; json_error_line_535341:Unterminated string starting at; json_error_line_535342:Expecting value; json_error_line_535343:Expecting value; json_error_line_535344:Expecting value; json_error_line_535345:Expecting value; json_error_line_535346:Expecting value; json_error_line_535347:Expecting value; json_error_line_535380:Unterminated string starting at; json_error_line_535381:Expecting value; json_error_line_535382:Expecting value; json_error_line_535407:Unterminated string starting at; json_error_line_535408:Expecting value; json_error_line_535409:Expecting value; json_error_line_535430:Unterminated string starting at; json_error_line_535431:Expecting value; json_error_line_535432:Expecting value; json_error_line_535436:Unterminated string starting at; json_error_line_535437:Expecting value; json_error_line_535438:Expecting value; json_error_line_535454:Unterminated string starting at; json_error_line_535455:Expecting value; json_error_line_535456:Expecting value; json_error_line_535457:Expecting value; json_error_line_535458:Expecting value; json_error_line_535490:Unterminated string starting at; json_error_line_535491:Expecting value; json_error_line_535492:Expecting value; json_error_line_535503:Unterminated string starting at; json_error_line_535504:Expecting value; json_error_line_535505:Expecting value; json_error_line_535511:Unterminated string starting at; json_error_line_535512:Expecting value; json_error_line_535513:Expecting value; json_error_line_535628:Unterminated string starting at; json_error_line_535629:Expecting value; json_error_line_535630:Expecting value; json_error_line_535662:Unterminated string starting at; json_error_line_535663:Expecting value; json_error_line_535664:Expecting value; json_error_line_535677:Unterminated string starting at; json_error_line_535678:Expecting value; json_error_line_535679:Expecting value; json_error_line_535704:Unterminated string starting at; json_error_line_535705:Expecting value; json_error_line_535706:Expecting value; json_error_line_535707:Expecting value; json_error_line_535708:Expecting value; json_error_line_535721:Unterminated string starting at; json_error_line_535722:Expecting value; json_error_line_535723:Expecting value; json_error_line_535757:Unterminated string starting at; json_error_line_535758:Expecting value; json_error_line_535759:Expecting value; json_error_line_535786:Unterminated string starting at; json_error_line_535787:Expecting value; json_error_line_535788:Expecting value; json_error_line_535789:Expecting value; json_error_line_535790:Expecting value; json_error_line_535806:Unterminated string starting at; json_error_line_535807:Expecting value; json_error_line_535808:Expecting value; json_error_line_535809:Expecting value; json_error_line_535810:Expecting value; json_error_line_535934:Unterminated string starting at; json_error_line_535935:Expecting value; json_error_line_535936:Expecting value; json_error_line_535954:Unterminated string starting at; json_error_line_535955:Expecting value; json_error_line_535956:Expecting value; json_error_line_535959:Unterminated string starting at; json_error_line_535960:Expecting value; json_error_line_535961:Expecting value; json_error_line_535979:Unterminated string starting at; json_error_line_535980:Expecting value; json_error_line_535981:Expecting value; json_error_line_535999:Unterminated string starting at; json_error_line_536000:Expecting value; json_error_line_536001:Expecting value; json_error_line_536044:Unterminated string starting at; json_error_line_536045:Expecting value; json_error_line_536046:Expecting value; json_error_line_536114:Unterminated string starting at; json_error_line_536115:Expecting value; json_error_line_536116:Expecting value; json_error_line_536376:Unterminated string starting at; json_error_line_536377:Expecting value; json_error_line_536378:Expecting value; json_error_line_536460:Unterminated string starting at; json_error_line_536461:Expecting value; json_error_line_536462:Expecting value; json_error_line_536669:Unterminated string starting at; json_error_line_536670:Expecting value; json_error_line_536671:Expecting value; json_error_line_536701:Unterminated string starting at; json_error_line_536702:Expecting value; json_error_line_536703:Expecting value; json_error_line_536704:Expecting value; json_error_line_536705:Expecting value; json_error_line_536706:Expecting value; json_error_line_536707:Expecting value; json_error_line_537083:Unterminated string starting at; json_error_line_537084:Expecting value; json_error_line_537085:Expecting value; json_error_line_537270:Unterminated string starting at; json_error_line_537271:Expecting value; json_error_line_537272:Expecting value; json_error_line_537273:Expecting value; json_error_line_537274:Expecting value; json_error_line_537275:Expecting value; json_error_line_537276:Expecting value; json_error_line_537420:Unterminated string starting at; json_error_line_537421:Expecting value; json_error_line_537422:Expecting value; json_error_line_537468:Unterminated string starting at; json_error_line_537469:Expecting value; json_error_line_537470:Expecting value; json_error_line_537753:Unterminated string starting at; json_error_line_537754:Expecting value; json_error_line_537755:Expecting value; json_error_line_537776:Unterminated string starting at; json_error_line_537777:Expecting value; json_error_line_537778:Expecting value`

### `datasets/processed/unified/unified_all.sanitized.jsonl`
- Stage: `processed`
- Kind: `jsonl`
- Rows: `561678`
- Schema change: `+0/-0 vs processed_baseline`
- Columns (11): `id, input, license, metadata, prompt, response, rubric, score, source, split, task`
- Datatypes:
  - `id`: `str`
  - `input`: `str`
  - `license`: `str`
  - `metadata`: `dict`
  - `prompt`: `str`
  - `response`: `str`
  - `rubric`: `str`
  - `score`: `float|null`
  - `source`: `str`
  - `split`: `str`
  - `task`: `str`
- Nullable fields (5): `input, prompt, response, rubric, score`
- Missing values (per column):
  - `id`: `0`
  - `input`: `116059`
  - `license`: `0`
  - `metadata`: `0`
  - `prompt`: `78653`
  - `response`: `561678`
  - `rubric`: `561442`
  - `score`: `162008`
  - `source`: `0`
  - `split`: `0`
  - `task`: `0`
- Notes: `encoding=utf-8-sig`

### `datasets/raw/asap_aes/Essay_Set_Descriptions/essay_set_descriptions.xlsx`
- Stage: `raw`
- Kind: `xlsx`
- Rows: `0`
- Schema change: `+0/-28 vs raw_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `excel_read_error:ImportError:`Import openpyxl` failed.  Use pip or conda to install the openpyxl package.`

### `datasets/raw/asap_aes/test_set.tsv`
- Stage: `raw`
- Kind: `tsv`
- Rows: `4261`
- Schema change: `+2/-25 vs raw_baseline`
- Columns (5): `essay_id, essay_set, essay, domain1_predictionid, domain2_predictionid`
- Datatypes:
  - `essay_id`: `str`
  - `essay_set`: `null|str`
  - `essay`: `null|str`
  - `domain1_predictionid`: `null|str`
  - `domain2_predictionid`: `null|str`
- Nullable fields (4): `domain1_predictionid, domain2_predictionid, essay, essay_set`
- Missing values (per column):
  - `essay_id`: `0`
  - `essay_set`: `3`
  - `essay`: `7`
  - `domain1_predictionid`: `11`
  - `domain2_predictionid`: `3661`
- Notes: `encoding=latin-1; delimiter='\t'`

### `datasets/raw/asap_aes/training_set_rel3.tsv`
- Stage: `raw`
- Kind: `tsv`
- Rows: `12991`
- Schema change: `baseline_raw`
- Columns (28): `essay_id, essay_set, essay, rater1_domain1, rater2_domain1, rater3_domain1, domain1_score, rater1_domain2, rater2_domain2, domain2_score, rater1_trait1, rater1_trait2, rater1_trait3, rater1_trait4, rater1_trait5, rater1_trait6, rater2_trait1, rater2_trait2, rater2_trait3, rater2_trait4, rater2_trait5, rater2_trait6, rater3_trait1, rater3_trait2, rater3_trait3, rater3_trait4, rater3_trait5, rater3_trait6`
- Datatypes:
  - `essay_id`: `str`
  - `essay_set`: `null|str`
  - `essay`: `null|str`
  - `rater1_domain1`: `null|str`
  - `rater2_domain1`: `null|str`
  - `rater3_domain1`: `null|str`
  - `domain1_score`: `null|str`
  - `rater1_domain2`: `null|str`
  - `rater2_domain2`: `null|str`
  - `domain2_score`: `null|str`
  - `rater1_trait1`: `null|str`
  - `rater1_trait2`: `null|str`
  - `rater1_trait3`: `null|str`
  - `rater1_trait4`: `null|str`
  - `rater1_trait5`: `null|str`
  - `rater1_trait6`: `null|str`
  - `rater2_trait1`: `null|str`
  - `rater2_trait2`: `null|str`
  - `rater2_trait3`: `null|str`
  - `rater2_trait4`: `null|str`
  - `rater2_trait5`: `null|str`
  - `rater2_trait6`: `null|str`
  - `rater3_trait1`: `null|str`
  - `rater3_trait2`: `null|str`
  - `rater3_trait3`: `null|str`
  - `rater3_trait4`: `null|str`
  - `rater3_trait5`: `null|str`
  - `rater3_trait6`: `null|str`
- Nullable fields (28): `domain1_score, domain2_score, essay, essay_id, essay_set, rater1_domain1, rater1_domain2, rater1_trait1, rater1_trait2, rater1_trait3, rater1_trait4, rater1_trait5, rater1_trait6, rater2_domain1, rater2_domain2, rater2_trait1, rater2_trait2, rater2_trait3, rater2_trait4, rater2_trait5, rater2_trait6, rater3_domain1, rater3_trait1, rater3_trait2, rater3_trait3, rater3_trait4, rater3_trait5, rater3_trait6`
- Missing values (per column):
  - `essay_id`: `1`
  - `essay_set`: `3`
  - `essay`: `3`
  - `rater1_domain1`: `27`
  - `rater2_domain1`: `15`
  - `rater3_domain1`: `12863`
  - `domain1_score`: `27`
  - `rater1_domain2`: `11191`
  - `rater2_domain2`: `11186`
  - `domain2_score`: `11186`
  - `rater1_trait1`: `10699`
  - `rater1_trait2`: `10699`
  - `rater1_trait3`: `10704`
  - `rater1_trait4`: `10704`
  - `rater1_trait5`: `12263`
  - `rater1_trait6`: `12263`
  - `rater2_trait1`: `10699`
  - `rater2_trait2`: `10699`
  - `rater2_trait3`: `10704`
  - `rater2_trait4`: `10704`
  - `rater2_trait5`: `12268`
  - `rater2_trait6`: `12268`
  - `rater3_trait1`: `12863`
  - `rater3_trait2`: `12863`
  - `rater3_trait3`: `12863`
  - `rater3_trait4`: `12863`
  - `rater3_trait5`: `12863`
  - `rater3_trait6`: `12863`
- Notes: `encoding=latin-1; delimiter='\t'`

### `datasets/raw/asap_aes/training_set_rel3.xls`
- Stage: `raw`
- Kind: `xls`
- Rows: `0`
- Schema change: `+0/-28 vs raw_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `excel_read_error:ImportError:`Import xlrd` failed. Install xlrd >= 2.0.1 for xls Excel support Use pip or conda to install the xlrd package.`

### `datasets/raw/asap_aes/training_set_rel3.xlsx`
- Stage: `raw`
- Kind: `xlsx`
- Rows: `0`
- Schema change: `+0/-28 vs raw_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `excel_read_error:ImportError:`Import openpyxl` failed.  Use pip or conda to install the openpyxl package.`

### `datasets/raw/asap_aes/valid_sample_submission_1_column.csv`
- Stage: `raw`
- Kind: `csv`
- Rows: `4818`
- Schema change: `+1/-28 vs raw_baseline`
- Columns (1): `predicted_score`
- Datatypes:
  - `predicted_score`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `predicted_score`: `0`
- Notes: `encoding=utf-8-sig; delimiter=','`

### `datasets/raw/asap_aes/valid_sample_submission_1_column_no_header.csv`
- Stage: `raw`
- Kind: `csv`
- Rows: `4817`
- Schema change: `+1/-28 vs raw_baseline`
- Columns (1): `7`
- Datatypes:
  - `7`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `7`: `0`
- Notes: `encoding=utf-8-sig; delimiter=','`

### `datasets/raw/asap_aes/valid_sample_submission_2_column.csv`
- Stage: `raw`
- Kind: `csv`
- Rows: `4818`
- Schema change: `+2/-28 vs raw_baseline`
- Columns (2): `prediction_id, predicted_score`
- Datatypes:
  - `prediction_id`: `str`
  - `predicted_score`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `prediction_id`: `0`
  - `predicted_score`: `0`
- Notes: `encoding=utf-8-sig; delimiter=','`

### `datasets/raw/asap_aes/valid_sample_submission_5_column.csv`
- Stage: `raw`
- Kind: `csv`
- Rows: `4818`
- Schema change: `+3/-26 vs raw_baseline`
- Columns (5): `prediction_id, essay_id, essay_set, essay_weight, predicted_score`
- Datatypes:
  - `prediction_id`: `str`
  - `essay_id`: `str`
  - `essay_set`: `str`
  - `essay_weight`: `str`
  - `predicted_score`: `str`
- Nullable fields (0): `none`
- Missing values (per column):
  - `prediction_id`: `0`
  - `essay_id`: `0`
  - `essay_set`: `0`
  - `essay_weight`: `0`
  - `predicted_score`: `0`
- Notes: `encoding=utf-8-sig; delimiter=','`

### `datasets/raw/asap_aes/valid_set.tsv`
- Stage: `raw`
- Kind: `tsv`
- Rows: `4221`
- Schema change: `+2/-25 vs raw_baseline`
- Columns (5): `essay_id, essay_set, essay, domain1_predictionid, domain2_predictionid`
- Datatypes:
  - `essay_id`: `str`
  - `essay_set`: `str`
  - `essay`: `str`
  - `domain1_predictionid`: `null|str`
  - `domain2_predictionid`: `null|str`
- Nullable fields (3): `domain1_predictionid, domain2_predictionid, essay`
- Missing values (per column):
  - `essay_id`: `0`
  - `essay_set`: `0`
  - `essay`: `3`
  - `domain1_predictionid`: `6`
  - `domain2_predictionid`: `3621`
- Notes: `encoding=latin-1; delimiter='\t'`

### `datasets/raw/asap_aes/valid_set.xls`
- Stage: `raw`
- Kind: `xls`
- Rows: `0`
- Schema change: `+0/-28 vs raw_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `excel_read_error:ImportError:`Import xlrd` failed. Install xlrd >= 2.0.1 for xls Excel support Use pip or conda to install the xlrd package.`

### `datasets/raw/asap_aes/valid_set.xlsx`
- Stage: `raw`
- Kind: `xlsx`
- Rows: `0`
- Schema change: `+0/-28 vs raw_baseline`
- Columns (0): `none`
- Datatypes: `none`
- Nullable fields (0): `none`
- Missing values: `none`
- Notes: `excel_read_error:ImportError:`Import openpyxl` failed.  Use pip or conda to install the openpyxl package.`

### `datasets/training`
- Stage: `training`
- Kind: `hf_disk`
- Rows: `12413`
- Schema change: `+0/-0 vs training_baseline`
- Columns (3): `essay, prompt, score`
- Datatypes:
  - `essay`: `Value('string')`
  - `prompt`: `Value('string')`
  - `score`: `Value('float64')`
- Nullable fields (0): `none`
- Missing values (per column):
  - `essay`: `0`
  - `prompt`: `0`
  - `score`: `0`
- Notes: `splits=test,train,validation`

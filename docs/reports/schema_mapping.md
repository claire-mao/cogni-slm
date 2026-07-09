# Schema Mapping Report

Unified schema:

- `id`
- `task`
- `prompt`
- `input`
- `response`
- `score`
- `rubric`
- `source`
- `license`
- `split`
- `metadata`

- Source cases normalized: `13`
- Total unified rows written: `54566`
- Total parse errors captured (as metadata rows): `0`
- Per-case unified outputs dir: `datasets/processed/unified`
- Combined unified output: `datasets/processed/unified/unified_all.jsonl`

## Per-Source Field Mapping

### hf/build_summary.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/hf__build_summary.jsonl`
- Rows normalized: `1`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (1), `<generated>` (1) |
| `task` | `<inferred>` (1), `<inferred:unknown>` (1) |
| `prompt` | `<inferred>` (1) |
| `input` | `<inferred>` (1) |
| `response` | `<inferred>` (1) |
| `score` | `<inferred>` (1) |
| `rubric` | `<inferred>` (1) |
| `source` | `<inferred>` (1), `<case_name>` (1) |
| `license` | `<inferred>` (1), `<unknown>` (1) |
| `split` | `<inferred>` (1) |

| Source field | Mapped to |
|---|---|
| `output_dir` | `metadata.original_fields` |
| `raw_root` | `metadata.original_fields` |
| `split_counts` | `metadata.original_fields` |
| `stats` | `metadata.original_fields` |

### hf/dataset_dict#hf

- Kind: `hf_dataset_dict`
- Unified output: `datasets/processed/unified/hf__dataset_dict_hf_hf.jsonl`
- Rows normalized: `12964`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (12964) |
| `task` | `<inferred>` (12964), `<inferred:essay_scoring>` (12964) |
| `prompt` | `prompt` (12964) |
| `input` | `text` (12964) |
| `response` | `<inferred>` (12964) |
| `score` | `score` (12964) |
| `rubric` | `<inferred>` (12964) |
| `source` | `source` (12964) |
| `license` | `<inferred>` (12964), `<unknown>` (12964) |
| `split` | `split` (12964) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `prompt` | `prompt` |
| `score` | `score` |
| `source` | `source` |
| `split` | `split` |
| `text` | `input` |

### hf/dataset_dict/dataset_dict.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/hf__dataset_dict__dataset_dict.jsonl`
- Rows normalized: `1`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (1), `<generated>` (1) |
| `task` | `<inferred>` (1), `<inferred:unknown>` (1) |
| `prompt` | `<inferred>` (1) |
| `input` | `<inferred>` (1) |
| `response` | `<inferred>` (1) |
| `score` | `<inferred>` (1) |
| `rubric` | `<inferred>` (1) |
| `source` | `<inferred>` (1), `<case_name>` (1) |
| `license` | `<inferred>` (1), `<unknown>` (1) |
| `split` | `<inferred>` (1) |

| Source field | Mapped to |
|---|---|
| `splits` | `metadata.original_fields` |

### hf/dataset_dict/train/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/hf__dataset_dict__train__dataset_info.jsonl`
- Rows normalized: `1`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (1), `<generated>` (1) |
| `task` | `<inferred>` (1), `<inferred:unknown>` (1) |
| `prompt` | `<inferred>` (1) |
| `input` | `<inferred>` (1) |
| `response` | `<inferred>` (1) |
| `score` | `<inferred>` (1) |
| `rubric` | `<inferred>` (1) |
| `source` | `<inferred>` (1), `<case_name>` (1) |
| `license` | `<inferred>` (1), `<unknown>` (1) |
| `split` | `<inferred>` (1) |

| Source field | Mapped to |
|---|---|
| `citation` | `metadata.original_fields` |
| `description` | `metadata.original_fields` |
| `features` | `metadata.original_fields` |
| `homepage` | `metadata.original_fields` |
| `license` | `metadata.original_fields` |

### hf/dataset_dict/train/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/hf__dataset_dict__train__state.jsonl`
- Rows normalized: `1`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (1), `<generated>` (1) |
| `task` | `<inferred>` (1), `<inferred:unknown>` (1) |
| `prompt` | `<inferred>` (1) |
| `input` | `<inferred>` (1) |
| `response` | `<inferred>` (1) |
| `score` | `<inferred>` (1) |
| `rubric` | `<inferred>` (1) |
| `source` | `<inferred>` (1), `<case_name>` (1) |
| `license` | `<inferred>` (1), `<unknown>` (1) |
| `split` | `<inferred>` (1) |

| Source field | Mapped to |
|---|---|
| `_data_files` | `metadata.original_fields` |
| `_fingerprint` | `metadata.original_fields` |
| `_format_columns` | `metadata.original_fields` |
| `_format_kwargs` | `metadata.original_fields` |
| `_format_type` | `metadata.original_fields` |
| `_output_all_columns` | `metadata.original_fields` |
| `_split` | `metadata.original_fields` |

### raw/asap_aes/.cache/huggingface/trees/a46733395585b56c3bbe88f1957360a632ac3e9e.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__.cache__huggingface__trees__a46733395585b56c3bbe88f1957360a632ac3e9e.jsonl`
- Rows normalized: `1`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (1), `<generated>` (1) |
| `task` | `<inferred>` (1), `<inferred:unknown>` (1) |
| `prompt` | `<inferred>` (1) |
| `input` | `<inferred>` (1) |
| `response` | `<inferred>` (1) |
| `score` | `<inferred>` (1) |
| `rubric` | `<inferred>` (1) |
| `source` | `<inferred>` (1), `<case_name>` (1) |
| `license` | `<inferred>` (1), `<unknown>` (1) |
| `split` | `<inferred>` (1) |

| Source field | Mapped to |
|---|---|
| `files` | `metadata.original_fields` |
| `format_version` | `metadata.original_fields` |

### raw/asap_aes/test_set.tsv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__test_set.jsonl`
- Rows normalized: `4254`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `essay_id` (4254) |
| `task` | `<inferred>` (4254), `<inferred:essay_scoring>` (4254) |
| `prompt` | `essay_set` (4254) |
| `input` | `essay` (4254) |
| `response` | `<inferred>` (4254) |
| `score` | `<inferred>` (4254) |
| `rubric` | `<inferred>` (4254) |
| `source` | `<inferred>` (4254), `<case_name>` (4254) |
| `license` | `<inferred>` (4254), `<unknown>` (4254) |
| `split` | `<inferred>` (4254) |

| Source field | Mapped to |
|---|---|
| `domain1_predictionid` | `metadata.original_fields` |
| `domain2_predictionid` | `metadata.original_fields` |
| `essay` | `input` |
| `essay_id` | `id` |
| `essay_set` | `prompt` |

### raw/asap_aes/training_set_rel3.tsv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__training_set_rel3.jsonl`
- Rows normalized: `12976`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `essay_id` (12976) |
| `task` | `<inferred>` (12976), `<inferred:essay_scoring>` (12976) |
| `prompt` | `essay_set` (12976) |
| `input` | `essay` (12976) |
| `response` | `<inferred>` (12976) |
| `score` | `domain1_score` (12976) |
| `rubric` | `<inferred>` (12976) |
| `source` | `<inferred>` (12976), `<case_name>` (12976) |
| `license` | `<inferred>` (12976), `<unknown>` (12976) |
| `split` | `<inferred>` (12976) |

| Source field | Mapped to |
|---|---|
| `domain1_score` | `score` |
| `domain2_score` | `metadata.original_fields` |
| `essay` | `input` |
| `essay_id` | `id` |
| `essay_set` | `prompt` |
| `rater1_domain1` | `metadata.original_fields` |
| `rater1_domain2` | `metadata.original_fields` |
| `rater1_trait1` | `metadata.original_fields` |
| `rater1_trait2` | `metadata.original_fields` |
| `rater1_trait3` | `metadata.original_fields` |
| `rater1_trait4` | `metadata.original_fields` |
| `rater1_trait5` | `metadata.original_fields` |
| `rater1_trait6` | `metadata.original_fields` |
| `rater2_domain1` | `metadata.original_fields` |
| `rater2_domain2` | `metadata.original_fields` |
| `rater2_trait1` | `metadata.original_fields` |
| `rater2_trait2` | `metadata.original_fields` |
| `rater2_trait3` | `metadata.original_fields` |
| `rater2_trait4` | `metadata.original_fields` |
| `rater2_trait5` | `metadata.original_fields` |
| `rater2_trait6` | `metadata.original_fields` |
| `rater3_domain1` | `metadata.original_fields` |
| `rater3_trait1` | `metadata.original_fields` |
| `rater3_trait2` | `metadata.original_fields` |
| `rater3_trait3` | `metadata.original_fields` |
| `rater3_trait4` | `metadata.original_fields` |
| `rater3_trait5` | `metadata.original_fields` |
| `rater3_trait6` | `metadata.original_fields` |

### raw/asap_aes/valid_sample_submission_1_column.csv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column.jsonl`
- Rows normalized: `4818`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (4818), `<generated>` (4818) |
| `task` | `<inferred>` (4818), `<inferred:unknown>` (4818) |
| `prompt` | `<inferred>` (4818) |
| `input` | `<inferred>` (4818) |
| `response` | `<inferred>` (4818) |
| `score` | `<inferred>` (4818) |
| `rubric` | `<inferred>` (4818) |
| `source` | `<inferred>` (4818), `<case_name>` (4818) |
| `license` | `<inferred>` (4818), `<unknown>` (4818) |
| `split` | `<inferred>` (4818) |

| Source field | Mapped to |
|---|---|
| `predicted_score` | `metadata.original_fields` |

### raw/asap_aes/valid_sample_submission_1_column_no_header.csv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column_no_header.jsonl`
- Rows normalized: `4817`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (4817), `<generated>` (4817) |
| `task` | `<inferred>` (4817), `<inferred:unknown>` (4817) |
| `prompt` | `<inferred>` (4817) |
| `input` | `<inferred>` (4817) |
| `response` | `<inferred>` (4817) |
| `score` | `<inferred>` (4817) |
| `rubric` | `<inferred>` (4817) |
| `source` | `<inferred>` (4817), `<case_name>` (4817) |
| `license` | `<inferred>` (4817), `<unknown>` (4817) |
| `split` | `<inferred>` (4817) |

| Source field | Mapped to |
|---|---|
| `7` | `metadata.original_fields` |

### raw/asap_aes/valid_sample_submission_2_column.csv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__valid_sample_submission_2_column.jsonl`
- Rows normalized: `4818`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (4818), `<generated>` (4818) |
| `task` | `<inferred>` (4818), `<inferred:unknown>` (4818) |
| `prompt` | `<inferred>` (4818) |
| `input` | `<inferred>` (4818) |
| `response` | `<inferred>` (4818) |
| `score` | `<inferred>` (4818) |
| `rubric` | `<inferred>` (4818) |
| `source` | `<inferred>` (4818), `<case_name>` (4818) |
| `license` | `<inferred>` (4818), `<unknown>` (4818) |
| `split` | `<inferred>` (4818) |

| Source field | Mapped to |
|---|---|
| `predicted_score` | `metadata.original_fields` |
| `prediction_id` | `metadata.original_fields` |

### raw/asap_aes/valid_sample_submission_5_column.csv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__valid_sample_submission_5_column.jsonl`
- Rows normalized: `4818`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `essay_id` (4818) |
| `task` | `<inferred>` (4818), `<inferred:unknown>` (4818) |
| `prompt` | `essay_set` (4818) |
| `input` | `<inferred>` (4818) |
| `response` | `<inferred>` (4818) |
| `score` | `<inferred>` (4818) |
| `rubric` | `<inferred>` (4818) |
| `source` | `<inferred>` (4818), `<case_name>` (4818) |
| `license` | `<inferred>` (4818), `<unknown>` (4818) |
| `split` | `<inferred>` (4818) |

| Source field | Mapped to |
|---|---|
| `essay_id` | `id` |
| `essay_set` | `prompt` |
| `essay_weight` | `metadata.original_fields` |
| `predicted_score` | `metadata.original_fields` |
| `prediction_id` | `metadata.original_fields` |

### raw/asap_aes/valid_set.tsv

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/raw__asap_aes__valid_set.jsonl`
- Rows normalized: `4218`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `essay_id` (4218) |
| `task` | `<inferred>` (4218), `<inferred:essay_scoring>` (4218) |
| `prompt` | `essay_set` (4218) |
| `input` | `essay` (4218) |
| `response` | `<inferred>` (4218) |
| `score` | `<inferred>` (4218) |
| `rubric` | `<inferred>` (4218) |
| `source` | `<inferred>` (4218), `<case_name>` (4218) |
| `license` | `<inferred>` (4218), `<unknown>` (4218) |
| `split` | `<inferred>` (4218) |

| Source field | Mapped to |
|---|---|
| `domain1_predictionid` | `metadata.original_fields` |
| `domain2_predictionid` | `metadata.original_fields` |
| `essay` | `input` |
| `essay_id` | `id` |
| `essay_set` | `prompt` |

## Preservation Guarantee

All parsed source keys and values are preserved verbatim under `metadata.original_fields` for every unified row.
Fields not directly mapped to a unified top-level field are listed in `metadata.unmapped_fields`.
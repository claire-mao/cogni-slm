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

- Source cases normalized: `49`
- Total unified rows written: `562856`
- Total parse errors captured (as metadata rows): `2356`
- Per-case unified outputs dir: `datasets/processed/unified`
- Combined unified output: `datasets/processed/unified/unified_all.jsonl`

## Per-Source Field Mapping

### eval/heldout_benchmark.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/eval__heldout_benchmark.jsonl`
- Rows normalized: `18`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `example_id` (18) |
| `task` | `task_mode` (18) |
| `prompt` | `context` (18) |
| `input` | `argument_text` (18) |
| `response` | `<inferred>` (18) |
| `score` | `<inferred>` (18) |
| `rubric` | `rubric_hooks` (18) |
| `source` | `<inferred>` (18), `<case_name>` (18) |
| `license` | `<inferred>` (18), `<unknown>` (18) |
| `split` | `<inferred>` (18) |

| Source field | Mapped to |
|---|---|
| `acceptable_alternative_labels` | `metadata.original_fields` |
| `adversarial_type` | `metadata.original_fields` |
| `argument_text` | `input` |
| `attack_target` | `metadata.original_fields` |
| `context` | `prompt` |
| `dataset_version` | `metadata.original_fields` |
| `difficulty_level` | `metadata.original_fields` |
| `example_id` | `id` |
| `expected_sections` | `metadata.original_fields` |
| `is_adversarial` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `primary_fallacy_label` | `metadata.original_fields` |
| `prohibited_behaviors` | `metadata.original_fields` |
| `required_behaviors` | `metadata.original_fields` |
| `rubric_hooks` | `rubric` |
| `source_id` | `metadata.original_fields` |
| `task_mode` | `task` |
| `taxonomy_version` | `metadata.original_fields` |

### final

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/final.jsonl`
- Rows normalized: `12413`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (12413) |
| `task` | `task` (12413) |
| `prompt` | `prompt` (12413) |
| `input` | `text` (12413) |
| `response` | `<inferred>` (12413) |
| `score` | `label` (12413) |
| `rubric` | `<inferred>` (12413) |
| `source` | `source` (12413) |
| `license` | `<inferred>` (12413), `<unknown>` (12413) |
| `split` | `split` (12413) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `label` | `score` |
| `metadata` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `source` | `source` |
| `split` | `split` |
| `task` | `task` |
| `text` | `input` |

### final/dataset_dict#hf

- Kind: `hf_dataset_dict`
- Unified output: `datasets/processed/unified/final__dataset_dict_hf_hf.jsonl`
- Rows normalized: `12960`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (12960) |
| `task` | `task` (12960) |
| `prompt` | `prompt` (12960) |
| `input` | `text` (12960) |
| `response` | `<inferred>` (12960) |
| `score` | `label` (12960) |
| `rubric` | `<inferred>` (12960) |
| `source` | `source` (12960) |
| `license` | `<inferred>` (12960), `<unknown>` (12960) |
| `split` | `split` (12960) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `label` | `score` |
| `metadata` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `source` | `source` |
| `split` | `split` |
| `task` | `task` |
| `text` | `input` |

### final/dataset_dict/dataset_dict.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__dataset_dict.jsonl`
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

### final/dataset_dict/test/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__test__dataset_info.jsonl`
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
| `builder_name` | `metadata.original_fields` |
| `citation` | `metadata.original_fields` |
| `config_name` | `metadata.original_fields` |
| `dataset_name` | `metadata.original_fields` |
| `dataset_size` | `metadata.original_fields` |
| `description` | `metadata.original_fields` |
| `download_size` | `metadata.original_fields` |
| `features` | `metadata.original_fields` |
| `homepage` | `metadata.original_fields` |
| `license` | `metadata.original_fields` |
| `size_in_bytes` | `metadata.original_fields` |
| `splits` | `metadata.original_fields` |
| `version` | `metadata.original_fields` |

### final/dataset_dict/test/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__test__state.jsonl`
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

### final/dataset_dict/train/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__train__dataset_info.jsonl`
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
| `builder_name` | `metadata.original_fields` |
| `citation` | `metadata.original_fields` |
| `config_name` | `metadata.original_fields` |
| `dataset_name` | `metadata.original_fields` |
| `dataset_size` | `metadata.original_fields` |
| `description` | `metadata.original_fields` |
| `download_size` | `metadata.original_fields` |
| `features` | `metadata.original_fields` |
| `homepage` | `metadata.original_fields` |
| `license` | `metadata.original_fields` |
| `size_in_bytes` | `metadata.original_fields` |
| `splits` | `metadata.original_fields` |
| `version` | `metadata.original_fields` |

### final/dataset_dict/train/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__train__state.jsonl`
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

### final/dataset_dict/validation/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__validation__dataset_info.jsonl`
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
| `builder_name` | `metadata.original_fields` |
| `citation` | `metadata.original_fields` |
| `config_name` | `metadata.original_fields` |
| `dataset_name` | `metadata.original_fields` |
| `dataset_size` | `metadata.original_fields` |
| `description` | `metadata.original_fields` |
| `download_size` | `metadata.original_fields` |
| `features` | `metadata.original_fields` |
| `homepage` | `metadata.original_fields` |
| `license` | `metadata.original_fields` |
| `size_in_bytes` | `metadata.original_fields` |
| `splits` | `metadata.original_fields` |
| `version` | `metadata.original_fields` |

### final/dataset_dict/validation/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/final__dataset_dict__validation__state.jsonl`
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

### final/merged_all.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/final__merged_all.jsonl`
- Rows normalized: `12413`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (12413) |
| `task` | `task` (12413) |
| `prompt` | `prompt` (12413) |
| `input` | `text` (12413) |
| `response` | `<inferred>` (12413) |
| `score` | `label` (12413) |
| `rubric` | `<inferred>` (12413) |
| `source` | `source` (12413) |
| `license` | `<inferred>` (12413), `<unknown>` (12413) |
| `split` | `split` (12413) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `label` | `score` |
| `metadata` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `source` | `source` |
| `split` | `split` |
| `task` | `task` |
| `text` | `input` |

### final/quality_deduped.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/final__quality_deduped.jsonl`
- Rows normalized: `12413`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (12413) |
| `task` | `task` (12413) |
| `prompt` | `prompt` (12413) |
| `input` | `input` (12413) |
| `response` | `<inferred>` (12413) |
| `score` | `score` (12413) |
| `rubric` | `<inferred>` (12413) |
| `source` | `source` (12413) |
| `license` | `license` (12413) |
| `split` | `split` (12413) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `input` | `input` |
| `license` | `license` |
| `metadata` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `quality` | `metadata.original_fields` |
| `response` | `metadata.original_fields` |
| `rubric` | `metadata.original_fields` |
| `score` | `score` |
| `source` | `source` |
| `split` | `split` |
| `task` | `task` |

### final/quality_filtered.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/final__quality_filtered.jsonl`
- Rows normalized: `149598`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (149598) |
| `task` | `task` (149598) |
| `prompt` | `prompt` (149598) |
| `input` | `input` (149598) |
| `response` | `<inferred>` (149598) |
| `score` | `score` (126087), `<inferred>` (23511) |
| `rubric` | `<inferred>` (149598) |
| `source` | `source` (149598) |
| `license` | `license` (149598) |
| `split` | `split` (149598) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `input` | `input` |
| `license` | `license` |
| `metadata` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `quality` | `metadata.original_fields` |
| `response` | `metadata.original_fields` |
| `rubric` | `metadata.original_fields` |
| `score` | `score` |
| `source` | `source` |
| `split` | `split` |
| `task` | `task` |

### final/quality_removed.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/final__quality_removed.jsonl`
- Rows normalized: `44591`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (44591) |
| `task` | `<inferred>` (44591), `<inferred:unknown>` (44591) |
| `prompt` | `<inferred>` (44591) |
| `input` | `<inferred>` (44591) |
| `response` | `<inferred>` (44591) |
| `score` | `<inferred>` (44591) |
| `rubric` | `<inferred>` (44591) |
| `source` | `source` (44591) |
| `license` | `<inferred>` (44591), `<unknown>` (44591) |
| `split` | `<inferred>` (44591) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `overall_quality_score` | `metadata.original_fields` |
| `reason` | `metadata.original_fields` |
| `source` | `source` |

### final/quality_scored.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/final__quality_scored.jsonl`
- Rows normalized: `194189`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (194189) |
| `task` | `task` (194189) |
| `prompt` | `prompt` (177158), `<inferred>` (17031) |
| `input` | `input` (156883), `<inferred>` (37306) |
| `response` | `<inferred>` (194189) |
| `score` | `score` (147236), `<inferred>` (46953) |
| `rubric` | `<inferred>` (194071), `rubric` (118) |
| `source` | `source` (194189) |
| `license` | `license` (194189) |
| `split` | `split` (194189) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `input` | `input` |
| `license` | `license` |
| `metadata` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `quality` | `metadata.original_fields` |
| `response` | `metadata.original_fields` |
| `rubric` | `rubric` |
| `score` | `score` |
| `source` | `source` |
| `split` | `split` |
| `task` | `task` |

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

### processed/golden/golden-20260708T183049Z/audit_traces.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl`
- Rows normalized: `50`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `example_id` (50) |
| `task` | `<inferred>` (50), `<inferred:fallacy_reasoning>` (50) |
| `prompt` | `<inferred>` (50) |
| `input` | `<inferred>` (50) |
| `response` | `<inferred>` (50) |
| `score` | `<inferred>` (50) |
| `rubric` | `<inferred>` (50) |
| `source` | `<inferred>` (50), `<case_name>` (50) |
| `license` | `<inferred>` (50), `<unknown>` (50) |
| `split` | `<inferred>` (50) |

| Source field | Mapped to |
|---|---|
| `critique_scores` | `metadata.original_fields` |
| `dedup_cluster_id` | `metadata.original_fields` |
| `example_id` | `id` |
| `filter_decisions` | `metadata.original_fields` |
| `is_adversarial` | `metadata.original_fields` |
| `is_no_fallacy` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `primary_fallacy_label` | `metadata.original_fields` |

### processed/golden/golden-20260708T183049Z/dataset.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl`
- Rows normalized: `50`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `example_id` (50) |
| `task` | `task_mode` (50) |
| `prompt` | `<inferred>` (50) |
| `input` | `argument_text` (50) |
| `response` | `<inferred>` (50) |
| `score` | `<inferred>` (50) |
| `rubric` | `rubric_hooks` (50) |
| `source` | `<inferred>` (50), `<case_name>` (50) |
| `license` | `<inferred>` (50), `<unknown>` (50) |
| `split` | `split_hint` (50) |

| Source field | Mapped to |
|---|---|
| `acceptable_alternative_labels` | `metadata.original_fields` |
| `adversarial_type` | `metadata.original_fields` |
| `analogy_source_domain` | `metadata.original_fields` |
| `analogy_target_domain` | `metadata.original_fields` |
| `argument_text` | `input` |
| `attack_target` | `metadata.original_fields` |
| `created_at` | `metadata.original_fields` |
| `critic_model_id` | `metadata.original_fields` |
| `critique_scores` | `metadata.original_fields` |
| `dataset_version` | `metadata.original_fields` |
| `decoding_config` | `metadata.original_fields` |
| `dedup_cluster_id` | `metadata.original_fields` |
| `difficulty_level` | `metadata.original_fields` |
| `domain_tag` | `metadata.original_fields` |
| `example_id` | `id` |
| `expected_sections` | `metadata.original_fields` |
| `filter_decisions` | `metadata.original_fields` |
| `generator_model_id` | `metadata.original_fields` |
| `is_adversarial` | `metadata.original_fields` |
| `is_no_fallacy` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `primary_fallacy_label` | `metadata.original_fields` |
| `prohibited_behaviors` | `metadata.original_fields` |
| `prompt_seed` | `metadata.original_fields` |
| `reflection_style_tag` | `metadata.original_fields` |
| `required_behaviors` | `metadata.original_fields` |
| `rubric_hooks` | `rubric` |
| `source_id` | `metadata.original_fields` |
| `split_hint` | `split` |
| `task_mode` | `task` |
| `taxonomy_version` | `metadata.original_fields` |
| `template_id` | `metadata.original_fields` |
| `template_version` | `metadata.original_fields` |
| `updated_at` | `metadata.original_fields` |
| `validation_status` | `metadata.original_fields` |

### processed/golden/golden-20260708T183049Z/manifest.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/processed__golden__golden-20260708T183049Z__manifest.jsonl`
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
| `adversarial_examples` | `metadata.original_fields` |
| `created_at` | `metadata.original_fields` |
| `dataset_name` | `metadata.original_fields` |
| `dataset_version` | `metadata.original_fields` |
| `domain_counts` | `metadata.original_fields` |
| `fallacy_counts` | `metadata.original_fields` |
| `generation_run_id` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `no_fallacy_examples` | `metadata.original_fields` |
| `prompt_bundle_version` | `metadata.original_fields` |
| `reflection_style_counts` | `metadata.original_fields` |
| `snapshot_hash` | `metadata.original_fields` |
| `taxonomy_version` | `metadata.original_fields` |
| `teacher_config_version` | `metadata.original_fields` |
| `total_examples` | `metadata.original_fields` |

### processed/golden/golden-20260708T202613Z/audit_traces.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl`
- Rows normalized: `50`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `example_id` (50) |
| `task` | `<inferred>` (50), `<inferred:fallacy_reasoning>` (50) |
| `prompt` | `<inferred>` (50) |
| `input` | `<inferred>` (50) |
| `response` | `<inferred>` (50) |
| `score` | `<inferred>` (50) |
| `rubric` | `<inferred>` (50) |
| `source` | `<inferred>` (50), `<case_name>` (50) |
| `license` | `<inferred>` (50), `<unknown>` (50) |
| `split` | `<inferred>` (50) |

| Source field | Mapped to |
|---|---|
| `critique_scores` | `metadata.original_fields` |
| `dedup_cluster_id` | `metadata.original_fields` |
| `example_id` | `id` |
| `filter_decisions` | `metadata.original_fields` |
| `is_adversarial` | `metadata.original_fields` |
| `is_no_fallacy` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `primary_fallacy_label` | `metadata.original_fields` |

### processed/golden/golden-20260708T202613Z/dataset.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl`
- Rows normalized: `50`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `example_id` (50) |
| `task` | `task_mode` (50) |
| `prompt` | `<inferred>` (50) |
| `input` | `argument_text` (50) |
| `response` | `<inferred>` (50) |
| `score` | `<inferred>` (50) |
| `rubric` | `rubric_hooks` (50) |
| `source` | `<inferred>` (50), `<case_name>` (50) |
| `license` | `<inferred>` (50), `<unknown>` (50) |
| `split` | `split_hint` (50) |

| Source field | Mapped to |
|---|---|
| `acceptable_alternative_labels` | `metadata.original_fields` |
| `adversarial_type` | `metadata.original_fields` |
| `analogy_source_domain` | `metadata.original_fields` |
| `analogy_target_domain` | `metadata.original_fields` |
| `argument_text` | `input` |
| `attack_target` | `metadata.original_fields` |
| `created_at` | `metadata.original_fields` |
| `critic_model_id` | `metadata.original_fields` |
| `critique_scores` | `metadata.original_fields` |
| `dataset_version` | `metadata.original_fields` |
| `decoding_config` | `metadata.original_fields` |
| `dedup_cluster_id` | `metadata.original_fields` |
| `difficulty_level` | `metadata.original_fields` |
| `domain_tag` | `metadata.original_fields` |
| `example_id` | `id` |
| `expected_sections` | `metadata.original_fields` |
| `filter_decisions` | `metadata.original_fields` |
| `generator_model_id` | `metadata.original_fields` |
| `is_adversarial` | `metadata.original_fields` |
| `is_no_fallacy` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `primary_fallacy_label` | `metadata.original_fields` |
| `prohibited_behaviors` | `metadata.original_fields` |
| `prompt_seed` | `metadata.original_fields` |
| `reflection_style_tag` | `metadata.original_fields` |
| `required_behaviors` | `metadata.original_fields` |
| `rubric_hooks` | `rubric` |
| `source_id` | `metadata.original_fields` |
| `split_hint` | `split` |
| `task_mode` | `task` |
| `taxonomy_version` | `metadata.original_fields` |
| `template_id` | `metadata.original_fields` |
| `template_version` | `metadata.original_fields` |
| `updated_at` | `metadata.original_fields` |
| `validation_status` | `metadata.original_fields` |

### processed/golden/golden-20260708T202613Z/manifest.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/processed__golden__golden-20260708T202613Z__manifest.jsonl`
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
| `adversarial_examples` | `metadata.original_fields` |
| `created_at` | `metadata.original_fields` |
| `dataset_name` | `metadata.original_fields` |
| `dataset_version` | `metadata.original_fields` |
| `domain_counts` | `metadata.original_fields` |
| `fallacy_counts` | `metadata.original_fields` |
| `generation_run_id` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `no_fallacy_examples` | `metadata.original_fields` |
| `prompt_bundle_version` | `metadata.original_fields` |
| `reflection_style_counts` | `metadata.original_fields` |
| `snapshot_hash` | `metadata.original_fields` |
| `taxonomy_version` | `metadata.original_fields` |
| `teacher_config_version` | `metadata.original_fields` |
| `total_examples` | `metadata.original_fields` |

### processed/normalized/all_datasets.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__normalized__all_datasets.jsonl`
- Rows normalized: `22326`
- Parse errors captured: `1178`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (21148), `<inferred>` (1178), `<generated>` (1178) |
| `task` | `task` (21148), `<inferred>` (1178), `<inferred:unknown>` (1178) |
| `prompt` | `prompt` (21148), `<inferred>` (1178) |
| `input` | `text` (21148), `<inferred>` (1178) |
| `response` | `<inferred>` (22326) |
| `score` | `label` (12786), `<inferred>` (9540) |
| `rubric` | `<inferred>` (22326) |
| `source` | `source` (21148), `<inferred>` (1178), `<case_name>` (1178) |
| `license` | `<inferred>` (22326), `<unknown>` (22326) |
| `split` | `<inferred>` (22326) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `label` | `score` |
| `line_number` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `parse_error` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `raw_line` | `metadata.original_fields` |
| `source` | `source` |
| `task` | `task` |
| `text` | `input` |

### processed/normalized/asap2.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__normalized__asap2.jsonl`
- Rows normalized: `0`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<none>` |
| `task` | `<none>` |
| `prompt` | `<none>` |
| `input` | `<none>` |
| `response` | `<none>` |
| `score` | `<none>` |
| `rubric` | `<none>` |
| `source` | `<none>` |
| `license` | `<none>` |
| `split` | `<none>` |

| Source field | Mapped to |
|---|---|

### processed/normalized/asap_aes.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__normalized__asap_aes.jsonl`
- Rows normalized: `22326`
- Parse errors captured: `1178`

| Unified field | Source field usage |
|---|---|
| `id` | `id` (21148), `<inferred>` (1178), `<generated>` (1178) |
| `task` | `task` (21148), `<inferred>` (1178), `<inferred:unknown>` (1178) |
| `prompt` | `prompt` (21148), `<inferred>` (1178) |
| `input` | `text` (21148), `<inferred>` (1178) |
| `response` | `<inferred>` (22326) |
| `score` | `label` (12786), `<inferred>` (9540) |
| `rubric` | `<inferred>` (22326) |
| `source` | `source` (21148), `<inferred>` (1178), `<case_name>` (1178) |
| `license` | `<inferred>` (22326), `<unknown>` (22326) |
| `split` | `<inferred>` (22326) |

| Source field | Mapped to |
|---|---|
| `id` | `id` |
| `label` | `score` |
| `line_number` | `metadata.original_fields` |
| `metadata` | `metadata.original_fields` |
| `parse_error` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `raw_line` | `metadata.original_fields` |
| `source` | `source` |
| `task` | `task` |
| `text` | `input` |

### processed/normalized/persuade2.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__normalized__persuade2.jsonl`
- Rows normalized: `0`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<none>` |
| `task` | `<none>` |
| `prompt` | `<none>` |
| `input` | `<none>` |
| `response` | `<none>` |
| `score` | `<none>` |
| `rubric` | `<none>` |
| `source` | `<none>` |
| `license` | `<none>` |
| `split` | `<none>` |

| Source field | Mapped to |
|---|---|

### processed/normalized/summary.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/processed__normalized__summary.jsonl`
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
| `combined_output` | `metadata.original_fields` |
| `datasets` | `metadata.original_fields` |
| `output_dir` | `metadata.original_fields` |
| `raw_root` | `metadata.original_fields` |

### processed/raw_essays.jsonl

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/processed__raw_essays.jsonl`
- Rows normalized: `0`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<none>` |
| `task` | `<none>` |
| `prompt` | `<none>` |
| `input` | `<none>` |
| `response` | `<none>` |
| `score` | `<none>` |
| `rubric` | `<none>` |
| `source` | `<none>` |
| `license` | `<none>` |
| `split` | `<none>` |

| Source field | Mapped to |
|---|---|

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

### training#hf

- Kind: `hf_dataset_dict`
- Unified output: `datasets/processed/unified/training_hf_hf.jsonl`
- Rows normalized: `12413`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (12413), `<generated>` (12413) |
| `task` | `<inferred>` (12413), `<inferred:essay_scoring>` (12413) |
| `prompt` | `prompt` (12413) |
| `input` | `essay` (12413) |
| `response` | `<inferred>` (12413) |
| `score` | `score` (12413) |
| `rubric` | `<inferred>` (12413) |
| `source` | `<inferred>` (12413), `<case_name>` (12413) |
| `license` | `<inferred>` (12413), `<unknown>` (12413) |
| `split` | `<inferred>` (12413) |

| Source field | Mapped to |
|---|---|
| `essay` | `input` |
| `prompt` | `prompt` |
| `score` | `score` |

### training/dataset_dict.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__dataset_dict.jsonl`
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

### training/test/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__test__dataset_info.jsonl`
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

### training/test/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__test__state.jsonl`
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

### training/train/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__train__dataset_info.jsonl`
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

### training/train/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__train__state.jsonl`
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

### training/validation/dataset_info.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__validation__dataset_info.jsonl`
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

### training/validation/state.json

- Kind: `structured_file`
- Unified output: `datasets/processed/unified/training__validation__state.jsonl`
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

### training_provenance

- Kind: `jsonl`
- Unified output: `datasets/processed/unified/training_provenance.jsonl`
- Rows normalized: `12413`
- Parse errors captured: `0`

| Unified field | Source field usage |
|---|---|
| `id` | `<inferred>` (12413), `<generated>` (12413) |
| `task` | `<inferred>` (12413), `<inferred:unknown>` (12413) |
| `prompt` | `prompt` (12413) |
| `input` | `<inferred>` (12413) |
| `response` | `<inferred>` (12413) |
| `score` | `score` (12413) |
| `rubric` | `<inferred>` (12413) |
| `source` | `<inferred>` (12413), `<case_name>` (12413) |
| `license` | `<inferred>` (12413), `<unknown>` (12413) |
| `split` | `split` (12413) |

| Source field | Mapped to |
|---|---|
| `essay_sha256` | `metadata.original_fields` |
| `example_index` | `metadata.original_fields` |
| `prompt` | `prompt` |
| `score` | `score` |
| `source_records` | `metadata.original_fields` |
| `split` | `split` |

## Preservation Guarantee

All parsed source keys and values are preserved verbatim under `metadata.original_fields` for every unified row.
Fields not directly mapped to a unified top-level field are listed in `metadata.unmapped_fields`.
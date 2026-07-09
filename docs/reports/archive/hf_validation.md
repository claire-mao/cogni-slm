# HF Validation Report

- Datasets root: `/Users/clairemao/Documents/cogni-slm/datasets`
- Dataset cases checked: `15`
- PASS: `9`
- FAIL: `6`

## Case Summary

| Dataset | Status | Splits | Rows |
|---|---|---|---|
| `eval/heldout_benchmark.jsonl` | **PASS** | `train` | `train:18` |
| `final` | **PASS** | `test, train, validation` | `test:1304, train:10365, validation:1291` |
| `final/merged_all.jsonl` | **PASS** | `train` | `train:12960` |
| `final/quality_filtered.jsonl` | **PASS** | `train` | `train:12959` |
| `final/quality_removed.jsonl` | **PASS** | `train` | `train:1` |
| `final/quality_scored.jsonl` | **FAIL** | `train` | `` |
| `processed/golden/golden-20260708T183049Z/audit_traces.jsonl` | **PASS** | `train` | `train:50` |
| `processed/golden/golden-20260708T183049Z/dataset.jsonl` | **PASS** | `train` | `train:50` |
| `processed/golden/golden-20260708T202613Z/audit_traces.jsonl` | **PASS** | `train` | `train:50` |
| `processed/golden/golden-20260708T202613Z/dataset.jsonl` | **PASS** | `train` | `train:50` |
| `processed/normalized/all_datasets.jsonl` | **FAIL** | `train` | `` |
| `processed/normalized/asap2.jsonl` | **FAIL** | `train` | `` |
| `processed/normalized/asap_aes.jsonl` | **FAIL** | `train` | `` |
| `processed/normalized/persuade2.jsonl` | **FAIL** | `train` | `` |
| `processed/raw_essays.jsonl` | **FAIL** | `train` | `` |

## Details

### eval/heldout_benchmark.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/eval/heldout_benchmark.jsonl`
- Feature types by split:
- `train`: `{"acceptable_alternative_labels": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "adversarial_type": {"_type": "Value", "dtype": "string"}, "argument_text": {"_type": "Value", "dtype": "string"}, "attack_target": {"_type": "Value", "dtype": "string"}, "context": {"placeholder": {"_type": "Value", "dtype": "bool"}, "source_dataset": {"_type": "Value", "dtype": "string"}, "source_example_id": {"_type": "Value", "dtype": "string"}}, "dataset_version": {"_type": "Value", "dtype": "string"}, "difficulty_level": {"_type": "Value", "dtype": "string"}, "example_id": {"_type": "Value", "dtype": "string"}, "expected_sections": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "is_adversarial": {"_type": "Value", "dtype": "bool"}, "metadata": {"ambiguity_expected": {"_type": "Value", "dtype": "bool"}, "assumption": {"_type": "Value", "dtype": "string"}, "placeholder": {"_type": "Value", "dtype": "bool"}, "placeholder_reason": {"_type": "Value", "dtype": "string"}}, "primary_fallacy_label": {"_type": "Value", "dtype": "string"}, "prohibited_behaviors": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "required_behaviors": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "rubric_hooks": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "source_id": {"_type": "Value", "dtype": "string"}, "task_mode": {"_type": "Value", "dtype": "string"}, "taxonomy_version": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### final
- Status: **PASS**
- Files:
- `test`: `/Users/clairemao/Documents/cogni-slm/datasets/final/test.jsonl`
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/final/train.jsonl`
- `validation`: `/Users/clairemao/Documents/cogni-slm/datasets/final/validation.jsonl`
- Feature types by split:
- `test`: `{"id": {"_type": "Value", "dtype": "string"}, "label": {"_type": "Value", "dtype": "float64"}, "metadata": {"source_row_index": {"_type": "Value", "dtype": "int64"}, "source_split": {"_type": "Value", "dtype": "string"}}, "prompt": {"_type": "Value", "dtype": "string"}, "source": {"_type": "Value", "dtype": "string"}, "split": {"_type": "Value", "dtype": "string"}, "task": {"_type": "Value", "dtype": "string"}, "text": {"_type": "Value", "dtype": "string"}}`
- `train`: `{"id": {"_type": "Value", "dtype": "string"}, "label": {"_type": "Value", "dtype": "float64"}, "metadata": {"source_row_index": {"_type": "Value", "dtype": "int64"}, "source_split": {"_type": "Value", "dtype": "string"}}, "prompt": {"_type": "Value", "dtype": "string"}, "source": {"_type": "Value", "dtype": "string"}, "split": {"_type": "Value", "dtype": "string"}, "task": {"_type": "Value", "dtype": "string"}, "text": {"_type": "Value", "dtype": "string"}}`
- `validation`: `{"id": {"_type": "Value", "dtype": "string"}, "label": {"_type": "Value", "dtype": "float64"}, "metadata": {"source_row_index": {"_type": "Value", "dtype": "int64"}, "source_split": {"_type": "Value", "dtype": "string"}}, "prompt": {"_type": "Value", "dtype": "string"}, "source": {"_type": "Value", "dtype": "string"}, "split": {"_type": "Value", "dtype": "string"}, "task": {"_type": "Value", "dtype": "string"}, "text": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### final/merged_all.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/final/merged_all.jsonl`
- Feature types by split:
- `train`: `{"id": {"_type": "Value", "dtype": "string"}, "label": {"_type": "Value", "dtype": "float64"}, "metadata": {"source_row_index": {"_type": "Value", "dtype": "int64"}, "source_split": {"_type": "Value", "dtype": "string"}}, "prompt": {"_type": "Value", "dtype": "string"}, "source": {"_type": "Value", "dtype": "string"}, "split": {"_type": "Value", "dtype": "string"}, "task": {"_type": "Value", "dtype": "string"}, "text": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### final/quality_filtered.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/final/quality_filtered.jsonl`
- Feature types by split:
- `train`: `{"id": {"_type": "Value", "dtype": "string"}, "label": {"_type": "Value", "dtype": "float64"}, "metadata": {"source_row_index": {"_type": "Value", "dtype": "int64"}, "source_split": {"_type": "Value", "dtype": "string"}}, "prompt": {"_type": "Value", "dtype": "string"}, "quality": {"duplicate_probability": {"_type": "Value", "dtype": "float64"}, "estimated_usefulness": {"_type": "Value", "dtype": "float64"}, "language_quality": {"_type": "Value", "dtype": "float64"}, "length_score": {"_type": "Value", "dtype": "float64"}, "missing_metadata_count": {"_type": "Value", "dtype": "int64"}, "missing_metadata_fields": {"_type": "List", "feature": {"_type": "Value", "dtype": "null"}}, "missing_metadata_score": {"_type": "Value", "dtype": "float64"}, "ocr_quality": {"_type": "Value", "dtype": "float64"}, "overall_quality_score": {"_type": "Value", "dtype": "float64"}, "readability": {"_type": "Value", "dtype": "float64"}}, "source": {"_type": "Value", "dtype": "string"}, "split": {"_type": "Value", "dtype": "string"}, "task": {"_type": "Value", "dtype": "string"}, "text": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### final/quality_removed.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/final/quality_removed.jsonl`
- Feature types by split:
- `train`: `{"id": {"_type": "Value", "dtype": "string"}, "label": {"_type": "Value", "dtype": "float64"}, "metadata": {"source_row_index": {"_type": "Value", "dtype": "int64"}, "source_split": {"_type": "Value", "dtype": "string"}}, "prompt": {"_type": "Value", "dtype": "string"}, "quality": {"duplicate_probability": {"_type": "Value", "dtype": "float64"}, "estimated_usefulness": {"_type": "Value", "dtype": "float64"}, "language_quality": {"_type": "Value", "dtype": "float64"}, "length_score": {"_type": "Value", "dtype": "float64"}, "missing_metadata_count": {"_type": "Value", "dtype": "int64"}, "missing_metadata_fields": {"_type": "List", "feature": {"_type": "Value", "dtype": "null"}}, "missing_metadata_score": {"_type": "Value", "dtype": "float64"}, "ocr_quality": {"_type": "Value", "dtype": "float64"}, "overall_quality_score": {"_type": "Value", "dtype": "float64"}, "readability": {"_type": "Value", "dtype": "float64"}, "removal_reasons": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}}, "source": {"_type": "Value", "dtype": "string"}, "split": {"_type": "Value", "dtype": "string"}, "task": {"_type": "Value", "dtype": "string"}, "text": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### final/quality_scored.jsonl
- Status: **FAIL**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/final/quality_scored.jsonl`
- Feature types by split:
- None
- Errors:
- DatasetGenerationError: An error occurred while generating the dataset | cause: Couldn't cast array of type
struct<length_score: double, language_quality: double, ocr_quality: double, duplicate_probability: double, missing_metadata_score: double, missing_metadata_count: int64, missing_metadata_fields: list<item: null>, readability: double, estimated_usefulness: double, overall_quality_score: double, removal_reasons: list<item: string>>
to
{'length_score': Value('float64'), 'language_quality': Value('float64'), 'ocr_quality': Value('float64'), 'duplicate_probability': Value('float64'), 'missing_metadata_score': Value('float64'), 'missing_metadata_count': Value('int64'), 'missing_metadata_fields': List(Value('null')), 'readability': Value('float64'), 'estimated_usefulness': Value('float64'), 'overall_quality_score': Value('float64')}

### processed/golden/golden-20260708T183049Z/audit_traces.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/golden/golden-20260708T183049Z/audit_traces.jsonl`
- Feature types by split:
- `train`: `{"critique_scores": {"overall": {"_type": "Value", "dtype": "float64"}}, "dedup_cluster_id": {"_type": "Value", "dtype": "null"}, "example_id": {"_type": "Value", "dtype": "string"}, "filter_decisions": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "is_adversarial": {"_type": "Value", "dtype": "bool"}, "is_no_fallacy": {"_type": "Value", "dtype": "bool"}, "metadata": {"_type": "Json"}, "primary_fallacy_label": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### processed/golden/golden-20260708T183049Z/dataset.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/golden/golden-20260708T183049Z/dataset.jsonl`
- Feature types by split:
- `train`: `{"acceptable_alternative_labels": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "adversarial_type": {"_type": "Value", "dtype": "string"}, "analogy_source_domain": {"_type": "Value", "dtype": "string"}, "analogy_target_domain": {"_type": "Value", "dtype": "string"}, "argument_text": {"_type": "Value", "dtype": "string"}, "attack_target": {"_type": "Value", "dtype": "string"}, "created_at": {"_type": "Value", "dtype": "string"}, "critic_model_id": {"_type": "Value", "dtype": "string"}, "critique_scores": {"overall": {"_type": "Value", "dtype": "float64"}}, "dataset_version": {"_type": "Value", "dtype": "string"}, "decoding_config": {"strategy": {"_type": "Value", "dtype": "string"}}, "dedup_cluster_id": {"_type": "Value", "dtype": "null"}, "difficulty_level": {"_type": "Value", "dtype": "string"}, "domain_tag": {"_type": "Value", "dtype": "string"}, "example_id": {"_type": "Value", "dtype": "string"}, "expected_sections": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "filter_decisions": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "generator_model_id": {"_type": "Value", "dtype": "string"}, "is_adversarial": {"_type": "Value", "dtype": "bool"}, "is_no_fallacy": {"_type": "Value", "dtype": "bool"}, "metadata": {"_type": "Json"}, "primary_fallacy_label": {"_type": "Value", "dtype": "string"}, "prohibited_behaviors": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "prompt_seed": {"_type": "Value", "dtype": "int64"}, "reflection_style_tag": {"_type": "Value", "dtype": "string"}, "required_behaviors": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "rubric_hooks": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "source_id": {"_type": "Value", "dtype": "string"}, "split_hint": {"_type": "Value", "dtype": "string"}, "task_mode": {"_type": "Value", "dtype": "string"}, "taxonomy_version": {"_type": "Value", "dtype": "string"}, "template_id": {"_type": "Value", "dtype": "string"}, "template_version": {"_type": "Value", "dtype": "string"}, "updated_at": {"_type": "Value", "dtype": "string"}, "validation_status": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### processed/golden/golden-20260708T202613Z/audit_traces.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/golden/golden-20260708T202613Z/audit_traces.jsonl`
- Feature types by split:
- `train`: `{"critique_scores": {"overall": {"_type": "Value", "dtype": "float64"}}, "dedup_cluster_id": {"_type": "Value", "dtype": "null"}, "example_id": {"_type": "Value", "dtype": "string"}, "filter_decisions": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "is_adversarial": {"_type": "Value", "dtype": "bool"}, "is_no_fallacy": {"_type": "Value", "dtype": "bool"}, "metadata": {"_type": "Json"}, "primary_fallacy_label": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### processed/golden/golden-20260708T202613Z/dataset.jsonl
- Status: **PASS**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/golden/golden-20260708T202613Z/dataset.jsonl`
- Feature types by split:
- `train`: `{"acceptable_alternative_labels": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "adversarial_type": {"_type": "Value", "dtype": "string"}, "analogy_source_domain": {"_type": "Value", "dtype": "string"}, "analogy_target_domain": {"_type": "Value", "dtype": "string"}, "argument_text": {"_type": "Value", "dtype": "string"}, "attack_target": {"_type": "Value", "dtype": "string"}, "created_at": {"_type": "Value", "dtype": "string"}, "critic_model_id": {"_type": "Value", "dtype": "string"}, "critique_scores": {"overall": {"_type": "Value", "dtype": "float64"}}, "dataset_version": {"_type": "Value", "dtype": "string"}, "decoding_config": {"strategy": {"_type": "Value", "dtype": "string"}}, "dedup_cluster_id": {"_type": "Value", "dtype": "null"}, "difficulty_level": {"_type": "Value", "dtype": "string"}, "domain_tag": {"_type": "Value", "dtype": "string"}, "example_id": {"_type": "Value", "dtype": "string"}, "expected_sections": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "filter_decisions": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "generator_model_id": {"_type": "Value", "dtype": "string"}, "is_adversarial": {"_type": "Value", "dtype": "bool"}, "is_no_fallacy": {"_type": "Value", "dtype": "bool"}, "metadata": {"_type": "Json"}, "primary_fallacy_label": {"_type": "Value", "dtype": "string"}, "prohibited_behaviors": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "prompt_seed": {"_type": "Value", "dtype": "int64"}, "reflection_style_tag": {"_type": "Value", "dtype": "string"}, "required_behaviors": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "rubric_hooks": {"_type": "List", "feature": {"_type": "Value", "dtype": "string"}}, "source_id": {"_type": "Value", "dtype": "string"}, "split_hint": {"_type": "Value", "dtype": "string"}, "task_mode": {"_type": "Value", "dtype": "string"}, "taxonomy_version": {"_type": "Value", "dtype": "string"}, "template_id": {"_type": "Value", "dtype": "string"}, "template_version": {"_type": "Value", "dtype": "string"}, "updated_at": {"_type": "Value", "dtype": "string"}, "validation_status": {"_type": "Value", "dtype": "string"}}`
- Errors:
- None

### processed/normalized/all_datasets.jsonl
- Status: **FAIL**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/normalized/all_datasets.jsonl`
- Feature types by split:
- None
- Errors:
- DatasetGenerationError: An error occurred while generating the dataset | cause: JSON parse error: Invalid encoding in string. in row 32

### processed/normalized/asap2.jsonl
- Status: **FAIL**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/normalized/asap2.jsonl`
- Feature types by split:
- None
- Errors:
- StopIteration: StopIteration()

### processed/normalized/asap_aes.jsonl
- Status: **FAIL**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/normalized/asap_aes.jsonl`
- Feature types by split:
- None
- Errors:
- DatasetGenerationError: An error occurred while generating the dataset | cause: Couldn't cast array of type double to null

### processed/normalized/persuade2.jsonl
- Status: **FAIL**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/normalized/persuade2.jsonl`
- Feature types by split:
- None
- Errors:
- StopIteration: StopIteration()

### processed/raw_essays.jsonl
- Status: **FAIL**
- Files:
- `train`: `/Users/clairemao/Documents/cogni-slm/datasets/processed/raw_essays.jsonl`
- Feature types by split:
- None
- Errors:
- StopIteration: StopIteration()

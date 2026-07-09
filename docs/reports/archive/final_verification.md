# Final Dataset Verification

- Dataset directory: `datasets/final`

## Check Status

- Schema consistency: **PASS**
- Duplicate IDs: **PASS**
- Duplicate text: **PASS**
- Score validity: **PASS**
- Split leakage (ID overlap): **PASS**
- Prompt leakage (prompt overlap): **FAIL**
- Train/test contamination (text overlap): **PASS**
- Corrupted files: **PASS**
- UTF-8 validity: **PASS**
- Hugging Face compatibility (`load_from_disk`): **PASS**

## Split Sizes

| split | rows |
|---|---:|
| train | 9940 |
| validation | 1241 |
| test | 1232 |

## Score Stats

| split | min | max | mean |
|---|---:|---:|---:|
| train | 0.0000 | 55.0000 | 7.0473 |
| validation | 0.0000 | 50.0000 | 6.9444 |
| test | 0.0000 | 60.0000 | 7.2029 |

## Duplicate Summary

| check | value |
|---|---:|
| duplicate IDs within train | 0 |
| duplicate IDs within validation | 0 |
| duplicate IDs within test | 0 |
| duplicate text within train | 0 |
| duplicate text within validation | 0 |
| duplicate text within test | 0 |
| ID overlap train∩validation | 0 |
| ID overlap train∩test | 0 |
| ID overlap validation∩test | 0 |
| text overlap train∩validation | 0 |
| text overlap train∩test | 0 |
| text overlap validation∩test | 0 |

## Prompt Leakage

| check | value |
|---|---:|
| prompt overlap train∩validation | 8 |
| prompt overlap train∩test | 8 |
| prompt overlap validation∩test | 8 |
| test prompts also in train (%) | 100.00 |
| validation prompts also in train (%) | 100.00 |

## File Integrity Details

### train
- Path: `datasets/final/train.jsonl`
- Parsed rows: `9940`
- UTF-8 errors: `0`
- JSON errors: `0`
- Schema/type errors: `0`
- Invalid score rows: `0`
- Invalid split rows: `0`
- Empty text rows: `0`
### validation
- Path: `datasets/final/validation.jsonl`
- Parsed rows: `1241`
- UTF-8 errors: `0`
- JSON errors: `0`
- Schema/type errors: `0`
- Invalid score rows: `0`
- Invalid split rows: `0`
- Empty text rows: `0`
### test
- Path: `datasets/final/test.jsonl`
- Parsed rows: `1232`
- UTF-8 errors: `0`
- JSON errors: `0`
- Schema/type errors: `0`
- Invalid score rows: `0`
- Invalid split rows: `0`
- Empty text rows: `0`

## Hugging Face Compatibility

- Saved/loaded dataset path: `datasets/final/dataset_dict`
- Result: **PASS**
- Message: OK

The dataset is directly loadable via `datasets.load_from_disk()` at the path above.
# Score Analysis

- Datasets discovered: `39`
- Datasets analyzed: `39`
- Skew-flagged datasets: `9`
- Imbalance-flagged datasets: `10`

## Summary Table

| Dataset | Rows | Scored | Missing score | Min | Max | Mean | Median | Std Dev |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/eval__heldout_benchmark.jsonl` | 18 | 0 | 18 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final.jsonl` | 12960 | 12960 | 0 | 0.0000 | 60.0000 | 6.8021 | 3.0000 | 8.9734 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict_hf_hf.jsonl` | 12960 | 12960 | 0 | 0.0000 | 60.0000 | 6.8021 | 3.0000 | 8.9734 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__dataset_dict.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__test__dataset_info.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__test__state.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__train__dataset_info.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__train__state.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__validation__dataset_info.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__validation__state.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__merged_all.jsonl` | 12960 | 12960 | 0 | 0.0000 | 60.0000 | 6.8021 | 3.0000 | 8.9734 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__quality_filtered.jsonl` | 12959 | 12959 | 0 | 0.0000 | 60.0000 | 6.8015 | 3.0000 | 8.9735 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__quality_removed.jsonl` | 1 | 1 | 0 | 15.0000 | 15.0000 | 15.0000 | 15.0000 | 0.0000 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__quality_scored.jsonl` | 12960 | 12960 | 0 | 0.0000 | 60.0000 | 6.8021 | 3.0000 | 8.9734 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__build_summary.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict_hf_hf.jsonl` | 12964 | 12964 | 0 | 0.0000 | 60.0000 | 6.8003 | 3.0000 | 8.9726 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict__dataset_dict.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict__train__dataset_info.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict__train__state.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl` | 50 | 0 | 50 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl` | 50 | 0 | 50 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T183049Z__manifest.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl` | 50 | 0 | 50 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl` | 50 | 0 | 50 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T202613Z__manifest.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__all_datasets.jsonl` | 22326 | 12786 | 9540 | 0.0000 | 60.0000 | 6.8153 | 3.0000 | 8.9970 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__asap2.jsonl` | 0 | 0 | 0 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__asap_aes.jsonl` | 22326 | 12786 | 9540 | 0.0000 | 60.0000 | 6.8153 | 3.0000 | 8.9970 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__persuade2.jsonl` | 0 | 0 | 0 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__summary.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__raw_essays.jsonl` | 0 | 0 | 0 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__.cache__huggingface__trees__a46733395585b56c3bbe88f1957360a632ac3e9e.jsonl` | 1 | 0 | 1 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__test_set.jsonl` | 4254 | 0 | 4254 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__training_set_rel3.jsonl` | 12976 | 12976 | 0 | 0.0000 | 60.0000 | 6.8002 | 3.0000 | 8.9707 |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column.jsonl` | 4818 | 0 | 4818 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column_no_header.jsonl` | 4817 | 0 | 4817 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_2_column.jsonl` | 4818 | 0 | 4818 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_5_column.jsonl` | 4818 | 0 | 4818 | N/A | N/A | N/A | N/A | N/A |
| `/Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_set.jsonl` | 4218 | 0 | 4218 | N/A | N/A | N/A | N/A | N/A |

## Per-Dataset Details

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/eval__heldout_benchmark.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8021`
- Median: `3.0000`
- Standard deviation: `8.9734`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.475).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2829.00).

Histogram:

```text
   0:    417 ####
   1:   1729 #################
   2:   2444 ########################
   3:   2829 ############################
   4:   1424 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    381 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     81 #
  14:    105 #
  15:     86 #
  16:    198 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     69 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict_hf_hf.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8021`
- Median: `3.0000`
- Standard deviation: `8.9734`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.475).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2829.00).

Histogram:

```text
   0:    417 ####
   1:   1729 #################
   2:   2444 ########################
   3:   2829 ############################
   4:   1424 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    381 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     81 #
  14:    105 #
  15:     86 #
  16:    198 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     69 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__dataset_dict.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__test__dataset_info.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__test__state.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__train__dataset_info.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__train__state.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__validation__dataset_info.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__dataset_dict__validation__state.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__merged_all.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8021`
- Median: `3.0000`
- Standard deviation: `8.9734`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.475).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2829.00).

Histogram:

```text
   0:    417 ####
   1:   1729 #################
   2:   2444 ########################
   3:   2829 ############################
   4:   1424 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    381 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     81 #
  14:    105 #
  15:     86 #
  16:    198 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     69 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__quality_filtered.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8015`
- Median: `3.0000`
- Standard deviation: `8.9735`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.476).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2829.00).

Histogram:

```text
   0:    417 ####
   1:   1729 #################
   2:   2444 ########################
   3:   2829 ############################
   4:   1424 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    381 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     81 #
  14:    105 #
  15:     85 #
  16:    198 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     69 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__quality_removed.jsonl

- Minimum score: `15.0000`
- Maximum score: `15.0000`
- Mean: `15.0000`
- Median: `15.0000`
- Standard deviation: `0.0000`
- Missing score ranges: No missing integer scores in [15, 15].
- Skew analysis: Insufficient samples (<3).
- Class imbalance: Severe imbalance (majority_share=1.000, max/min_count_ratio=1.00).

Histogram:

```text
  15:      1 ############################
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/final__quality_scored.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8021`
- Median: `3.0000`
- Standard deviation: `8.9734`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.475).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2829.00).

Histogram:

```text
   0:    417 ####
   1:   1729 #################
   2:   2444 ########################
   3:   2829 ############################
   4:   1424 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    381 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     81 #
  14:    105 #
  15:     86 #
  16:    198 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     69 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__build_summary.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict_hf_hf.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8003`
- Median: `3.0000`
- Standard deviation: `8.9726`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.476).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2829.00).

Histogram:

```text
   0:    418 ####
   1:   1731 #################
   2:   2445 ########################
   3:   2829 ############################
   4:   1424 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    381 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     81 #
  14:    105 #
  15:     86 #
  16:    198 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     69 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict__dataset_dict.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict__train__dataset_info.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/hf__dataset_dict__train__state.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T183049Z__audit_traces.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T183049Z__dataset.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T183049Z__manifest.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T202613Z__audit_traces.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T202613Z__dataset.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__golden__golden-20260708T202613Z__manifest.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__all_datasets.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8153`
- Median: `3.0000`
- Standard deviation: `8.9970`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.477).
- Class imbalance: Severe imbalance (majority_share=0.217, max/min_count_ratio=2773.00).

Histogram:

```text
   0:    417 ####
   1:   1716 #################
   2:   2381 ########################
   3:   2773 ############################
   4:   1419 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    379 ####
  10:    372 ####
  11:    163 ##
  12:    132 #
  13:     80 #
  14:    105 #
  15:     85 #
  16:    195 ##
  17:    156 ##
  18:    116 #
  19:     84 #
  20:     99 #
  21:     67 #
  22:     61 #
  23:     51 #
  24:     92 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__asap2.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__asap_aes.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8153`
- Median: `3.0000`
- Standard deviation: `8.9970`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.477).
- Class imbalance: Severe imbalance (majority_share=0.217, max/min_count_ratio=2773.00).

Histogram:

```text
   0:    417 ####
   1:   1716 #################
   2:   2381 ########################
   3:   2773 ############################
   4:   1419 ##############
   5:     95 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    379 ####
  10:    372 ####
  11:    163 ##
  12:    132 #
  13:     80 #
  14:    105 #
  15:     85 #
  16:    195 ##
  17:    156 ##
  18:    116 #
  19:     84 #
  20:     99 #
  21:     67 #
  22:     61 #
  23:     51 #
  24:     92 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__persuade2.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__normalized__summary.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/processed__raw_essays.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__.cache__huggingface__trees__a46733395585b56c3bbe88f1957360a632ac3e9e.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__test_set.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__training_set_rel3.jsonl

- Minimum score: `0.0000`
- Maximum score: `60.0000`
- Mean: `6.8002`
- Median: `3.0000`
- Standard deviation: `8.9707`
- Missing score ranges: Missing integer ranges within [0, 60]: 51-54, 56-59
- Skew analysis: Right-skewed (skewness=2.475).
- Class imbalance: Severe imbalance (majority_share=0.218, max/min_count_ratio=2830.00).

Histogram:

```text
   0:    418 ####
   1:   1736 #################
   2:   2445 ########################
   3:   2830 ############################
   4:   1424 ##############
   5:     96 #
   6:    137 #
   7:    163 ##
   8:    737 #######
   9:    383 ####
  10:    372 ####
  11:    165 ##
  12:    133 #
  13:     82 #
  14:    105 #
  15:     86 #
  16:    199 ##
  17:    160 ##
  18:    118 #
  19:     88 #
  20:    103 #
  21:     70 #
  22:     63 #
  23:     53 #
  24:     99 #
  25:      5 #
  26:      4 #
  27:      6 #
  28:     11 #
  29:      8 #
  30:     49 #
  31:     34 #
  32:     37 #
  33:     32 #
  34:     39 #
  35:     47 #
  36:     65 #
  37:     39 #
  38:     20 #
  39:      8 #
  40:    161 ##
  41:     22 #
  42:     23 #
  43:     15 #
  44:     14 #
  45:     31 #
  46:     13 #
  47:      7 #
  48:      3 #
  49:      2 #
  50:     13 #
  55:      2 #
  60:      1 #
```

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_1_column_no_header.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_2_column.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_sample_submission_5_column.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

### /Users/clairemao/Documents/cogni-slm/datasets/processed/unified/raw__asap_aes__valid_set.jsonl

- Minimum score: `N/A`
- Maximum score: `N/A`
- Mean: `N/A`
- Median: `N/A`
- Standard deviation: `N/A`
- Missing score ranges: No numeric scores.
- Skew analysis: No numeric scores.
- Class imbalance: No numeric scores.

Histogram:

- No numeric score histogram available.

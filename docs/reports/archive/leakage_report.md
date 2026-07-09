# Leakage Report

- Generated: `2026-07-09T01:36:43.814175+00:00`
- Scope: `datasets/final/train.jsonl`, `datasets/final/validation.jsonl`, `datasets/final/test.jsonl`
- Semantic model: `/Users/clairemao/.cache/huggingface/hub/models--sentence-transformers--clip-ViT-B-32/snapshots/327ab6726d33c0e22f920c83f2ff9e4bd38ca37f/0_CLIPModel` (CLIP text embeddings via `transformers`)

## Dataset Summary

| split | rows | unique_ids | unique_prompts | unique_sources |
|---|---:|---:|---:|---:|
| `train` | 9940 | 9940 | 8 | 1 |
| `validation` | 1241 | 1241 | 8 | 1 |
| `test` | 1232 | 1232 | 8 | 1 |

## Duplicate Essays (Exact)

- Cross-split duplicate essay groups: `0`
- Cross-split duplicate essay rows involved: `0`
- Within-split duplicate essay rows involved:
  - `train`: `0`
  - `validation`: `0`
  - `test`: `0`

## Duplicate IDs (Exact)

- Cross-split duplicate ID groups: `0`
- Cross-split duplicate ID rows involved: `0`
- Within-split duplicate ID rows involved:
  - `train`: `0`
  - `validation`: `0`
  - `test`: `0`

## Prompt Leakage

- `train` vs `validation`: overlap `8` / `8` and `8`
- `test` vs `train`: overlap `8` / `8` and `8`
- `test` vs `validation`: overlap `8` / `8` and `8`
- Prompts are mostly numeric IDs (`8/8`), so paraphrase-of-prompt detection is not meaningful.

## Source Leakage

| split | source distribution |
|---|---|
| `train` | asap_aes:9940 |
| `validation` | asap_aes:1241 |
| `test` | asap_aes:1232 |

- `train` vs `validation` shared sources: `['asap_aes']`
- `test` vs `train` shared sources: `['asap_aes']`
- `test` vs `validation` shared sources: `['asap_aes']`

## Split Contamination (Semantic Similarity)

| direction | mean | median | p95 | max | rate >=0.90 | rate >=0.92 | all pairs >=0.92 | all pairs >=0.95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `train->validation` | 0.9216 | 0.9281 | 0.9688 | 1.0000 | 76.25% | 59.01% | 91125 | 12146 |
| `validation->train` | 0.9353 | 0.9402 | 0.9757 | 1.0000 | 87.51% | 73.33% | 91125 | 12146 |
| `train->test` | 0.9214 | 0.9273 | 0.9689 | 0.9909 | 76.38% | 58.22% | 81588 | 10767 |
| `test->train` | 0.9339 | 0.9390 | 0.9753 | 0.9909 | 86.36% | 72.24% | 81588 | 10767 |
| `validation->test` | 0.9216 | 0.9270 | 0.9701 | 0.9961 | 76.39% | 57.86% | 10431 | 1494 |
| `test->validation` | 0.9198 | 0.9250 | 0.9691 | 0.9961 | 74.43% | 55.52% | 10431 | 1494 |

## Near-Duplicate Essays (Semantic)

- Threshold used: cosine >= `0.95`
- `validation->train` near-duplicate nearest-neighbor pairs: `446`
- `test->train` near-duplicate nearest-neighbor pairs: `433`
- `validation->test` near-duplicate nearest-neighbor pairs: `305`

| direction | left_id | right_id | left_prompt | right_prompt | cosine | lexical_jaccard |
|---|---|---|---|---|---:|---:|
| `validation->test` | `15273` | `15645` | `6` | `6` | 0.9961 | 0.4182 |
| `test->train` | `16188` | `16065` | `6` | `6` | 0.9839 | 0.3333 |
| `test->train` | `9821` | `9578` | `4` | `4` | 0.9834 | 0.3067 |
| `validation->train` | `15695` | `16100` | `6` | `6` | 0.9800 | 0.3265 |
| `validation->train` | `3242` | `3503` | `2` | `2` | 0.9796 | 0.1688 |
| `validation->train` | `16145` | `15746` | `6` | `6` | 0.9793 | 0.4539 |
| `test->train` | `15346` | `15856` | `6` | `6` | 0.9775 | 0.2891 |
| `validation->test` | `13583` | `12653` | `5` | `5` | 0.9763 | 0.3964 |
| `validation->test` | `3495` | `3647` | `2` | `2` | 0.9753 | 0.3266 |
| `test->train` | `10626` | `9403` | `4` | `4` | 0.9744 | 0.3238 |
| `test->train` | `12374` | `12544` | `5` | `5` | 0.9738 | 0.2263 |
| `validation->train` | `3270` | `3378` | `2` | `2` | 0.9723 | 0.2110 |
| `validation->test` | `15928` | `15533` | `6` | `6` | 0.9701 | 0.2183 |
| `validation->train` | `3442` | `4669` | `2` | `2` | 0.9689 | 0.3038 |
| `test->train` | `12318` | `13525` | `5` | `5` | 0.9686 | 0.2727 |
| `validation->test` | `15441` | `15450` | `6` | `6` | 0.9680 | 0.1765 |
| `validation->train` | `3401` | `4770` | `2` | `2` | 0.9677 | 0.2900 |
| `validation->train` | `15966` | `16336` | `6` | `6` | 0.9673 | 0.3761 |
| `validation->test` | `3270` | `4269` | `2` | `2` | 0.9664 | 0.2233 |
| `validation->test` | `15695` | `15711` | `6` | `6` | 0.9661 | 0.2680 |
| `validation->test` | `3553` | `4103` | `2` | `2` | 0.9658 | 0.2040 |
| `validation->train` | `4352` | `4507` | `2` | `2` | 0.9652 | 0.2135 |
| `validation->train` | `15441` | `16306` | `6` | `6` | 0.9647 | 0.2165 |
| `test->train` | `16089` | `15467` | `6` | `6` | 0.9644 | 0.2727 |
| `validation->test` | `3401` | `3647` | `2` | `2` | 0.9642 | 0.3046 |
| `validation->train` | `16431` | `16036` | `6` | `6` | 0.9633 | 0.1980 |
| `test->train` | `3046` | `3816` | `2` | `2` | 0.9628 | 0.2542 |
| `test->train` | `4122` | `3078` | `2` | `2` | 0.9625 | 0.2806 |
| `test->train` | `3699` | `3545` | `2` | `2` | 0.9621 | 0.1406 |
| `validation->test` | `16402` | `16188` | `6` | `6` | 0.9620 | 0.2147 |

## Paraphrased Duplicates (High Semantic, Low Lexical)

- Rule: cosine >= `0.92` and token Jaccard <= `0.35`
- Candidate paraphrased duplicate nearest-neighbor pairs: `14382`

| direction | left_id | right_id | left_prompt | right_prompt | cosine | lexical_jaccard |
|---|---|---|---|---|---:|---:|
| `train->validation` | `4014` | `3836` | `2` | `2` | 1.0000 | 0.2492 |
| `train->validation` | `3370` | `3836` | `2` | `2` | 1.0000 | 0.2694 |
| `validation->train` | `3836` | `3370` | `2` | `2` | 1.0000 | 0.2694 |
| `train->validation` | `4479` | `3836` | `2` | `2` | 1.0000 | 0.2711 |
| `train->validation` | `3832` | `3836` | `2` | `2` | 0.9946 | 0.2751 |
| `train->validation` | `15717` | `15273` | `6` | `6` | 0.9922 | 0.2975 |
| `validation->train` | `15273` | `15717` | `6` | `6` | 0.9922 | 0.2975 |
| `train->validation` | `9914` | `9911` | `4` | `4` | 0.9884 | 0.3014 |
| `validation->train` | `9911` | `9914` | `4` | `4` | 0.9884 | 0.3014 |
| `train->test` | `1628` | `1755` | `1` | `1` | 0.9881 | 0.2331 |
| `test->train` | `1755` | `1628` | `1` | `1` | 0.9881 | 0.2331 |
| `train->validation` | `1414` | `1141` | `1` | `1` | 0.9881 | 0.2786 |
| `validation->train` | `1141` | `1414` | `1` | `1` | 0.9881 | 0.2786 |
| `train->validation` | `15925` | `14836` | `6` | `6` | 0.9880 | 0.2830 |
| `validation->train` | `14836` | `15925` | `6` | `6` | 0.9880 | 0.2830 |
| `train->validation` | `1345` | `1316` | `1` | `1` | 0.9877 | 0.2721 |
| `validation->train` | `1316` | `1345` | `1` | `1` | 0.9877 | 0.2721 |
| `train->test` | `9914` | `9121` | `4` | `4` | 0.9869 | 0.3391 |
| `test->train` | `9121` | `9914` | `4` | `4` | 0.9869 | 0.3391 |
| `train->test` | `21163` | `21364` | `8` | `8` | 0.9869 | 0.2214 |
| `test->train` | `21364` | `21163` | `8` | `8` | 0.9869 | 0.2214 |
| `train->validation` | `16156` | `15273` | `6` | `6` | 0.9861 | 0.3462 |
| `train->test` | `1025` | `1270` | `1` | `1` | 0.9860 | 0.2311 |
| `test->train` | `1270` | `1025` | `1` | `1` | 0.9860 | 0.2311 |
| `train->validation` | `3105` | `3228` | `2` | `2` | 0.9859 | 0.1913 |
| `validation->train` | `3228` | `3105` | `2` | `2` | 0.9859 | 0.1913 |
| `train->test` | `21174` | `20876` | `8` | `8` | 0.9856 | 0.2906 |
| `test->train` | `20876` | `21174` | `8` | `8` | 0.9856 | 0.2906 |
| `train->validation` | `20848` | `20916` | `8` | `8` | 0.9854 | 0.2191 |
| `validation->train` | `20916` | `20848` | `8` | `8` | 0.9854 | 0.2191 |
| `train->test` | `9501` | `10364` | `4` | `4` | 0.9854 | 0.3434 |
| `test->train` | `10364` | `9501` | `4` | `4` | 0.9854 | 0.3434 |
| `train->test` | `14932` | `15483` | `6` | `6` | 0.9851 | 0.2403 |
| `test->train` | `15483` | `14932` | `6` | `6` | 0.9851 | 0.2403 |
| `train->validation` | `9255` | `9911` | `4` | `4` | 0.9847 | 0.3013 |
| `train->test` | `15190` | `15747` | `6` | `6` | 0.9847 | 0.2324 |
| `test->train` | `15747` | `15190` | `6` | `6` | 0.9847 | 0.2324 |
| `train->test` | `20804` | `21109` | `8` | `8` | 0.9844 | 0.2175 |
| `test->train` | `21109` | `20804` | `8` | `8` | 0.9844 | 0.2175 |
| `train->test` | `21253` | `21109` | `8` | `8` | 0.9843 | 0.2254 |

## Metadata Leakage

Metadata fields observed (top):
- `source_case`: present in `12413` rows
- `source_ref`: present in `12413` rows
- `row_index`: present in `12413` rows
- `encoding`: present in `12413` rows
- `score_raw`: present in `12413` rows
- `mapping`: present in `12413` rows
- `unmapped_fields`: present in `12413` rows
- `original_fields`: present in `12413` rows
- `license`: present in `12413` rows

- `metadata.score_raw` present: `12413` rows; equals label in `12413` rows
- `metadata.original_fields.label` present: `12413` rows; equals label in `12413` rows
- `metadata.original_fields.split` present: `12413` rows; equals row split in `12413` rows
- `metadata.source_ref` present: `12413` rows; contains current split name in `12413` rows

Cross-split overlaps in metadata identifiers:
- `source_ref`:
  - `train` vs `validation` overlap: `0`
  - `test` vs `train` overlap: `0`
  - `test` vs `validation` overlap: `0`
- `source_ref_row_index`:
  - `train` vs `validation` overlap: `0`
  - `test` vs `train` overlap: `0`
  - `test` vs `validation` overlap: `0`
- `orig_id`:
  - `train` vs `validation` overlap: `0`
  - `test` vs `train` overlap: `0`
  - `test` vs `validation` overlap: `0`

## Leakage Verdict

- No exact essay text duplication across splits.
- Prompt leakage present (same prompts appear across train/validation/test).
- Strong semantic split contamination detected (high nearest-train similarity for eval splits).
- Metadata contains direct target-label equivalents (`score_raw` / `original_fields.label`) and can leak supervision signal if used as model input.

## Notes

- Dataset files were not modified.
- Semantic similarity uses CLIP text embeddings with max token length 77 (long essays are truncated by the encoder).

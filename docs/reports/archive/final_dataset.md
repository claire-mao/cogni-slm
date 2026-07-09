# Final Dataset Merge Report

- Input root: `/Users/clairemao/Documents/cogni-slm/datasets/hf`
- Output directory: `/Users/clairemao/Documents/cogni-slm/datasets/final`
- Input rows: `12964`
- Dropped missing text: `0`
- Dropped missing score: `0`
- Dropped invalid score: `0`
- Rows kept before dedup: `12964`
- Dedup removed (duplicate ID): `0`
- Dedup removed (duplicate text): `4`
- Final rows: `12960`

## Split Counts

| split | count |
|---|---:|
| train | 10365 |
| validation | 1291 |
| test | 1304 |

## Source Distribution

| source | count |
|---|---:|
| asap_aes | 12960 |

## Task Distribution

| task | count |
|---|---:|
| essay_scoring | 12960 |

## Score Statistics

| split | count | min | max | mean | median |
|---|---:|---:|---:|---:|---:|
| train | 10365 | 0.0000 | 55.0000 | 6.8044 | 3.0000 |
| validation | 1291 | 0.0000 | 50.0000 | 6.7111 | 3.0000 |
| test | 1304 | 0.0000 | 60.0000 | 6.8735 | 3.0000 |

## Notes

- Source field is preserved per record.
- Metadata is preserved and includes source split and row index provenance.
- Splits are assigned using stratification by task and score buckets.
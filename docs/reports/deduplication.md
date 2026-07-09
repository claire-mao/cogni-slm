# Deduplication Report

- Input records: `32493`
- Kept after deduplication: `12413`
- Removed duplicate IDs: `12235`
- Removed duplicate text: `8`
- Skipped invalid rows: `7837`
- Final records materialized: `12413`
- Split assignment: deterministic hash partition (0.8/0.1/0.1)

## Final Split Counts

| split | records |
|---|---:|
| train | 9930 |
| validation | 1241 |
| test | 1242 |

## Label Summary

- Min label: `0.0000`
- Max label: `60.0000`
- Mean label: `7.0524`
# Dataset Validation Report

Configured thresholds: label in [0.0, 60.0], min_words=20, max_words=1500

## Summary

| File | Records | UTF-8 | empty_text | duplicate_id | duplicate_text | invalid_label | label_out_of_range | invalid_utf8 | whitespace_only | extremely_short | extremely_long |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `asap2.jsonl` | 0 | OK | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `asap_aes.jsonl` | 21148 | OK | 0 | 0 | 12 | 8362 | 0 | 0 | 0 | 157 | 0 |
| `persuade2.jsonl` | 0 | OK | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Detailed Findings

### `asap2.jsonl`
- No issues found.

### `asap_aes.jsonl`
- `duplicate_text`: 12
  - dataset-level: Text appears 2 times. Preview: Dear @ORGANIZATION2, @PERCENT1 of @LOCATION3 has possesion of a computer, says @
  - dataset-level: Text appears 2 times. Preview: The features in the story affect the cyclist by not having anything to drink. Th
  - dataset-level: Text appears 2 times. Preview: Snake, heat, hills-all are what the biker had to deal with because of certain se
  - dataset-level: Text appears 3 times. Preview: The author concluded this paragraph in this story because I think that he is tri
  - dataset-level: Text appears 4 times. Preview: NO IMAGE
  - dataset-level: Text appears 2 times. Preview: The author concludes the story with this paragraph for a couple of reasons.
  - dataset-level: Text appears 2 times. Preview: Dear @CAPS1 @CAPS2 Newspaper, Have you ever wanted to see your @CAPS3 that lives
  - dataset-level: Text appears 2 times. Preview: In the essay the features of the setting affected the cyclist. In the begginning
  - dataset-level: Text appears 2 times. Preview: In the setting of the essay; "Rough Road Ahead: Do not Exceed Posted Speed Limit
  - dataset-level: Text appears 2 times. Preview: The author concludes the story with that paragraph because it makes the story lo
  - dataset-level: Text appears 2 times. Preview: The author ends the story with When they come back, Saeng vowed silently, in th
  - dataset-level: Text appears 2 times. Preview: The short story Winter Hibiscus as written by author Minfong Ho, ends with mai
- `invalid_label`: 8362
  - line 1, id=2383: Label is missing.
  - line 2, id=2384: Label is missing.
  - line 3, id=2385: Label is missing.
  - line 4, id=2386: Label is missing.
  - line 5, id=2387: Label is missing.
  - line 6, id=2388: Label is missing.
  - line 7, id=2389: Label is missing.
  - line 8, id=2390: Label is missing.
  - line 9, id=2391: Label is missing.
  - line 10, id=2392: Label is missing.
  - line 11, id=2393: Label is missing.
  - line 12, id=2394: Label is missing.
  - line 13, id=2395: Label is missing.
  - line 14, id=2396: Label is missing.
  - line 15, id=2397: Label is missing.
  - line 16, id=2398: Label is missing.
  - line 17, id=2399: Label is missing.
  - line 18, id=2400: Label is missing.
  - line 19, id=2401: Label is missing.
  - line 20, id=2402: Label is missing.
  - line 21, id=2403: Label is missing.
  - line 22, id=2404: Label is missing.
  - line 23, id=2405: Label is missing.
  - line 24, id=2406: Label is missing.
  - line 25, id=2407: Label is missing.
- `extremely_short_essay`: 157
  - line 381, id=2760: Word count 19 < minimum 20.
  - line 1256, id=8339: Word count 15 < minimum 20.
  - line 1265, id=8349: Word count 19 < minimum 20.
  - line 1319, id=8392: Word count 12 < minimum 20.
  - line 1360, id=8431: Word count 10 < minimum 20.
  - line 1367, id=8439: Word count 13 < minimum 20.
  - line 1382, id=8454: Word count 12 < minimum 20.
  - line 1670, id=8723: Word count 15 < minimum 20.
  - line 1695, id=8745: Word count 16 < minimum 20.
  - line 1699, id=8749: Word count 16 < minimum 20.
  - line 1752, id=8794: Word count 16 < minimum 20.
  - line 1758, id=8801: Word count 10 < minimum 20.
  - line 1769, id=8812: Word count 15 < minimum 20.
  - line 1780, id=8823: Word count 16 < minimum 20.
  - line 1884, id=11292: Word count 17 < minimum 20.
  - line 2130, id=11526: Word count 12 < minimum 20.
  - line 2185, id=11571: Word count 2 < minimum 20.
  - line 2186, id=11572: Word count 13 < minimum 20.
  - line 2205, id=11589: Word count 2 < minimum 20.
  - line 2215, id=11597: Word count 16 < minimum 20.
  - line 2234, id=11610: Word count 12 < minimum 20.
  - line 2243, id=11619: Word count 18 < minimum 20.
  - line 2246, id=11622: Word count 8 < minimum 20.
  - line 2278, id=11650: Word count 14 < minimum 20.
  - line 2384, id=11752: Word count 15 < minimum 20.

### `persuade2.jsonl`
- No issues found.

## Recommendations

1. Drop or repair records flagged for `empty_text`/`whitespace_only_essay`.
2. Resolve `duplicate_id` and consider deduplicating `duplicate_text` entries.
3. Enforce numeric labels and clamp to expected range before model training.
4. Route files with `invalid_utf8` through encoding normalization prior to downstream processing.
5. Review extreme length outliers to avoid truncated supervision and unstable training dynamics.
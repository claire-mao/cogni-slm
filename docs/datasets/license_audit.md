# License Audit

Date: 2026-07-08

## Scope
This audit covers datasets currently represented in the repository:

- `datasets/raw/asap_aes/` (files present)
- `datasets/raw/asap2/` (directory present, no dataset files)
- `datasets/raw/persuade2/` (directory present, no dataset files)
- Derived artifacts in `datasets/processed/`, `datasets/final/`, and `datasets/training/` (all currently sourced from `asap_aes`)

## Method
Cross-checks were performed against official sources only:

- Official dataset website/host page
- Official repository page
- Official license declaration (license file or repository metadata)
- Dataset card (if present)

## Repository Reality Check

- `asap_aes`: present locally (`126` files under `datasets/raw/asap_aes`)
- `asap2`: no local dataset files
- `persuade2`: no local dataset files
- Canonical derived datasets (`datasets/final/*.jsonl`) currently show `source=asap_aes` for all examples

## Official Source Cross-Check

| Dataset | Official website | Official repository | License file / official license declaration | Dataset card status | Audit result |
|---|---|---|---|---|---|
| ASAP-AES | [Kaggle competition page](https://www.kaggle.com/c/asap-aes) | [HF mirror used in repo](https://huggingface.co/datasets/TasfiaS/ASAP-AES/tree/main) | No explicit license file found in local copy; HF page shows no dataset card/license metadata on the mirror page | [No dataset card yet](https://huggingface.co/datasets/TasfiaS/ASAP-AES) | **License/provenance not explicit for redistribution** |
| ASAP 2.0 | [Kaggle AES 2 competition context](https://www.kaggle.com/competitions/learning-agency-lab-automated-essay-scoring-2) | [HF mirror referenced by repo](https://huggingface.co/datasets/jatinmehra/Automated-Essay-Scoring-2.0/tree/main) | HF metadata declares `cc-by-nc-4.0` (non-commercial CC license) | Minimal HF card metadata only | Not locally included yet; if acquired from this source, **non-commercial only** |
| PERSUADE 2.0 | [Official corpus repository](https://github.com/scrosseye/persuade_corpus_2.0) and [Kaggle Feedback Prize context](https://www.kaggle.com/competitions/feedback-prize-effectiveness) | [scrosseye/persuade_corpus_2.0](https://github.com/scrosseye/persuade_corpus_2.0) | Official README states [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en) | No separate HF card in this repo’s local acquisition | Not locally included yet; if acquired from official repo, **non-commercial + share-alike** |

## License Requirement Verification

### ASAP-AES (currently included)

- Redistribution allowed: **UNVERIFIED / DO NOT REDISTRIBUTE**
- Commercial use: **UNVERIFIED / NOT APPROVED**
- Derivative works: **UNVERIFIED**
- Attribution requirement: **UNVERIFIED**

Reason: the repository currently contains this dataset, but no explicit license file is present in the checked-in source files, and the mirror page used in this repo does not provide a complete dataset card/license declaration.
Kaggle-hosted competition datasets are additionally governed by Kaggle platform terms/rules, not an automatically permissive open-data grant: [Kaggle Terms](https://www.kaggle.com/terms).

### ASAP 2.0 (not currently included)

Based on official repository metadata where present (`cc-by-nc-4.0`):

- Redistribution allowed: **Yes, with conditions**
- Commercial use: **No**
- Derivative works: **Yes, non-commercial, with attribution**
- Attribution requirement: **Yes**

Reference: [CC BY-NC 4.0 deed](https://creativecommons.org/licenses/by-nc/4.0/deed.en).

### PERSUADE 2.0 (not currently included)

Based on official repository declaration (`CC BY-NC-SA 4.0`):

- Redistribution allowed: **Yes, with conditions**
- Commercial use: **No**
- Derivative works: **Yes, non-commercial, share-alike required**
- Attribution requirement: **Yes**

Reference: [CC BY-NC-SA 4.0 deed](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en).

## Items Flagged As Not Legally Redistributable (Current Repo State)

1. `datasets/raw/asap_aes/` (license terms not explicitly established in-repo from official source artifacts)
2. All downstream derivatives sourced from ASAP-AES unless/until ASAP-AES redistribution rights are explicitly verified:
   - `datasets/processed/`
   - `datasets/final/`
   - `datasets/training/`

## Cross-Check Against Local Dataset Cards

- `docs/datasets/dataset_cards/asap_aes.md`: too weak for legal release decisions (states terms must be verified; no definitive license).
- `docs/datasets/dataset_cards/asap2.md`: lists unknown status; consistent with local absence, but misses explicit HF `cc-by-nc-4.0` metadata link.
- `docs/datasets/dataset_cards/persuade2.md`: partially aligned, but should explicitly capture official `CC BY-NC-SA 4.0` from the official repository.

## Decision

For public redistribution today:

- **Blocked** for any artifact containing ASAP-AES text until explicit upstream redistribution rights are documented from an official rights holder source.
- ASAP 2.0 and PERSUADE 2.0 are **not present locally**, so they are not currently being redistributed from this repository.

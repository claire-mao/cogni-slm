# Dataset Sources for Cogni Acquisition

This document tracks external essay datasets considered for acquisition in `scripts/download_datasets.py`.

## Summary Table

| Dataset | Homepage | License | Citation | Download Method | Essay Count (if known) | Scoring Labels | Manual Acceptance Required |
|---|---|---|---|---|---:|---|---|
| ASAP-AES | https://huggingface.co/datasets/TasfiaS/ASAP-AES | Unknown on mirror (verify before use) | Kaggle ASAP AES / Hewlett Foundation AES references | Hugging Face mirror (`datasets` + HF snapshot) | Unknown on mirror | Holistic essay score (typically prompt-dependent ranges) | Unknown (depends on mirror accessibility/terms) |
| PERSUADE 2.0 (Feedback Prize corpus context) | https://www.kaggle.com/competitions/feedback-prize-effectiveness | Competition terms / dataset license on Kaggle (verify and accept) | Kaggle Feedback Prize resources and PERSUADE corpus references | Try HF mirrors first; fallback to official Kaggle manual download | Varies by release/split; verify from source | Argument/feedback-related labels, rubric dimensions vary by release | Yes (for official Kaggle access) |
| ASAP 2.0 | https://huggingface.co/datasets/jatinmehra/Automated-Essay-Scoring-2.0 | Unknown on mirror (verify before use) | ASAP 2.0 mirror references | Hugging Face mirror (`datasets` + HF snapshot) | Unknown on mirror | Essay scoring labels (prompt-dependent) | Unknown (depends on mirror accessibility/terms) |

## Candidate Repositories Used by Downloader

- ASAP-AES:
  - `TasfiaS/ASAP-AES`
  - `llm-aes/asap-8-original` (fallback)
- PERSUADE 2.0:
  - `nlpatunt/D_persuade_2`
  - `Ateeqq/PERSUADE-2.0` (fallback)
  - Official fallback: Kaggle Feedback Prize / PERSUADE source
- ASAP 2.0:
  - `jatinmehra/Automated-Essay-Scoring-2.0`

## Important Usage Notes

1. Mirror repositories may not carry complete legal metadata.
2. Before training, verify license and allowed research/commercial usage from the official source.
3. Preserve original files and associated licenses/README files under `datasets/raw/<dataset>/source_files`.

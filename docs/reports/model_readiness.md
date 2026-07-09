# Model Readiness

## Verdict

Current status: **Partially ready for controlled internal experiments**, not yet ready for unrestricted/public training release.

## What Is Ready

- Reproducible dataset build scripts exist.
- Canonical train/validation/test splits are materialized.
- Training scaffold (`training/`) and evaluation harness (`evaluation/`) are implemented.
- Deterministic checks, baseline workflow, and report generation are available.

## What Still Blocks Full Readiness

- License certainty for included upstream data remains unresolved (ASAP-AES lineage risk).
- Dataset diversity is currently narrow (single dominant source in canonical splits).
- Additional leakage/contamination hardening is still recommended.

## Recommended Gate Before Full Training

1. Final license sign-off for all included sources.
2. Freeze Dataset v1 manifest and provenance verification.
3. Run final leakage + split checks on frozen artifact.
4. Execute one controlled training run and compare against baseline gates.

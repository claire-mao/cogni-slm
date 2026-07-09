# Pre-Commit Checklist

- [x] Repository builds from scratch
- [x] Tests passing
- [x] Ruff passing
- [x] Black passing
- [x] HF compatibility
- [x] Dataset reproducibility
- [x] Provenance verified
- [x] Leakage analyzed
- [x] Licensing reviewed
- [x] Documentation complete
- [x] Git clean
- [x] Ready for first commit

## Evidence

- Full rebuild: `python3 scripts/rebuild_all.py` PASS (see `docs/reports/rebuild.md`).
- Regression suite PASS: lint + format + tests + CLI smoke checks (see `docs/reports/final_regression.md`).
- HF validation PASS: `docs/reports/hf_validation.md` (`6/6` cases).
- Provenance and leakage artifacts present:
  - `docs/reports/provenance_repair.md`
  - `docs/reports/archive/leakage_report.md`
- Licensing review present: `docs/reports/license_review.md`.
- Documentation audit PASS: `docs/reports/documentation_audit.md`.
- Git hygiene policy PASS: `docs/reports/git_cleanliness.md`.

## Non-Blocking Caveat

- Rebuilt training dataset currently contains only `train` split rows under current reproducible inputs. This does not block the initial repository commit but should be resolved before first GPU training/evaluation cycle.

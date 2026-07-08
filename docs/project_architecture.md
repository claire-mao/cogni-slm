# Cogni Project Architecture

## 1. Architecture Purpose
Define a production-ready research architecture that:
- Preserves traceability from problem statement -> behavior spec -> implementation.
- Supports iterative experimentation without losing reproducibility.
- Fits the existing repository scaffold.

Primary behavioral authority: `docs/behavior_spec.md`.

## 2. Repository-Aligned Components
- `docs/`: source-of-truth specifications and design records.
- `configs/`: versioned configuration for data processing, evaluation settings, and later training/inference settings.
- `datasets/raw/`: immutable intake data.
- `datasets/processed/`: transformed, cleaned, and schema-validated datasets.
- `datasets/eval/`: held-out evaluation suites, challenge sets, and rubric metadata.
- `src/`: implementation modules (planned) for data contracts, preprocessing, prompting templates, and evaluation logic.
- `scripts/`: reproducible operational entrypoints for data prep and evaluation jobs.
- `tests/`: behavior, schema, and regression tests linked to the behavior spec.
- `models/`: checkpoints/adapters/tokenizers metadata (future phase).
- `outputs/`: run artifacts (logs, reports, analysis exports).

## 3. Planned Module Topology in `src/`
Proposed package layout (no implementation yet):
- `src/cogni/data/`: dataset schemas, loaders, and validators.
- `src/cogni/taxonomy/`: fallacy taxonomy and mapping utilities.
- `src/cogni/behavior/`: output contract, validators, and rule checks.
- `src/cogni/eval/`: scoring adapters and rubric execution.
- `src/cogni/common/`: shared utilities (config loading, typing, I/O helpers).

## 4. Data and Artifact Flow
1. Ingest source artifacts into `datasets/raw/` with provenance metadata.
2. Process and validate into `datasets/processed/` with deterministic transforms.
3. Build evaluation splits/challenge sets in `datasets/eval/`.
4. Run evaluation and analysis pipelines (future) producing files in `outputs/`.
5. Store model artifacts in `models/` once training begins.

Each transformation stage should be reproducible from committed configs and scripts.

## 5. Contracts and Invariants
- Behavior invariant: outputs must satisfy fields and constraints in `docs/behavior_spec.md`.
- Dataset invariant: every processed/eval item must map to a known fallacy taxonomy version.
- Reproducibility invariant: every generated artifact records config version and source revision.
- Testing invariant: regressions must be caught by tests tied to required/prohibited behaviors.

## 6. Configuration Strategy
- Keep configuration declarative and environment-agnostic.
- Separate concerns by config domain:
  - data processing
  - evaluation
  - training/inference (future)
- Maintain stable schema versions to reduce breaking changes across experiments.

## 7. Test Strategy (Pre-ML and Beyond)
- Unit tests for schema and behavior validators.
- Integration tests for data pipeline stage boundaries.
- Golden-case tests for behavior spec compliance with representative prompts/outputs.
- Regression tests for previously fixed failure modes.

## 8. Assumptions To Validate
- A1: Proposed module boundaries are sufficient for clean ownership and low coupling.
- A2: Behavior validator layer can enforce most critical output constraints automatically.
- A3: Dataset provenance metadata is practical to maintain at research velocity.
- A4: Config granularity is fine enough for reproducibility but not burdensome.
- A5: Planned taxonomy module can handle multi-label ambiguity without ad hoc rules.

## 9. Open Decisions
- Exact schema format for behavior outputs (strict JSON vs tagged text).
- Canonical taxonomy versioning policy.
- Choice of experiment tracking mechanism (lightweight file-based vs external service).
- Standardized annotation format for pedagogical quality review.


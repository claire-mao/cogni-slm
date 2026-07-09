# Mock/Stub Cleanup Report

## Scope
This cleanup removed mock inference paths, stub implementations, simulated outputs, and placeholder dataset bootstrapping from the teacher/evaluation/training pipeline code.

## Removed Mock/Stub Behavior

### 1) Label generation pipeline
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/generate_labels.py`
- Removed deterministic mock-output generation.
- `inference_mode` is now production-only (`precomputed`).
- Non-`precomputed` modes now fail with an explicit error.
- Added simulated-dataset row detection to block placeholder/synthetic rows before labeling.

### 2) SFT build and production dataset workflow
- Updated `/Users/clairemao/Documents/cogni-slm/src/data/build_sft_dataset.py`
- Updated `/Users/clairemao/Documents/cogni-slm/src/data/generate_production_dataset.py`
- Removed mock inference mode support from both CLIs.
- Added explicit failures for unsupported modes and missing precomputed teacher outputs.

### 3) Teacher experiment runner
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/run_teacher_experiments.py`
- Removed synthetic dry-run response generator.
- `--dry-run` is now preflight-only (config/plan validation), with no simulated responses.
- Added simulated-dataset row detection for evaluation inputs.

### 4) Teacher benchmark execution runner
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/run_teacher_benchmark_execution.py`
- Clarified prepare-only behavior to avoid placeholder-metric language.
- Added simulated/placeholder benchmark row detection with hard failure.

### 5) Single-teacher experiment path
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/run_teacher_experiment.py`
- Removed fabricated validation payload construction.
- Validation now uses actual model JSON output (`metadata.raw_json_output`) instead of synthesized rubric/reasoning structures.
- Added simulated-dataset row detection.

### 6) Provider normalization and metadata
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/providers/common.py`
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/providers/base.py`
- Removed fake defaults for missing `score`/`confidence` (previously coerced to `0.0`).
- Providers now keep `None` when values are missing.
- Raw parsed JSON is now preserved in metadata (`raw_json_output`) for downstream validation.

### 7) Local teacher inference script
- Updated `/Users/clairemao/Documents/cogni-slm/src/data/run_teacher_inference.py`
- Removed dry-run simulated output mode.
- Local model loading now fails with a clear message when model artifacts are unavailable offline.

### 8) Legacy training-data generator
- Updated `/Users/clairemao/Documents/cogni-slm/src/data/generate_training_dataset.py`
- Removed mock provider default and `NotImplementedError` stub path.
- Integrated production provider abstraction (`teacher.providers`).
- Added strict failure for non-JSON or incomplete provider responses.

### 9) Training scaffold placeholder dataset generation
- Updated `/Users/clairemao/Documents/cogni-slm/src/training/train_unsloth.py`
- Removed automatic placeholder dataset creation.
- Training initialization now requires an existing non-empty real dataset file and fails clearly otherwise.

### 10) Provenance naming cleanup
- Updated `/Users/clairemao/Documents/cogni-slm/src/data/create_provenance_index.py`
- Replaced `heldout_placeholder` identifiers with `heldout_benchmark_internal` to avoid placeholder-labeled dataset classification in provenance metadata.

### 11) Test updates
- Updated `/Users/clairemao/Documents/cogni-slm/tests/test_teacher_generate_labels.py`
- Replaced mock-mode unit test with precomputed-output test to match production-only pipeline behavior.

### 12) Documentation consistency
- Updated `/Users/clairemao/Documents/cogni-slm/src/teacher/README.md`
- Removed instruction text that referenced mock mode for label generation.

## Graceful Failure Guarantees
Where live dependencies are required (API keys/model artifacts), interfaces now fail with explicit, actionable errors instead of returning fake outputs.

## Validation
Test suite executed after cleanup:
- Command: `pytest -q`
- Result: `47 passed in 1.04s`


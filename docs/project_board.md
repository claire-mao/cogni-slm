# Cogni Project Board

## Milestones
- M1 Spec Lock
- M2 Data Pipeline
- M3 Training v1
- M4 Evaluation
- M5 Iteration + Ship

## Tickets
| Ticket | Description | Depends On |
|---|---|---|
| PLN-001 | Finalize strict behavior spec | - |
| PLN-002 | Finalize PRD and success metrics | PLN-001 |
| EVAL-001 | Build deterministic 7-step checker | PLN-001 |
| EVAL-002 | Build LLM-as-judge rubric/runner | PLN-001 |
| EVAL-003 | Baseline prompt-test run and report | EVAL-001,EVAL-002 |
| DATA-001 | Build AP+fallacy labeling candidates | PLN-002 |
| DATA-002 | Filter + dedup + split dataset | DATA-001 |
| DATA-003 | Publish dataset artifact package | DATA-002 |
| TRAIN-001 | Configure QLoRA experiment | DATA-002 |
| TRAIN-002 | Run Colab training v1 | TRAIN-001 |
| TRAIN-003 | Export adapter/model artifacts | TRAIN-002 |
| EVAL-004 | Run tuned-model held-out evaluation | TRAIN-003,EVAL-003 |
| EVAL-005 | Base-vs-tuned comparison report | EVAL-004 |
| ITER-001 | Failure analysis + data fixes | EVAL-005 |
| ITER-002 | Retrain and re-evaluate | ITER-001 |

## Dependencies
- Teacher API credentials + model access.
- Colab GPU runtime for QLoRA.
- Stable held-out benchmark.

## Risks
- Teacher outputs drift from behavior spec.
- Dataset leakage between train and held-out.
- Overfit to template style rather than reasoning.
- Colab runtime interruptions and checkpoint loss.

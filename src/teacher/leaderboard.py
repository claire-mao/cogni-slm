"""Automatic teacher leaderboard from existing experiment outputs.

Reads:
- outputs/teacher_runs/*/responses.jsonl
- outputs/teacher_runs/*/manifest.json
- configs/teacher/teacher_task_suite_v1.json

Computes per-model metrics:
- QWK
- MAE
- rubric adherence
- fallacy F1
- agreement
- consistency
- JSON validity
- hallucination rate (heuristic)
- latency
- cost

No experiments are executed by this module.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .metrics import clamp01, f1_precision_recall, mae, quadratic_weighted_kappa

_UNSUPPORTED_FEEDBACK_PATTERNS = (
    re.compile(r"\byour teacher said\b", re.IGNORECASE),
    re.compile(r"\baccording to (the )?data table\b", re.IGNORECASE),
    re.compile(r"\bas a (?:male|female|student from)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    required_output_fields: tuple[str, ...]


@dataclass(frozen=True)
class GoldSignals:
    gold_score: float | None
    expected_fallacies: tuple[str, ...]


@dataclass(frozen=True)
class LeaderboardRow:
    model: str
    responses: int
    qwk: float | None
    mae: float | None
    rubric_adherence: float
    fallacy_f1: float | None
    agreement: float | None
    consistency: float
    json_validity: float
    hallucination_rate: float
    latency_ms: float | None
    cost_usd: float | None
    rank_score: float
    rank: int


@dataclass(frozen=True)
class LeaderboardResult:
    runs_scanned: int
    responses_loaded: int
    models_ranked: int
    leaderboard: tuple[LeaderboardRow, ...]
    notes: tuple[str, ...]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL row is not object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _normalize_label(value: Any) -> str:
    text = " ".join(str(value or "").strip().lower().replace("-", " ").split())
    if not text:
        return ""
    return text.replace(" ", "_")


def _extract_required_fields(path: Path) -> dict[str, TaskSpec]:
    payload = _read_json(path)
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        return {}

    index: dict[str, TaskSpec] = {}
    for row in tasks:
        if not isinstance(row, dict):
            continue
        task_id = row.get("task_id")
        fields = row.get("required_output_fields")
        if not isinstance(task_id, str) or not task_id.strip():
            continue
        if not isinstance(fields, list):
            fields = []
        index[task_id] = TaskSpec(
            task_id=task_id,
            required_output_fields=tuple(str(item) for item in fields if str(item).strip()),
        )
    return index


def _extract_output_dict(row: dict[str, Any]) -> dict[str, Any] | None:
    value = row.get("raw_json_output")
    if isinstance(value, dict):
        return value

    raw_text = row.get("raw_response_text")
    if isinstance(raw_text, str) and raw_text.strip():
        try:
            payload = json.loads(raw_text)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            return None
    return None


def _extract_score(output_obj: dict[str, Any] | None) -> float | None:
    if not isinstance(output_obj, dict):
        return None
    for key in ("score", "predicted_score", "score_prediction"):
        value = _safe_float(output_obj.get(key))
        if value is not None:
            return value
    inner = output_obj.get("output")
    if isinstance(inner, dict):
        value = _safe_float(inner.get("score", inner.get("predicted_score")))
        if value is not None:
            return value
    return None


def _extract_fallacy(output_obj: dict[str, Any] | None) -> str:
    if not isinstance(output_obj, dict):
        return ""

    direct = output_obj.get("fallacy_label")
    label = _normalize_label(direct)
    if label:
        return label

    fallacies = output_obj.get("fallacies")
    if isinstance(fallacies, dict):
        return _normalize_label(fallacies.get("primary"))
    return ""


def _expected_fallacies_from_row(payload: dict[str, Any]) -> tuple[str, ...]:
    values = payload.get("expected_fallacies")
    if isinstance(values, list):
        labels = sorted(
            {
                _normalize_label(item)
                for item in values
                if _normalize_label(item) and _normalize_label(item) != "none"
            }
        )
        return tuple(labels)

    fallback = payload.get("gold_fallacy_label", payload.get("fallacy_label"))
    label = _normalize_label(fallback)
    if not label or label == "none":
        return ()
    return (label,)


def _load_gold_signals(path: Path) -> dict[str, GoldSignals]:
    if not path.exists():
        return {}
    rows = _read_jsonl(path)
    index: dict[str, GoldSignals] = {}
    for i, payload in enumerate(rows, start=1):
        example_id = str(payload.get("example_id") or payload.get("id") or f"row-{i:06d}").strip()
        score = _safe_float(payload.get("gold_score", payload.get("score", payload.get("label"))))
        fallacies = _expected_fallacies_from_row(payload)
        index[example_id] = GoldSignals(gold_score=score, expected_fallacies=fallacies)
    return index


def _is_hallucination(*, output_obj: dict[str, Any] | None, row: dict[str, Any]) -> bool:
    if not isinstance(output_obj, dict):
        return True
    parse_error = row.get("output_parse_error")
    if isinstance(parse_error, str) and parse_error.strip():
        return True
    text = json.dumps(output_obj, ensure_ascii=False).lower()
    return any(pattern.search(text) for pattern in _UNSUPPORTED_FEEDBACK_PATTERNS)


def _field_present(output_obj: dict[str, Any], field: str) -> bool:
    value = output_obj.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def _rubric_adherence(output_obj: dict[str, Any] | None, task: TaskSpec | None) -> float:
    if not isinstance(output_obj, dict) or task is None:
        return 0.0
    required = task.required_output_fields
    if not required:
        return 0.0
    present = sum(1 for field in required if _field_present(output_obj, field))
    return present / len(required)


def _normalize_efficiency(values: dict[str, float], *, lower_is_better: bool) -> dict[str, float]:
    if not values:
        return {}
    minimum = min(values.values())
    maximum = max(values.values())
    if maximum == minimum:
        return {key: 1.0 for key in values}
    scores: dict[str, float] = {}
    for key, value in values.items():
        norm = (value - minimum) / (maximum - minimum)
        scores[key] = 1.0 - norm if lower_is_better else norm
    return scores


def _group_key(row: dict[str, Any]) -> tuple[str, str, int, float]:
    task_id = str(row.get("task_id", "")).strip()
    example_id = str(row.get("example_id", "")).strip()
    seed = int(row.get("seed", 0) or 0)
    temperature = float(row.get("temperature", 0.0) or 0.0)
    return task_id, example_id, seed, temperature


def _compute_agreement(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    by_group: dict[tuple[str, str, int, float], list[dict[str, Any]]] = {}
    for row in rows:
        by_group.setdefault(_group_key(row), []).append(row)

    per_model_scores: dict[str, list[float]] = {}
    for (task_id, _example_id, _seed, _temperature), group in by_group.items():
        _ = task_id
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                left = group[i]
                right = group[j]
                left_model = str(left.get("model", ""))
                right_model = str(right.get("model", ""))
                left_output = _extract_output_dict(left)
                right_output = _extract_output_dict(right)
                left_score = _extract_score(left_output)
                right_score = _extract_score(right_output)

                numeric_agreement: float | None = None
                if left_score is not None and right_score is not None:
                    numeric_agreement = clamp01(1.0 - min(1.0, abs(left_score - right_score) / 4.0))

                left_fallacy = _extract_fallacy(left_output)
                right_fallacy = _extract_fallacy(right_output)
                label_agreement: float | None = None
                if left_fallacy or right_fallacy:
                    label_agreement = 1.0 if left_fallacy == right_fallacy else 0.0

                components = [
                    value for value in (numeric_agreement, label_agreement) if value is not None
                ]
                if not components:
                    continue
                pair_agreement = mean(components)
                per_model_scores.setdefault(left_model, []).append(pair_agreement)
                per_model_scores.setdefault(right_model, []).append(pair_agreement)

    return {model: (mean(values) if values else None) for model, values in per_model_scores.items()}


def _compute_consistency(rows: list[dict[str, Any]]) -> dict[str, float]:
    by_model_and_case: dict[tuple[str, str, str], list[str]] = {}
    for row in rows:
        model = str(row.get("model", "")).strip()
        task_id = str(row.get("task_id", "")).strip()
        example_id = str(row.get("example_id", "")).strip()
        output_obj = _extract_output_dict(row)
        canonical = (
            json.dumps(output_obj, ensure_ascii=False, sort_keys=True)
            if isinstance(output_obj, dict)
            else ""
        )
        by_model_and_case.setdefault((model, task_id, example_id), []).append(canonical)

    per_model: dict[str, list[float]] = {}
    for (model, _task, _example), outputs in by_model_and_case.items():
        if not outputs:
            continue
        consistent = 1.0 if len(set(outputs)) == 1 else 0.0
        per_model.setdefault(model, []).append(consistent)

    return {model: (mean(values) if values else 0.0) for model, values in per_model.items()}


def compute_leaderboard(
    *,
    runs_root: Path,
    task_config_path: Path,
) -> LeaderboardResult:
    """Compute automatic leaderboard from existing teacher run artifacts."""
    if not runs_root.exists():
        return LeaderboardResult(
            runs_scanned=0,
            responses_loaded=0,
            models_ranked=0,
            leaderboard=(),
            notes=("outputs/teacher_runs directory not found.",),
        )

    task_index = _extract_required_fields(task_config_path)

    runs: list[Path] = [path for path in sorted(runs_root.iterdir()) if path.is_dir()]
    all_rows: list[dict[str, Any]] = []
    notes: list[str] = []
    run_count = 0

    for run_dir in runs:
        manifest_path = run_dir / "manifest.json"
        responses_path = run_dir / "responses.jsonl"
        if not responses_path.exists():
            continue
        run_count += 1
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            manifest = _read_json(manifest_path)
            if bool(manifest.get("dry_run")):
                notes.append(f"Run `{run_dir.name}` is marked dry_run=true.")
        eval_path = manifest.get("evaluation_jsonl")
        gold_index: dict[str, GoldSignals] = {}
        if isinstance(eval_path, str) and eval_path.strip():
            gold_index = _load_gold_signals(Path(eval_path))
            if not gold_index:
                notes.append(f"Run `{run_dir.name}` has no readable gold signals at `{eval_path}`.")
        else:
            notes.append(f"Run `{run_dir.name}` missing evaluation_jsonl in manifest.")

        for row in _read_jsonl(responses_path):
            item = dict(row)
            item["_run_dir"] = run_dir.name
            example_id = str(row.get("example_id", "")).strip()
            gold = gold_index.get(example_id)
            if gold is not None:
                item["_gold_score"] = gold.gold_score
                item["_gold_fallacies"] = list(gold.expected_fallacies)
            else:
                item["_gold_score"] = None
                item["_gold_fallacies"] = []
            all_rows.append(item)

    if not all_rows:
        return LeaderboardResult(
            runs_scanned=run_count,
            responses_loaded=0,
            models_ranked=0,
            leaderboard=(),
            notes=tuple(notes + ["No responses.jsonl rows found under outputs/teacher_runs."]),
        )

    agreement_by_model = _compute_agreement(all_rows)
    consistency_by_model = _compute_consistency(all_rows)

    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in all_rows:
        model = str(row.get("model", "")).strip()
        if not model:
            continue
        by_model.setdefault(model, []).append(row)

    cost_means: dict[str, float] = {}
    latency_means: dict[str, float] = {}
    provisional_rows: list[dict[str, Any]] = []

    for model, rows in sorted(by_model.items()):
        json_valid_values: list[float] = []
        hallucinations: list[float] = []
        rubric_values: list[float] = []
        qwk_true: list[float] = []
        qwk_pred: list[float] = []
        mae_true: list[float] = []
        mae_pred: list[float] = []
        fallacy_expected: list[str] = []
        fallacy_predicted: list[str] = []
        latencies: list[float] = []
        costs: list[float] = []

        for row in rows:
            output_obj = _extract_output_dict(row)
            parse_error = row.get("output_parse_error")
            json_valid = isinstance(output_obj, dict) and not (
                isinstance(parse_error, str) and parse_error
            )
            json_valid_values.append(1.0 if json_valid else 0.0)

            task_id = str(row.get("task_id", "")).strip()
            task = task_index.get(task_id)
            rubric_values.append(_rubric_adherence(output_obj, task))
            hallucinations.append(1.0 if _is_hallucination(output_obj=output_obj, row=row) else 0.0)

            if task_id == "essay_scoring":
                gold_score = _safe_float(row.get("_gold_score"))
                predicted_score = _extract_score(output_obj)
                if gold_score is not None and predicted_score is not None:
                    qwk_true.append(gold_score)
                    qwk_pred.append(predicted_score)
                    mae_true.append(gold_score)
                    mae_pred.append(predicted_score)

            if task_id == "logical_fallacy_identification":
                expected_values = row.get("_gold_fallacies")
                if isinstance(expected_values, list):
                    expected = tuple(
                        _normalize_label(value)
                        for value in expected_values
                        if _normalize_label(value)
                    )
                else:
                    expected = ()
                predicted = _extract_fallacy(output_obj)
                if expected:
                    if predicted:
                        fallacy_expected.extend(expected)
                        fallacy_predicted.append(predicted)
                    else:
                        fallacy_expected.extend(expected)
                        fallacy_predicted.extend([""] * len(expected))

            latency = _safe_float(row.get("latency_ms"))
            if latency is not None:
                latencies.append(latency)
            cost = _safe_float(row.get("estimated_cost_usd"))
            if cost is not None:
                costs.append(cost)

        qwk_value = quadratic_weighted_kappa(qwk_true, qwk_pred) if qwk_true else None
        mae_value = mae(mae_true, mae_pred) if mae_true else None
        if fallacy_expected and fallacy_predicted:
            same_length = len(fallacy_expected) == len(fallacy_predicted)
        else:
            same_length = False
        if same_length:
            precision, recall, f1 = f1_precision_recall(fallacy_expected, fallacy_predicted)
            _ = precision
            _ = recall
            fallacy_f1 = f1
        else:
            fallacy_f1 = None

        latency_mean = mean(latencies) if latencies else None
        cost_mean = mean(costs) if costs else None
        if latency_mean is not None:
            latency_means[model] = latency_mean
        if cost_mean is not None:
            cost_means[model] = cost_mean

        provisional_rows.append(
            {
                "model": model,
                "responses": len(rows),
                "qwk": qwk_value,
                "mae": mae_value,
                "rubric_adherence": mean(rubric_values) if rubric_values else 0.0,
                "fallacy_f1": fallacy_f1,
                "agreement": agreement_by_model.get(model),
                "consistency": consistency_by_model.get(model, 0.0),
                "json_validity": mean(json_valid_values) if json_valid_values else 0.0,
                "hallucination_rate": mean(hallucinations) if hallucinations else 1.0,
                "latency_ms": latency_mean,
                "cost_usd": cost_mean,
            }
        )

    latency_eff = _normalize_efficiency(latency_means, lower_is_better=True)
    cost_eff = _normalize_efficiency(cost_means, lower_is_better=True)

    scored_rows: list[dict[str, Any]] = []
    for row in provisional_rows:
        model = row["model"]
        qwk_component = None
        if row["qwk"] is not None:
            qwk_component = clamp01((float(row["qwk"]) + 1.0) / 2.0)

        mae_component = None
        if row["mae"] is not None:
            mae_component = clamp01(1.0 - min(1.0, float(row["mae"]) / 4.0))

        components = {
            "qwk": qwk_component,
            "mae": mae_component,
            "rubric": float(row["rubric_adherence"]),
            "fallacy_f1": row["fallacy_f1"],
            "agreement": row["agreement"],
            "consistency": float(row["consistency"]),
            "json_validity": float(row["json_validity"]),
            "hallucination_inverse": 1.0 - float(row["hallucination_rate"]),
            "latency_efficiency": latency_eff.get(model),
            "cost_efficiency": cost_eff.get(model),
        }
        weights = {
            "qwk": 0.16,
            "mae": 0.10,
            "rubric": 0.12,
            "fallacy_f1": 0.12,
            "agreement": 0.10,
            "consistency": 0.10,
            "json_validity": 0.10,
            "hallucination_inverse": 0.10,
            "latency_efficiency": 0.05,
            "cost_efficiency": 0.05,
        }
        weighted_values = [
            weights[key] * value for key, value in components.items() if value is not None
        ]
        used_weight = sum(weights[key] for key, value in components.items() if value is not None)
        rank_score = sum(weighted_values) / used_weight if used_weight > 0 else 0.0
        row["rank_score"] = rank_score
        scored_rows.append(row)

    sorted_rows = sorted(
        scored_rows,
        key=lambda item: (
            -float(item["rank_score"]),
            -float(item["json_validity"]),
            float(item["hallucination_rate"]),
        ),
    )

    leaderboard: list[LeaderboardRow] = []
    for index, row in enumerate(sorted_rows, start=1):
        leaderboard.append(
            LeaderboardRow(
                model=str(row["model"]),
                responses=int(row["responses"]),
                qwk=_safe_float(row["qwk"]),
                mae=_safe_float(row["mae"]),
                rubric_adherence=float(row["rubric_adherence"]),
                fallacy_f1=_safe_float(row["fallacy_f1"]),
                agreement=_safe_float(row["agreement"]),
                consistency=float(row["consistency"]),
                json_validity=float(row["json_validity"]),
                hallucination_rate=float(row["hallucination_rate"]),
                latency_ms=_safe_float(row["latency_ms"]),
                cost_usd=_safe_float(row["cost_usd"]),
                rank_score=float(row["rank_score"]),
                rank=index,
            )
        )

    return LeaderboardResult(
        runs_scanned=run_count,
        responses_loaded=len(all_rows),
        models_ranked=len(leaderboard),
        leaderboard=tuple(leaderboard),
        notes=tuple(dict.fromkeys(notes)),
    )


def render_markdown(result: LeaderboardResult) -> str:
    lines = [
        "# Teacher Leaderboard",
        "",
        "## Coverage",
        "",
        f"- runs_scanned: `{result.runs_scanned}`",
        f"- responses_loaded: `{result.responses_loaded}`",
        f"- models_ranked: `{result.models_ranked}`",
        "",
        "## Metrics",
        "",
        "- QWK",
        "- MAE",
        "- rubric adherence",
        "- fallacy F1",
        "- agreement",
        "- consistency",
        "- JSON validity",
        "- hallucination rate",
        "- latency",
        "- cost",
        "",
        "## Ranking",
        "",
        (
            "| rank | model | responses | qwk | mae | rubric | fallacy_f1 | agreement | "
            "consistency | json_validity | hallucination_rate | latency_ms | "
            "cost_usd | rank_score |"
        ),
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in result.leaderboard:
        qwk_text = f"{row.qwk:.4f}" if row.qwk is not None else "n/a"
        mae_text = f"{row.mae:.4f}" if row.mae is not None else "n/a"
        fallacy_text = f"{row.fallacy_f1:.4f}" if row.fallacy_f1 is not None else "n/a"
        agreement_text = f"{row.agreement:.4f}" if row.agreement is not None else "n/a"
        latency_text = f"{row.latency_ms:.2f}" if row.latency_ms is not None else "n/a"
        cost_text = f"{row.cost_usd:.6f}" if row.cost_usd is not None else "n/a"
        lines.append(
            f"| {row.rank} | {row.model} | {row.responses} | {qwk_text} | {mae_text} "
            f"| {row.rubric_adherence:.4f} | {fallacy_text} | {agreement_text} "
            f"| {row.consistency:.4f} | {row.json_validity:.4f} | {row.hallucination_rate:.4f} "
            f"| {latency_text} | {cost_text} | {row.rank_score:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Method Notes",
            "",
            "- `rubric adherence` is task-field coverage on `rubric_adherence` task outputs.",
            (
                "- `agreement` combines pairwise score agreement and fallacy-label "
                "agreement where available."
            ),
            (
                "- `consistency` checks identical canonical JSON for repeated runs of "
                "same model/task/example."
            ),
            (
                "- `hallucination rate` is heuristic and flags parse failures plus known "
                "unsupported-claim patterns."
            ),
            (
                "- Composite `rank_score` normalizes available metrics and reweights if "
                "some metrics are unavailable."
            ),
        ]
    )

    if result.notes:
        lines.extend(["", "## Data Notes", ""])
        for note in result.notes:
            lines.append(f"- {note}")

    return "\n".join(lines) + "\n"


def write_report(path: Path, result: LeaderboardResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(result), encoding="utf-8")
    json_path = path.with_suffix(".json")
    json_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate automatic teacher leaderboard.")
    parser.add_argument("--runs-root", default="outputs/teacher_runs")
    parser.add_argument("--task-config", default="configs/teacher/teacher_task_suite_v1.json")
    parser.add_argument("--report-path", default="docs/reports/teacher_leaderboard.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = compute_leaderboard(
        runs_root=Path(args.runs_root),
        task_config_path=Path(args.task_config),
    )
    write_report(Path(args.report_path), result)
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

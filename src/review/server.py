"""Lightweight human review interface for teacher outputs.

Compares:
- gold answer
- selected teacher answer
- multiple teacher outputs

Reviewer actions:
- accept
- reject
- edit
- flag hallucination
- flag rubric error

Reviews are saved under `datasets/review/`.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import parse


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    parsed = _safe_float(value)
    return int(parsed) if parsed is not None else default


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL row must be object at {path}:{line_number}")
            rows.append(payload)
    return rows


@dataclass(frozen=True)
class TeacherOutput:
    """One teacher response row."""

    model: str
    run_id: str
    task_id: str
    example_id: str
    seed: int
    temperature: float
    prompt_version: str
    confidence: float | None
    output_json: dict[str, Any] | None
    output_parse_error: str | None
    raw_response_text: str | None
    raw_row: dict[str, Any]


class ReviewStore:
    """Persist review actions under datasets/review."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.reviews_path = self.root / "reviews.jsonl"
        self.latest_path = self.root / "latest_reviews.json"

    def _load_latest_map(self) -> dict[str, dict[str, Any]]:
        if not self.latest_path.exists():
            return {}
        payload = _read_json(self.latest_path)
        latest: dict[str, dict[str, Any]] = {}
        for key, value in payload.items():
            if isinstance(key, str) and isinstance(value, dict):
                latest[key] = value
        return latest

    def save_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        decision = _normalize_text(payload.get("decision")).lower()
        if decision not in {"accept", "reject", "edit"}:
            raise ValueError("decision must be one of: accept, reject, edit")

        case_id = _normalize_text(payload.get("case_id"))
        if not case_id:
            raise ValueError("case_id is required")

        edited_output = payload.get("edited_output")
        if isinstance(edited_output, str):
            text = edited_output.strip()
            if text:
                try:
                    edited_output = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"edited_output invalid JSON: {exc.msg}") from exc
            else:
                edited_output = None

        if edited_output is not None and not isinstance(edited_output, dict):
            raise ValueError("edited_output must be JSON object or empty")
        if decision == "edit" and edited_output is None:
            raise ValueError("edited_output is required when decision=edit")

        flags_in = payload.get("flags")
        flags: dict[str, bool] = {"hallucination": False, "rubric_error": False}
        if isinstance(flags_in, dict):
            flags["hallucination"] = bool(flags_in.get("hallucination", False))
            flags["rubric_error"] = bool(flags_in.get("rubric_error", False))

        record = {
            "review_id": str(uuid.uuid4()),
            "created_at": _utc_now(),
            "case_id": case_id,
            "run_id": _normalize_text(payload.get("run_id")),
            "example_id": _normalize_text(payload.get("example_id")),
            "task_id": _normalize_text(payload.get("task_id")),
            "reviewer_id": _normalize_text(payload.get("reviewer_id")) or "anonymous",
            "decision": decision,
            "selected_teacher_model": _normalize_text(payload.get("selected_teacher_model")),
            "edited_output": edited_output,
            "flags": flags,
            "notes": _normalize_text(payload.get("notes")),
        }

        with self.reviews_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

        latest = self._load_latest_map()
        latest[case_id] = record
        self.latest_path.write_text(
            json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return record

    def get_latest_by_case(self, case_id: str) -> dict[str, Any] | None:
        return self._load_latest_map().get(case_id)

    def list_reviews(self, case_id: str | None = None) -> list[dict[str, Any]]:
        rows = _read_jsonl(self.reviews_path)
        if case_id is None:
            return rows
        return [row for row in rows if _normalize_text(row.get("case_id")) == case_id]


class CaseRepository:
    """Load gold answers and teacher outputs into reviewable cases."""

    def __init__(
        self,
        *,
        gold_path: Path,
        runs_root: Path,
        source_run_id: str | None,
    ) -> None:
        self.gold_path = gold_path
        self.runs_root = runs_root
        self.source_run_id = source_run_id
        self._cases: dict[str, dict[str, Any]] = {}
        self._case_order: list[str] = []
        self._meta: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        gold_rows = _read_jsonl(self.gold_path)
        gold_index: dict[str, dict[str, Any]] = {}
        for i, row in enumerate(gold_rows, start=1):
            example_id = _normalize_text(row.get("example_id") or row.get("id")) or f"gold-{i:06d}"
            prompt = _normalize_text(row.get("prompt") or row.get("prompt_text"))
            essay = _normalize_text(
                row.get("essay") or row.get("essay_text") or row.get("text") or row.get("input")
            )
            gold_answer = {
                "score": row.get("gold_score", row.get("score")),
                "rubric": row.get("rubric", row.get("gold_rubric_items")),
                "expected_fallacies": row.get("expected_fallacies", row.get("gold_fallacy_label")),
                "notes": row.get("notes_for_reviewers", row.get("reviewer_notes")),
            }
            gold_index[example_id] = {
                "example_id": example_id,
                "prompt": prompt,
                "essay": essay,
                "gold_answer": gold_answer,
                "source": _normalize_text(row.get("source")) or "unknown",
                "difficulty": _normalize_text(row.get("difficulty")) or "unknown",
            }

        run_dirs: list[Path] = []
        if self.source_run_id:
            candidate = self.runs_root / self.source_run_id
            if candidate.exists() and candidate.is_dir():
                run_dirs = [candidate]
        else:
            run_dirs = [
                path
                for path in sorted(self.runs_root.iterdir())
                if path.is_dir() and (path / "responses.jsonl").exists()
            ]

        grouped: dict[tuple[str, str, str, int, float, str], list[TeacherOutput]] = {}
        available_runs: set[str] = set()
        available_tasks: set[str] = set()
        available_models: set[str] = set()

        for run_dir in run_dirs:
            run_id = run_dir.name
            rows = _read_jsonl(run_dir / "responses.jsonl")
            if not rows:
                continue
            available_runs.add(run_id)
            for row in rows:
                model = _normalize_text(row.get("model"))
                task_id = _normalize_text(row.get("task_id"))
                example_id = _normalize_text(row.get("example_id"))
                if not model or not task_id or not example_id:
                    continue
                output_json = row.get("raw_json_output")
                if not isinstance(output_json, dict):
                    output_json = None
                confidence = _safe_float(row.get("confidence"))
                if confidence is not None and confidence > 1.0:
                    confidence = confidence / 100.0
                parse_error = row.get("output_parse_error")
                if not isinstance(parse_error, str):
                    parse_error = None

                output = TeacherOutput(
                    model=model,
                    run_id=run_id,
                    task_id=task_id,
                    example_id=example_id,
                    seed=_safe_int(row.get("seed"), default=0),
                    temperature=float(_safe_float(row.get("temperature")) or 0.0),
                    prompt_version=_normalize_text(row.get("prompt_version")) or "unknown",
                    confidence=confidence,
                    output_json=output_json,
                    output_parse_error=parse_error,
                    raw_response_text=(
                        str(row.get("raw_response_text"))
                        if isinstance(row.get("raw_response_text"), str)
                        else None
                    ),
                    raw_row=dict(row),
                )
                key = (
                    run_id,
                    task_id,
                    example_id,
                    output.seed,
                    output.temperature,
                    output.prompt_version,
                )
                grouped.setdefault(key, []).append(output)
                available_tasks.add(task_id)
                available_models.add(model)

        cases: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        for key in sorted(grouped.keys()):
            run_id, task_id, example_id, seed, temperature, prompt_version = key
            outputs = sorted(grouped[key], key=lambda item: item.model)
            hash_key = "|".join(
                [
                    run_id,
                    task_id,
                    example_id,
                    str(seed),
                    f"{temperature:.4f}",
                    prompt_version,
                ]
            )
            case_id = hashlib.sha1(hash_key.encode("utf-8")).hexdigest()[:16]
            gold = gold_index.get(example_id, {})

            output_rows = []
            for output in outputs:
                output_rows.append(
                    {
                        "model": output.model,
                        "confidence": output.confidence,
                        "output_json": output.output_json,
                        "output_parse_error": output.output_parse_error,
                        "raw_response_text": output.raw_response_text,
                    }
                )

            cases[case_id] = {
                "case_id": case_id,
                "run_id": run_id,
                "task_id": task_id,
                "example_id": example_id,
                "seed": seed,
                "temperature": temperature,
                "prompt_version": prompt_version,
                "prompt": gold.get("prompt", ""),
                "essay": gold.get("essay", ""),
                "source": gold.get("source", "unknown"),
                "difficulty": gold.get("difficulty", "unknown"),
                "gold_answer": gold.get("gold_answer", {}),
                "teacher_outputs": output_rows,
            }
            order.append(case_id)

        self._cases = cases
        self._case_order = order
        self._meta = {
            "runs": sorted(available_runs),
            "tasks": sorted(available_tasks),
            "models": sorted(available_models),
            "cases_total": len(order),
        }

    @property
    def meta(self) -> dict[str, Any]:
        return dict(self._meta)

    def list_cases(
        self,
        *,
        offset: int,
        limit: int,
        run_id: str | None = None,
        task_id: str | None = None,
        model: str | None = None,
        query: str | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        query_norm = _normalize_text(query).lower()
        filtered: list[dict[str, Any]] = []
        for case_id in self._case_order:
            case = self._cases[case_id]
            if run_id and case["run_id"] != run_id:
                continue
            if task_id and case["task_id"] != task_id:
                continue
            models = [row["model"] for row in case["teacher_outputs"]]
            if model and model not in models:
                continue
            if query_norm:
                haystack = " ".join(
                    [
                        str(case["example_id"]),
                        str(case["task_id"]),
                        str(case["prompt"]),
                        str(case["essay"]),
                    ]
                ).lower()
                if query_norm not in haystack:
                    continue

            filtered.append(
                {
                    "case_id": case["case_id"],
                    "run_id": case["run_id"],
                    "task_id": case["task_id"],
                    "example_id": case["example_id"],
                    "seed": case["seed"],
                    "temperature": case["temperature"],
                    "prompt_version": case["prompt_version"],
                    "source": case["source"],
                    "difficulty": case["difficulty"],
                    "teacher_models": models,
                }
            )

        total = len(filtered)
        page = filtered[offset : offset + limit]
        return total, page

    def get_case(self, case_id: str, *, teacher_model: str | None = None) -> dict[str, Any] | None:
        case = self._cases.get(case_id)
        if case is None:
            return None
        payload = copy.deepcopy(case)
        outputs = payload.get("teacher_outputs", [])
        selected = None
        if isinstance(outputs, list) and outputs:
            if teacher_model:
                for row in outputs:
                    if row.get("model") == teacher_model:
                        selected = row
                        break
            if selected is None:
                selected = outputs[0]
        payload["teacher_answer"] = selected
        payload["multiple_teacher_outputs"] = outputs
        return payload


class ReviewApp:
    """Application state and API handlers."""

    def __init__(
        self,
        *,
        gold_path: Path,
        runs_root: Path,
        reviews_root: Path,
        source_run_id: str | None,
        static_dir: Path,
    ) -> None:
        self.repo = CaseRepository(
            gold_path=gold_path,
            runs_root=runs_root,
            source_run_id=source_run_id,
        )
        self.store = ReviewStore(reviews_root)
        self.static_dir = static_dir

    def status(self) -> dict[str, Any]:
        payload = self.repo.meta
        payload["reviews_root"] = str(self.store.root)
        payload["updated_at"] = _utc_now()
        return payload

    def list_cases(self, query: dict[str, list[str]]) -> dict[str, Any]:
        offset = _safe_int((query.get("offset") or ["0"])[0], default=0)
        limit = _safe_int((query.get("limit") or ["25"])[0], default=25)
        run_id = _normalize_text((query.get("run_id") or [""])[0]) or None
        task_id = _normalize_text((query.get("task_id") or [""])[0]) or None
        model = _normalize_text((query.get("model") or [""])[0]) or None
        search = _normalize_text((query.get("query") or [""])[0]) or None
        total, page = self.repo.list_cases(
            offset=max(0, offset),
            limit=max(1, min(limit, 200)),
            run_id=run_id,
            task_id=task_id,
            model=model,
            query=search,
        )
        return {"total": total, "offset": offset, "limit": limit, "cases": page}

    def get_case(self, case_id: str, query: dict[str, list[str]]) -> dict[str, Any]:
        teacher_model = _normalize_text((query.get("teacher_model") or [""])[0]) or None
        case = self.repo.get_case(case_id, teacher_model=teacher_model)
        if case is None:
            raise KeyError("case_not_found")
        case["latest_review"] = self.store.get_latest_by_case(case_id)
        return case

    def list_reviews(self, query: dict[str, list[str]]) -> dict[str, Any]:
        case_id = _normalize_text((query.get("case_id") or [""])[0]) or None
        return {"reviews": self.store.list_reviews(case_id=case_id)}

    def save_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = self.store.save_review(payload)
        return {"ok": True, "review": record}


class ReviewRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for review UI and JSON API."""

    app: ReviewApp | None = None

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_json_body(self) -> dict[str, Any]:
        length = _safe_int(self.headers.get("Content-Length"), default=0)
        body = self.rfile.read(length) if length > 0 else b""
        if not body:
            return {}
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        if self.app is None:
            self._send_json(
                {"error": "server_not_initialized"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        parsed = parse.urlparse(self.path)
        path = parsed.path
        query = parse.parse_qs(parsed.query)

        if path == "/":
            self._send_file(self.app.static_dir / "index.html", "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            rel = path.removeprefix("/static/")
            candidate = (self.app.static_dir / rel).resolve()
            static_root = self.app.static_dir.resolve()
            if static_root not in candidate.parents and candidate != static_root:
                self._send_json({"error": "forbidden"}, status=HTTPStatus.FORBIDDEN)
                return
            if rel.endswith(".js"):
                ctype = "application/javascript; charset=utf-8"
            elif rel.endswith(".css"):
                ctype = "text/css; charset=utf-8"
            else:
                ctype = "text/plain; charset=utf-8"
            self._send_file(candidate, ctype)
            return
        if path == "/api/status":
            self._send_json(self.app.status())
            return
        if path == "/api/cases":
            self._send_json(self.app.list_cases(query))
            return
        if path.startswith("/api/cases/"):
            case_id = path.removeprefix("/api/cases/")
            try:
                self._send_json(self.app.get_case(case_id, query))
            except KeyError:
                self._send_json({"error": "case_not_found"}, status=HTTPStatus.NOT_FOUND)
            return
        if path == "/api/reviews":
            self._send_json(self.app.list_reviews(query))
            return

        self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.app is None:
            self._send_json(
                {"error": "server_not_initialized"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return
        parsed = parse.urlparse(self.path)
        if parsed.path != "/api/reviews":
            self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._parse_json_body()
            result = self.app.save_review(payload)
            self._send_json(result, status=HTTPStatus.OK)
        except ValueError as exc:
            self._send_json(
                {"error": "validation_error", "message": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        except json.JSONDecodeError as exc:
            self._send_json(
                {"error": "invalid_json", "message": exc.msg},
                status=HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._send_json(
                {"error": "internal_error", "message": f"{type(exc).__name__}: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        # Keep console output concise.
        return


def run_server(
    *,
    host: str,
    port: int,
    gold_path: Path,
    runs_root: Path,
    reviews_root: Path,
    source_run_id: str | None,
) -> None:
    """Start the review interface server."""
    static_dir = Path(__file__).resolve().parent / "static"
    app = ReviewApp(
        gold_path=gold_path,
        runs_root=runs_root,
        reviews_root=reviews_root,
        source_run_id=source_run_id,
        static_dir=static_dir,
    )
    ReviewRequestHandler.app = app
    server = ThreadingHTTPServer((host, port), ReviewRequestHandler)
    print(
        json.dumps(
            {
                "status": "serving",
                "host": host,
                "port": port,
                "gold_path": str(gold_path),
                "runs_root": str(runs_root),
                "reviews_root": str(reviews_root),
                "source_run_id": source_run_id,
            },
            ensure_ascii=False,
        )
    )
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lightweight human review interface.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--gold-path", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--runs-root", default="outputs/teacher_runs")
    parser.add_argument("--reviews-root", default="datasets/review")
    parser.add_argument("--source-run-id", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_server(
        host=str(args.host),
        port=int(args.port),
        gold_path=Path(args.gold_path),
        runs_root=Path(args.runs_root),
        reviews_root=Path(args.reviews_root),
        source_run_id=str(args.source_run_id) if args.source_run_id else None,
    )


if __name__ == "__main__":
    main()

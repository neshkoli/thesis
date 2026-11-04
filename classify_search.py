#!/usr/bin/env python3
"""Classify Talmud search-result snippets with Gemini and write a CSV."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.8-flash"

SOURCE_FIELDS = [
    "corpus",
    "masechet",
    "seder",
    "perek",
    "perek_number",
    "halacha",
    "halacha_number",
    "daf",
    "part",
    "sefaria_ref",
    "source_pdf",
    "matched",
    "snippet",
]

CATEGORIES = ["Intellectual", "Institutional", "Political", "Aristocratic", "Halakhic_Activity"]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "Authority_Axes": {
            "type": "object",
            "properties": {
                key: {"type": "integer", "minimum": 0, "maximum": 3}
                for key in CATEGORIES[:4]
            },
            "required": CATEGORIES[:4],
        },
        "Halakhic_Activity": {"type": ["integer", "null"], "enum": [0, 1, None]},
        "Reasoning": {"type": "string"},
    },
    "required": ["Authority_Axes", "Halakhic_Activity", "Reasoning"],
}

ClassifyFn = Callable[[dict[str, Any], str], dict[str, Any]]


def is_retryable_error(exc: BaseException) -> bool:
    text = str(exc)
    return "HTTP 429" in text or "HTTP 503" in text


def retry_delay_seconds(exc: BaseException, fallback: float) -> float:
    match = re.search(r"retry in ([\d.]+)\s*s", str(exc), re.I)
    if match:
        return float(match.group(1)) + 1.0
    return fallback


def call_with_retries(
    operation: Callable[[], Any],
    *,
    attempts: int = 8,
    base_delay: float = 2.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Any:
    last_exc: BaseException | None = None
    for index in range(attempts):
        try:
            return operation()
        except Exception as exc:
            last_exc = exc
            if not is_retryable_error(exc) or index == attempts - 1:
                raise
            delay = retry_delay_seconds(exc, base_delay * (2**index))
            sys.stdout.write("\n")
            print(f"WARNING: retry in {delay:.1f}s ({exc})", flush=True)
            sleep_fn(delay)
    raise last_exc  # pragma: no cover


def load_api_key(env_path: Path | None = None) -> str:
    path = env_path or (ROOT / ".env")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("GEMINI_KEY not found in .env")


def load_system_prompt(path: Path | None = None) -> str:
    return (path or (ROOT / "classification.md")).read_text(encoding="utf-8")


def flatten_scores(payload: dict[str, Any]) -> dict[str, int]:
    axes = payload.get("Authority_Axes") or {}
    if not isinstance(axes, dict):
        axes = {}
    flat: dict[str, int | None] = {}
    for key in CATEGORIES[:4]:
        value = axes.get(key, 0)
        try:
            flat[key] = int(value)
        except (TypeError, ValueError):
            flat[key] = 0
    value = payload.get("Halakhic_Activity")
    if value is None:
        flat["Halakhic_Activity"] = None
    else:
        try:
            flat["Halakhic_Activity"] = int(value)
        except (TypeError, ValueError):
            flat["Halakhic_Activity"] = None
    return flat


def row_from_hit(hit: dict[str, Any], scores: dict[str, int]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for field in SOURCE_FIELDS:
        value = hit.get(field)
        row[field] = "" if value is None else value
    row.update(scores)
    return row


def classify_hits(
    data: dict[str, Any],
    *,
    classify_fn: ClassifyFn,
    model: str = DEFAULT_MODEL,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for hit in data.get("hits") or []:
        payload = classify_fn(hit, model)
        rows.append(row_from_hit(hit, flatten_scores(payload)))
    return rows


def rows_to_csv(rows: Iterable[dict[str, Any]], include_totals: bool = False) -> str:
    written = list(rows)
    if include_totals:
        total = totals_row(written)
        written.append(total)
        written.append(ratio_row(total))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=SOURCE_FIELDS + CATEGORIES, extrasaction="ignore")
    writer.writeheader()
    for row in written:
        writer.writerow(row)
    return buffer.getvalue()


def user_prompt(hit: dict[str, Any]) -> str:
    return (
        "סווג את קטע התלמוד הבא לפי ההנחיות.\n\n"
        f"מקור: {hit.get('sefaria_ref')} "
        f"({hit.get('corpus')} {hit.get('masechet')} {hit.get('daf')})\n\n"
        f"{hit.get('snippet') or ''}"
    )


def build_batch_item(key: str, hit: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    return {
        "key": key,
        "request": {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt(hit)}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": RESPONSE_SCHEMA,
            },
        },
    }


def parse_batch_result(line: dict[str, Any]) -> dict[str, Any]:
    key = str(line.get("key") if line.get("key") is not None else "")
    if line.get("error"):
        err = line["error"]
        message = err.get("message") if isinstance(err, dict) else str(err)
        return {"key": key, "scores": None, "error": message, "raw": line, "payload": None}
    try:
        text = line["response"]["candidates"][0]["content"]["parts"][0]["text"]
        payload = json.loads(text)
        return {
            "key": key,
            "scores": flatten_scores(payload),
            "error": None,
            "raw": line,
            "payload": payload,
        }
    except Exception as exc:
        return {"key": key, "scores": None, "error": str(exc), "raw": line, "payload": None}


def _as_number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value == int(value) else value
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return int(number) if number == int(number) else number


def totals_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total: dict[str, Any] = {field: "" for field in SOURCE_FIELDS + CATEGORIES}
    total["corpus"] = "TOTAL"
    for category in CATEGORIES:
        total[category] = sum(int(_as_number(row.get(category)) or 0) for row in rows)
    return total


def ratio_row(total: dict[str, Any]) -> dict[str, Any]:
    ratio: dict[str, Any] = {field: "" for field in SOURCE_FIELDS + CATEGORIES}
    ratio["corpus"] = "RATIO"
    grand = sum(float(_as_number(total.get(category)) or 0) for category in CATEGORIES)
    if grand == 0:
        for category in CATEGORIES:
            ratio[category] = 0.0
        return ratio
    remaining = 1.0
    for index, category in enumerate(CATEGORIES):
        if index == len(CATEGORIES) - 1:
            ratio[category] = remaining
            break
        value = float(_as_number(total.get(category)) or 0) / grand
        ratio[category] = value
        remaining -= value
    return ratio


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = path.open("w", encoding="utf-8")
        self._write(f"=== classify_search log {time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    def _write(self, text: str) -> None:
        self._handle.write(text)
        if not text.endswith("\n"):
            self._handle.write("\n")
        self._handle.flush()

    def request(self, key: str, payload: Any) -> None:
        self._write(f"\n=== REQUEST {key} ===")
        self._write(json.dumps(payload, ensure_ascii=False, indent=2))

    def response(self, key: str, payload: Any) -> None:
        self._write(f"\n=== RESPONSE {key} ===")
        self._write(json.dumps(payload, ensure_ascii=False, indent=2))

    def error(self, key: str, message: str, detail: Any = None) -> None:
        self._write(f"\n=== ERROR {key} ===")
        self._write(message)
        if detail is not None:
            if isinstance(detail, str):
                self._write(detail)
            else:
                self._write(json.dumps(detail, ensure_ascii=False, indent=2))

    def close(self) -> None:
        self._handle.close()


def gemini_classify(
    hit: dict[str, Any],
    model: str,
    *,
    api_key: str,
    system_prompt: str,
    timeout: int = 120,
) -> dict[str, Any]:
    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt(hit)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": RESPONSE_SCHEMA,
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{model} HTTP {exc.code}: {detail[:500]}") from exc
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + "_classified.csv")


def default_log_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + "_classified.log")


def _to_dict(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {key: _to_dict(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(value) for value in obj]
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        try:
            return _to_dict(dump(mode="python"))
        except TypeError:
            return _to_dict(dump())
    if hasattr(obj, "__dict__"):
        return {
            key: _to_dict(value)
            for key, value in vars(obj).items()
            if not key.startswith("_")
        }
    return str(obj)


def _http_json(method: str, url: str, api_key: str, body: Any = None, timeout: int = 120) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method.upper())
    request.add_header("x-goog-api-key", api_key)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {url}: {detail[:2000]}") from exc
    return json.loads(raw) if raw else {}


def _batch_state(job: dict[str, Any]) -> str:
    metadata = job.get("metadata") or {}
    for candidate in (
        job.get("state"),
        metadata.get("state"),
        (job.get("batch") or {}).get("state"),
    ):
        if isinstance(candidate, dict):
            name = candidate.get("name") or candidate.get("state")
            if name:
                return str(name)
        if candidate:
            return str(candidate)
    if job.get("done") is True:
        return "JOB_STATE_SUCCEEDED" if not job.get("error") else "JOB_STATE_FAILED"
    return "JOB_STATE_PENDING"


def _normalize_batch_line(raw: dict[str, Any], fallback_key: str) -> dict[str, Any]:
    if "key" in raw and ("response" in raw or "error" in raw):
        return raw
    if "response" in raw or "error" in raw:
        raw = dict(raw)
        raw.setdefault("key", fallback_key)
        return raw
    metadata = raw.get("metadata") or {}
    key = raw.get("key") or metadata.get("key") or fallback_key
    if "candidates" in raw:
        return {"key": key, "response": raw}
    return {"key": key, "response": raw.get("inlinedResponse") or raw}


def extract_batch_result_lines(job: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dest = job.get("dest") or {}
    response = job.get("response") or {}
    inlined = (
        dest.get("inlinedResponses")
        or dest.get("inlined_responses")
        or response.get("inlinedResponses")
        or response.get("inlined_responses")
        or (job.get("metadata") or {}).get("dest", {}).get("inlinedResponses")
    )
    lines: list[Any]
    if isinstance(inlined, dict):
        lines = inlined.get("inlinedResponses") or inlined.get("inlined_responses") or []
    elif isinstance(inlined, list):
        lines = inlined
    else:
        lines = []
    if not lines:
        raise RuntimeError(f"batch succeeded but no inlined responses: {json.dumps(job)[:1500]}")
    normalized = []
    for index, line in enumerate(lines):
        fallback = items[index]["key"] if index < len(items) else str(index)
        as_dict = line if isinstance(line, dict) else _to_dict(line)
        normalized.append(_normalize_batch_line(as_dict, fallback))
    return normalized


def _print_wait_status(state: str, started: float) -> None:
    elapsed = int(time.time() - started)
    line = f"Still running, waiting... ({state}, {elapsed}s elapsed)"
    padded = line.ljust(80)
    sys.stdout.write("\r" + padded)
    sys.stdout.flush()


def _end_wait_status() -> None:
    sys.stdout.write("\n")
    sys.stdout.flush()


def submit_batch_rest(
    items: list[dict[str, Any]],
    *,
    api_key: str,
    model: str,
    display_name: str,
    poll_seconds: float,
    timeout: float,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    requests = [
        {"request": item["request"], "metadata": {"key": item["key"]}}
        for item in items
    ]
    body = {
        "batch": {
            "displayName": display_name,
            "inputConfig": {"requests": {"requests": requests}},
        }
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchGenerateContent"
    job = _http_json("POST", url, api_key, body)
    name = job.get("name")
    if not name:
        raise RuntimeError(f"batch create returned no name: {json.dumps(job)[:1500]}")
    print(f"Created batch job {name}", flush=True)
    started = time.time()
    terminal = {
        "JOB_STATE_SUCCEEDED",
        "JOB_STATE_FAILED",
        "JOB_STATE_CANCELLED",
        "JOB_STATE_EXPIRED",
    }
    while True:
        state = _batch_state(job)
        _print_wait_status(state, started)
        if state in terminal or job.get("done") is True:
            _end_wait_status()
            break
        if time.time() - started > timeout:
            _end_wait_status()
            raise RuntimeError(f"batch timed out in state {state}")
        sleep_fn(poll_seconds)
        job = _http_json("GET", f"https://generativelanguage.googleapis.com/v1beta/{name}", api_key)
    state = _batch_state(job)
    if job.get("error") or state in {"JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}:
        raise RuntimeError(f"batch {state}: {job.get('error') or job}")
    dest = job.get("dest") or (job.get("response") or {}).get("dest") or {}
    file_name = dest.get("fileName") or dest.get("file_name")
    if file_name:
        downloaded = _http_json(
            "GET",
            f"https://generativelanguage.googleapis.com/download/v1beta/{file_name}:download?alt=media",
            api_key,
        )
        # download may not be JSON object
        raise RuntimeError(f"file dest not supported in REST helper: {file_name} {downloaded}")
    return extract_batch_result_lines(job.get("response") or job, items)


def submit_batch_sdk(
    items: list[dict[str, Any]],
    *,
    api_key: str,
    model: str,
    jsonl_path: Path,
    poll_seconds: float,
    timeout: float,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    from google import genai
    from google.genai import types

    jsonl_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items),
        encoding="utf-8",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_path = Path(tmpdir) / "taxonomy-classify-batch.jsonl"
        shutil.copyfile(jsonl_path, upload_path)
        client = genai.Client(api_key=api_key)
        uploaded = client.files.upload(
            file=str(upload_path),
            config=types.UploadFileConfig(display_name="taxonomy-classify-batch", mime_type="jsonl"),
        )
        print(f"Uploaded batch file {uploaded.name}", flush=True)
        job = client.batches.create(
            model=model,
            src=uploaded.name,
            config={"display_name": "taxonomy-classify-batch"},
        )
        print(f"Created batch job {job.name}", flush=True)
        terminal = {
            "JOB_STATE_SUCCEEDED",
            "JOB_STATE_FAILED",
            "JOB_STATE_CANCELLED",
            "JOB_STATE_EXPIRED",
        }
        started = time.time()
        state = getattr(job.state, "name", str(job.state))
        while state not in terminal:
            _print_wait_status(state, started)
            if time.time() - started > timeout:
                _end_wait_status()
                raise RuntimeError(f"batch timed out in state {state}")
            sleep_fn(poll_seconds)
            try:
                job = client.batches.get(name=job.name)
            except Exception as exc:
                if "503" in str(exc) or "UNAVAILABLE" in str(exc):
                    _end_wait_status()
                    print(f"WARNING: poll unavailable, retrying: {exc}", flush=True)
                    continue
                _end_wait_status()
                raise
            state = getattr(job.state, "name", str(job.state))
        _end_wait_status()
        if state != "JOB_STATE_SUCCEEDED":
            raise RuntimeError(f"batch {state}: {getattr(job, 'error', None)}")
        dest = job.dest
        file_name = getattr(dest, "file_name", None) if dest is not None else None
        if file_name:
            raw = client.files.download(file=file_name)
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        inlined = getattr(dest, "inlined_responses", None) if dest is not None else None
        if inlined:
            lines = []
            for index, item in enumerate(inlined):
                fallback = items[index]["key"] if index < len(items) else str(index)
                lines.append(_normalize_batch_line(_to_dict(item), fallback))
            return lines
        return extract_batch_result_lines(_to_dict(job), items)


def submit_batch_and_collect(
    items: list[dict[str, Any]],
    *,
    api_key: str,
    model: str,
    jsonl_path: Path,
    poll_seconds: float = 10,
    timeout: float = 7200,
) -> list[dict[str, Any]]:
    try:
        import google.genai  # noqa: F401
    except ImportError:
        print("WARNING: google-genai not installed; using REST batch API", flush=True)
        return submit_batch_rest(
            items,
            api_key=api_key,
            model=model,
            display_name="taxonomy-classify-batch",
            poll_seconds=poll_seconds,
            timeout=timeout,
        )
    return submit_batch_sdk(
        items,
        api_key=api_key,
        model=model,
        jsonl_path=jsonl_path,
        poll_seconds=poll_seconds,
        timeout=timeout,
    )


def rows_from_batch_results(
    hits: list[dict[str, Any]],
    items: list[dict[str, Any]],
    raw_results: list[dict[str, Any]],
    logger: RunLogger,
) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for raw in raw_results:
        parsed = parse_batch_result(raw)
        by_key[parsed["key"]] = parsed
        if parsed["error"]:
            logger.error(parsed["key"], parsed["error"], parsed.get("raw"))
            print(f"ERROR {parsed['key']}: {parsed['error']}", flush=True)
        else:
            logger.response(parsed["key"], parsed.get("payload") or parsed.get("raw"))
    zeros = {key: 0 for key in CATEGORIES}
    rows: list[dict[str, Any]] = []
    for item, hit in zip(items, hits):
        parsed = by_key.get(item["key"])
        if parsed is None:
            logger.error(item["key"], "missing batch result")
            print(f"ERROR {item['key']}: missing batch result", flush=True)
            rows.append(row_from_hit(hit, zeros))
            continue
        if parsed["error"] or parsed["scores"] is None:
            rows.append(row_from_hit(hit, zeros))
            continue
        rows.append(row_from_hit(hit, parsed["scores"]))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify search-result snippets with Gemini (standard generateContent API)."
    )
    parser.add_argument("input_json", type=Path, help="Search results JSON file")
    parser.add_argument("--output", type=Path, help="CSV output path")
    parser.add_argument("--log", type=Path, help="Run log path")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Seconds to wait between successful API calls",
    )
    args = parser.parse_args(argv)

    input_path = args.input_json
    if not input_path.is_absolute():
        input_path = (ROOT / input_path).resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    hits = data.get("hits") or []
    api_key = load_api_key()
    system_prompt = load_system_prompt()
    output_path = args.output or default_output_path(input_path)
    log_path = args.log or default_log_path(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger = RunLogger(log_path)
    print(f"Classifying {len(hits)} snippets with {args.model} (standard API)", flush=True)
    rows: list[dict[str, Any]] = []
    try:
        for index, hit in enumerate(hits, start=1):
            key = str(index - 1)
            line = f"Classifying {index}/{len(hits)} with {args.model}..."
            sys.stdout.write("\r" + line.ljust(80))
            sys.stdout.flush()
            logger.request(
                key,
                {
                    "model": args.model,
                    "sefaria_ref": hit.get("sefaria_ref"),
                    "snippet": hit.get("snippet"),
                },
            )
            try:
                payload = call_with_retries(
                    lambda hit=hit: gemini_classify(
                        hit,
                        args.model,
                        api_key=api_key,
                        system_prompt=system_prompt,
                    )
                )
            except Exception as exc:
                sys.stdout.write("\n")
                print(f"ERROR {key}: {exc}", flush=True)
                logger.error(key, str(exc))
                raise
            logger.response(key, payload)
            rows.append(row_from_hit(hit, flatten_scores(payload)))
            output_path.write_text(rows_to_csv(rows, include_totals=True), encoding="utf-8")
            if args.sleep:
                time.sleep(args.sleep)
        sys.stdout.write("\n")
        print(f"Wrote {output_path} ({len(rows)} rows + TOTAL + RATIO)", flush=True)
        print(f"Wrote {log_path}", flush=True)
        return 0
    except Exception as exc:
        sys.stdout.write("\n")
        print(f"ERROR: classification failed: {exc}", flush=True)
        logger.error("run", str(exc))
        return 1
    finally:
        logger.close()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Disambiguate Rabban Gamliel snippets using Gemini and partition into separate JSON files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.8-flash"

FIGURE_MAP = {
    "הזקן": "רבן גמליאל הזקן",
    "דיבנה": "רבן גמליאל דיבנה",
    "בר רבי": "רבן גמליאל ברבי",
    "מאוחר": "רבן גמליאל המאוחר",
    "ספק": "רבן גמליאל ספק",
}

GAMLIEL_SCHEMA = {
    "type": "object",
    "properties": {
        "Identified_Figure": {
            "type": "string",
            "enum": ["הזקן", "דיבנה", "בר רבי", "מאוחר", "ספק"],
        },
        "Confidence_Level": {
            "type": "string",
            "enum": ["High", "Medium", "Low"],
        },
        "Key_Anchors": {
            "type": "array",
            "items": {"type": "string"},
        },
        "Reasoning": {
            "type": "string",
        },
    },
    "required": ["Identified_Figure", "Confidence_Level", "Key_Anchors", "Reasoning"],
}


def load_api_key(env_path: Path | None = None) -> str:
    path = env_path or (ROOT / ".env")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("GEMINI_KEY not found in .env")


def load_system_prompt(path: Path | None = None) -> str:
    return (path or (ROOT / "classified-gamliel.md")).read_text(encoding="utf-8")


def is_retryable_error(exc: BaseException) -> bool:
    text = str(exc)
    return "HTTP 429" in text or "HTTP 503" in text or "RESOURCE_EXHAUSTED" in text or "timed out" in text


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
            delay = retry_delay_seconds(exc, base_delay * (1.5**index))
            print(f"WARNING: retry in {delay:.1f}s ({exc})", flush=True)
            sleep_fn(delay)
    raise last_exc  # pragma: no cover


def user_prompt(hit: dict[str, Any]) -> str:
    return (
        "סווג את קטע התלמוד הבא לפי ההנחיות כדי לזהות לאיזה רבן גמליאל הכוונה.\n\n"
        f"מקור: {hit.get('sefaria_ref')} "
        f"({hit.get('corpus')} {hit.get('masechet')} {hit.get('daf') or hit.get('perek')})\n\n"
        f"{hit.get('snippet') or ''}"
    )


def gemini_classify_gamliel(
    hit: dict[str, Any],
    model: str,
    *,
    api_key: str,
    system_prompt: str,
    timeout: int = 60,
) -> dict[str, Any]:
    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt(hit)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": GAMLIEL_SCHEMA,
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


def corpus_counts(hits: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(hit.get("corpus") or "unknown" for hit in hits)
    return {
        "Bavli": counts.get("Bavli", 0),
        "Yerushalmi": counts.get("Yerushalmi", 0),
    }


def normalize_figure(figure_str: str) -> str:
    figure_str = figure_str.strip()
    if figure_str in FIGURE_MAP:
        return figure_str
    for key in FIGURE_MAP:
        if key in figure_str:
            return key
    return "ספק"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Disambiguate Rabban Gamliel hits into separate JSON files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "search-results-commentary" / "רבן_גמליאל.json",
        help="Input JSON file",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "search-results-commentary",
        help="Output directory for separated JSON files",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument(
        "--cache-file",
        type=Path,
        default=ROOT / "search-results-commentary" / "רבן_גמליאל_classification_cache.json",
        help="Cache file for intermediate classification results",
    )
    args = parser.parse_args(argv)

    api_key = load_api_key()
    system_prompt = load_system_prompt()
    input_path = args.input if args.input.is_absolute() else (ROOT / args.input).resolve()
    out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir).resolve()
    cache_path = args.cache_file if args.cache_file.is_absolute() else (ROOT / args.cache_file).resolve()

    data = json.loads(input_path.read_text(encoding="utf-8"))
    hits = data.get("hits") or []
    print(f"Loaded {len(hits)} hits from {input_path}")

    # Load cache if available
    cache: dict[str, dict[str, Any]] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"Loaded {len(cache)} cached classifications from {cache_path}")
        except Exception as e:
            print(f"Could not load cache: {e}")

    def process_item(index: int, hit: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        cache_key = str(index)
        if cache_key in cache:
            return index, cache[cache_key]

        res = call_with_retries(
            lambda: gemini_classify_gamliel(
                hit,
                args.model,
                api_key=api_key,
                system_prompt=system_prompt,
            )
        )
        return index, res

    items_to_process = [(idx, hit) for idx, hit in enumerate(hits) if str(idx) not in cache]
    print(f"Processing {len(items_to_process)} hits with {args.workers} workers...")

    completed_count = len(cache)
    total_hits = len(hits)

    if items_to_process:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_item, idx, hit): idx
                for idx, hit in items_to_process
            }
            last_save_time = time.time()
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    _, classification = future.result()
                    cache[str(idx)] = classification
                    completed_count += 1
                    sys.stdout.write(f"\rProgress: {completed_count}/{total_hits} ({(completed_count/total_hits)*100:.1f}%)")
                    sys.stdout.flush()

                    # Save cache periodically every 5 seconds
                    if time.time() - last_save_time > 5:
                        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                        last_save_time = time.time()

                except Exception as e:
                    print(f"\nFailed on hit index {idx}: {e}")
                    raise

        # Save final cache
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nAll items processed and cache saved.")
    else:
        print("All items were already cached.")

    # Partition hits by figure
    categorized_hits: dict[str, list[dict[str, Any]]] = {
        key: [] for key in FIGURE_MAP
    }

    for idx, hit in enumerate(hits):
        classification = cache.get(str(idx), {})
        raw_figure = classification.get("Identified_Figure", "ספק")
        figure_key = normalize_figure(raw_figure)

        enriched_hit = dict(hit)
        enriched_hit["classification"] = classification
        categorized_hits[figure_key].append(enriched_hit)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_counts = {}

    for fig_key, name in FIGURE_MAP.items():
        person_hits = categorized_hits[fig_key]
        counts = corpus_counts(person_hits)
        filename = f"{name.replace(' ', '_')}.json"
        filepath = out_dir / filename

        payload = {
            "query": name,
            "layer": data.get("layer", "commentary"),
            "figure_key": fig_key,
            "total": len(person_hits),
            "by_corpus": counts,
            "hits": person_hits,
        }
        filepath.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary_counts[name] = {
            "total": len(person_hits),
            "bavli": counts["Bavli"],
            "yerushalmi": counts["Yerushalmi"],
            "file": filename,
        }
        print(f"Saved {filepath.name}: {len(person_hits)} hits (Bavli: {counts['Bavli']}, Yerushalmi: {counts['Yerushalmi']})")

    # Print summary
    print("\nSummary of classification:")
    for name, stats in summary_counts.items():
        print(f"  {name}: {stats['total']} (Bavli: {stats['bavli']}, Yerushalmi: {stats['yerushalmi']}) -> {stats['file']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

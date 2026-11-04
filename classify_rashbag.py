#!/usr/bin/env python3
"""Classify Rabban Shimon ben Gamliel snippets and split them by figure."""
from __future__ import annotations

import argparse
import json
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
    "רשב\"ג הראשון": "רבן שמעון בן גמליאל הראשון",
    "רשב\"ג השני": "רבן שמעון בן גמליאל השני",
    "ספק": "רבן שמעון בן גמליאל ספק",
}
SCHEMA = {
    "type": "object",
    "properties": {
        "Identified_Figure": {"type": "string", "enum": list(FIGURE_MAP)},
        "Confidence_Level": {"type": "string", "enum": ["High", "Medium", "Low"]},
        "Key_Anchors": {"type": "array", "items": {"type": "string"}},
        "Reasoning": {"type": "string"},
    },
    "required": ["Identified_Figure", "Confidence_Level", "Key_Anchors", "Reasoning"],
}


def load_key() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("GEMINI_KEY not found")


def retryable(exc: BaseException) -> bool:
    text = str(exc)
    return any(token in text for token in ("HTTP 429", "HTTP 503", "RESOURCE_EXHAUSTED", "timed out"))


def retry_delay(exc: BaseException, fallback: float) -> float:
    match = re.search(r"retry in ([\d.]+)\s*s", str(exc), re.I)
    return float(match.group(1)) + 1 if match else fallback


def with_retries(operation: Callable[[], Any]) -> Any:
    last = None
    for attempt in range(8):
        try:
            return operation()
        except Exception as exc:
            last = exc
            if not retryable(exc) or attempt == 7:
                raise
            time.sleep(retry_delay(exc, 2 * 1.5**attempt))
    raise last


def classify(hit: dict[str, Any], *, key: str, prompt: str, model: str) -> dict[str, Any]:
    text = (
        "סווג את קטע התלמוד הבא לפי ההנחיות.\n\n"
        f"מקור: {hit.get('sefaria_ref')} ({hit.get('corpus')} {hit.get('masechet')} {hit.get('daf') or hit.get('perek')})\n\n"
        f"{hit.get('snippet') or ''}"
    )
    body = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": SCHEMA},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:500]}") from exc
    return json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])


def corpus_counts(hits: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(h.get("corpus") or "unknown" for h in hits)
    return {"Bavli": counts.get("Bavli", 0), "Yerushalmi": counts.get("Yerushalmi", 0)}


def normalize(value: Any) -> str:
    value = str(value or "").strip()
    if value in FIGURE_MAP:
        return value
    if "ראשון" in value:
        return 'רשב"ג הראשון'
    if "שני" in value:
        return 'רשב"ג השני'
    return "ספק"


def source_key(hit: dict[str, Any]) -> tuple[Any, ...]:
    fields = ("corpus", "masechet", "seder", "perek", "perek_number", "halacha", "halacha_number", "daf", "part", "sefaria_ref", "source_pdf")
    return tuple(hit.get(f) for f in fields) + (hit.get("snippet") or "",)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "search-results-commentary" / "רבן_שמעון_בן_גמליאל.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "search-results-commentary")
    parser.add_argument("--cache-file", type=Path, default=ROOT / "search-results-commentary" / "רבן_שמעון_בן_גמליאל_classification_cache.json")
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    hits = data.get("hits") or []
    prompt = (ROOT / "classified-rashbag.md").read_text(encoding="utf-8")
    key = load_key()
    cache = json.loads(args.cache_file.read_text(encoding="utf-8")) if args.cache_file.exists() else {}
    pending = [(i, hit) for i, hit in enumerate(hits) if str(i) not in cache]
    print(f"Loaded {len(hits)} hits; {len(pending)} classifications pending")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(lambda i=i, h=h: with_retries(lambda: classify(h, key=key, prompt=prompt, model=args.model)), i): i for i, h in pending}
        done = len(cache)
        for future in as_completed(futures):
            index = futures[future]
            cache[str(index)] = future.result()
            done += 1
            args.cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\rProgress: {done}/{len(hits)}", end="", flush=True)
    args.cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print()

    groups = {key: [] for key in FIGURE_MAP}
    for index, hit in enumerate(hits):
        classification = cache[str(index)]
        enriched = dict(hit)
        enriched["classification"] = classification
        groups[normalize(classification.get("Identified_Figure"))].append(enriched)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for group, name in FIGURE_MAP.items():
        unique = []
        seen = set()
        for hit in groups[group]:
            key_ = source_key(hit)
            if key_ not in seen:
                seen.add(key_)
                unique.append(hit)
        counts = corpus_counts(unique)
        payload = {"query": name, "layer": data.get("layer", "commentary"), "figure_key": group, "total": len(unique), "by_corpus": counts, "hits": unique}
        path = args.out_dir / f"{name.replace(' ', '_')}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(unique)} ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

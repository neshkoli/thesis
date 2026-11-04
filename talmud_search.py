"""Search Bavli and Yerushalmi JSON for person names, including small spelling variants."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
DEFAULT_ROOTS = ("source/Bavli", "source/Yerushalmi")
DEFAULT_COMMENTARY_ROOTS = ("commentary/Bavli", "commentary/Yerushalmi")
SNIPPET_WORDS_BEFORE = 15
SNIPPET_WORDS_AFTER = 80
PUNCT_STRIP = ".,;:!?\"״''()[]"


def resolve_json_root(root: str | Path) -> Path:
    path = Path(root)
    if path.is_absolute():
        return path
    under_project = ROOT / path
    if under_project.exists():
        return under_project
    return path.resolve()


def resolve_json_roots(roots: Iterable[str | Path] | None = None) -> list[Path]:
    if roots is None:
        roots = DEFAULT_ROOTS
    seen: set[Path] = set()
    resolved: list[Path] = []
    for root in roots:
        path = resolve_json_root(root)
        if path not in seen:
            seen.add(path)
            resolved.append(path)
    return resolved


RABBI_ALIASES = r"(?:רבי|ר'|רב)"


HEBREW_OR_LATIN = r"0-9A-Za-z\u05d0-\u05ea"
NOT_WORD = rf"(?<![{HEBREW_OR_LATIN}])"
NOT_WORD_END = rf"(?![{HEBREW_OR_LATIN}])"


def _variant_word(word: str) -> str:
    if word in {"רבי", "רב", "ר'"}:
        return RABBI_ALIASES
    escaped = re.escape(word)
    if word.endswith("יא"):
        without_yud = re.escape(word[:-2] + "א")
        return rf"(?:{escaped}|{without_yud})ה?"
    if word.endswith("א"):
        stem = re.escape(word[:-1])
        return rf"(?:{escaped}|{stem}יא|{stem})ה?"
    return escaped + r"ה?"


def name_pattern(query: str) -> re.Pattern[str]:
    parts = [p for p in query.strip().split() if p]
    if not parts:
        raise ValueError("empty name query")
    body = r"\s+".join(_variant_word(p) for p in parts)
    prefixed = r"[דבולמכשה]?" + body
    return re.compile(NOT_WORD + prefixed + NOT_WORD_END)


def _token_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"\S+", text):
        token = match.group().strip(PUNCT_STRIP)
        if not token:
            continue
        leading = match.group()[: len(match.group()) - len(match.group().lstrip(PUNCT_STRIP))]
        trailing_len = len(match.group()) - len(match.group().rstrip(PUNCT_STRIP))
        start = match.start() + len(leading)
        end = match.end() - trailing_len
        if start < end:
            spans.append((start, end))
    return spans


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"[.!?]+", text):
        end = match.end()
        if text[start:end].strip():
            spans.append((start, end))
        start = end
    remainder = text[start:]
    if remainder.strip():
        spans.append((start, len(text)))
    if not spans and text:
        spans.append((0, len(text)))
    return spans


def _token_index_at(tokens: list[tuple[int, int]], pos: int, *, end: bool = False) -> int:
    if not tokens:
        return 0
    if end:
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i][0] < pos:
                return i
        return 0
    for i, (start, stop) in enumerate(tokens):
        if stop > pos:
            return i
    return len(tokens) - 1


def _snap_from_inside_name(
    text: str,
    tokens: list[tuple[int, int]],
    from_i: int,
    query: str,
) -> int:
    if from_i <= 0:
        return from_i
    pos = tokens[from_i][0]
    for match in name_pattern(query).finditer(text):
        if match.start() < pos < match.end():
            return _token_index_at(tokens, match.start())
    return from_i


def snippet_around(
    text: str,
    span_start: int,
    span_end: int,
    *,
    before: int = SNIPPET_WORDS_BEFORE,
    after: int = SNIPPET_WORDS_AFTER,
    following_texts: Iterable[str] | None = None,
    name_query: str | None = None,
) -> str:
    tokens = _token_spans(text)
    if not tokens:
        return text[span_start:span_end].strip()
    first = _token_index_at(tokens, span_start)
    last = _token_index_at(tokens, span_end, end=True)
    if last < first:
        first, last = last, first
    from_i = max(0, first - before)
    from_i = min(from_i, first)
    if name_query:
        from_i = _snap_from_inside_name(text, tokens, from_i, name_query)
    available_after = len(tokens) - 1 - last
    to_i = min(len(tokens) - 1, last + after)
    to_i = max(to_i, last)
    snippet = text[tokens[from_i][0] : tokens[to_i][1]].strip()
    needed = after - available_after
    if needed <= 0:
        return snippet
    extras: list[str] = []
    for follow in following_texts or []:
        follow_tokens = _token_spans(follow)
        if not follow_tokens:
            continue
        take = min(needed, len(follow_tokens))
        extras.append(follow[follow_tokens[0][0] : follow_tokens[take - 1][1]].strip())
        needed -= take
        if needed <= 0:
            break
    if extras:
        return f"{snippet} {' '.join(extras)}".strip()
    return snippet


def _iter_halachot(doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    corpus = doc.get("corpus")
    for chapter in doc.get("chapters") or []:
        for halacha in chapter.get("halachot") or []:
            yield {
                "corpus": corpus,
                "masechet": doc.get("masechet") or doc.get("title"),
                "seder": doc.get("seder"),
                "source_pdf": doc.get("source_pdf"),
                "sefaria_ref": halacha.get("sefaria_ref") or chapter.get("sefaria_ref") or doc.get("sefaria_ref"),
                "perek": chapter.get("perek") or halacha.get("perek"),
                "perek_number": chapter.get("perek_number") or halacha.get("perek_number"),
                "halacha": halacha.get("halacha"),
                "halacha_number": halacha.get("halacha_number"),
                "daf": chapter.get("daf") or halacha.get("daf"),
                "part": chapter.get("part") or halacha.get("part"),
                "text": halacha.get("text") or "",
            }
    if not doc.get("chapters") and doc.get("text"):
        yield {
            "corpus": corpus,
            "masechet": doc.get("masechet") or doc.get("title"),
            "seder": doc.get("seder"),
            "source_pdf": doc.get("source_pdf"),
            "sefaria_ref": doc.get("sefaria_ref"),
            "perek": None,
            "perek_number": None,
            "halacha": None,
            "halacha_number": None,
            "daf": None,
            "part": None,
            "text": doc["text"],
        }


def _hit_from_matches(
    loc: dict[str, Any],
    matches: list[re.Match[str]],
    *,
    following_texts: Iterable[str] | None = None,
    name_query: str | None = None,
) -> dict[str, Any]:
    first, last = matches[0], matches[-1]
    matched_forms: list[str] = []
    for match in matches:
        form = match.group(0)
        if form not in matched_forms:
            matched_forms.append(form)
    return {
        "corpus": loc.get("corpus"),
        "masechet": loc["masechet"],
        "seder": loc["seder"],
        "perek": loc["perek"],
        "perek_number": loc["perek_number"],
        "halacha": loc["halacha"],
        "halacha_number": loc["halacha_number"],
        "daf": loc.get("daf"),
        "part": loc.get("part"),
        "sefaria_ref": loc.get("sefaria_ref"),
        "source_pdf": loc["source_pdf"],
        "matched": " | ".join(matched_forms),
        "snippet": snippet_around(
            loc["text"],
            first.start(),
            last.end(),
            following_texts=following_texts,
            name_query=name_query,
        ),
    }


def _hit_key(hit: dict[str, Any]) -> tuple[Any, ...]:
    return (
        hit.get("corpus"),
        hit.get("masechet"),
        hit.get("seder"),
        hit.get("perek_number"),
        hit.get("halacha_number"),
        hit.get("daf"),
        hit.get("part"),
        hit.get("sefaria_ref"),
        hit.get("snippet"),
    )


def find_name_hits(docs: Iterable[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    pattern = name_pattern(query)
    hits: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for doc in docs:
        locs = list(_iter_halachot(doc))
        for i, loc in enumerate(locs):
            text = loc["text"]
            matches = list(pattern.finditer(text))
            if not matches:
                continue
            sentences = _sentence_spans(text)
            grouped: dict[int, list[re.Match[str]]] = {}
            for match in matches:
                sentence_i = next(
                    (i for i, (start, end) in enumerate(sentences) if start <= match.start() < end),
                    0,
                )
                grouped.setdefault(sentence_i, []).append(match)
            following = [later["text"] for later in locs[i + 1 :]]
            for sentence_i in sorted(grouped):
                hit = _hit_from_matches(
                    loc,
                    grouped[sentence_i],
                    following_texts=following,
                    name_query=query,
                )
                key = _hit_key(hit)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(hit)
    return hits


def load_docs(
    json_root: Path | Iterable[Path] | None = None,
    *,
    commentary: bool = False,
) -> list[dict[str, Any]]:
    if json_root is None:
        roots = resolve_json_roots(DEFAULT_COMMENTARY_ROOTS if commentary else None)
    elif isinstance(json_root, (str, Path)):
        roots = resolve_json_roots([json_root])
    else:
        roots = resolve_json_roots(json_root)

    docs: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for json_root_path in roots:
        corpus_guess = json_root_path.name
        for path in sorted(json_root_path.rglob("*.json")):
            if path.name == "index.json" or path.name.endswith("-index.json"):
                continue
            resolved = path.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            doc = json.loads(path.read_text(encoding="utf-8"))
            if not doc.get("corpus"):
                doc["corpus"] = corpus_guess
            docs.append(doc)
    return docs


def format_index(hits: list[dict[str, Any]], query: str) -> str:
    lines = [f"query: {query}", f"hits: {len(hits)}", ""]
    for i, hit in enumerate(hits, 1):
        corpus = hit.get("corpus")
        prefix = f"{corpus} " if corpus else ""
        if hit.get("daf"):
            loc = f"{prefix}{hit['masechet']} {hit['daf']}"
        elif hit.get("part"):
            loc = (
                f"{prefix}{hit['masechet']} {hit['part']} "
                f"פרק {hit['perek_number']} פסקה {hit['halacha_number']}"
            )
        else:
            loc = f"{prefix}{hit['masechet']} פרק {hit['perek_number']} הלכה {hit['halacha_number']}"
        lines.append(f"{i}. {loc}")
        lines.append(f"   matched: {hit['matched']}")
        lines.append(f"   snippet: {hit['snippet']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search Bavli and Yerushalmi JSON for a person name.")
    parser.add_argument("name", nargs="+", help="Name to search, e.g. רבי יודן נשייא")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text index")
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help=(
            "JSON folder to search (repeatable). "
            "Defaults to source/Bavli and source/Yerushalmi. "
            "Examples: source/Yerushalmi, source/Bavli, commentary/Bavli"
        ),
    )
    parser.add_argument(
        "--commentary",
        action="store_true",
        help="Search commentary/Bavli and commentary/Yerushalmi instead of the source texts",
    )
    args = parser.parse_args(argv)
    query = " ".join(args.name)
    hits = find_name_hits(load_docs(args.root, commentary=args.commentary), query)
    if args.json:
        print(json.dumps({"query": query, "hits": hits}, ensure_ascii=False, indent=2))
    else:
        print(format_index(hits, query), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

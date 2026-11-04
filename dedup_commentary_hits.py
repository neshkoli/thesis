#!/usr/bin/env python3
"""Merge overlapping commentary search-result snippets within the same source."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


OVERLAP_THRESHOLD = 0.5


def tokens(text: str) -> list[str]:
    return (text or "").split()


def suffix_prefix_overlap(left: list[str], right: list[str], min_k: int = 1) -> int:
    max_k = min(len(left), len(right))
    for k in range(max_k, min_k - 1, -1):
        if left[-k:] == right[:k]:
            return k
    return 0


def containment(a: list[str], b: list[str]) -> bool:
    if not a or len(a) > len(b):
        return False
    n, m = len(a), len(b)
    for i in range(m - n + 1):
        if b[i : i + n] == a:
            return True
    return False


def token_lcs_len(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    n, m = len(a), len(b)
    prev = [0] * (m + 1)
    best = 0
    for i in range(1, n + 1):
        curr = [0] * (m + 1)
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                curr[j] = prev[j - 1] + 1
                if curr[j] > best:
                    best = curr[j]
        prev = curr
    return best


def source_key(hit: dict) -> tuple:
    ref = (hit.get("sefaria_ref") or "").strip()
    if ref:
        return ("ref", ref)
    return (
        "loc",
        hit.get("corpus"),
        hit.get("masechet"),
        hit.get("daf") or hit.get("perek"),
        hit.get("halacha"),
        hit.get("part"),
    )


def try_stitch(a: str, b: str) -> str | None:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return None
    shorter = min(len(ta), len(tb))
    need = max(1, int(shorter * OVERLAP_THRESHOLD))

    if ta == tb:
        return a
    if containment(ta, tb):
        return b
    if containment(tb, ta):
        return a

    ab = suffix_prefix_overlap(ta, tb, need)
    ba = suffix_prefix_overlap(tb, ta, need)
    best = max(ab, ba)
    if best >= need:
        if ab >= ba:
            return " ".join(ta + tb[ab:])
        return " ".join(tb + ta[ba:])

    lcs = token_lcs_len(ta, tb)
    if lcs >= need:
        return a if len(ta) >= len(tb) else b
    return None


def merge_hit_meta(keep: dict, other: dict, snippet: str) -> dict:
    merged = dict(keep)
    merged["snippet"] = snippet
    matched_i = keep.get("matched") or ""
    matched_j = other.get("matched") or ""
    if matched_j and matched_j not in matched_i:
        merged["matched"] = f"{matched_i} | {matched_j}" if matched_i else matched_j
    return merged


def merge_group(items: list[tuple[int, dict]]) -> list[tuple[int, dict]]:
    remaining = [(i, dict(h)) for i, h in items]
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(remaining):
            j = i + 1
            merged_any = False
            while j < len(remaining):
                idx_i, hit_i = remaining[i]
                idx_j, hit_j = remaining[j]
                stitched = try_stitch(hit_i["snippet"], hit_j["snippet"])
                if stitched is None:
                    j += 1
                    continue
                remaining[i] = (
                    min(idx_i, idx_j),
                    merge_hit_meta(hit_i, hit_j, stitched),
                )
                del remaining[j]
                changed = True
                merged_any = True
                break
            if not merged_any:
                i += 1
    remaining.sort(key=lambda pair: pair[0])
    return remaining


def dedup_hits(hits: list[dict]) -> list[dict]:
    groups: dict[tuple, list[tuple[int, dict]]] = {}
    for idx, hit in enumerate(hits):
        groups.setdefault(source_key(hit), []).append((idx, hit))

    merged: list[tuple[int, dict]] = []
    for items in groups.values():
        merged.extend(merge_group(items))
    merged.sort(key=lambda pair: pair[0])
    return [hit for _, hit in merged]


def recount(hits: list[dict]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for hit in hits:
        corpus = hit.get("corpus") or "unknown"
        counts[corpus] += 1
    return dict(counts)


def process_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    hits = data.get("hits") or []
    before = len(hits)
    after_hits = dedup_hits(hits)
    after = len(after_hits)
    removed = before - after
    data["hits"] = after_hits
    data["total"] = after
    data["by_corpus"] = recount(after_hits)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "file": path.name,
        "before": before,
        "after": after,
        "removed": removed,
    }


def main() -> None:
    folder = Path(__file__).resolve().parent / "search-results-commentary"
    json_files = sorted(
        p for p in folder.glob("*.json") if p.name != "summary.json"
    )
    rows = [process_file(p) for p in json_files]
    report_lines = [
        "# Commentary snippet deduplication report",
        "",
        "Rule: within the same original source (`sefaria_ref`, or corpus/masechet/daf if missing),",
        "snippets with at least 50% token overlap were merged into one paragraph.",
        "",
        "| File | Before | After | Duplicates removed |",
        "|---|---:|---:|---:|",
    ]
    total_before = total_after = total_removed = 0
    for row in rows:
        report_lines.append(
            f"| {row['file']} | {row['before']} | {row['after']} | {row['removed']} |"
        )
        total_before += row["before"]
        total_after += row["after"]
        total_removed += row["removed"]
    report_lines.extend(
        [
            f"| **Total** | **{total_before}** | **{total_after}** | **{total_removed}** |",
            "",
        ]
    )
    report_path = folder / "dedup-report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))
    print(f"\nWrote {report_path}")


if __name__ == "__main__":
    main()

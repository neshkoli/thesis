"""Download Midrash source texts from Sefaria into source/Midrash."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
from typing import Any

from sefaria_bavli import _fetch_once
from sefaria_yerushalmi import (
    ROOT,
    _http_get_json,
    _join_segments,
    int_to_hebrew,
)

SEFARIA_API = "https://www.sefaria.org/api"
MIDRASH_ROOT = ROOT / "source" / "Midrash"
SKIP_TITLE_PREFIXES = (
    "Footnotes ",
    "Notes and Corrections",
    "Buber footnotes",
    "Learning to Read",
)
SKIP_TITLES = {
    "Legends of the Jews",
    "Ein Yaakov (Glick Edition)",
    "Ruth Rabbah (Lerner)",
    "Sifrei Zuta; Midrashah shel Lod",
}
PAGE_BY_CHAPTER = {
    "Yalkut Shimoni on Torah",
}


def jagged_to_chapters(
    raw: list[Any],
    *,
    sefaria_ref: str,
    part: str | None = None,
    part_he: str | None = None,
) -> list[dict[str, Any]]:
    if not raw:
        return []
    if all(isinstance(x, str) for x in raw):
        raw = [raw]
    chapters: list[dict[str, Any]] = []
    for chap_i, chap in enumerate(raw, 1):
        paras = [chap] if isinstance(chap, str) else (chap if isinstance(chap, list) else [])
        halachot = []
        for hal_i, hal in enumerate(paras, 1):
            text = _join_segments(hal)
            if not text:
                continue
            item = {
                "halacha": int_to_hebrew(hal_i),
                "halacha_number": hal_i,
                "perek": int_to_hebrew(chap_i),
                "perek_number": chap_i,
                "sefaria_ref": f"{sefaria_ref} {chap_i}:{hal_i}",
                "text": text,
            }
            if part:
                item["part"] = part
            halachot.append(item)
        if not halachot:
            continue
        chapter = {
            "perek": int_to_hebrew(chap_i),
            "perek_number": chap_i,
            "halachot": halachot,
        }
        if part:
            chapter["part"] = part
        if part_he:
            chapter["part_he"] = part_he
        chapters.append(chapter)
    return chapters


def midrash_to_doc(
    raw: list[Any],
    *,
    title: str,
    he_title: str,
    category: str,
    edition: str | None,
    extra_chapters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    chapters = extra_chapters if extra_chapters is not None else jagged_to_chapters(
        raw, sefaria_ref=title
    )
    return {
        "title": he_title,
        "masechet": he_title,
        "corpus": "Midrash",
        "category": category,
        "sefaria_ref": title,
        "edition": edition,
        "source": "sefaria",
        "chapters": chapters,
    }


def _slug(title: str) -> str:
    slug = title.lower().replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", slug).strip("-")


def _category_folder(cats: list[str]) -> str:
    if len(cats) >= 3:
        return _slug(cats[2])
    if len(cats) >= 2:
        return _slug(cats[1])
    return "midrash"


def _is_source_midrash(title: str, cats: list[str]) -> bool:
    if not cats or cats[0] != "Midrash":
        return False
    if "Commentary" in cats or "Modern Texts" in cats:
        return False
    if title in SKIP_TITLES or title.startswith(SKIP_TITLE_PREFIXES):
        return False
    return True


def list_midrashim() -> list[dict[str, str]]:
    found: list[dict[str, str]] = []

    def walk(nodes: Any) -> None:
        if isinstance(nodes, list):
            for n in nodes:
                walk(n)
            return
        if not isinstance(nodes, dict):
            return
        title = nodes.get("title")
        cats = nodes.get("categories") or []
        if isinstance(title, str) and _is_source_midrash(title, cats):
            found.append(
                {
                    "title": title,
                    "he_title": nodes.get("heTitle") or title,
                    "category": _category_folder(cats),
                    "slug": _slug(title),
                }
            )
        walk(nodes.get("contents") or nodes.get("nodes"))

    walk(_http_get_json(f"{SEFARIA_API}/index/"))
    return found


def iter_leaves(schema: dict[str, Any], book_title: str):
    children = schema.get("nodes") or []
    if not children:
        yield book_title, schema.get("heTitle") or book_title, schema
        return
    for child in children:
        child_title = child.get("title") or child.get("key") or ""
        ref = f"{book_title}, {child_title}" if child_title else book_title
        if child.get("nodes"):
            yield from iter_leaves(child, ref)
        else:
            yield ref, child.get("heTitle") or child_title, child


def fetch_index(title: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    return _http_get_json(f"{SEFARIA_API}/index/{encoded}")


def _is_same_book_chapter(title: str, nxt: str | None) -> bool:
    if not nxt:
        return False
    prefix = title + " "
    if not nxt.startswith(prefix):
        return False
    rest = nxt[len(prefix) :]
    return bool(rest) and rest[0].isdigit() and "," not in rest


def fetch_via_next(title: str) -> tuple[list[Any], str | None]:
    collected: list[Any] = []
    edition = None
    ref = f"{title} 1"
    seen: set[str] = set()
    while ref and ref not in seen:
        seen.add(ref)
        if len(seen) == 1 or len(seen) % 50 == 0:
            print(f"    paging {ref}", flush=True)
        encoded = urllib.parse.quote(ref.replace(" ", "_"))
        data = _http_get_json(
            f"{SEFARIA_API}/v3/texts/{encoded}?return_format=text_only&version=hebrew"
        )
        versions = data.get("versions") or []
        if not versions:
            break
        edition = versions[0].get("versionTitle")
        text = versions[0].get("text")
        if isinstance(text, list) and text:
            collected.append(text)
        nxt = data.get("next")
        if not _is_same_book_chapter(title, str(nxt) if nxt else None):
            break
        ref = str(nxt)
        time.sleep(0.05)
    if not collected:
        raise RuntimeError(f"paged fetch empty for {title}")
    return collected, edition


def fetch_hebrew(title: str) -> tuple[list[Any], str | None]:
    if title in PAGE_BY_CHAPTER:
        return fetch_via_next(title)
    try:
        return _fetch_once(title, "hebrew")
    except Exception as exc:
        if "IncompleteRead" in type(exc).__name__ or "IncompleteRead" in str(exc):
            print(f"    paging by chapter: {title}")
            return fetch_via_next(title)
        encoded = urllib.parse.quote(title.replace(" ", "_"))
        try:
            data = _http_get_json(f"{SEFARIA_API}/v3/texts/{encoded}?return_format=text_only")
        except Exception:
            raise RuntimeError(f"no text for {title}") from exc
        versions = [v for v in (data.get("versions") or []) if v.get("language") == "he"] or (
            data.get("versions") or []
        )
        if not versions or not isinstance(versions[0].get("text"), list):
            raise RuntimeError(f"no text for {title}") from exc
        return versions[0]["text"], versions[0].get("versionTitle")


def _row(dest, work: dict[str, str], doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "json": str(dest.relative_to(ROOT)),
        "masechet": doc.get("masechet"),
        "category": work["category"],
        "sefaria_ref": work["title"],
        "chapters": len(doc.get("chapters") or []),
        "halachot": sum(len(ch.get("halachot") or []) for ch in doc.get("chapters") or []),
    }


def download_all(out_root=MIDRASH_ROOT, delay_s: float = 0.2) -> list[dict[str, Any]]:
    works = list_midrashim()
    summary: list[dict[str, Any]] = []
    for i, work in enumerate(works, 1):
        dest = out_root / work["category"] / f"{work['slug']}.json"
        print(f"[Midrash {i}/{len(works)}] {work['title']}", flush=True)
        if dest.exists() and dest.stat().st_size > 100:
            summary.append(_row(dest, work, json.loads(dest.read_text(encoding="utf-8"))))
            continue
        try:
            schema = (fetch_index(work["title"]).get("schema") or {})
            chapters: list[dict[str, Any]] = []
            edition = None
            for ref, he_part, _node in iter_leaves(schema, work["title"]):
                print(f"    {ref}")
                try:
                    raw, edition = fetch_hebrew(ref)
                except Exception as leaf_exc:
                    print(f"    skip leaf ({leaf_exc})")
                    continue
                part = None if ref == work["title"] else ref.split(", ", 1)[-1]
                chapters.extend(
                    jagged_to_chapters(raw, sefaria_ref=ref, part=part, part_he=he_part if part else None)
                )
                time.sleep(delay_s)
            if not chapters:
                print(f"    fallback whole book {work['title']}")
                raw, edition = fetch_hebrew(work["title"])
                chapters = jagged_to_chapters(raw, sefaria_ref=work["title"])
            doc = midrash_to_doc(
                [],
                title=work["title"],
                he_title=work["he_title"],
                category=work["category"],
                edition=edition,
                extra_chapters=chapters,
            )
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary.append(_row(dest, work, doc))
        except Exception as exc:
            print(f"    FAILED: {exc}")
            summary.append({"json": str(dest.relative_to(ROOT)), "sefaria_ref": work["title"], "error": str(exc)})
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    summary = download_all()
    ok = [s for s in summary if not s.get("error")]
    print(f"Wrote {len(ok)}/{len(summary)} midrashim under {MIDRASH_ROOT}")
    return 0 if len(ok) == len(summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())

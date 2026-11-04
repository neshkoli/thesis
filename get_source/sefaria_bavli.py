"""Download Talmud Bavli source and Steinsaltz commentary from Sefaria."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
from typing import Any

from sefaria_yerushalmi import (
    ROOT,
    SEDER_SLUG as YERU_SEDER,
    _http_get_json,
    _join_segments,
    sefaria_text_to_doc,
)

SEFARIA_API = "https://www.sefaria.org/api"
BAVLI_SOURCE_ROOT = ROOT / "source" / "Bavli"
BAVLI_COMMENTARY_ROOT = ROOT / "commentary" / "Bavli"
YERUSHALMI_STEIN_ROOT = ROOT / "commentary" / "Yerushalmi"
BAVLI_SOURCE_VERSION = "hebrew|William Davidson Edition - Aramaic"
STEIN_VERSION = "hebrew|William Davidson Edition - Hebrew"
SEDER_SLUG = {**YERU_SEDER, "Seder Kodashim": "kodashim"}


def index_to_daf(index: int) -> tuple[str, int, str]:
    daf_number = (index + 2) // 2
    amud = "a" if index % 2 == 0 else "b"
    return f"{daf_number}{amud}", daf_number, amud


def bavli_text_to_doc(
    dapim_raw: list[Any],
    *,
    title: str,
    he_title: str,
    masechet: str,
    seder: str,
    edition: str | None,
    sefaria_ref: str,
    corpus: str = "Bavli",
) -> dict[str, Any]:
    chapters = []
    for i, amud in enumerate(dapim_raw or []):
        text = _join_segments(amud)
        if not text:
            continue
        daf, daf_number, amud_letter = index_to_daf(i)
        chapters.append(
            {
                "perek": daf,
                "perek_number": daf_number,
                "daf": daf,
                "amud": amud_letter,
                "halachot": [
                    {
                        "halacha": amud_letter,
                        "halacha_number": 1,
                        "perek": daf,
                        "perek_number": daf_number,
                        "daf": daf,
                        "sefaria_ref": f"{sefaria_ref} {daf}",
                        "text": text,
                    }
                ],
            }
        )
    return {
        "title": he_title,
        "masechet": masechet,
        "seder": seder,
        "corpus": corpus,
        "sefaria_ref": sefaria_ref,
        "edition": edition,
        "source": "sefaria",
        "chapters": chapters,
    }


def _walk_toc(nodes: Any, visit) -> None:
    if isinstance(nodes, list):
        for n in nodes:
            _walk_toc(n, visit)
        return
    if isinstance(nodes, dict):
        visit(nodes)
        _walk_toc(nodes.get("contents") or nodes.get("nodes"), visit)


def _collect(pred) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []

    def visit(node: dict[str, Any]) -> None:
        row = pred(node)
        if row:
            found.append(row)

    _walk_toc(_http_get_json(f"{SEFARIA_API}/index/"), visit)
    return found


def _row(title: str, he: str, seder_cat: str, slug: str) -> dict[str, str]:
    return {
        "title": title,
        "he_title": he,
        "masechet": he,
        "seder": SEDER_SLUG.get(seder_cat, ""),
        "slug": slug,
    }


def list_bavli_tractates() -> list[dict[str, str]]:
    def pred(node: dict[str, Any]) -> dict[str, str] | None:
        title = node.get("title")
        cats = node.get("categories") or []
        if not isinstance(title, str) or cats[:2] != ["Talmud", "Bavli"]:
            return None
        if " on " in title or title.startswith(("Rif ", "Ein ")):
            return None
        seder_cat = next((c for c in cats if c in SEDER_SLUG), "")
        if not seder_cat:
            return None
        he = node.get("heTitle") or title
        return _row(title, he, seder_cat, title.lower().replace(" ", "-"))

    return _collect(pred)


def list_bavli_steinsaltz() -> list[dict[str, str]]:
    def pred(node: dict[str, Any]) -> dict[str, str] | None:
        title = node.get("title")
        cats = node.get("categories") or []
        if not isinstance(title, str) or not title.startswith("Steinsaltz on "):
            return None
        if cats[:2] != ["Talmud", "Bavli"]:
            return None
        base = title[len("Steinsaltz on ") :]
        seder_cat = next((c for c in cats if c in SEDER_SLUG), "")
        he = (node.get("heTitle") or "").replace("ביאור שטיינזלץ על ", "")
        return _row(title, he, seder_cat, base.lower().replace(" ", "-"))

    return _collect(pred)


def daf_to_index(daf: str) -> int:
    number = int(daf[:-1])
    return number * 2 - 2 + (0 if daf.endswith("a") else 1)


def _fetch_once(title: str, version: str) -> tuple[list[Any], str | None]:
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    ver = urllib.parse.quote(version, safe="")
    data = _http_get_json(
        f"{SEFARIA_API}/v3/texts/{encoded}?return_format=text_only&version={ver}"
    )
    versions = data.get("versions") or []
    if not versions or not isinstance(versions[0].get("text"), list):
        raise RuntimeError(f"no version/text for {title}")
    return versions[0]["text"], versions[0].get("versionTitle")


def fetch_text_paged(title: str, version: str) -> tuple[list[Any], str | None]:
    ver = urllib.parse.quote(version, safe="")
    ref = f"{title}.2a"
    by_index: dict[int, list[Any]] = {}
    edition = None
    while ref:
        encoded = urllib.parse.quote(ref.replace(" ", "_"))
        data = _http_get_json(
            f"{SEFARIA_API}/v3/texts/{encoded}?return_format=text_only&version={ver}"
        )
        versions = data.get("versions") or []
        if not versions:
            break
        edition = versions[0].get("versionTitle")
        sections = data.get("sections") or []
        daf = str(sections[0]) if sections else ""
        if daf.endswith(("a", "b")):
            by_index[daf_to_index(daf)] = versions[0].get("text") or []
        nxt = data.get("next")
        if not nxt or not str(nxt).startswith(title):
            break
        ref = str(nxt).replace(" ", ".")
        time.sleep(0.05)
    if not by_index:
        raise RuntimeError(f"paged fetch empty for {title}")
    size = max(by_index) + 1
    return [by_index.get(i, []) for i in range(size)], edition


def fetch_text(title: str, version: str) -> tuple[list[Any], str | None]:
    try:
        return _fetch_once(title, version)
    except Exception as exc:
        print(f"  whole-book fetch failed ({exc}); paging by daf")
        return fetch_text_paged(title, version)


def _write_index(out_root, summary: list[dict[str, Any]], name: str = "index.json") -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / name).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _save(doc: dict[str, Any], dest, extra: dict[str, str]) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "json": str(dest.relative_to(ROOT)),
        "masechet": doc["masechet"],
        "seder": extra.get("seder"),
        "sefaria_ref": extra.get("title") or doc.get("sefaria_ref"),
        "chapters": len(doc["chapters"]),
        "halachot": sum(len(ch["halachot"]) for ch in doc["chapters"]),
    }


def download_bavli_source(out_root=BAVLI_SOURCE_ROOT, delay_s: float = 0.25):
    tractates = list_bavli_tractates()
    if len(tractates) != 37:
        raise RuntimeError(f"expected 37 Bavli, found {len(tractates)} {[t['title'] for t in tractates]}")
    summary = []
    for i, t in enumerate(tractates, 1):
        print(f"[Bavli source {i}/{len(tractates)}] {t['title']}")
        raw, edition = fetch_text(t["title"], BAVLI_SOURCE_VERSION)
        doc = bavli_text_to_doc(
            raw, title=t["title"], he_title=t["he_title"], masechet=t["masechet"],
            seder=t["seder"], edition=edition, sefaria_ref=t["title"],
        )
        summary.append(_save(doc, out_root / t["seder"] / f"{t['slug']}.json", t))
        time.sleep(delay_s)
    _write_index(out_root, summary)
    return summary


def download_bavli_steinsaltz(out_root=BAVLI_COMMENTARY_ROOT, delay_s: float = 0.25):
    tractates = list_bavli_steinsaltz()
    if len(tractates) != 37:
        raise RuntimeError(f"expected 37 Steinsaltz Bavli, found {len(tractates)}")
    summary = []
    for i, t in enumerate(tractates, 1):
        dest = out_root / t["seder"] / f"{t['slug']}.json"
        print(f"[Steinsaltz Bavli {i}/{len(tractates)}] {t['title']}")
        if dest.exists() and dest.stat().st_size > 100:
            doc = json.loads(dest.read_text(encoding="utf-8"))
            summary.append(
                {
                    "json": str(dest.relative_to(ROOT)),
                    "masechet": doc["masechet"],
                    "seder": t["seder"],
                    "sefaria_ref": t["title"],
                    "chapters": len(doc["chapters"]),
                    "halachot": sum(len(ch["halachot"]) for ch in doc["chapters"]),
                }
            )
            continue
        raw, edition = fetch_text(t["title"], STEIN_VERSION)
        doc = bavli_text_to_doc(
            raw, title=t["title"], he_title=t["he_title"], masechet=t["masechet"],
            seder=t["seder"], edition=edition, sefaria_ref=t["title"],
        )
        doc["kind"] = "steinsaltz"
        summary.append(_save(doc, dest, t))
        time.sleep(delay_s)
    _write_index(out_root, summary)
    return summary


def download_yerushalmi_steinsaltz(out_root=YERUSHALMI_STEIN_ROOT, delay_s: float = 0.25):
    title = "Steinsaltz on Jerusalem Talmud Shekalim"
    print(f"[Steinsaltz Yerushalmi] {title}")
    raw, edition = fetch_text(title, STEIN_VERSION)
    doc = sefaria_text_to_doc(
        raw, title=title, he_title="ביאור שטיינזלץ על תלמוד ירושלמי שקלים",
        masechet="שקלים", seder="moed", edition=edition,
    )
    doc["kind"] = "steinsaltz"
    summary = [_save(doc, out_root / "moed" / "steinsaltz-yeru-shkalim.json", {"title": title, "seder": "moed"})]
    _write_index(out_root, summary, "steinsaltz-index.json")
    time.sleep(delay_s)
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "what", nargs="*",
        default=["bavli-source", "bavli-steinsaltz", "yerushalmi-steinsaltz"],
        choices=["bavli-source", "bavli-steinsaltz", "yerushalmi-steinsaltz"],
    )
    args = parser.parse_args(argv)
    jobs = args.what
    if "bavli-source" in jobs:
        print(f"Wrote {len(download_bavli_source())} under {BAVLI_SOURCE_ROOT}")
    if "bavli-steinsaltz" in jobs:
        print(f"Wrote {len(download_bavli_steinsaltz())} under {BAVLI_COMMENTARY_ROOT}")
    if "yerushalmi-steinsaltz" in jobs:
        print(f"Wrote {len(download_yerushalmi_steinsaltz())} Yerushalmi Steinsaltz files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

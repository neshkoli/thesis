"""Run Talmud name search for a fixed list of persons and write JSON + summary."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from talmud_search import ROOT, find_name_hits, load_docs

OUT_DIR = ROOT / "search-results"
COMMENTARY_OUT_DIR = ROOT / "search-results-commentary"

PERSONS = [
    # "רבי יהודה הנשיא",
    # "רבי יהודה נשיאה",
    # "רבי יודן נשייא",
    # "רבן גמליאל",
    # "רבן שמעון בן גמליאל",
    # "רבי גמליאל ברבי",
    # "רבי אומר",
    "גמליאל הזקן"
    
    # "חנינא בר חמא",
]


def result_filename(name: str) -> str:
    return name.replace(" ", "_") + ".json"


def corpus_counts(hits: list[dict]) -> dict[str, int]:
    counts = Counter(hit.get("corpus") or "unknown" for hit in hits)
    return {
        "Bavli": counts.get("Bavli", 0),
        "Yerushalmi": counts.get("Yerushalmi", 0),
    }


def write_summary(rows: list[dict], path: Path, *, commentary: bool) -> None:
    searched = (
        "`commentary/Bavli` and `commentary/Yerushalmi`"
        if commentary
        else "`source/Bavli` and `source/Yerushalmi`"
    )
    lines = [
        "# Search summary",
        "",
        f"Searched {searched}.",
        "",
        "| name | Bavli | Yerushalmi | total | file |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['bavli']} | {row['yerushalmi']} | {row['total']} | `{row['file']}` |"
        )
    lines.extend(
        [
            "",
            f"**Grand total:** {sum(row['total'] for row in rows)}",
            f"**Bavli:** {sum(row['bavli'] for row in rows)}",
            f"**Yerushalmi:** {sum(row['yerushalmi'] for row in rows)}",
            "",
            "Notes:",
            "",
            "- `רבי אומר` is the phrase “Rabbi says”, not a personal name.",
            "- Name spelling variants (for example נשייא / נשיאה) follow `talmud_search.py`.",
            "- Search source with: `python3 talmud_search.py --json \"רבי יוחנן\"`",
            "- Search commentary with: `python3 talmud_search.py --commentary --json \"רבי יוחנן\"`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search a fixed list of persons in Talmud JSON.")
    parser.add_argument(
        "--commentary",
        action="store_true",
        help="Search Steinsaltz commentary instead of the source texts",
    )
    args = parser.parse_args(argv)
    out_dir = COMMENTARY_OUT_DIR if args.commentary else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = load_docs(commentary=args.commentary)
    rows: list[dict] = []
    for name in PERSONS:
        hits = find_name_hits(docs, name)
        counts = corpus_counts(hits)
        filename = result_filename(name)
        payload = {
            "query": name,
            "layer": "commentary" if args.commentary else "source",
            "total": len(hits),
            "by_corpus": counts,
            "hits": hits,
        }
        (out_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        row = {
            "name": name,
            "bavli": counts["Bavli"],
            "yerushalmi": counts["Yerushalmi"],
            "total": len(hits),
            "file": filename,
        }
        rows.append(row)
        print(f"{name}: {row['total']} (Bavli {row['bavli']}, Yerushalmi {row['yerushalmi']}) -> {filename}")

    write_summary(rows, out_dir / "summary.md", commentary=args.commentary)
    (out_dir / "summary.json").write_text(
        json.dumps(
            {
                "layer": "commentary" if args.commentary else "source",
                "names": [
                    {
                        "name": row["name"],
                        "bavli": row["bavli"],
                        "yerushalmi": row["yerushalmi"],
                        "total": row["total"],
                        "file": row["file"],
                    }
                    for row in rows
                ],
                "grand_total": sum(row["total"] for row in rows),
                "grand_total_bavli": sum(row["bavli"] for row in rows),
                "grand_total_yerushalmi": sum(row["yerushalmi"] for row in rows),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

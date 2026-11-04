#!/usr/bin/env python3
"""Convert downloaded Yerushalmi Meir PDFs into hierarchical JSON files."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from yerushalmi_parse import parse_masechet_text

ROOT = Path(__file__).resolve().parent
PDF_ROOT = ROOT / "pdfs"
JSON_ROOT = ROOT / "commentary" / "Yerushalmi"
MANIFEST = ROOT / "pdf-manifest.json"


def extract_pdf_text(pdf_path: Path) -> str:
    return subprocess.check_output(
        ["pdftotext", "-enc", "UTF-8", str(pdf_path), "-"],
        text=True,
    )


def section_count(doc: dict) -> int:
    return sum(len(ch["halachot"]) for ch in doc.get("chapters", []))


def main() -> int:
    with MANIFEST.open(encoding="utf-8") as f:
        manifest = json.load(f)

    JSON_ROOT.mkdir(parents=True, exist_ok=True)
    summary = []

    for item in manifest["pdfs"]:
        pdf_path = ROOT / item["local_path"]
        rel = Path(item["local_path"]).relative_to("pdfs")
        out_path = JSON_ROOT / rel.with_suffix(".json")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        raw = extract_pdf_text(pdf_path)
        title = item.get("title", "").strip().rstrip(",")
        seder = rel.parts[0] if len(rel.parts) > 1 else None
        doc = parse_masechet_text(raw, title=title)
        doc["seder"] = seder
        doc["source_pdf"] = item["local_path"]
        doc["source_url"] = item["url"]
        n = section_count(doc)
        empty = 0
        if doc["chapters"]:
            empty = sum(1 for ch in doc["chapters"] for h in ch["halachot"] if not h["text"])
        else:
            empty = 0 if doc.get("text") else 1

        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary.append(
            {
                "json": str(out_path.relative_to(ROOT)),
                "masechet": doc.get("masechet") or title,
                "chapters": len(doc["chapters"]),
                "halachot": n if n else (1 if doc.get("text") else 0),
                "empty": empty,
            }
        )
        print(
            f"{out_path.relative_to(ROOT)}  masechet={doc.get('masechet') or title}  "
            f"chapters={len(doc['chapters'])}  halachot={n}  empty={empty}"
        )

    (JSON_ROOT / "index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {len(summary)} JSON files under commentary/Yerushalmi/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

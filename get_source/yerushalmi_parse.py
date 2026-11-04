"""Parse Yerushalmi Meir PDF text into hierarchical JSON."""

from __future__ import annotations

import re
from typing import Any

BIDI_RE = re.compile(r"[\u202a-\u202e\u200e\u200f\ufeff]")
PAGE_NUM_RE = re.compile(r"(?m)^\s*\d+\s*$")
MASECHET_NAME = r"[\u05d0-\u05ea]+(?:\s+[\u05d0-\u05ea]+){0,3}"
SECTION_RE = re.compile(
    rf"(?:תלמוד\s+ירושלמי\s*\((?P<edition>[^)]+)\)\s*מסכת\s+(?P<masechet>{MASECHET_NAME})\s+)?"
    rf"פרק\s+(?P<perek>[\u05d0-\u05ea]{{1,4}})\s+"
    rf"הלכה\s+(?P<halacha>[\u05d0-\u05ea]{{1,4}})"
)

HEBREW_VALUES = {
    "א": 1,
    "ב": 2,
    "ג": 3,
    "ד": 4,
    "ה": 5,
    "ו": 6,
    "ז": 7,
    "ח": 8,
    "ט": 9,
    "י": 10,
    "כ": 20,
    "ל": 30,
    "מ": 40,
    "נ": 50,
    "ס": 60,
    "ע": 70,
    "פ": 80,
    "צ": 90,
    "ק": 100,
}


def hebrew_to_int(letters: str) -> int:
    letters = letters.replace('"', "").replace("״", "").replace("'", "")
    if letters == "טו":
        return 15
    if letters == "טז":
        return 16
    return sum(HEBREW_VALUES[ch] for ch in letters)


def clean_extracted_text(raw: str) -> str:
    text = BIDI_RE.sub("", raw)
    text = text.replace("\x0c", "\n")
    text = PAGE_NUM_RE.sub("", text)
    text = re.sub(r"([.:;,])(?=[\u05d0-\u05ea'’])", r"\1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_body(text: str) -> str:
    text = re.sub(r"([.:;,])(?=[\u05d0-\u05ea'’])", r"\1 ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_masechet_text(raw: str, title: str | None = None) -> dict[str, Any]:
    text = clean_extracted_text(raw)
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return {
            "title": title,
            "masechet": None,
            "edition": None,
            "chapters": [],
            "text": _normalize_body(text),
        }

    names: list[str] = []
    edition = None
    for match in matches:
        if match.group("masechet"):
            names.append(re.sub(r"\s+", " ", match.group("masechet")).strip())
            if match.group("edition"):
                edition = match.group("edition").strip()
    masechet = max(names, key=len) if names else None

    preamble = _normalize_body(text[: matches[0].start()])
    sections: list[dict[str, Any]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = _normalize_body(text[match.end() : end])
        if not body:
            continue
        perek = match.group("perek")
        halacha = match.group("halacha")
        sections.append(
            {
                "perek": perek,
                "perek_number": hebrew_to_int(perek),
                "halacha": halacha,
                "halacha_number": hebrew_to_int(halacha),
                "text": body,
            }
        )

    chapters: list[dict[str, Any]] = []
    for section in sections:
        if not chapters or chapters[-1]["perek"] != section["perek"]:
            chapters.append(
                {
                    "perek": section["perek"],
                    "perek_number": section["perek_number"],
                    "halachot": [],
                }
            )
        chapters[-1]["halachot"].append(
            {
                "halacha": section["halacha"],
                "halacha_number": section["halacha_number"],
                "perek": section["perek"],
                "perek_number": section["perek_number"],
                "text": section["text"],
            }
        )

    return {
        "title": title or (f"מסכת {masechet}" if masechet else None),
        "masechet": masechet,
        "edition": edition,
        "preamble": preamble or None,
        "chapters": chapters,
    }

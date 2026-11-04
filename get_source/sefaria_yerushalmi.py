"""Convert Sefaria Jerusalem Talmud API payloads into searchable JSON."""

from __future__ import annotations

import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "source" / "Yerushalmi"

SEFARIA_API = "https://www.sefaria.org/api"
USER_AGENT = "yerushalmi-source-download/1.0 (local research)"

NIKKUD_RE = re.compile(r"[\u0591-\u05c7]")
HTML_RE = re.compile(r"<[^>]+>")

SEDER_SLUG = {
    "Seder Zeraim": "zraim",
    "Seder Moed": "moed",
    "Seder Nashim": "nashim",
    "Seder Nezikin": "nezikin",
    "Seder Tahorot": "taharot",
}

# Filenames match the existing commentary JSON layout.
FILE_SLUG = {
    "Jerusalem Talmud Berakhot": "yeru-brachot",
    "Jerusalem Talmud Peah": "yeru-peah",
    "Jerusalem Talmud Demai": "yeru-demai",
    "Jerusalem Talmud Kilayim": "yeru-kilayim",
    "Jerusalem Talmud Sheviit": "yeru-shviit",
    "Jerusalem Talmud Terumot": "yeru-trumot",
    "Jerusalem Talmud Maasrot": "yeru-maasrot",
    "Jerusalem Talmud Maaser Sheni": "yeru-maaser-sheni",
    "Jerusalem Talmud Challah": "yeru-chala",
    "Jerusalem Talmud Orlah": "yeru-orla",
    "Jerusalem Talmud Bikkurim": "yeru-bikurim",
    "Jerusalem Talmud Shabbat": "yeru-shabat",
    "Jerusalem Talmud Eruvin": "yeru-eruvin",
    "Jerusalem Talmud Pesachim": "yeru-psachim",
    "Jerusalem Talmud Yoma": "yeru-yoma",
    "Jerusalem Talmud Shekalim": "yeru-shkalim",
    "Jerusalem Talmud Sukkah": "yeru-suka",
    "Jerusalem Talmud Rosh Hashanah": "yeru-rosh-hashana",
    "Jerusalem Talmud Beitzah": "yeru-beiza",
    "Jerusalem Talmud Taanit": "yeru-taanit",
    "Jerusalem Talmud Megillah": "yeru-megila",
    "Jerusalem Talmud Chagigah": "yeru-chagiga",
    "Jerusalem Talmud Moed Katan": "yeru-moed-katan",
    "Jerusalem Talmud Yevamot": "yeru-yevamot",
    "Jerusalem Talmud Sotah": "yeru-sota",
    "Jerusalem Talmud Ketubot": "yeru-ktubot",
    "Jerusalem Talmud Nedarim": "yeru-nedarim",
    "Jerusalem Talmud Nazir": "yeru-nazir",
    "Jerusalem Talmud Gittin": "yeru-gitin",
    "Jerusalem Talmud Kiddushin": "yeru-kidushin",
    "Jerusalem Talmud Bava Kamma": "yeru-kama",
    "Jerusalem Talmud Bava Metzia": "yeru-metzia",
    "Jerusalem Talmud Bava Batra": "yeru-batra",
    "Jerusalem Talmud Sanhedrin": "yeru-sanhedrin",
    "Jerusalem Talmud Shevuot": "yeru-shvuot",
    "Jerusalem Talmud Avodah Zarah": "yeru-avoda-zara",
    "Jerusalem Talmud Makkot": "yeru-makot",
    "Jerusalem Talmud Horayot": "yeru-horayot",
    "Jerusalem Talmud Niddah": "yeru-nida",
}

ONES = "אבגדהוזחט"
TENS = "יכלמנסעפצ"


def int_to_hebrew(n: int) -> str:
    if n <= 0:
        raise ValueError(f"cannot convert {n} to Hebrew numerals")
    if n == 15:
        return "טו"
    if n == 16:
        return "טז"
    parts: list[str] = []
    hundreds, n = divmod(n, 100)
    if hundreds:
        parts.append("קרשת"[hundreds - 1] if hundreds <= 4 else "ת" * (hundreds - 4) + "ק")
    tens, ones = divmod(n, 10)
    if tens:
        parts.append(TENS[tens - 1])
    if ones:
        parts.append(ONES[ones - 1])
    return "".join(parts)


def normalize_hebrew(text: str) -> str:
    text = HTML_RE.sub("", text or "")
    text = NIKKUD_RE.sub("", text)
    text = text.replace("\u05f3", "'").replace("׳", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _join_segments(segments: Any) -> str:
    if isinstance(segments, str):
        return normalize_hebrew(segments)
    if not isinstance(segments, list):
        return ""
    parts = [normalize_hebrew(p) for p in segments if isinstance(p, str)]
    return " ".join(p for p in parts if p)


def sefaria_text_to_doc(
    chapters_raw: list[Any],
    *,
    title: str,
    he_title: str,
    masechet: str,
    seder: str,
    edition: str | None,
) -> dict[str, Any]:
    chapters: list[dict[str, Any]] = []
    for chap_i, chap in enumerate(chapters_raw or [], 1):
        if not isinstance(chap, list):
            continue
        halachot: list[dict[str, Any]] = []
        for hal_i, hal in enumerate(chap, 1):
            text = _join_segments(hal)
            if not text:
                continue
            halachot.append(
                {
                    "halacha": int_to_hebrew(hal_i),
                    "halacha_number": hal_i,
                    "perek": int_to_hebrew(chap_i),
                    "perek_number": chap_i,
                    "sefaria_ref": f"{title} {chap_i}:{hal_i}",
                    "text": text,
                }
            )
        if not halachot:
            continue
        chapters.append(
            {
                "perek": int_to_hebrew(chap_i),
                "perek_number": chap_i,
                "halachot": halachot,
            }
        )
    return {
        "title": he_title,
        "masechet": masechet,
        "seder": seder,
        "sefaria_ref": title,
        "edition": edition,
        "source": "sefaria",
        "chapters": chapters,
    }


def _http_get_json(url: str) -> Any:
    last: Exception | None = None
    for attempt in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                exc.close()
            except Exception:
                pass
            if exc.code not in {500, 502, 503, 504}:
                raise
            last = exc
            time.sleep(2 ** attempt)
        except http.client.IncompleteRead:
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise last or RuntimeError(f"failed to fetch {url}")


def list_yerushalmi_tractates() -> list[dict[str, str]]:
    toc = _http_get_json(f"{SEFARIA_API}/index/")
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
        if (
            isinstance(title, str)
            and title.startswith("Jerusalem Talmud ")
            and " on " not in title
            and cats[:2] == ["Talmud", "Yerushalmi"]
            and title in FILE_SLUG
        ):
            seder_cat = next((c for c in cats if c in SEDER_SLUG), "")
            found.append(
                {
                    "title": title,
                    "he_title": nodes.get("heTitle") or title,
                    "masechet": (nodes.get("heTitle") or "").replace("תלמוד ירושלמי ", ""),
                    "seder": SEDER_SLUG.get(seder_cat, seder_cat.lower()),
                    "slug": FILE_SLUG[title],
                }
            )
        walk(nodes.get("contents") or nodes.get("nodes"))

    walk(toc)
    return found


def fetch_tractate_hebrew(title: str) -> tuple[list[Any], str | None]:
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = (
        f"{SEFARIA_API}/v3/texts/{encoded}"
        "?return_format=text_only&version=hebrew"
    )
    data = _http_get_json(url)
    versions = data.get("versions") or []
    if not versions:
        raise RuntimeError(f"no Hebrew version for {title}")
    text = versions[0].get("text")
    if not isinstance(text, list):
        raise RuntimeError(f"unexpected text shape for {title}")
    edition = versions[0].get("versionTitle")
    return text, edition


def download_all(out_root: Path = SOURCE_ROOT, delay_s: float = 0.3) -> list[dict[str, Any]]:
    out_root.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, Any]] = []
    tractates = list_yerushalmi_tractates()
    if len(tractates) != 39:
        raise RuntimeError(f"expected 39 Yerushalmi masechtot, found {len(tractates)}")
    for i, t in enumerate(tractates, 1):
        print(f"[{i}/{len(tractates)}] {t['title']}")
        raw, edition = fetch_tractate_hebrew(t["title"])
        doc = sefaria_text_to_doc(
            raw,
            title=t["title"],
            he_title=t["he_title"],
            masechet=t["masechet"],
            seder=t["seder"],
            edition=edition,
        )
        dest = out_root / t["seder"] / f"{t['slug']}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n_hal = sum(len(ch["halachot"]) for ch in doc["chapters"])
        summary.append(
            {
                "json": str(dest.relative_to(ROOT)),
                "masechet": doc["masechet"],
                "seder": t["seder"],
                "sefaria_ref": t["title"],
                "chapters": len(doc["chapters"]),
                "halachot": n_hal,
            }
        )
        time.sleep(delay_s)
    (out_root / "index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    summary = download_all()
    print(f"Wrote {len(summary)} masechtot under {SOURCE_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

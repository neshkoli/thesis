#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Bundler for Patriarchate Research Website (אתר מחקר שושלת הנשיאים)
Synchronized 100% with Thesis Chapter 8:
"תמורות בתפקיד הנשיא: דפוסי מנהיגות בראי הניתוח הכמותי"

Generates static JavaScript ES-modules:
- thesis-website/data/prompts_data.js
- thesis-website/data/summary_data.js
- thesis-website/data/default_data.js
"""

import os
import sys
import csv
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent / "data"

# The 7 canonical Patriarchs in strict chronological sequence (Table 8.4 in Thesis)
CANONICAL_NESIIM_METADATA = [
    {
        "order": 1,
        "filename": "רבן_גמליאל_הזקן_classified.csv",
        "nasi_name": "רבן גמליאל הזקן",
        "display_name": "רבן גמליאל הזקן",
        "generation": "בית שני (תנאים א׳)",
        "short_gen": "בית שני",
        "era": "בית שני",
        "years": "20 – 50 לספירה בקירוב",
        "period": "תקופה א׳: התבססות ועיצוב"
    },
    {
        "order": 2,
        "filename": "רבן_שמעון_בן_גמליאל_הראשון_classified.csv",
        "nasi_name": "רבן שמעון בן גמליאל הראשון",
        "display_name": "רשב\"ג הראשון",
        "generation": "ערב החורבן (תנאים ב׳)",
        "short_gen": "חורבן",
        "era": "חורבן",
        "years": "50 – 70 לספירה (המרד הגדול)",
        "period": "תקופה א׳: התבססות ועיצוב"
    },
    {
        "order": 3,
        "filename": "רבן_גמליאל_דיבנה_classified.csv",
        "nasi_name": "רבן גמליאל דיבנה",
        "display_name": "רבן גמליאל דיבנה",
        "generation": "יבנה (תנאים ג׳)",
        "short_gen": "יבנה",
        "era": "יבנה",
        "years": "80 – 115 לספירה",
        "period": "תקופה א׳: התבססות ועיצוב"
    },
    {
        "order": 4,
        "filename": "רבן_שמעון_בן_גמליאל_השני_classified.csv",
        "nasi_name": "רבן שמעון בן גמליאל השני",
        "display_name": "רשב\"ג השני",
        "generation": "אושא (תנאים ד׳)",
        "short_gen": "אושא",
        "era": "אושא",
        "years": "140 – 170 לספירה (לאחר מרד בר כוכבא)",
        "period": "תקופה א׳: התבססות ועיצוב"
    },
    {
        "order": 5,
        "filename": "רבי_יהודה_הנשיא_classified.csv",
        "nasi_name": "רבי יהודה הנשיא",
        "display_name": "רבי יהודה הנשיא ('רבי')",
        "generation": "חתימת המשנה (תנאים ה׳)",
        "short_gen": "חתימת משנה",
        "era": "ציפורי / משנה",
        "years": "175 – 220 לספירה",
        "period": "תקופה א׳: התבססות ועיצוב"
    },
    {
        "order": 6,
        "filename": "רבן_גמליאל_ברבי_classified.csv",
        "nasi_name": "רבן גמליאל ברבי",
        "display_name": "רבן גמליאל ברבי",
        "generation": "דור המעבר (אמוראים א׳)",
        "short_gen": "מעבר",
        "era": "מעבר לתקופת האמוראים",
        "years": "220 – 235 לספירה",
        "period": "תקופה ב׳: ממלכתיות והפרדת רשויות"
    },
    {
        "order": 7,
        "filename": "רבי_יהודה_נשיאה_classified.csv",
        "nasi_name": "רבי יהודה נשיאה",
        "display_name": "רבי יהודה נשיאה",
        "generation": "אמוראי א״י א׳-ב׳ (טבריה)",
        "short_gen": "אמוראים",
        "era": "אמוראים",
        "years": "235 – 275 לספירה",
        "period": "תקופה ב׳: ממלכתיות והפרדת רשויות"
    }
]

# Supplementary figures documented in Chapter 8
SUPPLEMENTARY_NESIIM_METADATA = [
    {
        "order": 0,
        "filename": "הלל_classified.csv",
        "nasi_name": "הלל",
        "display_name": "הלל הזקן",
        "generation": "סוף ימי הבית השני (זוגות)",
        "short_gen": "זוגות",
        "era": "בית שני",
        "years": "30 לפנה״ס – 10 לספירה",
        "period": "תקופה א׳: התבססות ועיצוב",
        "note": "הוחרג מהטבלאות הרשמיות עקב ספק היסטוריוגרפי בשיוכו לשושלת (הערת שוליים 4 בתזה), אך נכלל במניין 2,097 קטעים בתקופה א'."
    },
    {
        "order": 8,
        "filename": "רבן_גמליאל_המאוחר_classified.csv",
        "nasi_name": "רבן גמליאל המאוחר",
        "display_name": "רבן גמליאל בן רבי יהודה נשיאה",
        "generation": "שלהי תקופת האמוראים",
        "short_gen": "אמוראים מאוחר",
        "era": "אמוראים",
        "years": "המאה ה-3 וה-4 לספירה",
        "period": "שלהי האמוראים",
        "note": "נמצאו 7 אזכורים בלבד (2 בבלי, 5 ירושלמי). הוחרג מהמדד הסטטיסטי עקב מיעוט מופעים (סעיף 8.2)."
    },
    {
        "order": 9,
        "filename": "רבן_גמליאל_ספק_classified.csv",
        "nasi_name": "רבן גמליאל ספק",
        "display_name": "רבן גמליאל (ספק זיהוי)",
        "generation": "קטעים ללא הכרעה מובהקת",
        "short_gen": "ספק זיהוי",
        "era": "כללי",
        "note": "קטעים שבהם מופיע השם הגנרי רבן גמליאל ללא עוגנים הקשריים חד-משמעיים (4 קטעים)."
    }
]

# OFFICIAL THESIS TABLE 8.4 VALUES (From Chapter 8 text)
THESIS_TABLE_8_4 = [
    {
        "order": 1,
        "nasi_name": "רבן גמליאל הזקן",
        "display_name": "רבן גמליאל הזקן",
        "generation": "בית שני",
        "intellectual_pct": 39.8,
        "institutional_pct": 43.9,
        "external_pct": 16.3,
        "total_quotes": 66,
        "period": "תקופה א׳"
    },
    {
        "order": 2,
        "nasi_name": "רבן שמעון בן גמליאל הראשון",
        "display_name": "רשב\"ג הראשון",
        "generation": "חורבן",
        "intellectual_pct": 55.3,
        "institutional_pct": 32.9,
        "external_pct": 11.8,
        "total_quotes": 19,
        "period": "תקופה א׳"
    },
    {
        "order": 3,
        "nasi_name": "רבן גמליאל דיבנה",
        "display_name": "רבן גמליאל דיבנה",
        "generation": "יבנה",
        "intellectual_pct": 65.9,
        "institutional_pct": 15.5,
        "external_pct": 18.6,
        "total_quotes": 558,
        "period": "תקופה א׳"
    },
    {
        "order": 4,
        "nasi_name": "רבן שמעון בן גמליאל השני",
        "display_name": "רשב\"ג השני",
        "generation": "אושא",
        "intellectual_pct": 87.8,
        "institutional_pct": 9.3,
        "external_pct": 2.9,
        "total_quotes": 859,
        "period": "תקופה א׳"
    },
    {
        "order": 5,
        "nasi_name": "רבי יהודה הנשיא",
        "display_name": "רבי יהודה הנשיא",
        "generation": "חתימת משנה",
        "intellectual_pct": 91.7,
        "institutional_pct": 5.9,
        "external_pct": 2.4,
        "total_quotes": 555,
        "period": "תקופה א׳"
    },
    {
        "order": 6,
        "nasi_name": "רבן גמליאל ברבי",
        "display_name": "רבן גמליאל ברבי",
        "generation": "מעבר",
        "intellectual_pct": 63.4,
        "institutional_pct": 22.1,
        "external_pct": 14.5,
        "total_quotes": 28,
        "period": "תקופה ב׳"
    },
    {
        "order": 7,
        "nasi_name": "רבי יהודה נשיאה",
        "display_name": "רבי יהודה נשיאה",
        "generation": "אמוראים",
        "intellectual_pct": 42.8,
        "institutional_pct": 22.6,
        "external_pct": 34.6,
        "total_quotes": 83,
        "period": "תקופה ב׳"
    }
]

# Supplementary row for Hillel (from teza-7-15.md table before footnote 4 omission)
HILLEL_TABLE_ENTRY = {
    "order": 0,
    "nasi_name": "הלל הזקן",
    "display_name": "הלל הזקן",
    "generation": "זוגות",
    "intellectual_pct": 66.7,
    "institutional_pct": 24.3,
    "external_pct": 9.0,
    "total_quotes": 40,
    "period": "תקופה א׳",
    "is_supplementary": True
}

# OFFICIAL THESIS TABLE 8.2 VALUES (From Chapter 8 text)
THESIS_TABLE_8_2 = [
    {
        "order": 1,
        "nasi_name": "רבן גמליאל הזקן",
        "display_name": "רבן גמליאל הזקן",
        "bavli": 37,
        "yerushalmi": 29,
        "total": 66,
        "bavli_pct": 56.1,
        "yerushalmi_pct": 43.9,
        "is_included": True
    },
    {
        "order": 2,
        "nasi_name": "רבן שמעון בן גמליאל הראשון",
        "display_name": "רשב\"ג הראשון",
        "bavli": 13,
        "yerushalmi": 6,
        "total": 19,
        "bavli_pct": 68.4,
        "yerushalmi_pct": 31.6,
        "is_included": True
    },
    {
        "order": 3,
        "nasi_name": "רבן גמליאל דיבנה",
        "display_name": "רבן גמליאל דיבנה",
        "bavli": 416,
        "yerushalmi": 142,
        "total": 558,
        "bavli_pct": 74.6,
        "yerushalmi_pct": 25.4,
        "is_included": True
    },
    {
        "order": 4,
        "nasi_name": "רבן שמעון בן גמליאל השני",
        "display_name": "רשב\"ג השני",
        "bavli": 692,
        "yerushalmi": 167,
        "total": 859,
        "bavli_pct": 80.6,
        "yerushalmi_pct": 19.4,
        "is_included": True
    },
    {
        "order": 5,
        "nasi_name": "רבי יהודה הנשיא",
        "display_name": "רבי יהודה הנשיא",
        "bavli": 397,
        "yerushalmi": 158,
        "total": 555,
        "bavli_pct": 71.5,
        "yerushalmi_pct": 28.5,
        "is_included": True
    },
    {
        "order": 6,
        "nasi_name": "רבן גמליאל ברבי",
        "display_name": "רבן גמליאל ברבי",
        "bavli": 17,
        "yerushalmi": 11,
        "total": 28,
        "bavli_pct": 60.7,
        "yerushalmi_pct": 39.3,
        "is_included": True
    },
    {
        "order": 7,
        "nasi_name": "רבי יהודה נשיאה",
        "display_name": "רבי יהודה נשיאה",
        "bavli": 41,
        "yerushalmi": 42,
        "total": 83,
        "bavli_pct": 49.4,
        "yerushalmi_pct": 50.6,
        "is_included": True
    },
    {
        "order": 8,
        "nasi_name": "רבן גמליאל בן רבי יהודה נשיאה",
        "display_name": "רבן גמליאל בן רבי יהודה נשיאה",
        "bavli": 2,
        "yerushalmi": 5,
        "total": 7,
        "bavli_pct": 28.6,
        "yerushalmi_pct": 71.4,
        "is_included": False,
        "exclusion_reason": "מיעוט מופעים - נמוך מכדי לספק ניתוח סטטיסטי"
    },
    {
        "order": 0,
        "nasi_name": "הלל הזקן",
        "display_name": "הלל הזקן",
        "bavli": 25,
        "yerushalmi": 15,
        "total": 40,
        "bavli_pct": 62.5,
        "yerushalmi_pct": 37.5,
        "is_included": False,
        "exclusion_reason": "הוחרג בטבלאות התזה עקב ספק היסטוריוגרפי בשיוכו לשושלת (הערת שוליים 4)"
    }
]

# OFFICIAL TWO-PERIOD MACRO COMPARISON (Section 8.4 in Thesis)
THESIS_PERIODS_MACRO = {
    "period_a": {
        "title": "תקופה א': תקופת ההתבססות והעיצוב",
        "subtitle": "מהלל ורבן גמליאל הזקן ועד רבי יהודה הנשיא",
        "span": "סוף ימי הבית השני ועד סוף דור התנאים (חתימת המשנה)",
        "total_quotes": 2097,
        "internal_pct": 92.0,
        "external_pct": 8.0,
        "description": "הנשיא פועל כ'ראשון בין שווים' בתוך עולם החכמים; סמכותו נובעת מגדלותו בתורה ומהנהגת בית הדין והסנהדרין."
    },
    "period_b": {
        "title": "תקופה ב': תקופת הממלכתיות והפרדת הרשויות",
        "subtitle": "רבן גמליאל ברבי ורבי יהודה נשיאה",
        "span": "תקופת האמוראים (טבריה)",
        "total_quotes": 111,
        "internal_pct": 70.4,
        "external_pct": 29.6,
        "description": "הנשיא מתרחק מן המעורבות האקטיבית בבית המדרש לטובת גינוני כבוד, ייצוג האומה וניהול כוחני, בעוד מונופול הפסיקה האינטלקטואלית עובר לאמוראים."
    }
}


def read_text_file(path: Path) -> str:
    """Read a text file with UTF-8 encoding."""
    if not path.exists():
        print(f"Warning: File {path} does not exist.")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def clean_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def map_to_thesis_norm(val: int) -> float:
    """Map raw model integer scores (0, 1, 2, 3) to official thesis scale (0, 0.25, 0.5, 1.0)."""
    if val == 0:
        return 0.0
    if val == 1:
        return 0.25
    if val == 2:
        return 0.5
    if val >= 3:
        return 1.0
    return 0.0


def parse_classified_csv(file_path: Path):
    """Parse a classified CSV, mapping both raw (0-3) and normalized (0-1) scores."""
    rows = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, r in enumerate(reader):
            corpus = str(r.get("corpus", "")).strip()
            if corpus.upper() in ["TOTAL", "RATIO", "SUMMARY", "AVERAGE"]:
                continue
            
            intellectual_raw = clean_int(r.get("Intellectual", 0))
            institutional_raw = clean_int(r.get("Institutional", 0))
            political_raw = clean_int(r.get("Political", 0))
            aristocratic_raw = clean_int(r.get("Aristocratic", 0))
            external_raw = political_raw + aristocratic_raw
            
            # Map to official thesis scale (0, 0.25, 0.5, 1.0)
            intellectual_norm = map_to_thesis_norm(intellectual_raw)
            institutional_norm = map_to_thesis_norm(institutional_raw)
            political_norm = map_to_thesis_norm(political_raw)
            aristocratic_norm = map_to_thesis_norm(aristocratic_raw)
            external_norm = max(political_norm, aristocratic_norm)
            
            hal_raw = r.get("Halakhic_Activity")
            if hal_raw is None or str(hal_raw).strip() == "" or str(hal_raw).lower() == "null":
                halakhic_activity = None
            else:
                try:
                    halakhic_activity = int(float(hal_raw))
                except (ValueError, TypeError):
                    halakhic_activity = None

            row_data = {
                "id": idx + 1,
                "corpus": corpus,
                "masechet": str(r.get("masechet", "")).strip(),
                "seder": str(r.get("seder", "")).strip(),
                "perek": str(r.get("perek", "")).strip(),
                "perek_number": str(r.get("perek_number", "")).strip(),
                "halacha": str(r.get("halacha", "")).strip(),
                "halacha_number": str(r.get("halacha_number", "")).strip(),
                "daf": str(r.get("daf", "")).strip(),
                "part": str(r.get("part", "")).strip(),
                "sefaria_ref": str(r.get("sefaria_ref", "")).strip(),
                "source_pdf": str(r.get("source_pdf", "")).strip(),
                "matched": str(r.get("matched", "")).strip(),
                "snippet": str(r.get("snippet", "")).strip(),
                # Raw scores (0-3)
                "Intellectual": intellectual_raw,
                "Institutional": institutional_raw,
                "Political": political_raw,
                "Aristocratic": aristocratic_raw,
                "External": external_raw,
                # Official thesis normalized scores (0, 0.25, 0.5, 1.0)
                "Intellectual_norm": intellectual_norm,
                "Institutional_norm": institutional_norm,
                "Political_norm": political_norm,
                "Aristocratic_norm": aristocratic_norm,
                "External_norm": external_norm,
                "Halakhic_Activity": halakhic_activity,
                "Reasoning": str(r.get("Reasoning", "")).strip()
            }
            rows.append(row_data)

    # Clean CSV lines without summary rows
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        clean_lines = []
        for line in lines:
            c = line.split(",")[0].strip().upper()
            if c not in ["TOTAL", "RATIO", "SUMMARY", "AVERAGE"]:
                clean_lines.append(line)
        raw_csv = "".join(clean_lines)

    return rows, raw_csv


def generate_prompts_data():
    """Build prompts_data.js containing thesis methodology chapters and raw prompts."""
    classification_md = read_text_file(WORKSPACE_ROOT / "classification.md")
    gamliel_md = read_text_file(WORKSPACE_ROOT / "classified-gamliel.md")
    rashbag_md = read_text_file(WORKSPACE_ROOT / "classified-rashbag.md")
    
    thesis_methodology_text = {
        "section_8_1": {
            "title": "8.1 מתודולוגיה של מדידת מנהיגות: בניית הכלי הכמותי",
            "content": """חקר מוסד הנשיאות בתקופת המשנה והתלמוד נשען עד כה בעיקר על כלים של ניתוח היסטורי, טקסטואלי ופילולוגי. כדי להוכיח בצורה מובהקת ואמפירית את הטענה המרכזית של מחקר זה — כי חלו תמורות משמעותיות בהגדרת תפקיד הנשיא לאורך הדורות, מהנהגה רוחנית ומשפטית פנימית להנהגה מדינית, ייצוגית ואריסטוקרטית — עולה הצורך בהרחבת ארגז הכלים המחקרי באמצעות מדעי הרוח הדיגיטליים (Digital Humanities).

בהשראת מחקריו של חיים לפין (Lapin) על התפתחות טקסט המשנה, ועבודותיהם של שמידמן, קופל ופורת מפרויקט 'דיקטה' (Dicta) לסיווג טקסטים וביקורת מקורות ממוחשבת, פותח מדד כמותי של 'טקסונומיה תלמודית'. כלי זה אסף ומיין את כלל המופעים של שושלת הנשיאים במקורות התלמודיים (הבבלי והירושלמי) כדי לייצר מדד יחס כמותי בין סוגי ההנהגה על ציר הזמן."""
        },
        "section_8_2": {
            "title": "8.2 איסוף הנתונים, זיהוי האישים ושיטת החישוב",
            "content": """המחקר שאב מעל 2,200 אזכורים של שמות הנשיאים מתוך קורפוס התלמוד הבבלי והירושלמי. הנשיאים המרכזיים עבורם נעשה הניתוח הם: רבן גמליאל הזקן, רשב״ג הראשון, רבן גמליאל דיבנה, רשב״ג השני, רבי יהודה הנשיא, רבן גמליאל ברבי, ורבי יהודה נשיאה.

ביאור הטקסטים: סיווג על גבי טקסט מקור ארמי לא הניב דיוק מספק. לכן, החיפוש והסיווג נעשו על גבי טקסטים הכוללים ביאור עברי מלא (ביאור הרב עדין שטיינזלץ לבבלי מאתר ספריא, וביאור הרב מאיר כהן לירושלמי מאתר דעת).
חלון הטקסט: נשמר מקטע של כ-90 מילים (15 לפני השם ו-75 לאחריו) בצירוף מראי מקום מדויקים. מופעים כפולים באותו חלון אוחדו.
בדיקת תוקף: נערכה בדיקת תוקף ידנית על מדגם אקראי של כ-10% מהטקסטים לווידוא מהימנות הסיווג.
עוגנים הקשריים לזיהוי שמות זהים (Contextual Anchors):
1. רשתות חכמים (זיהוי בני השיח כגון ר' אליעזר ור' יהושע לר"ג דיבנה).
2. עוגנים גאוגרפיים (ירושלים, יבנה, אושא, טבריה).
3. זיהוי מעביר השמועה מול גיבור המעשה (הפרדה בין החכם המצטט לבין הנשיא הנזכר)."""
        },
        "section_8_3": {
            "title": "8.3 מודל הסיווג: שלושת כובעי המנהיגות והתמודדות עם הטיית הקורפוס",
            "content": """התלמוד נוטה תדיר לעטוף אירועים פוליטיים וכלכליים בשיח הלכתי (Corpus Bias). כפי שמציינים ורטיאנן וסאילי (Vartiainen & Saili), קורפוס עתיק אינו חלון שקוף אלא מעוצב על ידי האליטה שחיברה אותו. לפי מודל ה-Bias-Aware Framework של זילמה ולוטרה, אין לראות במעטפת זו רעש סטטיסטי אלא קטגוריה אנליטית.
הטקסונומיה קילפה את 'המעטפת ההלכתית' לפי שלושה צירי סמכות מרכזיים:
1. סמכות אינטלקטואלית-תורנית: הנשיא כחכם המוסר מסורת, דורש דרשות ופוסק הלכה מכוח סברתו.
2. סמכות מוסדית-חקיקתית: הנשיא כראש הסנהדרין המתקין תקנות ציבוריות ('מפני תיקון העולם'), ממנה דיינים וקובע את לוח השנה.
3. הנהגה חיצונית-מעמדית: הנשיא כראש האומה מול הרשויות הזרות, וכאיש שררה בעל הון, שכירי חרב, כפייה וגינוני כבוד.

סולם הניקוד:
0 = לא קיים כלל
0.25 = רמז עקיף
0.5 = נוכחות בינונית
1.0 = זהו מוקד הקטע
הנתונים נורמלו למדד יחסי (100%) כדי לנטרל את פערי נפח הציטוטים בין הנשיאים."""
        },
        "section_8_4": {
            "title": "8.4 ממצאי המחקר וחלוקה לשתי תקופות",
            "content": """הממצאים מצביעים על שחיקה הדרגתית של הסמכות האינטלקטואלית והמוסדית לטובת זינוק חד בהנהגה החיצונית והשררה.
חלוקת הנתונים לשתי תקופות היסטוריות רחבות סביב פטירת רבי יהודה הנשיא:
תקופה א' (התבססות ועיצוב - הלל עד רבי יהודה הנשיא, 2,097 קטעים):
- הנהגה פנימית: 92.0%
- הנהגה חיצונית: 8.0%
תקופה ב' (ממלכתיות והפרדת רשויות - רבן גמליאל ברבי ורבי יהודה נשיאה, 111 קטעים):
- הנהגה פנימית: 70.4%
- הנהגה חיצונית: 29.6% (זינוק של פי 14.4 מרבי!)"""
        }
    }

    prompts_obj = {
        "thesis_methodology": thesis_methodology_text,
        "prompts": [
            {
                "id": "prompt-taxonomy",
                "title": "פרומפט סיווג טקסונומי וניקוד צירי הסמכות (classification.md)",
                "filename": "classification.md",
                "badge": "ליבת הסיווג",
                "description": "הפרומפט המרכזי שנשלח למודל השפה (Gemini) לסריקת כל קטע תלמודי, חילוץ ציוני הסמכות בשלושת הצירים וקביעת מדד האקטיביות ההלכתית.",
                "content": classification_md
            },
            {
                "id": "prompt-gamliel",
                "title": "פרומפט הבחנה וזיהוי: שושלת רבן גמליאל (classified-gamliel.md)",
                "filename": "classified-gamliel.md",
                "badge": "זיהוי אישים",
                "description": "אלגוריתם ההבחנה בין ארבעת הנשיאים שנקראו 'רבן גמליאל' (הזקן, דיבנה, ברבי, והמאוחר) תוך שימוש ברשתות חכמים ועוגנים כרונולוגיים.",
                "content": gamliel_md
            },
            {
                "id": "prompt-rashbag",
                "title": "פרומפט הבחנה וזיהוי: רשב\"ג הראשון מול השני (classified-rashbag.md)",
                "filename": "classified-rashbag.md",
                "badge": "זיהוי אישים",
                "description": "קריטריונים היסטוריים להפרדה בין רבן שמעון בן גמליאל הזקן (ערב החורבן) לרשב\"ג השני (דור אושא שלאחר מרד בר כוכבא).",
                "content": rashbag_md
            }
        ]
    }
    
    prompts_js = f"// Automatically generated by bundle_data.py\nexport const PROMPTS_DATA = {json.dumps(prompts_obj, ensure_ascii=False, indent=2)};\n"
    prompts_path = OUTPUT_DIR / "prompts_data.js"
    with open(prompts_path, "w", encoding="utf-8") as f:
        f.write(prompts_js)
    print(f"Generated {prompts_path} ({len(prompts_js)} bytes)")


def generate_data_bundles():
    """Build summary_data.js and default_data.js."""
    all_passages = {}
    default_csv_data = {}
    
    # Process all canonical and supplementary files
    all_meta = CANONICAL_NESIIM_METADATA + SUPPLEMENTARY_NESIIM_METADATA
    for meta in all_meta:
        csv_path = WORKSPACE_ROOT / "classified-results" / meta["filename"]
        if csv_path.exists():
            rows, raw_csv = parse_classified_csv(csv_path)
            all_passages[meta["filename"]] = rows
            default_csv_data[meta["filename"]] = raw_csv
        else:
            print(f"Warning: {csv_path} not found!")

    # Official Thesis Proof Cards for Executive Presentation
    proof_cards = [
        {
            "id": "proof-institutional-peak",
            "title": "שיא החקיקה המוסדית בבית שני",
            "badge": "סמכות מוסדית-חקיקתית",
            "stat": "43.9%",
            "subtitle": "מכלל פעילות רבן גמליאל הזקן",
            "description": "בתקופת הבית השני והתנאים המוקדמת, מוקד הסמכות היה תקנות ציבוריות לעיצוב החברה (כגון תקנות גיטין 'מפני תיקון העולם' והסדרת עדות החודש).",
            "color": "#059669"
        },
        {
            "id": "proof-intellectual-peak",
            "title": "שיא הריכוזיות התורנית בחתימת המשנה",
            "badge": "סמכות אינטלקטואלית",
            "stat": "91.7%",
            "subtitle": "אצל רבי יהודה הנשיא ('רבי')",
            "description": "שיא חסר תקדים בסמכות התורנית סביב עריכת המשנה וחתימתה, תוך הפיכת בית הנשיא למוקד הפסיקה והסמכות ההלכתית הבלעדית.",
            "color": "#2563eb"
        },
        {
            "id": "proof-external-surge",
            "title": "זינוק חסר תקדים בהנהגה חיצונית ושררה",
            "badge": "הנהגה חיצונית-מעמדית",
            "stat": "34.6%",
            "subtitle": "אצל רבי יהודה נשיאה (זינוק פי 14.4 מרבי!)",
            "description": "בתקופת האמוראים בטבריה, ההנהגה החיצונית (קשרים עם רומא, עושר, אריסטוקרטיה ועבדי הנשיא) מזנקת מ-2.4% בלבד בימי רבי ל-34.6% בימי נכדו.",
            "color": "#9333ea"
        },
        {
            "id": "proof-macro-periods",
            "title": "הפרדת הרשויות ושחיקת המעמד הפנימי",
            "badge": "השוואת שתי התקופות",
            "stat": "29.6%",
            "subtitle": "שררה חיצונית בתקופה ב' (לעומת 8.0% בתקופה א')",
            "description": "צניחה חדה של הסמכות הפנימית מ-92.0% בתקופת העיצוב ל-70.4% בלבד בתקופת הממלכתיות, כאשר מונופול הפסיקה עבר לידי האמוראים.",
            "color": "#d97706"
        }
    ]

    # Structure summary_data.js
    summary_obj = {
        "canonical_nesiim": CANONICAL_NESIIM_METADATA,
        "supplementary_nesiim": SUPPLEMENTARY_NESIIM_METADATA,
        "thesis_table_8_4": THESIS_TABLE_8_4,
        "hillel_table_entry": HILLEL_TABLE_ENTRY,
        "thesis_table_8_2": THESIS_TABLE_8_2,
        "thesis_periods_macro": THESIS_PERIODS_MACRO,
        "proof_cards": proof_cards
    }
    
    summary_js = f"// Automatically generated by bundle_data.py\nexport const SUMMARY_DATA = {json.dumps(summary_obj, ensure_ascii=False, indent=2)};\n"
    summary_path = OUTPUT_DIR / "summary_data.js"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_js)
    print(f"Generated {summary_path} ({len(summary_js)} bytes)")

    # Generate default_data.js (Structured records & raw CSV compatibility)
    default_data_js = f"""// Automatically generated by bundle_data.py
export const PASSAGES_DATA = {json.dumps(all_passages, ensure_ascii=False, indent=2)};

export const DEFAULT_CSV_DATA = {json.dumps(default_csv_data, ensure_ascii=False, indent=2)};
"""
    default_data_path = OUTPUT_DIR / "default_data.js"
    with open(default_data_path, "w", encoding="utf-8") as f:
        f.write(default_data_js)
    print(f"Generated {default_data_path} ({len(default_data_js)} bytes)")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Bundling research data into {OUTPUT_DIR}...")
    generate_prompts_data()
    generate_data_bundles()
    print("All Phase 1 data bundles compiled successfully!")


if __name__ == "__main__":
    main()

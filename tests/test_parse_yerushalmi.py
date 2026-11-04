from yerushalmi_parse import hebrew_to_int, parse_masechet_text, clean_extracted_text


def test_hebrew_to_int_basic():
    assert hebrew_to_int("א") == 1
    assert hebrew_to_int("י") == 10
    assert hebrew_to_int("יא") == 11
    assert hebrew_to_int("טו") == 15
    assert hebrew_to_int("טז") == 16


def test_clean_strips_bidi_and_page_numbers():
    raw = "\u202bתלמוד\u202c\n\n\u202a1\u202c\n\nמתני':לפני"
    cleaned = clean_extracted_text(raw)
    assert "\u202b" not in cleaned
    assert cleaned.startswith("תלמוד")
    assert "מתני': לפני" in cleaned or "מתני' : לפני" in cleaned


SAMPLE_TWO_HALACHOT = """
תלמוד ירושלמי (וילנא) מסכת עבודה זרה

פרק א הלכה א
[דף א עמוד א] מתני' :לפני אידיהן של נכרים.
גמ' :רבי חמא בר עוקבה.

תלמוד ירושלמי (וילנא) מסכת עבודה זרה

פרק א הלכה ב
מתני' :אלו הן אידיהן.
"""


def test_splits_on_perek_halacha_headers():
    doc = parse_masechet_text(SAMPLE_TWO_HALACHOT)
    assert doc["masechet"] == "עבודה זרה"
    assert doc["edition"] == "וילנא"
    assert len(doc["chapters"]) == 1
    assert doc["chapters"][0]["perek"] == "א"
    assert doc["chapters"][0]["perek_number"] == 1
    halachot = doc["chapters"][0]["halachot"]
    assert [h["halacha"] for h in halachot] == ["א", "ב"]
    assert "לפני אידיהן" in halachot[0]["text"]
    assert "אלו הן אידיהן" in halachot[1]["text"]
    assert "פרק א הלכה" not in halachot[0]["text"]
    assert "תלמוד ירושלמי" not in halachot[0]["text"]


def test_concatenated_header_on_one_line():
    text = """
תלמוד ירושלמי (וילנא) מסכת ברכות פרק א הלכה ב
מתני’ :מאימתי קורין את שמע בשחרית?
"""
    doc = parse_masechet_text(text)
    assert doc["masechet"] == "ברכות"
    h = doc["chapters"][0]["halachot"][0]
    assert h["perek"] == "א"
    assert h["halacha"] == "ב"
    assert "מאימתי קורין" in h["text"]


def test_header_split_across_lines():
    text = """
תלמוד ירושלמי (וילנא) מסכת סוכה פרק

ה הלכה ו

מתני' :אין פוחתין מכ"א תקיעות במקדש
"""
    doc = parse_masechet_text(text)
    h = doc["chapters"][0]["halachot"][0]
    assert h["perek"] == "ה"
    assert h["halacha"] == "ו"
    assert "אין פוחתין" in h["text"]


def test_groups_halachot_into_chapters():
    text = """
פרק א הלכה י
סוף פרק א.

פרק ב הלכה א
תחילת פרק ב.
"""
    doc = parse_masechet_text(text)
    assert [c["perek"] for c in doc["chapters"]] == ["א", "ב"]
    assert doc["chapters"][0]["halachot"][0]["halacha_number"] == 10
    assert doc["chapters"][1]["halachot"][0]["halacha_number"] == 1


def test_skips_empty_section_when_headers_are_consecutive():
    text = """
פרק ה הלכה ו

פרק ה הלכה ז
תוכן הלכה ז.
"""
    doc = parse_masechet_text(text)
    assert [h["halacha"] for h in doc["chapters"][0]["halachot"]] == ["ז"]


def test_hakdama_has_plain_text_without_chapters():
    text = "ירושלמי מאיר\nהקדמה לביאור."
    doc = parse_masechet_text(text, title="הקדמה")
    assert doc["chapters"] == []
    assert "הקדמה לביאור" in doc["text"]

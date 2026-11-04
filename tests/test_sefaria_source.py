from sefaria_yerushalmi import (
    int_to_hebrew,
    normalize_hebrew,
    sefaria_text_to_doc,
)


def test_int_to_hebrew():
    assert int_to_hebrew(1) == "א"
    assert int_to_hebrew(12) == "יב"
    assert int_to_hebrew(15) == "טו"
    assert int_to_hebrew(16) == "טז"


def test_normalize_strips_nikkud():
    assert normalize_hebrew("רִבִּי יוֹחָנָן") == "רבי יוחנן"


def test_sefaria_text_to_doc_keeps_perek_and_halacha():
    raw = [
        [
            ["משנה: מאימתי קורין", "הלכה: אנן תנינן"],
            ["משנה: מאימתי בשחרית"],
        ],
        [
            ["היה קורא בתורה"],
        ],
    ]
    doc = sefaria_text_to_doc(
        raw,
        title="Jerusalem Talmud Berakhot",
        he_title="תלמוד ירושלמי ברכות",
        masechet="ברכות",
        seder="zraim",
        edition="Guggenheimer",
    )
    assert doc["masechet"] == "ברכות"
    assert doc["seder"] == "zraim"
    assert doc["sefaria_ref"] == "Jerusalem Talmud Berakhot"
    assert len(doc["chapters"]) == 2
    ch1 = doc["chapters"][0]
    assert ch1["perek_number"] == 1
    assert ch1["perek"] == "א"
    assert ch1["halachot"][0]["halacha_number"] == 1
    assert ch1["halachot"][0]["halacha"] == "א"
    assert "מאימתי קורין" in ch1["halachot"][0]["text"]
    assert "אנן תנינן" in ch1["halachot"][0]["text"]
    assert ch1["halachot"][1]["halacha_number"] == 2
    assert doc["chapters"][1]["perek_number"] == 2
    assert doc["chapters"][1]["halachot"][0]["sefaria_ref"] == "Jerusalem Talmud Berakhot 2:1"

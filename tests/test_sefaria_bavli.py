from sefaria_bavli import bavli_text_to_doc, daf_to_index, index_to_daf


def test_index_to_daf():
    assert index_to_daf(2) == ("2a", 2, "a")
    assert index_to_daf(3) == ("2b", 2, "b")
    assert daf_to_index("2a") == 2
    assert daf_to_index("2b") == 3
    assert daf_to_index("3a") == 4


def test_bavli_text_to_doc_keeps_daf():
    raw = [[], [], ["מאימתי קורין את שמע", "משעה שהכהנים"], ["דילמא ביאת אורו"]]
    doc = bavli_text_to_doc(
        raw,
        title="Berakhot",
        he_title="ברכות",
        masechet="ברכות",
        seder="zraim",
        edition="William Davidson Edition - Aramaic",
        sefaria_ref="Berakhot",
    )
    assert doc["masechet"] == "ברכות"
    assert doc["corpus"] == "Bavli"
    assert [ch["daf"] for ch in doc["chapters"]] == ["2a", "2b"]
    assert doc["chapters"][0]["perek_number"] == 2
    assert "מאימתי קורין" in doc["chapters"][0]["halachot"][0]["text"]
    assert doc["chapters"][0]["halachot"][0]["sefaria_ref"] == "Berakhot 2a"

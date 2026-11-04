from sefaria_midrash import _is_same_book_chapter, jagged_to_chapters, midrash_to_doc


def test_same_book_chapter_next():
    title = "Yalkut Shimoni on Torah"
    assert _is_same_book_chapter(title, "Yalkut Shimoni on Torah 2")
    assert not _is_same_book_chapter(title, title)
    assert not _is_same_book_chapter(title, "Yalkut Shimoni on Nach 1")
    assert not _is_same_book_chapter(title, None)


def test_jagged_chapters_and_paragraphs():
    raw = [["רבי הושעיה רבה פתח", "דבר אחר"], ["ויאמר אלהים"]]
    chapters = jagged_to_chapters(raw, sefaria_ref="Bereshit Rabbah")
    assert len(chapters) == 2
    assert chapters[0]["perek_number"] == 1
    assert chapters[0]["halachot"][0]["halacha_number"] == 1
    assert "הושעיה" in chapters[0]["halachot"][0]["text"]
    assert chapters[1]["halachot"][0]["sefaria_ref"] == "Bereshit Rabbah 2:1"


def test_midrash_to_doc_sets_corpus():
    doc = midrash_to_doc(
        [[["פתח רבי"]], [["דבר אחר"]]],
        title="Bereshit Rabbah",
        he_title="בראשית רבה",
        category="midrash-rabbah",
        edition="Midrash Rabbah",
    )
    assert doc["corpus"] == "Midrash"
    assert doc["masechet"] == "בראשית רבה"
    assert doc["sefaria_ref"] == "Bereshit Rabbah"

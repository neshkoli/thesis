from talmud_search import (
    ROOT,
    find_name_hits,
    load_docs,
    name_pattern,
    resolve_json_root,
    snippet_around,
)


def test_resolve_root_maps_source_to_project_folder():
    assert resolve_json_root("source") == ROOT / "source"
    assert resolve_json_root("json") == ROOT / "json"


def test_name_pattern_matches_nasia_variants():
    pat = name_pattern("רבי יודן נשייא")
    assert pat.search("רבי יודן נשייא שלח לרבי")
    assert pat.search("רבי יודן נשיא שלח לרבי")
    assert not pat.search("רבי יודן אמר")


def test_name_pattern_matches_rabbi_abbreviation():
    pat = name_pattern("רבי יודן נשייא")
    assert pat.search("ר' יודן נשייא הוה")


def test_name_pattern_matches_nasiah_with_heh():
    pat = name_pattern("רבי יודן נשייא")
    assert pat.search("רבי יודן נשיאה נותנין לה עונה")


def test_snippet_includes_ten_words_before_and_forty_after():
    before = " ".join(f"לפני{i}" for i in range(1, 12))
    after = " ".join(f"אחרי{i}" for i in range(1, 45))
    text = f"{before} רבי יודן נשייא {after}"
    start = text.index("רבי יודן נשייא")
    end = start + len("רבי יודן נשייא")
    snippet = snippet_around(text, start, end)
    assert snippet.startswith("לפני2")
    assert "לפני1 " not in snippet
    assert snippet.endswith("אחרי40")
    assert "אחרי41" not in snippet


def test_snippet_skips_leading_punctuation():
    docs = [
        {
            "corpus": "Yerushalmi",
            "masechet": "חגיגה",
            "seder": "moed",
            "source_pdf": "pdfs/moed/yeru-chagiga.pdf",
            "chapters": [
                {
                    "perek": "א",
                    "perek_number": 1,
                    "halachot": [
                        {
                            "halacha": "ז",
                            "halacha_number": 7,
                            "text": "רבי יודן נשייא , שלח לרבי חייה ולר' אסי ולר' אמי",
                        }
                    ],
                }
            ],
        }
    ]
    hits = find_name_hits(docs, "רבי יודן נשייא")
    assert hits[0]["matched"] == "רבי יודן נשייא"
    assert hits[0]["snippet"] == "רבי יודן נשייא , שלח לרבי חייה ולר' אסי ולר' אמי"
    docs = [
        {
            "corpus": "Yerushalmi",
            "masechet": "חגיגה",
            "seder": "moed",
            "source_pdf": "pdfs/moed/yeru-chagiga.pdf",
            "chapters": [
                {
                    "perek": "א",
                    "perek_number": 1,
                    "halachot": [
                        {
                            "halacha": "ז",
                            "halacha_number": 7,
                            "perek": "א",
                            "perek_number": 1,
                            "text": (
                                "רבי יודן נשייא שלח לרבי חייה ולר' אסי ולר' אמי "
                                "למיעבור בקירייתא"
                            ),
                        }
                    ],
                }
            ],
        }
    ]
    hits = find_name_hits(docs, "רבי יודן נשייא")
    assert len(hits) == 1
    hit = hits[0]
    assert hit["masechet"] == "חגיגה"
    assert hit["perek_number"] == 1
    assert hit["halacha_number"] == 7
    assert hit["matched"] == "רבי יודן נשייא"
    assert hit["snippet"] == (
        "רבי יודן נשייא שלח לרבי חייה ולר' אסי ולר' אמי למיעבור בקירייתא"
    )


def test_same_sentence_occurrences_merge_into_one_hit():
    docs = [
        {
            "corpus": "Yerushalmi",
            "masechet": "כתובות",
            "seder": "nashim",
            "source_pdf": "pdfs/nashim/yeru-ktubot.pdf",
            "chapters": [
                {
                    "perek": "י",
                    "perek_number": 10,
                    "halachot": [
                        {
                            "halacha": "ה",
                            "halacha_number": 5,
                            "text": (
                                "עבדוי דרבי יודן נשייא ואפיק מינה אחר כך "
                                "עבדוי דרבי יודן נשיא ואפיק מינה שוב"
                            ),
                        }
                    ],
                }
            ],
        }
    ]
    hits = find_name_hits(docs, "רבי יודן נשייא")
    assert len(hits) == 1
    assert hits[0]["matched"] == "דרבי יודן נשייא | דרבי יודן נשיא"
    assert "יודן נשייא ואפיק" in hits[0]["snippet"]
    assert "יודן נשיא ואפיק" in hits[0]["snippet"]


def test_different_sentences_stay_separate_hits():
    docs = [
        {
            "corpus": "Bavli",
            "masechet": "ברכות",
            "seder": "zraim",
            "chapters": [
                {
                    "perek": "2a",
                    "perek_number": 2,
                    "daf": "2a",
                    "halachot": [
                        {
                            "halacha": "a",
                            "halacha_number": 1,
                            "daf": "2a",
                            "sefaria_ref": "Berakhot 2a",
                            "text": (
                                "רבן גמליאל אומר עד שיעלה עמוד השחר "
                                + " ".join(f"מילה{i}" for i in range(1, 50))
                                + ". "
                                + " ".join(f"סוף{i}" for i in range(1, 20))
                                + " רבן גמליאל אמר להם אם לא עלה "
                                + " ".join(f"אחר{i}" for i in range(1, 45))
                                + "."
                            ),
                        }
                    ],
                }
            ],
        }
    ]
    hits = find_name_hits(docs, "רבן גמליאל")
    assert len(hits) == 2
    assert hits[0]["corpus"] == "Bavli"
    assert hits[0]["daf"] == "2a"


def test_duplicate_hits_are_removed():
    loc = {
        "corpus": "Bavli",
        "masechet": "ברכות",
        "seder": "zraim",
        "chapters": [
            {
                "perek": "2a",
                "perek_number": 2,
                "daf": "2a",
                "halachot": [
                    {
                        "halacha": "a",
                        "halacha_number": 1,
                        "daf": "2a",
                        "sefaria_ref": "Berakhot 2a",
                        "text": "רבן גמליאל אומר עד שיעלה עמוד השחר.",
                    }
                ],
            }
        ],
    }
    hits = find_name_hits([loc, loc], "רבן גמליאל")
    assert len(hits) == 1


def test_snippet_does_not_start_in_the_middle_of_the_name():
    between = " ".join(f"מילה{i}" for i in range(9))
    text = f"רבן גמליאל {between} רבן גמליאל אמר עוד דברים"
    start = text.rindex("רבן גמליאל")
    end = start + len("רבן גמליאל")
    snippet = snippet_around(text, start, end, name_query="רבן גמליאל")
    assert snippet.split()[0] != "גמליאל"
    assert snippet.startswith("רבן גמליאל") or "רבן גמליאל" in " ".join(snippet.split()[:12])


def test_wrapped_snippet_keeps_the_name_in_the_opening_words():
    text = "סיום רבן גמליאל"
    nxt = " ".join(f"המשך{i}" for i in range(1, 45))
    start = text.index("רבן גמליאל")
    end = start + len("רבן גמליאל")
    snippet = snippet_around(text, start, end, following_texts=[nxt], name_query="רבן גמליאל")
    opening = " ".join(snippet.split()[:6])
    assert "רבן גמליאל" in opening


def test_snippet_pulls_missing_after_words_from_next_text():
    current = "מילה אחת שתיים שלוש רבי יודן נשייא סוף1 סוף2"
    nxt = " ".join(f"המשך{i}" for i in range(1, 45))
    start = current.index("רבי יודן נשייא")
    end = start + len("רבי יודן נשייא")
    snippet = snippet_around(current, start, end, following_texts=[nxt])
    assert "סוף1" in snippet
    assert "סוף2" in snippet
    assert snippet.endswith("המשך38")
    assert "המשך39" not in snippet


def test_find_name_hits_extends_snippet_from_next_halacha():
    following_words = " ".join(f"המשך{i}" for i in range(1, 45))
    docs = [
        {
            "corpus": "Bavli",
            "masechet": "ברכות",
            "seder": "zraim",
            "source_pdf": "x",
            "chapters": [
                {
                    "perek": "2a",
                    "perek_number": 2,
                    "daf": "2a",
                    "halachot": [
                        {
                            "halacha": "a",
                            "halacha_number": 1,
                            "daf": "2a",
                            "text": "רבן גמליאל אמר דבר קצר",
                        }
                    ],
                },
                {
                    "perek": "2b",
                    "perek_number": 2,
                    "daf": "2b",
                    "halachot": [
                        {
                            "halacha": "b",
                            "halacha_number": 1,
                            "daf": "2b",
                            "text": following_words,
                        }
                    ],
                },
            ],
        }
    ]
    hits = find_name_hits(docs, "רבן גמליאל")
    assert len(hits) == 1
    assert "אמר דבר קצר" in hits[0]["snippet"]
    assert "המשך37" in hits[0]["snippet"]
    assert "המשך38" not in hits[0]["snippet"]


def test_commentary_roots_point_at_commentary_folders():
    from talmud_search import DEFAULT_COMMENTARY_ROOTS, resolve_json_roots

    roots = resolve_json_roots(DEFAULT_COMMENTARY_ROOTS)
    assert roots == [ROOT / "commentary" / "Bavli", ROOT / "commentary" / "Yerushalmi"]
    assert (ROOT / "commentary" / "Bavli" / "zraim" / "berakhot.json").exists()

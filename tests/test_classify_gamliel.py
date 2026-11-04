import json
from pathlib import Path
from classify_gamliel import (
    FIGURE_MAP,
    GAMLIEL_SCHEMA,
    corpus_counts,
    normalize_figure,
)


def test_normalize_figure():
    assert normalize_figure("הזקן") == "הזקן"
    assert normalize_figure("דיבנה") == "דיבנה"
    assert normalize_figure("בר רבי") == "בר רבי"
    assert normalize_figure("מאוחר") == "מאוחר"
    assert normalize_figure("ספק") == "ספק"
    assert normalize_figure("רבן גמליאל הזקן") == "הזקן"
    assert normalize_figure("לא ידוע") == "ספק"


def test_corpus_counts():
    hits = [
        {"corpus": "Bavli"},
        {"corpus": "Bavli"},
        {"corpus": "Yerushalmi"},
    ]
    counts = corpus_counts(hits)
    assert counts == {"Bavli": 2, "Yerushalmi": 1}


def test_schema_structure():
    assert "Identified_Figure" in GAMLIEL_SCHEMA["properties"]
    assert "Confidence_Level" in GAMLIEL_SCHEMA["properties"]
    assert "Key_Anchors" in GAMLIEL_SCHEMA["properties"]
    assert "Reasoning" in GAMLIEL_SCHEMA["properties"]

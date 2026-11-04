import csv
import io
from pathlib import Path

from classify_search import (
    CATEGORIES,
    SOURCE_FIELDS,
    RunLogger,
    call_with_retries,
    classify_hits,
    flatten_scores,
    ratio_row,
    rows_to_csv,
    totals_row,
)


SAMPLE_HIT = {
    "corpus": "Bavli",
    "masechet": "ערכין",
    "seder": "kodashim",
    "perek": "17a",
    "perek_number": 17,
    "halacha": "a",
    "halacha_number": 1,
    "daf": "17a",
    "part": None,
    "sefaria_ref": "Steinsaltz on Arakhin 17a",
    "source_pdf": None,
    "matched": "ר' יהודה נשיאה",
    "snippet": "פליגי בה ר' יהודה נשיאה ורבנן",
}

SAMPLE_SCORES = {
    "Authority_Axes": {
        "Intellectual": 3,
        "Institutional": 0,
        "Political": 0,
        "Aristocratic": 2,
    },
    "Halakhic_Activity": 1,
    "Reasoning": "אגדה על פרנס הדור",
}

def test_flatten_scores_returns_new_classification_columns():
    flat = flatten_scores(SAMPLE_SCORES)
    assert list(flat) == list(CATEGORIES)
    assert len(CATEGORIES) == 5
    assert flat["Intellectual"] == 3
    assert flat["Aristocratic"] == 2
    assert flat["Institutional"] == 0


def test_csv_includes_source_fields_then_new_categories():
    rows = classify_hits(
        {"query": "רבי יהודה נשיאה", "layer": "commentary", "hits": [SAMPLE_HIT]},
        classify_fn=lambda hit, model: SAMPLE_SCORES,
    )
    text = rows_to_csv(rows)
    reader = csv.DictReader(io.StringIO(text))
    assert reader.fieldnames == SOURCE_FIELDS + CATEGORIES
    row = next(reader)
    assert row["sefaria_ref"] == SAMPLE_HIT["sefaria_ref"]
    assert row["snippet"] == SAMPLE_HIT["snippet"]
    assert row["Intellectual"] == "3"
    assert row["Aristocratic"] == "2"


def test_classify_hits_uses_only_the_requested_model():
    calls: list[str] = []

    def classify_fn(hit, model):
        calls.append(model)
        return SAMPLE_SCORES

    rows = classify_hits(
        {"hits": [SAMPLE_HIT]},
        classify_fn=classify_fn,
        model="gemini-3.8-flash",
    )
    assert calls == ["gemini-3.8-flash"]
    assert rows[0]["Intellectual"] == 3


def test_retries_transient_http_errors_then_succeeds():
    attempts = {"n": 0}

    def operation():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("gemini-3.8-flash HTTP 503: high demand")
        return SAMPLE_SCORES

    result = call_with_retries(operation, attempts=4, sleep_fn=lambda _s: None)
    assert result is SAMPLE_SCORES
    assert attempts["n"] == 3


def test_csv_appends_sum_and_ratio_rows_for_classification_only():
    rows = [
        classify_hits(
            {"hits": [SAMPLE_HIT]},
            classify_fn=lambda hit, model: SAMPLE_SCORES,
        )[0],
        classify_hits(
            {"hits": [SAMPLE_HIT]},
            classify_fn=lambda hit, model: SAMPLE_SCORES,
        )[0],
    ]
    rows[1]["Institutional"] = 3
    rows[1]["Intellectual"] = 0
    total = totals_row(rows)
    assert total["corpus"] == "TOTAL"
    assert total["Intellectual"] == 3
    assert total["Aristocratic"] == 4
    assert total["Institutional"] == 3
    assert total["perek_number"] == ""
    assert total["halacha_number"] == ""
    assert total["seder"] == ""
    assert total["daf"] == ""
    ratio = ratio_row(total)
    assert ratio["corpus"] == "RATIO"
    assert ratio["perek_number"] == ""
    assert abs(ratio["Intellectual"] - 3 / 12) < 1e-9
    assert abs(ratio["Aristocratic"] - 4 / 12) < 1e-9
    assert abs(ratio["Institutional"] - 3 / 12) < 1e-9
    assert abs(sum(ratio[cat] for cat in CATEGORIES) - 1.0) < 1e-9
    text = rows_to_csv(rows, include_totals=True)
    written = list(csv.DictReader(io.StringIO(text)))
    assert written[-2]["corpus"] == "TOTAL"
    assert written[-2]["Intellectual"] == "3"
    assert written[-2]["perek_number"] == ""
    assert written[-1]["corpus"] == "RATIO"
    assert written[-1]["Institutional"] == "0.25"


def test_run_logger_records_request_response_and_error(tmp_path: Path):
    log_path = tmp_path / "run.log"
    logger = RunLogger(log_path)
    logger.request("hit-0", {"key": "hit-0", "snippet": "abc"})
    logger.response("hit-0", {"Purity": 3})
    logger.error("hit-1", "item failed", {"message": "boom"})
    logger.close()
    text = log_path.read_text(encoding="utf-8")
    assert "REQUEST hit-0" in text
    assert '"snippet": "abc"' in text
    assert "RESPONSE hit-0" in text
    assert "ERROR hit-1" in text
    assert "boom" in text

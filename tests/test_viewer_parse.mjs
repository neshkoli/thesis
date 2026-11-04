import test from "node:test";
import assert from "node:assert/strict";
import { parseCsv, dataRows } from "../viewer/parse.js";

test("parseCsv splits quoted fields that contain commas", () => {
  const csv = [
    "corpus,masechet,snippet,Taxation",
    'Bavli,גיטין,"שלום, עולם",2',
    "",
  ].join("\n");

  const rows = parseCsv(csv);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].corpus, "Bavli");
  assert.equal(rows[0].masechet, "גיטין");
  assert.equal(rows[0].snippet, "שלום, עולם");
  assert.equal(rows[0].Taxation, "2");
});

test("parseCsv unescapes doubled quotes inside a field", () => {
  const csv = 'a,b\n"אמר ""שלום""","x"\n';
  const rows = parseCsv(csv);
  assert.equal(rows[0].a, 'אמר "שלום"');
});

test("dataRows skips a totals row without a snippet", () => {
  const csv = [
    "corpus,snippet,Taxation",
    "Bavli,קטע,1",
    ",,36",
  ].join("\n");

  const rows = dataRows(parseCsv(csv));
  assert.equal(rows.length, 1);
  assert.equal(rows[0].snippet, "קטע");
});

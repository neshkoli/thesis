import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseCsv } from "../viewer/parse.js";
import {
  calculateTopicScores,
  calculateAllSummaries,
  TOPIC_KEYS,
  AUTHORITY_KEYS,
  filterValidPassages,
  exportSummariesToCsv,
} from "../viewer/summary.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const classifiedDir = join(root, "classified-results");

test("TOPIC_KEYS and AUTHORITY_KEYS contain the expected taxonomy fields", () => {
  assert.equal(AUTHORITY_KEYS.length, 4);
  assert.ok(AUTHORITY_KEYS.includes("Intellectual"));
  assert.ok(AUTHORITY_KEYS.includes("Institutional"));
  assert.ok(AUTHORITY_KEYS.includes("Political"));
  assert.ok(AUTHORITY_KEYS.includes("Aristocratic"));

  assert.equal(TOPIC_KEYS.length, 5);
  assert.ok(TOPIC_KEYS.includes("Halakhic_Activity"));
});

test("filterValidPassages excludes TOTAL and RATIO rows and filters by corpus", () => {
  const sample = [
    { corpus: "Bavli", snippet: "קטע בבלי", Intellectual: "2" },
    { corpus: "Yerushalmi", snippet: "קטע ירושלמי", Intellectual: "3" },
    { corpus: "TOTAL", snippet: "", Intellectual: "5" },
    { corpus: "RATIO", snippet: "", Intellectual: "0.5" },
  ];

  const all = filterValidPassages(sample, "all");
  assert.equal(all.length, 2);

  const bavli = filterValidPassages(sample, "Bavli");
  assert.equal(bavli.length, 1);
  assert.equal(bavli[0].corpus, "Bavli");

  const yeru = filterValidPassages(sample, "Yerushalmi");
  assert.equal(yeru.length, 1);
  assert.equal(yeru[0].corpus, "Yerushalmi");
});

test("calculateTopicScores correctly computes authority scores and halakhic activity", () => {
  const rows = [
    {
      corpus: "Bavli",
      snippet: "קטע 1",
      Intellectual: "3",
      Institutional: "1",
      Political: "0",
      Aristocratic: "0",
      Halakhic_Activity: "1",
    },
    {
      corpus: "Yerushalmi",
      snippet: "קטע 2",
      Intellectual: "1",
      Institutional: "2",
      Political: "0",
      Aristocratic: "1",
      Halakhic_Activity: "0",
    },
  ];

  // Authority scores:
  // Intellectual: 3 + 1 = 4
  // Institutional: 1 + 2 = 3
  // Political: 0
  // Aristocratic: 0 + 1 = 1
  // Total authority score = 4 + 3 + 0 + 1 = 8
  const summary = calculateTopicScores(rows, { corpus: "all", gradeFilter: "1-2-3" });
  assert.equal(summary.passageCount, 2);
  assert.equal(summary.totalAuthorityScore, 8);
  assert.equal(summary.scores.Intellectual, 4);
  assert.equal(summary.ratios.Intellectual, 4 / 8);
  assert.equal(summary.scores.Institutional, 3);
  assert.equal(summary.ratios.Institutional, 3 / 8);
  assert.equal(summary.scores.Aristocratic, 1);
  assert.equal(summary.ratios.Aristocratic, 1 / 8);

  // Halakhic activity: 1 active out of 2 total = 50%
  assert.equal(summary.halakhicActiveCount, 1);
  assert.equal(summary.halakhicTotalCount, 2);
  assert.equal(summary.halakhicActiveRatio, 0.5);
});

test("calculateTopicScores respects gradeFilter '2-3' and '3'", () => {
  const rows = [
    {
      corpus: "Bavli",
      snippet: "קטע",
      Intellectual: "1",
      Institutional: "2",
      Political: "0",
      Aristocratic: "3",
      Halakhic_Activity: "1",
    },
  ];

  // With 2-3 filter: 1 is ignored; 2 and 3 remain. Total = 2 + 3 = 5.
  const summary23 = calculateTopicScores(rows, { corpus: "all", gradeFilter: "2-3" });
  assert.equal(summary23.totalAuthorityScore, 5);
  assert.equal(summary23.scores.Intellectual, 0);
  assert.equal(summary23.scores.Institutional, 2);
  assert.equal(summary23.ratios.Institutional, 2 / 5);
  assert.equal(summary23.scores.Aristocratic, 3);
  assert.equal(summary23.ratios.Aristocratic, 3 / 5);

  // With 3 filter: only 3 remains. Total = 3.
  const summary3 = calculateTopicScores(rows, { corpus: "all", gradeFilter: "3" });
  assert.equal(summary3.totalAuthorityScore, 3);
  assert.equal(summary3.scores.Aristocratic, 3);
  assert.equal(summary3.scores.Institutional, 0);
  assert.equal(summary3.ratios.Aristocratic, 1.0);
});

test("Real CSV files in classified-results directory compute valid summaries", () => {
  const hillelPath = join(classifiedDir, "הלל_classified.csv");
  if (!existsSync(hillelPath)) return;

  const raw = readFileSync(hillelPath, "utf-8");
  const rows = parseCsv(raw);
  const hillel = calculateTopicScores(rows);

  assert.ok(hillel.passageCount > 0);
  assert.ok(hillel.totalAuthorityScore > 0);
  assert.ok(hillel.scores.Intellectual > 0);
});

test("calculateAllSummaries orders figures chronologically by generation", () => {
  const mockDatasets = [
    { fileName: "רבי_יהודה_נשיאה_classified.csv", rows: [] },
    { fileName: "הלל_classified.csv", rows: [] },
    { fileName: "רבי_יהודה_הנשיא_classified.csv", rows: [] },
    { fileName: "רבן_גמליאל_הזקן_classified.csv", rows: [] },
  ];

  const sorted = calculateAllSummaries(mockDatasets);
  const names = sorted.map((s) => s.personName);

  assert.equal(names[0], "הלל");
  assert.equal(names[1], "רבן גמליאל הזקן");
  assert.equal(names[2], "רבי יהודה הנשיא");
  assert.equal(names[3], "רבי יהודה נשיאה");
});

test("exportSummariesToCsv generates valid CSV with BOM and columns", () => {
  const mockSummaries = [
    {
      personName: "הלל",
      order: 1,
      generation: "תנאים",
      passageCount: 10,
      totalAuthorityScore: 25,
      scores: { Intellectual: 20, Institutional: 5, Political: 0, Aristocratic: 0 },
      ratios: { Intellectual: 0.8, Institutional: 0.2, Political: 0, Aristocratic: 0 },
      averages: { Intellectual: 2.0, Institutional: 0.5, Political: 0, Aristocratic: 0 },
      halakhicActiveRatio: 0.7,
      halakhicActiveCount: 7,
      halakhicTotalCount: 10,
    },
  ];

  const csvOutput = exportSummariesToCsv(mockSummaries);
  assert.ok(csvOutput.startsWith("\uFEFF"));
  assert.ok(csvOutput.includes("סמכות אינטלקטואלית־תורנית"));
  assert.ok(csvOutput.includes("הלל"));
});

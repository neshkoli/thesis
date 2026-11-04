import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseCsv, dataRows } from "../viewer/parse.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

test("dataRows keeps snippets from the Hillel classified file", () => {
  const csv = readFileSync(
    join(root, "search-results-commentary", "הלל_הזקן_classified.csv"),
    "utf8",
  );
  const rows = dataRows(parseCsv(csv));
  assert.ok(rows.length >= 30);
  assert.equal(rows[0].corpus, "Bavli");
  assert.equal(rows[0].masechet, "זבחים");
  assert.ok(rows[0].snippet.includes("הלל"));
  assert.equal(rows[0].Shabbat_Holidays, "2");
  assert.ok(rows.every((row) => row.snippet.trim() !== ""));
});

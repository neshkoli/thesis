import test from "node:test";
import assert from "node:assert/strict";
import { highlightNameInText, phraseFromFileName } from "../viewer/highlight.js";

test("phraseFromFileName turns הלל_הזקן_classified.csv into הלל הזקן", () => {
  assert.equal(phraseFromFileName("הלל_הזקן_classified.csv"), "הלל הזקן");
});

test("highlightNameInText bolds the file-name phrase", () => {
  const html = highlightNameInText(
    "אמרו עליו על הלל הזקן שכך היה נוהג",
    "הלל הזקן",
  );
  assert.match(html, /<mark class="name-hit">הלל הזקן<\/mark>/);
  assert.ok(html.startsWith("אמרו עליו על "));
});

test("highlightNameInText bolds a prefixed form such as בהלל הזקן", () => {
  const html = highlightNameInText("מעשה בהלל הזקן שהביא", "הלל הזקן");
  assert.match(html, /<mark class="name-hit">בהלל הזקן<\/mark>/);
});

test("highlightNameInText escapes HTML in the snippet", () => {
  const html = highlightNameInText('<b>הלל הזקן</b>', "הלל הזקן");
  assert.equal(html.includes("<b>"), false);
  assert.match(html, /<mark class="name-hit">הלל הזקן<\/mark>/);
});

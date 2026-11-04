function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function phraseFromFileName(fileName) {
  const base = String(fileName ?? "")
    .replace(/^.*[/\\]/, "")
    .replace(/_classified\.csv$/i, "")
    .replace(/\.csv$/i, "");
  return base.replaceAll("_", " ").trim();
}

export const AUTHORITY_KEYWORDS = {
  Institutional: [
    "מפני תיקון העולם",
    "תיקון העולם",
    "התקין",
    "התקינו",
    "תקנה",
    "תקנת",
    "תקנות",
    "פרוזבול",
    "פרוסבול",
    "קידוש החודש",
    "עיבור השנה",
    "סנהדרין",
    "בית הדין",
    "בית דין",
  ],
  Aristocratic: [
    "עבדי דרבי",
    "עבדים",
    "עבדו",
    "עבדי",
    "שומרי",
    "שוטרים",
    "בלשא",
    "באלושי",
    "דמי כלילא",
    "דמי חומה",
    "עושר",
    "שררה",
    "כבוד",
    "אריסטוקרט",
    "סוס לרכוב עליו",
    "עבד לרוץ לפניו",
    "מלך",
    "מלכות",
    "זהב",
  ],
  Political: [
    "רומי",
    "רומיים",
    "קיסר",
    "אנטונינוס",
    "אנטונינוס ורבי",
    "שלטון",
    "הגמון",
    "דוכס",
    "מלכות הרשעה",
    "גזירה",
    "גזירות",
    "דיפלומטיה",
  ],
};

export function highlightNameInText(text, phrase) {
  const source = String(text ?? "");
  const words = String(phrase ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!source) return "";

  const prefix = "[\\u05D1\\u05DB\\u05DC\\u05DE\\u05E9\\u05D5\\u05D4]{0,3}";
  const nameParts = words.map(escapeRegExp);
  const phrasePattern = `(?:${prefix})?${nameParts.join("\\s+")}`;
  const wordPatterns = nameParts.map((w) => `(?:${prefix})?${w}`);

  // Build pattern for person name
  const nameRegex = words.length > 0
    ? new RegExp(`(${phrasePattern}|${wordPatterns.join("|")})`, "g")
    : null;

  let html = escapeHtml(source);

  if (nameRegex) {
    html = html.replace(nameRegex, '<mark class="name-hit">$1</mark>');
  }

  // Highlight authority keywords subtly
  for (const [axisKey, keywords] of Object.entries(AUTHORITY_KEYWORDS)) {
    const kwPattern = keywords
      .map((k) => `(?:${prefix})?${escapeRegExp(k)}`)
      .join("|");
    const regex = new RegExp(`(?<![\\u0590-\\u05FF])(${kwPattern})(?![\\u0590-\\u05FF])`, "g");
    html = html.replace(
      regex,
      `<mark class="keyword-hit keyword-${axisKey.toLowerCase()}" title="מונח מובהק לציר ${axisKey}">$1</mark>`,
    );
  }

  return html;
}

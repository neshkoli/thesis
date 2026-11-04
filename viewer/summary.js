import {
  AUTHORITY_AXES_CONFIG,
  HALAKHIC_ACTIVITY_CONFIG,
  SCORE_COLUMNS,
} from "./taxonomy.js";
import { phraseFromFileName } from "./highlight.js";

export const AUTHORITY_KEYS = AUTHORITY_AXES_CONFIG.map((a) => a.key);

export const TOPIC_KEYS = SCORE_COLUMNS.flatMap((col) =>
  col.items.map(([key]) => key),
);

export const TOPIC_LABELS = Object.fromEntries(
  SCORE_COLUMNS.flatMap((col) => col.items),
);

export const TOPIC_DOMAIN_MAP = Object.fromEntries(
  SCORE_COLUMNS.flatMap((col) =>
    col.items.map(([key]) => [key, col.title]),
  ),
);

export const GENERATIONS_MAP = {
  "הלל": {
    order: 1,
    generation: "סוף תקופת הזוגות / ראשית התנאים",
    shortGen: "זוגות / תנאים א׳",
    era: "בית שני",
  },
  "הלל הזקן": {
    order: 1,
    generation: "סוף תקופת הזוגות / ראשית התנאים",
    shortGen: "זוגות / תנאים א׳",
    era: "בית שני",
  },
  "הלל הבבלי": {
    order: 1,
    generation: "סוף תקופת הזוגות / ראשית התנאים",
    shortGen: "זוגות / תנאים א׳",
    era: "בית שני",
  },

  "גמליאל הזקן": {
    order: 2,
    generation: "דור ראשון לתנאים (בית שני)",
    shortGen: "תנאים א׳ (בית שני)",
    era: "בית שני",
  },
  "רבן גמליאל הזקן": {
    order: 2,
    generation: "דור ראשון לתנאים (בית שני)",
    shortGen: "תנאים א׳ (בית שני)",
    era: "בית שני",
  },

  "רבן שמעון בן גמליאל הראשון": {
    order: 3,
    generation: "דור שני לתנאים (חורבן הבית והמרד הגדול)",
    shortGen: "תנאים ב׳ (חורבן)",
    era: "חורבן",
  },
  "רבן שמעון בן גמליאל הזקן": {
    order: 3,
    generation: "דור שני לתנאים (חורבן הבית והמרד הגדול)",
    shortGen: "תנאים ב׳ (חורבן)",
    era: "חורבן",
  },

  "רבן גמליאל דיבנה": {
    order: 4,
    generation: "דור שלישי לתנאים (דור יבנה)",
    shortGen: "תנאים ג׳ (יבנה)",
    era: "יבנה",
  },
  "רבן גמליאל": {
    order: 4,
    generation: "דור שלישי לתנאים (דור יבנה)",
    shortGen: "תנאים ג׳ (יבנה)",
    era: "יבנה",
  },

  "רבן שמעון בן גמליאל השני": {
    order: 5,
    generation: "דור רביעי לתנאים (דור אושה, לאחר בר כוכבא)",
    shortGen: "תנאים ד׳ (אושה)",
    era: "אושה",
  },
  "רבן שמעון בן גמליאל": {
    order: 5,
    generation: "דור רביעי לתנאים (דור אושה, לאחר בר כוכבא)",
    shortGen: "תנאים ד׳ (אושה)",
    era: "אושה",
  },

  "רבי יהודה הנשיא": {
    order: 6,
    generation: "דור חמישי לתנאים (חתימת המשנה)",
    shortGen: "תנאים ה׳ (רבי)",
    era: "ציפורי/משנה",
  },
  "רבי": {
    order: 6,
    generation: "דור חמישי לתנאים (חתימת המשנה)",
    shortGen: "תנאים ה׳ (רבי)",
    era: "ציפורי/משנה",
  },

  "רבן גמליאל ברבי": {
    order: 7,
    generation: "דור המעבר בין תנאים לאמוראים",
    shortGen: "מעבר לאמוראים",
    era: "מעבר",
  },

  "רבי יהודה נשיאה": {
    order: 8,
    generation: "דור ראשון–שני לאמוראי ארץ ישראל",
    shortGen: "אמוראי א״י א׳-ב׳",
    era: "אמוראים",
  },
  "רבי יודן נשיאה": {
    order: 8,
    generation: "דור ראשון–שני לאמוראי ארץ ישראל",
    shortGen: "אמוראי א״י א׳-ב׳",
    era: "אמוראים",
  },
  "רבי יודן נשייא": {
    order: 8,
    generation: "דור ראשון–שני לאמוראי ארץ ישראל",
    shortGen: "אמוראי א״י א׳-ב׳",
    era: "אמוראים",
  },

  "רבן גמליאל המאוחר": {
    order: 9,
    generation: "נשיאי תקופת האמוראים המאוחרת",
    shortGen: "אמוראים מאוחר",
    era: "אמוראים",
  },
  "רבן גמליאל ספק": {
    order: 10,
    generation: "ספק זיהוי / מסורות רב-דוריות",
    shortGen: "ספק זיהוי",
    era: "ספק",
  },
};

export function getGenerationInfo(personName) {
  const clean = String(personName ?? "").trim();
  if (GENERATIONS_MAP[clean]) return GENERATIONS_MAP[clean];
  for (const [k, v] of Object.entries(GENERATIONS_MAP)) {
    if (clean === k || clean.includes(k) || k.includes(clean)) return v;
  }
  return {
    order: 99,
    generation: "חכמי המשנה והתלמוד",
    shortGen: "חכמים",
    era: "כללי",
  };
}

export function filterValidPassages(rows, corpusFilter = "all") {
  if (!Array.isArray(rows)) return [];
  return rows.filter((row) => {
    const snippet = String(row.snippet ?? "").trim();
    if (!snippet) return false;

    const corpus = String(row.corpus ?? "").trim();
    if (corpus === "TOTAL" || corpus === "RATIO") return false;

    if (corpusFilter === "Bavli") {
      return corpus.toLowerCase() === "bavli";
    }
    if (corpusFilter === "Yerushalmi") {
      return corpus.toLowerCase() === "yerushalmi";
    }
    return true;
  });
}

export function parseScore(val) {
  const n = Number.parseInt(String(val ?? "").trim(), 10);
  if (Number.isNaN(n)) return 0;
  return Math.min(3, Math.max(0, n));
}

export function isGradeCounted(grade, gradeFilter = "1-2-3") {
  if (grade <= 0) return false;
  if (gradeFilter === "3") return grade === 3;
  if (gradeFilter === "2-3") return grade >= 2;
  return grade >= 1; // "1-2-3"
}

export function calculateTopicScores(rows, options = {}) {
  const corpusFilter = options.corpus ?? "all";
  const gradeFilter = options.gradeFilter ?? "1-2-3";

  const passages = filterValidPassages(rows, corpusFilter);
  const scores = {};
  const topicPassageCounts = {};
  const prominentCounts = {}; // score >= 2

  TOPIC_KEYS.forEach((k) => {
    scores[k] = 0;
    topicPassageCounts[k] = 0;
    prominentCounts[k] = 0;
  });

  let totalAuthorityScore = 0;
  let halakhicActiveCount = 0;
  let halakhicPassiveCount = 0;
  let halakhicTotalCount = 0;

  for (const row of passages) {
    // 1. Process 4 Authority Axes
    for (const key of AUTHORITY_KEYS) {
      const grade = parseScore(row[key]);
      if (isGradeCounted(grade, gradeFilter)) {
        scores[key] += grade;
        topicPassageCounts[key] += 1;
        totalAuthorityScore += grade;
      }
      if (grade >= 2) {
        prominentCounts[key] += 1;
      }
    }

    // 2. Process Halakhic Activity (Task B in classification.md)
    const rawActivity = row.Halakhic_Activity;
    if (rawActivity !== undefined && rawActivity !== null) {
      const actStr = String(rawActivity).trim();
      if (actStr === "1") {
        halakhicActiveCount += 1;
        halakhicTotalCount += 1;
      } else if (actStr === "0") {
        halakhicPassiveCount += 1;
        halakhicTotalCount += 1;
      }
    }
  }

  // Set Halakhic_Activity in scores object for generic renderers
  scores.Halakhic_Activity = halakhicActiveCount;
  topicPassageCounts.Halakhic_Activity = halakhicActiveCount;

  // Compute Ratios (relative composition of the 4 authority axes)
  const ratios = {};
  const averages = {};
  const prominentRatios = {};

  for (const key of AUTHORITY_KEYS) {
    ratios[key] =
      totalAuthorityScore > 0 ? scores[key] / totalAuthorityScore : 0;
    averages[key] =
      passages.length > 0 ? scores[key] / passages.length : 0;
    prominentRatios[key] =
      passages.length > 0 ? prominentCounts[key] / passages.length : 0;
  }

  const halakhicActiveRatio =
    halakhicTotalCount > 0 ? halakhicActiveCount / halakhicTotalCount : 0;

  ratios.Halakhic_Activity = halakhicActiveRatio;
  averages.Halakhic_Activity = halakhicActiveRatio;

  return {
    passageCount: passages.length,
    totalAuthorityScore,
    totalScore: totalAuthorityScore, // alias for backwards compatibility
    scores,
    ratios,
    averages,
    prominentCounts,
    prominentRatios,
    topicPassageCounts,
    halakhicActiveCount,
    halakhicPassiveCount,
    halakhicTotalCount,
    halakhicActiveRatio,
  };
}

export function calculateAllSummaries(filesList, options = {}) {
  const list = filesList.map((item) => {
    const personName = item.personName || phraseFromFileName(item.fileName);
    const summary = calculateTopicScores(item.rows, options);
    const genInfo = getGenerationInfo(personName);

    return {
      fileName: item.fileName,
      personName,
      generation: genInfo.generation,
      shortGen: genInfo.shortGen,
      era: genInfo.era,
      order: genInfo.order,
      ...summary,
    };
  });

  // Sort strictly by historical chronological order, then by name
  return list.sort((a, b) => {
    if (a.order !== b.order) return a.order - b.order;
    return a.personName.localeCompare(b.personName, "he");
  });
}

export function exportSummariesToCsv(summaries, options = {}) {
  const metric = options.metric ?? "percent"; // "percent" | "decimal" | "score" | "avg"
  const headers = [
    "דמות",
    "סדר כרונולוגי",
    "דור / תקופה",
    "מספר קטעים",
    "סך נקודות סמכות",
    "סמכות אינטלקטואלית־תורנית",
    "סמכות מוסדית־חקיקתית",
    "סמכות פוליטית־ייצוגית",
    "מעמד אריסטוקרטי ושררה",
    "אחוז אקטיביות הלכתית",
    "קטעי הכרעה אקטיביים",
  ];

  const lines = [headers.join(",")];

  for (const s of summaries) {
    const formatAxisVal = (k) => {
      if (metric === "score") return s.scores[k];
      if (metric === "avg") return s.averages[k].toFixed(2);
      if (metric === "decimal") return s.ratios[k].toFixed(3);
      return `${(s.ratios[k] * 100).toFixed(1)}%`;
    };

    const row = [
      `"${s.personName}"`,
      s.order,
      `"${s.generation}"`,
      s.passageCount,
      s.totalAuthorityScore,
      `"${formatAxisVal("Intellectual")}"`,
      `"${formatAxisVal("Institutional")}"`,
      `"${formatAxisVal("Political")}"`,
      `"${formatAxisVal("Aristocratic")}"`,
      `"${(s.halakhicActiveRatio * 100).toFixed(1)}%"`,
      `"${s.halakhicActiveCount}/${s.halakhicTotalCount}"`,
    ];
    lines.push(row.join(","));
  }

  // Prepend UTF-8 BOM so Excel opens Hebrew properly
  return `\uFEFF${lines.join("\r\n")}`;
}

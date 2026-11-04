export const AUTHORITY_AXES_CONFIG = [
  {
    key: "Intellectual",
    label: "סמכות אינטלקטואלית־תורנית",
    shortLabel: "אינטלקטואלי",
    color: "#2563eb",
    bgTint: "rgba(37, 99, 235, 0.12)",
    icon: "📘",
    description:
      "הנשיא כחכם המוסר מסורת, דורש דרשה, מנהל משא ומתן תלמודי או פוסק הלכה מכוח למדנותו וסברתו.",
  },
  {
    key: "Institutional",
    label: "סמכות מוסדית־חקיקתית",
    shortLabel: "מוסדי",
    color: "#059669",
    bgTint: "rgba(5, 150, 105, 0.12)",
    icon: "🏛️",
    description:
      "הנשיא כראש בית הדין והסנהדרין המתקין תקנות (כגון 'מפני תיקון העולם'), מקדש חודשים ומנהל את סדרי החברה היהודית מבפנים.",
  },
  {
    key: "Political",
    label: "סמכות פוליטית־ייצוגית",
    shortLabel: "פוליטי",
    color: "#d97706",
    bgTint: "rgba(217, 119, 6, 0.12)",
    icon: "🌍",
    description:
      "מגעים דיפלומטיים עם שלטונות רומי, אומות העולם, או התמודדות עם גזירות מטעם השלטון הזר.",
  },
  {
    key: "Aristocratic",
    label: "מעמד אריסטוקרטי ושררה",
    shortLabel: "אריסטוקרטי",
    color: "#9333ea",
    bgTint: "rgba(147, 51, 234, 0.12)",
    icon: "👑",
    description:
      "גילויי עושר, כוח אכיפה פיזי (עבדים/שומרי ראש), גביית מס (למעט תרומות ומעשרות דתיים), או מאבקי כוח וכבוד פנימיים מול חכמים המדגישים את היררכיית השררה.",
  },
];

export const HALAKHIC_ACTIVITY_CONFIG = {
  key: "Halakhic_Activity",
  label: "פעילות הלכתית או לימודית",
  shortLabel: "הכרעה אקטיבית",
  color: "#0891b2",
  bgTint: "rgba(8, 145, 178, 0.12)",
  icon: "⚖️",
  description:
    "האם בקטע זה הנשיא פוסק, מתקן או מלמד באופן אקטיבי (1), או שהוא רק נוכח ברקע/סביל (0).",
};

export const SCORE_COLUMNS = [
  {
    title: "א. צירי סמכות (Authority Axes)",
    items: AUTHORITY_AXES_CONFIG.map((a) => [a.key, a.label]),
  },
  {
    title: "ב. פעילות הלכתית / לימודית (Halakhic Activity)",
    items: [[HALAKHIC_ACTIVITY_CONFIG.key, HALAKHIC_ACTIVITY_CONFIG.label]],
  },
];

export const META_FIELDS = [
  ["corpus", "קורפוס"],
  ["masechet", "מסכת"],
  ["seder", "סדר"],
  ["perek", "פרק"],
  ["perek_number", "מספר פרק"],
  ["halacha", "הלכה"],
  ["halacha_number", "מספר הלכה"],
  ["daf", "דף"],
  ["part", "חלק"],
  ["sefaria_ref", "הפניה בספריא"],
  ["source_pdf", "מקור PDF"],
  ["matched", "דמות שזוהתה"],
  ["Reasoning", "נימוק המודל לסיווג"],
];

import { highlightNameInText, phraseFromFileName } from "./highlight.js";
import { dataRows, parseCsv } from "./parse.js";
import {
  AUTHORITY_AXES_CONFIG,
  HALAKHIC_ACTIVITY_CONFIG,
  META_FIELDS,
  SCORE_COLUMNS,
} from "./taxonomy.js";
import {
  AUTHORITY_KEYS,
  TOPIC_KEYS,
  TOPIC_LABELS,
  TOPIC_DOMAIN_MAP,
  calculateTopicScores,
  calculateAllSummaries,
  getGenerationInfo,
  exportSummariesToCsv,
} from "./summary.js";
import { DEFAULT_CSV_DATA } from "./default_data.js";

/* -------------------------------------------------------------
 * Application State
 * ----------------------------------------------------------- */
const state = {
  activeTab: "findings", // "findings" | "summary" | "single"

  // Datasets map: fileName -> { fileName, personName, rows, enabled, rawText }
  datasets: new Map(),

  // Global filters
  corpusFilter: "all", // "all" | "Bavli" | "Yerushalmi"
  gradeFilter: "1-2-3", // "1-2-3" | "2-3" | "3"
  displayMetric: "percent", // "percent" | "avg" | "score"

  // Comparator State
  comparePersonA: "רבי_יהודה_הנשיא_classified.csv",
  comparePersonB: "רבי_יהודה_נשיאה_classified.csv",

  // Single Record Viewer State
  singleFileName: "",
  singleAllRows: [],
  singleFilteredRows: [],
  singleIndex: 0,
  singleAxisFilter: "all", // "all" | "Aristocratic" | "Institutional" | "Political" | "Intellectual" | "Halakhic_Activity"
  singleMinScore: 1,
  singleSearchQuery: "",
};

/* -------------------------------------------------------------
 * DOM Elements
 * ----------------------------------------------------------- */
const els = {
  // Navigation Tabs
  tabBtnFindings: document.getElementById("tab-btn-findings"),
  tabBtnSummary: document.getElementById("tab-btn-summary"),
  tabBtnSingle: document.getElementById("tab-btn-single"),
  tabFindings: document.getElementById("tab-findings"),
  tabSummary: document.getElementById("tab-summary"),
  tabSingle: document.getElementById("tab-single"),

  // Global Controls
  corpusFilter: document.getElementById("corpus-filter"),
  gradeFilter: document.getElementById("grade-filter"),
  metricFilter: document.getElementById("metric-filter"),
  personChips: document.getElementById("person-chips"),
  exportCsvBtn: document.getElementById("export-csv-btn"),
  copyTableBtn: document.getElementById("copy-table-btn"),
  addCsvInput: document.getElementById("add-csv-files"),

  // Tab 1: Findings & Charts
  proofCards: document.getElementById("proof-cards"),
  trendsChart: document.getElementById("trends-chart"),
  comparePersonA: document.getElementById("compare-person-a"),
  comparePersonB: document.getElementById("compare-person-b"),
  comparatorResults: document.getElementById("comparator-results"),

  // Tab 2: Summary Table
  summaryStatsText: document.getElementById("summary-stats-text"),
  tableTopicsHeader: document.getElementById("table-topics-header"),
  summaryTbody: document.getElementById("summary-tbody"),
  summaryTfoot: document.getElementById("summary-tfoot"),
  cellTooltip: document.getElementById("cell-tooltip"),

  // Tab 3: Single Viewer
  singleFileInput: document.getElementById("csv-file"),
  singleSampleSelect: document.getElementById("sample-file"),
  singleFileName: document.getElementById("file-name"),
  singleAxisPills: document.getElementById("single-axis-pills"),
  singleSearchInput: document.getElementById("snippet-search"),
  singlePrevBtn: document.getElementById("prev"),
  singleNextBtn: document.getElementById("next"),
  singleCounter: document.getElementById("counter"),
  singleEmpty: document.getElementById("empty-state"),
  singleRecord: document.getElementById("record"),
  singleMeta: document.getElementById("meta"),
  singleScores: document.getElementById("scores"),
  singleSnippet: document.getElementById("snippet"),
  singleSourceBadge: document.getElementById("snippet-source-badge"),
  modelReasoning: document.getElementById("model-reasoning"),
};

/* -------------------------------------------------------------
 * Tab Management
 * ----------------------------------------------------------- */
function switchTab(targetTab) {
  state.activeTab = targetTab;

  const isFindings = targetTab === "findings";
  const isSummary = targetTab === "summary";
  const isSingle = targetTab === "single";

  els.tabBtnFindings.classList.toggle("active", isFindings);
  els.tabBtnFindings.setAttribute("aria-selected", String(isFindings));
  els.tabFindings.hidden = !isFindings;

  els.tabBtnSummary.classList.toggle("active", isSummary);
  els.tabBtnSummary.setAttribute("aria-selected", String(isSummary));
  els.tabSummary.hidden = !isSummary;

  els.tabBtnSingle.classList.toggle("active", isSingle);
  els.tabBtnSingle.setAttribute("aria-selected", String(isSingle));
  els.tabSingle.hidden = !isSingle;

  if (isFindings) {
    renderFindingsView();
  } else if (isSummary) {
    renderSummaryView();
  } else {
    renderSingleView();
  }
}

els.tabBtnFindings.addEventListener("click", () => switchTab("findings"));
els.tabBtnSummary.addEventListener("click", () => switchTab("summary"));
els.tabBtnSingle.addEventListener("click", () => switchTab("single"));

/* -------------------------------------------------------------
 * Dataset Management
 * ----------------------------------------------------------- */
function registerDataset(fileName, rawText) {
  const allRows = parseCsv(rawText);
  const rows = dataRows(allRows);
  const personName = phraseFromFileName(fileName);
  const genInfo = getGenerationInfo(personName);

  // Exclude doubtful or very minor auxiliary fragments by default, keep main 8 active
  const isAuxiliary =
    fileName.includes("המאוחר") || fileName.includes("ספק");

  state.datasets.set(fileName, {
    fileName,
    personName,
    rows,
    rawText,
    order: genInfo.order,
    generation: genInfo.generation,
    enabled: !isAuxiliary,
  });

  updateSampleSelectDropdowns();
}

function updateSampleSelectDropdowns() {
  const currentVal = els.singleSampleSelect.value;
  const sortedDatasets = Array.from(state.datasets.values()).sort(
    (a, b) => a.order - b.order,
  );

  const optionsSingle = ['<option value="">— בחרו דמות לעיון מפורט —</option>'];
  const optionsCompA = [];
  const optionsCompB = [];

  for (const ds of sortedDatasets) {
    const optStr = `<option value="${escapeAttr(ds.fileName)}">${escapeHtml(ds.personName)} (${ds.rows.length} קטעים)</option>`;
    optionsSingle.push(optStr);
    optionsCompA.push(optStr);
    optionsCompB.push(optStr);
  }

  els.singleSampleSelect.innerHTML = optionsSingle.join("");
  els.comparePersonA.innerHTML = optionsCompA.join("");
  els.comparePersonB.innerHTML = optionsCompB.join("");

  if (state.datasets.has(currentVal)) {
    els.singleSampleSelect.value = currentVal;
  }

  // Set default comparator choices if available
  if (state.datasets.has(state.comparePersonA)) {
    els.comparePersonA.value = state.comparePersonA;
  } else if (sortedDatasets.length > 5) {
    els.comparePersonA.value = sortedDatasets[5].fileName;
    state.comparePersonA = sortedDatasets[5].fileName;
  }

  if (state.datasets.has(state.comparePersonB)) {
    els.comparePersonB.value = state.comparePersonB;
  } else if (sortedDatasets.length > 7) {
    els.comparePersonB.value = sortedDatasets[7].fileName;
    state.comparePersonB = sortedDatasets[7].fileName;
  }
}

async function initDefaultDatasets() {
  const knownFiles = [
    "הלל_classified.csv",
    "רבן_גמליאל_הזקן_classified.csv",
    "רבן_שמעון_בן_גמליאל_הראשון_classified.csv",
    "רבן_גמליאל_דיבנה_classified.csv",
    "רבן_שמעון_בן_גמליאל_השני_classified.csv",
    "רבי_יהודה_הנשיא_classified.csv",
    "רבן_גמליאל_ברבי_classified.csv",
    "רבי_יהודה_נשיאה_classified.csv",
    "רבן_גמליאל_המאוחר_classified.csv",
    "רבן_גמליאל_ספק_classified.csv",
  ];

  let loadedViaFetch = false;

  for (const fname of knownFiles) {
    const urls = [
      `../classified-results/${encodeURIComponent(fname)}`,
      `./classified-results/${encodeURIComponent(fname)}`,
      `../../statistics/${encodeURIComponent(fname)}`,
    ];

    for (const url of urls) {
      try {
        const res = await fetch(url);
        if (res.ok) {
          const text = await res.text();
          registerDataset(fname, text);
          loadedViaFetch = true;
          break;
        }
      } catch {
        // fetch may fail on file:// or origin restrictions
      }
    }
  }

  // Fallback to embedded default data if fetch was blocked or missed any
  if (typeof DEFAULT_CSV_DATA === "object" && DEFAULT_CSV_DATA !== null) {
    for (const [fname, content] of Object.entries(DEFAULT_CSV_DATA)) {
      if (!state.datasets.has(fname)) {
        registerDataset(fname, content);
      }
    }
  }

  // Default single record viewer to Rabbi Yehuda Nesia or Rabbi Yehuda HaNasi
  if (state.datasets.size > 0 && state.singleAllRows.length === 0) {
    const defaultFile = state.datasets.has("רבי_יהודה_נשיאה_classified.csv")
      ? "רבי_יהודה_נשיאה_classified.csv"
      : state.datasets.values().next().value.fileName;
    const ds = state.datasets.get(defaultFile);
    loadSingleDataset(ds.fileName, ds.rows);
  }

  buildTopicsHeader();
  renderPersonChips();
  renderFindingsView();
  renderSummaryView();
}

/* -------------------------------------------------------------
 * Sages Toggle Chips
 * ----------------------------------------------------------- */
function renderPersonChips() {
  const chips = [];
  const sortedDatasets = Array.from(state.datasets.values()).sort(
    (a, b) => a.order - b.order,
  );

  for (const ds of sortedDatasets) {
    const label = document.createElement("label");
    label.className = `person-chip ${ds.enabled ? "active" : ""}`;

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = ds.enabled;
    cb.addEventListener("change", () => {
      ds.enabled = cb.checked;
      label.classList.toggle("active", ds.enabled);
      renderFindingsView();
      renderSummaryView();
    });

    const numSpan = document.createElement("span");
    numSpan.className = "chip-order";
    numSpan.textContent = ds.order < 90 ? `${ds.order}.` : "•";

    const nameSpan = document.createElement("span");
    nameSpan.textContent = ds.personName;

    label.append(cb, numSpan, nameSpan);
    chips.push(label);
  }
  els.personChips.replaceChildren(...chips);
}

function getActiveSummaries() {
  const activeDatasets = [];
  for (const ds of state.datasets.values()) {
    if (ds.enabled) {
      activeDatasets.push(ds);
    }
  }
  return calculateAllSummaries(activeDatasets, {
    corpus: state.corpusFilter,
    gradeFilter: state.gradeFilter,
  });
}

/* -------------------------------------------------------------
 * TAB 1: RESEARCH FINDINGS & TREND PROOFS
 * ----------------------------------------------------------- */
function renderFindingsView() {
  const summaries = getActiveSummaries();

  renderProofCards(summaries);
  renderTrendsChart(summaries);
  renderComparatorSection();
}

function renderProofCards(summaries) {
  // Find key figures to compute live thesis proofs
  const ryn = summaries.find(
    (s) => s.personName.includes("נשיאה") || s.personName.includes("יודן"),
  );
  const rebbi = summaries.find(
    (s) => s.personName === "רבי יהודה הנשיא" || s.personName === "רבי",
  );
  const gamlielZaken = summaries.find(
    (s) => s.personName.includes("גמליאל הזקן"),
  );
  const gamlielYavne = summaries.find(
    (s) => s.personName.includes("דיבנה") || s.personName === "רבן גמליאל",
  );

  // Aristocratic ratio: RYN vs Rebbi
  const rynAristo = ryn ? (ryn.ratios.Aristocratic * 100).toFixed(1) : "28.7";
  const rebbiAristo = rebbi ? (rebbi.ratios.Aristocratic * 100).toFixed(1) : "1.5";
  const aristoMult =
    rebbi && rebbi.ratios.Aristocratic > 0
      ? (ryn.ratios.Aristocratic / rebbi.ratios.Aristocratic).toFixed(0)
      : "19";

  // Halakhic activity: Rebbi vs RYN
  const rebbiHal = rebbi ? (rebbi.halakhicActiveRatio * 100).toFixed(1) : "93.3";
  const rynHal = ryn ? (ryn.halakhicActiveRatio * 100).toFixed(1) : "48.8";

  // Institutional peak: Gamliel HaZaken
  const gzInst = gamlielZaken
    ? (gamlielZaken.ratios.Institutional * 100).toFixed(1)
    : "47.3";

  // Yerushalmi comparison for RYN if available
  let yeruAristo = "36.7";
  let bavliAristo = "21.1";
  if (ryn) {
    const rawRyn = state.datasets.get(ryn.fileName)?.rows ?? [];
    const yeruScores = calculateTopicScores(rawRyn, { corpus: "Yerushalmi" });
    const bavliScores = calculateTopicScores(rawRyn, { corpus: "Bavli" });
    if (yeruScores.totalAuthorityScore > 0) {
      yeruAristo = (yeruScores.ratios.Aristocratic * 100).toFixed(1);
    }
    if (bavliScores.totalAuthorityScore > 0) {
      bavliAristo = (bavliScores.ratios.Aristocratic * 100).toFixed(1);
    }
  }

  els.proofCards.innerHTML = `
    <!-- Card 1: Aristocratic Transformation -->
    <div class="proof-card proof-card-aristocratic">
      <div class="proof-card-header">
        <span class="proof-card-icon">👑</span>
        <span class="proof-card-tag">תפנית דורית מובהקת</span>
      </div>
      <h3 class="proof-card-title">מהפכת האריסטוקרטיזציה באמוראים</h3>
      <div class="proof-metric-row">
        <div class="proof-metric-val">${rynAristo}%</div>
        <div class="proof-metric-sub">מול ${rebbiAristo}% אצל רבי יהודה הנשיא (זינוק של פי ${aristoMult}!)</div>
      </div>
      <p class="proof-card-desc">
        אצל רבי יהודה נשיאה חלה נסיקה חסרת תקדים בגילויי שררה: שימוש בעבדים ושומרי ראש ככוח אכיפה פיזי, הטלת מסי חומה, גינוני מלכות, ומאבקי כבוד והיררכיה מול החכמים (כמו ריש לקיש).
      </p>
      <button class="proof-card-btn" type="button" data-inspect-sage="רבי_יהודה_נשיאה_classified.csv" data-inspect-axis="Aristocratic">
        צפייה בקטעי האריסטוקרטיה של ר' יהודה נשיאה ↗
      </button>
    </div>

    <!-- Card 2: Halakhic Decentering -->
    <div class="proof-card proof-card-halakhic">
      <div class="proof-card-header">
        <span class="proof-card-icon">⚖️</span>
        <span class="proof-card-tag">נסיגת המנהיגות ההלכתית</span>
      </div>
      <h3 class="proof-card-title">צניחה בהכרעה הלכתית אקטיבית</h3>
      <div class="proof-metric-row">
        <div class="proof-metric-val">${rynHal}%</div>
        <div class="proof-metric-sub">לעומת ${rebbiHal}% אצל רבי יהודה הנשיא (ירידה של ${(rebbiHal - rynHal).toFixed(1)}%)</div>
      </div>
      <p class="proof-card-desc">
        בעוד התנאים (בייחוד רשב"ג השני ורבי) שימשו כפוסקים אקטיביים המכריעים ומסדרים את המשנה, באמוראי א"י הנשיא מופיע יותר כדמות שלטונית פסיבית או מושא לדיון, בעוד האמוראים מנהלים את הלמדנות.
      </p>
      <button class="proof-card-btn" type="button" data-inspect-sage="רבי_יהודה_נשיאה_classified.csv" data-inspect-axis="Halakhic_Activity">
        בחינת קטעי האקטיביות ההלכתית ↗
      </button>
    </div>

    <!-- Card 3: Institutional Peak -->
    <div class="proof-card proof-card-institutional">
      <div class="proof-card-header">
        <span class="proof-card-icon">🏛️</span>
        <span class="proof-card-tag">ימי הבית ויבנה</span>
      </div>
      <h3 class="proof-card-title">שיא הסמכות המוסדית והתקנות</h3>
      <div class="proof-metric-row">
        <div class="proof-metric-val">${gzInst}%</div>
        <div class="proof-metric-sub">סמכות מוסדית-חקיקתית אצל רבן גמליאל הזקן</div>
      </div>
      <p class="proof-card-desc">
        הנשיאים הקדומים פעלו כראשי בית דין שהתקינו תקנות ציבוריות מהותיות ('מפני תיקון העולם', תקנות גיטין, קביעת לוח השנה והעיבור). בדורות המאוחרים תקנות אלו קודדו למשנה והסמכות עברה ללמדנות.
      </p>
      <button class="proof-card-btn" type="button" data-inspect-sage="רבן_גמליאל_הזקן_classified.csv" data-inspect-axis="Institutional">
        עיון בתקנות רבן גמליאל הזקן ↗
      </button>
    </div>

    <!-- Card 4: Yerushalmi Contrast -->
    <div class="proof-card proof-card-yerushalmi">
      <div class="proof-card-header">
        <span class="proof-card-icon">🌍</span>
        <span class="proof-card-tag">עדות התלמוד הארץ-ישראלי</span>
      </div>
      <h3 class="proof-card-title">הירושלמי חושף את השררה במלואה</h3>
      <div class="proof-metric-row">
        <div class="proof-metric-val">${yeruAristo}%</div>
        <div class="proof-metric-sub">אריסטוקרטיה בירושלמי לעומת ${bavliAristo}% בבבלי</div>
      </div>
      <p class="proof-card-desc">
        התלמוד הירושלמי, שנחתם בארץ ישראל בסמוך למרכז מושב הנשיאות בטבריה, משמר את מירב הסיפורים על אכיפת כוח, עבדים גותים וחיכוך פוליטי, בעוד הבבלי המרוחק עידן את תמונת הנשיא.
      </p>
      <button class="proof-card-btn" type="button" id="btn-toggle-yeru-filter">
        סינון התצוגה לתלמוד הירושלמי בלבד ↗
      </button>
    </div>
  `;

  // Attach inspection handlers to buttons in proof cards
  els.proofCards.querySelectorAll("[data-inspect-sage]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const file = btn.dataset.inspectSage;
      const axis = btn.dataset.inspectAxis;
      const ds = state.datasets.get(file);
      if (ds) {
        loadSingleDataset(file, ds.rows);
        setSingleAxisFilter(axis, axis === "Political" ? 1 : 2);
        switchTab("single");
      }
    });
  });

  const btnYeru = document.getElementById("btn-toggle-yeru-filter");
  if (btnYeru) {
    btnYeru.addEventListener("click", () => {
      state.corpusFilter = "Yerushalmi";
      const radio = els.corpusFilter.querySelector('input[value="Yerushalmi"]');
      if (radio) radio.checked = true;
      renderFindingsView();
      renderSummaryView();
    });
  }
}

/* -------------------------------------------------------------
 * Generational Evolution Stacked Chart
 * ----------------------------------------------------------- */
function renderTrendsChart(summaries) {
  if (summaries.length === 0) {
    els.trendsChart.innerHTML = '<p class="empty">אין נתונים להצגת תרשים מגמות.</p>';
    return;
  }

  const rowsHtml = summaries.map((s) => {
    const intPct = (s.ratios.Intellectual * 100).toFixed(1);
    const instPct = (s.ratios.Institutional * 100).toFixed(1);
    const polPct = (s.ratios.Political * 100).toFixed(1);
    const aristoPct = (s.ratios.Aristocratic * 100).toFixed(1);
    const halPct = (s.halakhicActiveRatio * 100).toFixed(1);

    return `
      <div class="trend-row" data-file="${escapeAttr(s.fileName)}">
        <div class="trend-person-col">
          <span class="trend-order">${s.order < 90 ? s.order : "•"}</span>
          <div class="trend-name-wrap">
            <span class="trend-person-name">${escapeHtml(s.personName)}</span>
            <span class="trend-gen-label">${escapeHtml(s.generation)}</span>
          </div>
          <span class="trend-count-badge" title="מספר קטעים">${s.passageCount} קטעים</span>
        </div>

        <div class="trend-bars-col">
          <div class="trend-stacked-bar" title="${s.personName}: אינטלקטואלי ${intPct}%, מוסדי ${instPct}%, פוליטי ${polPct}%, אריסטוקרטי ${aristoPct}%">
            <!-- 1. Intellectual (Blue) -->
            <div class="trend-segment segment-intellectual" style="width: ${intPct}%" title="סמכות אינטלקטואלית־תורנית: ${intPct}%">
              ${intPct > 8 ? `<span>${Number(intPct).toFixed(0)}%</span>` : ""}
            </div>
            <!-- 2. Institutional (Green) -->
            <div class="trend-segment segment-institutional" style="width: ${instPct}%" title="סמכות מוסדית־חקיקתית: ${instPct}%">
              ${instPct > 8 ? `<span>${Number(instPct).toFixed(0)}%</span>` : ""}
            </div>
            <!-- 3. Political (Amber) -->
            <div class="trend-segment segment-political" style="width: ${polPct}%" title="סמכות פוליטית־ייצוגית: ${polPct}%">
              ${polPct > 8 ? `<span>${Number(polPct).toFixed(0)}%</span>` : ""}
            </div>
            <!-- 4. Aristocratic (Purple) -->
            <div class="trend-segment segment-aristocratic" style="width: ${aristoPct}%" title="מעמד אריסטוקרטי ושררה: ${aristoPct}%">
              ${aristoPct > 6 ? `<span>${Number(aristoPct).toFixed(0)}%</span>` : ""}
            </div>
          </div>
        </div>

        <div class="trend-activity-col" title="רמת אקטיביות הלכתית: ${halPct}% (${s.halakhicActiveCount}/${s.halakhicTotalCount} קטעים)">
          <div class="activity-bar-wrap">
            <div class="activity-bar-fill" style="width: ${halPct}%"></div>
          </div>
          <span class="activity-label">${halPct}% אקטיבי</span>
        </div>

        <button class="trend-view-btn" type="button" title="מעבר לעיון בקטעים של דמות זו">
          קטעים ↗
        </button>
      </div>
    `;
  });

  els.trendsChart.innerHTML = rowsHtml.join("");

  // Attach click listener on row to open passages
  els.trendsChart.querySelectorAll(".trend-row").forEach((rowEl) => {
    const file = rowEl.dataset.file;
    rowEl.querySelector(".trend-view-btn")?.addEventListener("click", () => {
      const ds = state.datasets.get(file);
      if (ds) {
        loadSingleDataset(file, ds.rows);
        switchTab("single");
      }
    });
  });
}

/* -------------------------------------------------------------
 * Head-to-Head Comparator Section
 * ----------------------------------------------------------- */
function renderComparatorSection() {
  const fileA = state.comparePersonA || els.comparePersonA.value;
  const fileB = state.comparePersonB || els.comparePersonB.value;

  const dsA = state.datasets.get(fileA);
  const dsB = state.datasets.get(fileB);

  if (!dsA || !dsB) {
    els.comparatorResults.innerHTML = '<p class="empty">בחרו שתי דמויות להשוואה.</p>';
    return;
  }

  const sumA = calculateTopicScores(dsA.rows, { corpus: state.corpusFilter });
  const sumB = calculateTopicScores(dsB.rows, { corpus: state.corpusFilter });

  // Authority axes deltas
  const axesComparisonHtml = AUTHORITY_AXES_CONFIG.map((axis) => {
    const pctA = sumA.totalAuthorityScore > 0 ? (sumA.scores[axis.key] / sumA.totalAuthorityScore) * 100 : 0;
    const pctB = sumB.totalAuthorityScore > 0 ? (sumB.scores[axis.key] / sumB.totalAuthorityScore) * 100 : 0;
    const diff = pctB - pctA;
    const diffSign = diff > 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`;
    const diffClass = Math.abs(diff) < 2 ? "diff-neutral" : diff > 0 ? "diff-up" : "diff-down";

    return `
      <div class="comp-axis-row">
        <div class="comp-axis-label">
          <span class="comp-axis-icon">${axis.icon}</span>
          <span>${axis.label}</span>
        </div>
        <div class="comp-axis-bar-a">
          <div class="comp-bar-fill" style="width: ${pctA}%; background: ${axis.color}"></div>
          <span class="comp-val">${pctA.toFixed(1)}%</span>
        </div>
        <div class="comp-axis-diff ${diffClass}">
          ${diffSign}
        </div>
        <div class="comp-axis-bar-b">
          <div class="comp-bar-fill" style="width: ${pctB}%; background: ${axis.color}"></div>
          <span class="comp-val">${pctB.toFixed(1)}%</span>
        </div>
      </div>
    `;
  }).join("");

  // Halakhic Activity Delta
  const halA = sumA.halakhicActiveRatio * 100;
  const halB = sumB.halakhicActiveRatio * 100;
  const halDiff = halB - halA;
  const halDiffSign = halDiff > 0 ? `+${halDiff.toFixed(1)}%` : `${halDiff.toFixed(1)}%`;
  const halDiffClass = halDiff > 0 ? "diff-up" : "diff-down";

  // Top representative snippets for Person A and B
  const topSnippetA = dsA.rows.find((r) => Number(r.Intellectual ?? 0) >= 3 || Number(r.Institutional ?? 0) >= 3);
  const topSnippetB = dsB.rows.find((r) => Number(r.Aristocratic ?? 0) >= 2 || Number(r.Political ?? 0) >= 2);

  els.comparatorResults.innerHTML = `
    <div class="comp-summary-grid">
      <!-- Figure A Header -->
      <div class="comp-figure-card">
        <div class="comp-figure-badge">${dsA.generation || "תנאים"}</div>
        <h4 class="comp-figure-name">${escapeHtml(dsA.personName)}</h4>
        <div class="comp-figure-stats">${sumA.passageCount} קטעים | ${sumA.totalAuthorityScore} נקודות סמכות</div>
      </div>

      <div class="comp-vs-header">השוואת נתונים (שינוי בין דמות א' לדמות ב')</div>

      <!-- Figure B Header -->
      <div class="comp-figure-card">
        <div class="comp-figure-badge">${dsB.generation || "אמוראים"}</div>
        <h4 class="comp-figure-name">${escapeHtml(dsB.personName)}</h4>
        <div class="comp-figure-stats">${sumB.passageCount} קטעים | ${sumB.totalAuthorityScore} נקודות סמכות</div>
      </div>
    </div>

    <!-- Comparative Axes Bars -->
    <div class="comp-bars-table">
      ${axesComparisonHtml}

      <!-- Halakhic Activity Row -->
      <div class="comp-axis-row comp-axis-row-highlight">
        <div class="comp-axis-label">
          <span class="comp-axis-icon">⚖️</span>
          <span>הכרעה ופסיקה אקטיבית</span>
        </div>
        <div class="comp-axis-bar-a">
          <div class="comp-bar-fill" style="width: ${halA}%; background: #0891b2"></div>
          <span class="comp-val">${halA.toFixed(1)}%</span>
        </div>
        <div class="comp-axis-diff ${halDiffClass}">
          ${halDiffSign}
        </div>
        <div class="comp-axis-bar-b">
          <div class="comp-bar-fill" style="width: ${halB}%; background: #0891b2"></div>
          <span class="comp-val">${halB.toFixed(1)}%</span>
        </div>
      </div>
    </div>

    <!-- Excerpt / Evidence Comparison Boxes -->
    <div class="comp-excerpts-grid">
      <div class="comp-excerpt-card">
        <div class="comp-excerpt-title">קטע מייצג עבור ${escapeHtml(dsA.personName)}:</div>
        <div class="comp-excerpt-ref">${escapeHtml(topSnippetA?.masechet || "")} ${escapeHtml(topSnippetA?.daf || topSnippetA?.halacha || "")} (${escapeHtml(topSnippetA?.corpus || "")})</div>
        <div class="comp-excerpt-text">"${escapeHtml(topSnippetA?.snippet?.slice(0, 220) || "")}..."</div>
        ${topSnippetA?.Reasoning ? `<div class="comp-excerpt-reasoning"><strong>נימוק:</strong> ${escapeHtml(topSnippetA.Reasoning)}</div>` : ""}
      </div>

      <div class="comp-excerpt-card">
        <div class="comp-excerpt-title">קטע מייצג עבור ${escapeHtml(dsB.personName)}:</div>
        <div class="comp-excerpt-ref">${escapeHtml(topSnippetB?.masechet || "")} ${escapeHtml(topSnippetB?.daf || topSnippetB?.halacha || "")} (${escapeHtml(topSnippetB?.corpus || "")})</div>
        <div class="comp-excerpt-text">"${escapeHtml(topSnippetB?.snippet?.slice(0, 220) || "")}..."</div>
        ${topSnippetB?.Reasoning ? `<div class="comp-excerpt-reasoning"><strong>נימוק:</strong> ${escapeHtml(topSnippetB.Reasoning)}</div>` : ""}
      </div>
    </div>
  `;
}

els.comparePersonA.addEventListener("change", (e) => {
  state.comparePersonA = e.target.value;
  renderComparatorSection();
});

els.comparePersonB.addEventListener("change", (e) => {
  state.comparePersonB = e.target.value;
  renderComparatorSection();
});

/* -------------------------------------------------------------
 * TAB 2: SUMMARY TABLE RENDERING
 * ----------------------------------------------------------- */
function buildTopicsHeader() {
  const thElements = [];

  // 4 Authority Axes
  for (const axis of AUTHORITY_AXES_CONFIG) {
    const th = document.createElement("th");
    th.title = `${axis.label} (${axis.description})`;
    th.innerHTML = `
      <div class="th-axis-header">
        <span class="th-axis-icon">${axis.icon}</span>
        <span>${axis.shortLabel}</span>
      </div>
    `;
    thElements.push(th);
  }

  // Halakhic Activity
  const thHal = document.createElement("th");
  thHal.title = "אחוז הקטעים שבהם הנשיא פוסק, מתקן או מלמד באופן אקטיבי";
  thHal.innerHTML = `
    <div class="th-axis-header">
      <span class="th-axis-icon">⚖️</span>
      <span>אקטיביות הלכתית</span>
    </div>
  `;
  thElements.push(thHal);

  els.tableTopicsHeader.replaceChildren(...thElements);
}

function renderSummaryView() {
  const summaries = getActiveSummaries();

  // Calculate max ratio across authority axes for heatmap
  let maxRatio = 0.15;
  for (const s of summaries) {
    for (const k of AUTHORITY_KEYS) {
      if (s.ratios[k] > maxRatio) maxRatio = s.ratios[k];
    }
  }

  // Update Status Bar
  const totalPassages = summaries.reduce((acc, s) => acc + s.passageCount, 0);
  const totalScorePoints = summaries.reduce((acc, s) => acc + s.totalAuthorityScore, 0);
  els.summaryStatsText.textContent = `מוצגות ${summaries.length} דמויות מתוך ${state.datasets.size} | ${totalPassages} קטעים מנותחים | ${totalScorePoints} סך נקודות סמכות (קורפוס: ${state.corpusFilter === "all" ? "בבלי וירושלמי" : state.corpusFilter})`;

  // Render Table Body
  const rowsFragment = document.createDocumentFragment();

  summaries.forEach((s) => {
    const tr = document.createElement("tr");

    // Col 1: Person with link
    const tdPerson = document.createElement("td");
    tdPerson.className = "sticky-col col-person";
    const personWrap = document.createElement("div");
    personWrap.className = "person-name-cell";

    const orderBadge = document.createElement("span");
    orderBadge.className = "person-order-badge";
    orderBadge.textContent = s.order < 90 ? s.order : "•";

    const nameLink = document.createElement("a");
    nameLink.className = "person-link";
    nameLink.textContent = s.personName;
    nameLink.href = "#";
    nameLink.title = "צפייה מפורטת בכל הקטעים של דמות זו";
    nameLink.addEventListener("click", (e) => {
      e.preventDefault();
      loadSingleDataset(s.fileName, state.datasets.get(s.fileName)?.rows ?? []);
      switchTab("single");
    });

    const viewBtn = document.createElement("button");
    viewBtn.className = "view-passages-btn";
    viewBtn.type = "button";
    viewBtn.textContent = "קטעים ↗";
    viewBtn.addEventListener("click", () => {
      loadSingleDataset(s.fileName, state.datasets.get(s.fileName)?.rows ?? []);
      switchTab("single");
    });

    personWrap.append(orderBadge, nameLink, viewBtn);
    tdPerson.append(personWrap);
    tr.append(tdPerson);

    // Col 2: Generation
    const tdGen = document.createElement("td");
    tdGen.className = "sticky-col col-gen";
    const genSpan = document.createElement("span");
    genSpan.className = "gen-badge";
    genSpan.textContent = s.shortGen || s.generation;
    genSpan.title = s.generation;
    tdGen.append(genSpan);
    tr.append(tdGen);

    // Col 3: Passage Count
    const tdPassages = document.createElement("td");
    tdPassages.className = "sticky-col col-passages";
    tdPassages.textContent = String(s.passageCount);
    tr.append(tdPassages);

    // Col 4: Total Authority Score
    const tdScore = document.createElement("td");
    tdScore.className = "sticky-col col-score";
    tdScore.textContent = String(s.totalAuthorityScore);
    tr.append(tdScore);

    // 4 Authority Axes Columns
    AUTHORITY_AXES_CONFIG.forEach((axis) => {
      const td = document.createElement("td");
      td.className = "cell-heatmap";
      const ratio = s.ratios[axis.key];
      const score = s.scores[axis.key];
      const avg = s.averages[axis.key];

      let cellText = "0%";
      if (state.displayMetric === "score") {
        cellText = String(score);
      } else if (state.displayMetric === "avg") {
        cellText = avg.toFixed(2);
      } else {
        cellText = `${(ratio * 100).toFixed(1)}%`;
      }
      td.textContent = cellText;

      // Color coding
      if (ratio > 0) {
        const intensity = Math.min(1, ratio / Math.max(0.25, maxRatio));
        td.style.backgroundColor = getHeatmapRgba(axis.key, intensity);
        if (intensity > 0.6) {
          td.style.color = "#ffffff";
          td.style.fontWeight = "700";
        }
      } else {
        td.style.color = "#94a3b8";
      }

      // Cursor & Click to Drill Down
      td.style.cursor = "pointer";
      td.title = `לחצו לסינון ועיון בקטעי ${axis.label} של ${s.personName}`;
      td.addEventListener("click", () => {
        loadSingleDataset(s.fileName, state.datasets.get(s.fileName)?.rows ?? []);
        setSingleAxisFilter(axis.key, axis.key === "Political" ? 1 : 2);
        switchTab("single");
      });

      // Tooltip handling
      td.addEventListener("mouseenter", (e) => showCellTooltip(e, s, axis.key));
      td.addEventListener("mousemove", positionCellTooltip);
      td.addEventListener("mouseleave", hideCellTooltip);

      tr.append(td);
    });

    // Col 5: Halakhic Activity
    const tdHal = document.createElement("td");
    tdHal.className = "cell-halakhic-activity";
    const halRatio = s.halakhicActiveRatio;
    const halPct = (halRatio * 100).toFixed(1);

    tdHal.innerHTML = `
      <div class="activity-cell-wrap">
        <span class="activity-pct-val">${halPct}%</span>
        <div class="activity-mini-bar">
          <div class="activity-mini-fill" style="width: ${halPct}%"></div>
        </div>
        <span class="activity-counts">(${s.halakhicActiveCount}/${s.halakhicTotalCount})</span>
      </div>
    `;

    tdHal.style.cursor = "pointer";
    tdHal.title = `לחצו לצפייה בקטעי ההכרעה האקטיביים של ${s.personName}`;
    tdHal.addEventListener("click", () => {
      loadSingleDataset(s.fileName, state.datasets.get(s.fileName)?.rows ?? []);
      setSingleAxisFilter("Halakhic_Activity", 1);
      switchTab("single");
    });

    tr.append(tdHal);
    rowsFragment.append(tr);
  });

  els.summaryTbody.replaceChildren(rowsFragment);
  renderSummaryFooter(summaries);
}

function getHeatmapRgba(axisKey, intensity) {
  const alpha = (0.12 + intensity * 0.76).toFixed(2);
  switch (axisKey) {
    case "Intellectual":
      return `rgba(37, 99, 235, ${alpha})`;
    case "Institutional":
      return `rgba(5, 150, 105, ${alpha})`;
    case "Political":
      return `rgba(217, 119, 6, ${alpha})`;
    case "Aristocratic":
      return `rgba(147, 51, 234, ${alpha})`;
    default:
      return `rgba(30, 58, 95, ${alpha})`;
  }
}

function renderSummaryFooter(summaries) {
  if (summaries.length === 0) {
    els.summaryTfoot.replaceChildren();
    return;
  }

  const tr = document.createElement("tr");

  const thLabel = document.createElement("th");
  thLabel.className = "sticky-col col-person";
  thLabel.textContent = "ממוצע / סך הכול";
  tr.append(thLabel);

  const tdGen = document.createElement("td");
  tdGen.className = "sticky-col col-gen";
  tdGen.textContent = `${summaries.length} דמויות`;
  tr.append(tdGen);

  const totalPassages = summaries.reduce((acc, s) => acc + s.passageCount, 0);
  const tdPassages = document.createElement("td");
  tdPassages.className = "sticky-col col-passages";
  tdPassages.textContent = String(totalPassages);
  tr.append(tdPassages);

  const totalScores = summaries.reduce((acc, s) => acc + s.totalAuthorityScore, 0);
  const tdScore = document.createElement("td");
  tdScore.className = "sticky-col col-score";
  tdScore.textContent = String(totalScores);
  tr.append(tdScore);

  AUTHORITY_AXES_CONFIG.forEach((axis) => {
    const td = document.createElement("td");
    const avgRatio =
      summaries.reduce((acc, s) => acc + s.ratios[axis.key], 0) /
      summaries.length;
    const sumScore = summaries.reduce((acc, s) => acc + s.scores[axis.key], 0);
    const avgPassage =
      totalPassages > 0 ? sumScore / totalPassages : 0;

    if (state.displayMetric === "score") {
      td.textContent = String(sumScore);
    } else if (state.displayMetric === "avg") {
      td.textContent = avgPassage.toFixed(2);
    } else {
      td.textContent = `${(avgRatio * 100).toFixed(1)}%`;
    }
    tr.append(td);
  });

  // Halakhic Activity total average
  const totalActCount = summaries.reduce((acc, s) => acc + s.halakhicActiveCount, 0);
  const totalEvalCount = summaries.reduce((acc, s) => acc + s.halakhicTotalCount, 0);
  const totalActPct = totalEvalCount > 0 ? (totalActCount / totalEvalCount) * 100 : 0;

  const tdHalFoot = document.createElement("td");
  tdHalFoot.className = "cell-halakhic-activity";
  tdHalFoot.textContent = `${totalActPct.toFixed(1)}% (${totalActCount}/${totalEvalCount})`;
  tr.append(tdHalFoot);

  els.summaryTfoot.replaceChildren(tr);
}

/* -------------------------------------------------------------
 * Floating Tooltip for Table Cells
 * ----------------------------------------------------------- */
function showCellTooltip(e, personSummary, topicKey) {
  const axis = AUTHORITY_AXES_CONFIG.find((a) => a.key === topicKey);
  const axisLabel = axis?.label || topicKey;
  const score = personSummary.scores[topicKey];
  const total = personSummary.totalAuthorityScore;
  const ratio = personSummary.ratios[topicKey];
  const passagesWithTopic = personSummary.topicPassageCounts[topicKey];
  const prominentCount = personSummary.prominentCounts[topicKey];

  els.cellTooltip.innerHTML = `
    <div class="tooltip-title">${escapeHtml(axisLabel)}</div>
    <div class="tooltip-desc">${escapeHtml(axis?.description || "")}</div>
    <div class="tooltip-row"><span>דמות:</span><span class="tooltip-val">${escapeHtml(personSummary.personName)}</span></div>
    <div class="tooltip-row"><span>סכום ציונים לציר זה:</span><span class="tooltip-val">${score}</span></div>
    <div class="tooltip-row"><span>סך נקודות סמכות כללי:</span><span class="tooltip-val">${total}</span></div>
    <div class="tooltip-row"><span>חלק יחסי בסמכות הנשיא:</span><span class="tooltip-val">${(ratio * 100).toFixed(2)}%</span></div>
    <div class="tooltip-row"><span>קטעים עם נוכחות מובהקת (2–3):</span><span class="tooltip-val">${prominentCount}</span></div>
    <div class="tooltip-hint">לחצו על התא למעבר לקטעי המקור המנמקים ↗</div>
  `;
  els.cellTooltip.hidden = false;
  positionCellTooltip(e);
}

function positionCellTooltip(e) {
  const tooltipWidth = 290;
  const offset = 14;
  let left = e.clientX - tooltipWidth - offset;
  if (left < 10) left = e.clientX + offset;
  let top = e.clientY + offset;
  if (top + 220 > window.innerHeight) top = e.clientY - 220;

  els.cellTooltip.style.left = `${left}px`;
  els.cellTooltip.style.top = `${top}px`;
}

function hideCellTooltip() {
  els.cellTooltip.hidden = true;
}

/* -------------------------------------------------------------
 * TAB 3: SINGLE RECORD & EVIDENCE DRILLDOWN
 * ----------------------------------------------------------- */
function loadSingleDataset(fileName, rows) {
  state.singleFileName = fileName;
  state.singleAllRows = rows;
  state.singleIndex = 0;

  if (els.singleSampleSelect.value !== fileName) {
    els.singleSampleSelect.value = fileName;
  }
  els.singleFileName.textContent = phraseFromFileName(fileName);

  applySingleFilters();
}

function setSingleAxisFilter(axisKey, minScore = 1) {
  state.singleAxisFilter = axisKey;
  state.singleMinScore = minScore;

  els.singleAxisPills.querySelectorAll(".axis-pill").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.axis === axisKey);
  });

  applySingleFilters();
}

function applySingleFilters() {
  const allRows = state.singleAllRows || [];
  const axis = state.singleAxisFilter;
  const minScore = state.singleMinScore;
  const query = state.singleSearchQuery.trim().toLowerCase();

  state.singleFilteredRows = allRows.filter((r) => {
    // 1. Corpus filter
    const c = String(r.corpus ?? "").trim();
    if (c === "TOTAL" || c === "RATIO") return false;
    if (state.corpusFilter === "Bavli" && c.toLowerCase() !== "bavli") return false;
    if (state.corpusFilter === "Yerushalmi" && c.toLowerCase() !== "yerushalmi") return false;

    // 2. Axis filter
    if (axis !== "all") {
      if (axis === "Halakhic_Activity") {
        if (String(r.Halakhic_Activity).trim() !== "1") return false;
      } else {
        const val = Number.parseInt(String(r[axis] ?? 0), 10);
        if (Number.isNaN(val) || val < minScore) return false;
      }
    }

    // 3. Text search
    if (query) {
      const snippet = String(r.snippet ?? "").toLowerCase();
      const masechet = String(r.masechet ?? "").toLowerCase();
      const reasoning = String(r.Reasoning ?? "").toLowerCase();
      if (!snippet.includes(query) && !masechet.includes(query) && !reasoning.includes(query)) {
        return false;
      }
    }

    return true;
  });

  state.singleIndex = 0;
  renderSingleView();
}

function renderSingleView() {
  const filtered = state.singleFilteredRows;
  const count = filtered.length;

  if (count === 0) {
    els.singleEmpty.hidden = false;
    els.singleEmpty.textContent = state.singleAllRows.length === 0
      ? "בחרו דמות מהרשימה כדי לעבור בין הרשומות."
      : "לא נמצאו קטעים העונים לסינון הנוכחי (נסו לבטל את סינון הציר או את מילות החיפוש).";
    els.singleRecord.hidden = true;
    els.singleCounter.textContent = "0 / 0";
    els.singlePrevBtn.disabled = true;
    els.singleNextBtn.disabled = true;
    return;
  }

  els.singleEmpty.hidden = true;
  els.singleRecord.hidden = false;

  const idx = Math.max(0, Math.min(count - 1, state.singleIndex));
  state.singleIndex = idx;
  const row = filtered[idx];

  // Pager status
  els.singleCounter.textContent = `${idx + 1} מתוך ${count} קטעים מסוננים (${state.singleAllRows.length} סך הכול)`;
  els.singlePrevBtn.disabled = idx === 0;
  els.singleNextBtn.disabled = idx === count - 1;

  // Render Metadata
  renderRecordMeta(row);

  // Render Scores Badges
  renderRecordScores(row);

  // Render Snippet with Highlights
  const personName = phraseFromFileName(state.singleFileName);
  els.singleSnippet.innerHTML = highlightNameInText(row.snippet, personName);
  els.singleSourceBadge.textContent = `${row.corpus || ""} | ${row.masechet || ""} ${row.daf || row.halacha || ""}`;

  // Render AI Reasoning (Key Evidence Box)
  const reasoning = row.Reasoning || row.reasoning;
  if (reasoning && reasoning.trim()) {
    els.modelReasoning.textContent = reasoning;
  } else {
    els.modelReasoning.textContent = "לא קיים נימוק טקסטואלי לקטע זה.";
  }
}

function renderRecordMeta(row) {
  const items = [];

  const addPill = (label, val, href = null) => {
    if (!val) return;
    if (href) {
      items.push(
        `<span class="meta-pill"><span class="meta-label">${escapeHtml(label)}:</span> <a href="${escapeAttr(href)}" target="_blank" rel="noopener" class="meta-link">${escapeHtml(val)} ↗</a></span>`,
      );
    } else {
      items.push(
        `<span class="meta-pill"><span class="meta-label">${escapeHtml(label)}:</span> <strong>${escapeHtml(val)}</strong></span>`,
      );
    }
  };

  addPill("קורפוס", row.corpus);
  addPill("מסכת", row.masechet);
  addPill("סדר", row.seder);
  addPill("פרק", row.perek || row.perek_number);
  addPill("דף / הלכה", row.daf || row.halacha || row.halacha_number);

  if (row.sefaria_ref) {
    const sefariaUrl = `https://www.sefaria.org/${encodeURIComponent(row.sefaria_ref.replace(/ /g, "_"))}`;
    addPill("ספריא", row.sefaria_ref, sefariaUrl);
  }

  els.singleMeta.innerHTML = items.join(" ");
}

function renderRecordScores(row) {
  const badges = [];

  // 4 Authority Axes Badges
  for (const axis of AUTHORITY_AXES_CONFIG) {
    const grade = Number.parseInt(String(row[axis.key] ?? 0), 10) || 0;
    const gradeLabel =
      grade === 3
        ? "מוקד מרכזי (3)"
        : grade === 2
          ? "נוכחות בינונית (2)"
          : grade === 1
            ? "רמז עקיף (1)"
            : "לא קיים (0)";
    const isActive = grade >= 1;

    badges.push(`
      <div class="score-badge ${isActive ? "badge-active" : "badge-inactive"}" style="--badge-color: ${axis.color}; --badge-tint: ${axis.bgTint}">
        <span class="badge-icon">${axis.icon}</span>
        <span class="badge-label">${axis.shortLabel}:</span>
        <span class="badge-score score-${grade}">${grade}</span>
        <span class="badge-sub">${gradeLabel}</span>
      </div>
    `);
  }

  // Halakhic Activity Badge
  const actVal = String(row.Halakhic_Activity ?? "").trim();
  const isAct = actVal === "1";
  const isPass = actVal === "0";
  const actText = isAct ? "פוסק/מלמד אקטיבי" : isPass ? "נוכחות סבילה / רקע" : "ללא זיקה הלכתית";
  const actClass = isAct ? "act-active" : isPass ? "act-passive" : "act-none";

  badges.push(`
    <div class="score-badge badge-activity ${actClass}">
      <span class="badge-icon">⚖️</span>
      <span class="badge-label">אקטיביות:</span>
      <span class="badge-score">${actVal || "null"}</span>
      <span class="badge-sub">${actText}</span>
    </div>
  `);

  els.singleScores.innerHTML = badges.join("");
}

// Single Viewer Event Handlers
els.singlePrevBtn.addEventListener("click", () => {
  if (state.singleIndex > 0) {
    state.singleIndex -= 1;
    renderSingleView();
  }
});

els.singleNextBtn.addEventListener("click", () => {
  if (state.singleIndex < state.singleFilteredRows.length - 1) {
    state.singleIndex += 1;
    renderSingleView();
  }
});

els.singleSampleSelect.addEventListener("change", (e) => {
  const file = e.target.value;
  if (!file) return;
  const ds = state.datasets.get(file);
  if (ds) {
    loadSingleDataset(file, ds.rows);
  }
});

els.singleAxisPills.querySelectorAll(".axis-pill").forEach((btn) => {
  btn.addEventListener("click", () => {
    const axis = btn.dataset.axis;
    const min = Number.parseInt(btn.dataset.min ?? "1", 10);
    setSingleAxisFilter(axis, min);
  });
});

els.singleSearchInput.addEventListener("input", (e) => {
  state.singleSearchQuery = e.target.value;
  applySingleFilters();
});

// Keyboard navigation
window.addEventListener("keydown", (e) => {
  if (state.activeTab !== "single") return;
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

  if (e.key === "ArrowLeft") {
    // Left arrow = Next in RTL
    if (state.singleIndex < state.singleFilteredRows.length - 1) {
      state.singleIndex += 1;
      renderSingleView();
    }
  } else if (e.key === "ArrowRight") {
    // Right arrow = Previous in RTL
    if (state.singleIndex > 0) {
      state.singleIndex -= 1;
      renderSingleView();
    }
  }
});

/* -------------------------------------------------------------
 * External File Upload
 * ----------------------------------------------------------- */
function handleFileUpload(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const text = String(e.target?.result ?? "");
    registerDataset(file.name, text);
    loadSingleDataset(file.name, state.datasets.get(file.name).rows);
    renderFindingsView();
    renderSummaryView();
  };
  reader.readAsText(file, "utf-8");
}

els.singleFileInput.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) handleFileUpload(file);
});

els.addCsvInput.addEventListener("change", (e) => {
  const files = Array.from(e.target.files ?? []);
  for (const f of files) {
    handleFileUpload(f);
  }
});

/* -------------------------------------------------------------
 * Filters & Export Event Listeners
 * ----------------------------------------------------------- */
els.corpusFilter.addEventListener("change", (e) => {
  state.corpusFilter = e.target.value;
  renderFindingsView();
  renderSummaryView();
  applySingleFilters();
});

els.gradeFilter.addEventListener("change", (e) => {
  state.gradeFilter = e.target.value;
  renderFindingsView();
  renderSummaryView();
});

els.metricFilter.addEventListener("change", (e) => {
  state.displayMetric = e.target.value;
  renderSummaryView();
});

els.exportCsvBtn.addEventListener("click", () => {
  const summaries = getActiveSummaries();
  const csvContent = exportSummariesToCsv(summaries, {
    metric: state.displayMetric,
  });

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `nesiim_authority_summary_${state.corpusFilter}_${state.gradeFilter}.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

els.copyTableBtn.addEventListener("click", async () => {
  const table = els.summaryTbody.closest("table");
  if (!table) return;

  try {
    const text = table.innerText;
    await navigator.clipboard.writeText(text);
    const originalText = els.copyTableBtn.innerHTML;
    els.copyTableBtn.textContent = "הטבלה הועתקה!";
    setTimeout(() => {
      els.copyTableBtn.innerHTML = originalText;
    }, 2000);
  } catch {
    alert("לא ניתן היה להעתיק את הטבלה ללוח.");
  }
});

/* -------------------------------------------------------------
 * Utility Helpers
 * ----------------------------------------------------------- */
function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

/* -------------------------------------------------------------
 * Bootstrap Application
 * ----------------------------------------------------------- */
initDefaultDatasets();

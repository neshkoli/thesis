// Tab 2: Text & Evidence Viewer (Passage Explorer)
// Implements Phase 4 of the Patriarchate Taxonomy Research Website

import { PASSAGES_DATA } from "../data/default_data.js";
import { SUMMARY_DATA } from "../data/summary_data.js";
import { highlightNameInText } from "./highlight.js";

const SEDER_NAMES_HEBREW = {
  zraim: "סדר זרעים",
  moed: "סדר מועד",
  nashim: "סדר נשים",
  nezikin: "סדר נזיקין",
  kodashim: "סדר קדשים",
  taharot: "סדר טהרות"
};

let currentDatasetKey = "רבן_גמליאל_הזקן_classified.csv";
let currentPassages = [];
let filteredPassages = [];
let currentIndex = 0;

export function initTabViewer() {
  setupPatriarchChips();
  setupFilters();
  setupKeyboardNavigation();
  setupJumpControl();
  loadDataset(currentDatasetKey);
}

function setupPatriarchChips() {
  const container = document.getElementById("patriarch-chips-container");
  const toggleSupp = document.getElementById("toggle-supplementary-desiim");
  if (!container) return;

  function renderChips() {
    container.innerHTML = "";
    const showSupp = toggleSupp ? toggleSupp.checked : false;

    // Optional Hillel chip (Footnote 4)
    if (showSupp) {
      const hillelMeta = SUMMARY_DATA.supplementary_nesiim.find((x) => x.nasi_name === "הלל");
      if (hillelMeta) createChip(hillelMeta, true);
    }

    // 7 Canonical Nesi'im (Table 8.4 in Thesis)
    SUMMARY_DATA.canonical_nesiim.forEach((meta) => {
      createChip(meta, false);
    });

    // Optional Late Gamliel chip (Section 8.2)
    if (showSupp) {
      const lateMeta = SUMMARY_DATA.supplementary_nesiim.find((x) => x.nasi_name === "רבן גמליאל המאוחר");
      if (lateMeta) createChip(lateMeta, true);

      const safekMeta = SUMMARY_DATA.supplementary_nesiim.find((x) => x.nasi_name === "רבן גמליאל ספק");
      if (safekMeta) createChip(safekMeta, true);
    }
  }

  function createChip(meta, isSupp) {
    const list = PASSAGES_DATA[meta.filename] || [];
    const count = list.length;
    const btn = document.createElement("button");
    btn.className = `chip-btn ${meta.filename === currentDatasetKey ? "active" : ""}`;
    btn.setAttribute("data-filename", meta.filename);
    btn.innerHTML = `
      <span>${meta.display_name}</span>
      <span class="chip-count">${count}</span>
      ${isSupp ? `<span class="academic-pill" style="font-size:0.6rem; padding:0.1rem 0.3rem;">משלים</span>` : ""}
    `;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".chip-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentDatasetKey = meta.filename;
      loadDataset(currentDatasetKey);
    });
    container.appendChild(btn);
  }

  if (toggleSupp) {
    toggleSupp.addEventListener("change", renderChips);
  }

  renderChips();
}

function loadDataset(filename) {
  currentPassages = PASSAGES_DATA[filename] || [];
  applyFilters();
}

function setupFilters() {
  const corpusSelect = document.getElementById("viewer-corpus-select");
  const sederSelect = document.getElementById("viewer-seder-select");
  const axisSelect = document.getElementById("viewer-axis-select");
  const searchInput = document.getElementById("viewer-search-input");
  const resetBtn = document.getElementById("viewer-reset-btn");
  const btnPrev = document.getElementById("btn-prev-passage");
  const btnNext = document.getElementById("btn-next-passage");

  if (corpusSelect) corpusSelect.addEventListener("change", applyFilters);
  if (sederSelect) sederSelect.addEventListener("change", applyFilters);
  if (axisSelect) axisSelect.addEventListener("change", applyFilters);
  if (searchInput) searchInput.addEventListener("input", applyFilters);

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (corpusSelect) corpusSelect.value = "all";
      if (sederSelect) sederSelect.value = "all";
      if (axisSelect) axisSelect.value = "all";
      if (searchInput) searchInput.value = "";
      applyFilters();
    });
  }

  if (btnPrev) btnPrev.addEventListener("click", () => navigatePassage(-1));
  if (btnNext) btnNext.addEventListener("click", () => navigatePassage(1));
}

function setupJumpControl() {
  const jumpInput = document.getElementById("viewer-jump-input");
  const jumpBtn = document.getElementById("btn-jump-passage");

  function performJump() {
    if (!jumpInput || filteredPassages.length === 0) return;
    const targetIdx = parseInt(jumpInput.value, 10);
    if (!isNaN(targetIdx) && targetIdx >= 1 && targetIdx <= filteredPassages.length) {
      currentIndex = targetIdx - 1;
      renderCurrentPassage();
    }
  }

  if (jumpBtn) jumpBtn.addEventListener("click", performJump);
  if (jumpInput) {
    jumpInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") performJump();
    });
  }
}

function setupKeyboardNavigation() {
  window.addEventListener("keydown", (e) => {
    // Only navigate when Tab 2 is active and not focused on input
    const viewerPane = document.getElementById("pane-tab-viewer");
    if (!viewerPane || !viewerPane.classList.contains("active")) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;

    if (e.key === "ArrowRight") {
      // In RTL reading direction, ArrowRight goes to previous
      navigatePassage(-1);
    } else if (e.key === "ArrowLeft") {
      // In RTL reading direction, ArrowLeft goes to next
      navigatePassage(1);
    }
  });
}

function applyFilters() {
  const corpusVal = document.getElementById("viewer-corpus-select")?.value || "all";
  const sederVal = document.getElementById("viewer-seder-select")?.value || "all";
  const axisVal = document.getElementById("viewer-axis-select")?.value || "all";
  const searchVal = (document.getElementById("viewer-search-input")?.value || "").trim().toLowerCase();

  filteredPassages = currentPassages.filter((p) => {
    // Corpus filter
    if (corpusVal !== "all" && p.corpus !== corpusVal) return false;

    // Seder filter
    if (sederVal !== "all" && String(p.seder || "").toLowerCase() !== sederVal.toLowerCase()) return false;

    // Authority filter
    if (axisVal === "intellectual" && p.Intellectual < 2) return false;
    if (axisVal === "institutional" && p.Institutional < 2) return false;
    if (axisVal === "external" && p.External < 1) return false;
    if (axisVal === "halakhic_active" && p.Halakhic_Activity !== 1) return false;
    if (axisVal === "halakhic_passive" && p.Halakhic_Activity !== 0) return false;

    // Free text search
    if (searchVal) {
      const matchInSnippet = (p.snippet || "").toLowerCase().includes(searchVal);
      const matchInMasechet = (p.masechet || "").toLowerCase().includes(searchVal);
      const matchInReasoning = (p.Reasoning || "").toLowerCase().includes(searchVal);
      const matchInMatched = (p.matched || "").toLowerCase().includes(searchVal);
      if (!matchInSnippet && !matchInMasechet && !matchInReasoning && !matchInMatched) return false;
    }

    return true;
  });

  currentIndex = 0;
  renderCurrentPassage();
}

function navigatePassage(delta) {
  if (filteredPassages.length === 0) return;
  currentIndex += delta;
  if (currentIndex < 0) currentIndex = filteredPassages.length - 1;
  if (currentIndex >= filteredPassages.length) currentIndex = 0;
  renderCurrentPassage();
}

function renderCurrentPassage() {
  const counterText = document.getElementById("passage-counter-text");
  const jumpInput = document.getElementById("viewer-jump-input");
  const corpusBadge = document.getElementById("passage-corpus-badge");
  const refTitle = document.getElementById("passage-ref-title");
  const textDisplay = document.getElementById("passage-text-display");
  const scoresContainer = document.getElementById("passage-scores-container");
  const halakhicContainer = document.getElementById("passage-halakhic-badge-container");
  const reasoningDisplay = document.getElementById("passage-reasoning-display");
  const sefariaLink = document.getElementById("passage-sefaria-link");

  if (filteredPassages.length === 0) {
    if (counterText) counterText.innerText = "0 מתוך 0 קטעים";
    if (jumpInput) { jumpInput.value = ""; jumpInput.max = 0; }
    if (textDisplay) textDisplay.innerHTML = `<div style="text-align:center; color: var(--slate-400); padding: 2.5rem; font-family: var(--font-ui);">לא נמצאו קטעים התואמים את הסינונים שנבחרו. נסה לאפס את הסינון.</div>`;
    if (reasoningDisplay) reasoningDisplay.innerText = "אין נימוק זמין";
    if (scoresContainer) scoresContainer.innerHTML = "";
    if (halakhicContainer) halakhicContainer.innerHTML = "";
    return;
  }

  const p = filteredPassages[currentIndex];

  // Update counter & jump input
  if (counterText) {
    counterText.innerText = `קטע ${currentIndex + 1} מתוך ${filteredPassages.length} (סך הכל ${currentPassages.length})`;
  }
  if (jumpInput) {
    jumpInput.value = currentIndex + 1;
    jumpInput.max = filteredPassages.length;
  }

  // Corpus Badge
  if (corpusBadge) {
    corpusBadge.innerText = p.corpus === "Bavli" ? "תלמוד בבלי" : "תלמוד ירושלמי";
  }

  // Ref Title & Seder
  if (refTitle) {
    let loc = "";
    if (p.corpus === "Bavli") {
      loc = `דף ${p.daf || p.perek || ""}`;
    } else {
      loc = `פרק ${p.perek_number || p.perek || ""}, הלכה ${p.halacha_number || p.halacha || ""}`;
    }
    const sederHeb = SEDER_NAMES_HEBREW[String(p.seder).toLowerCase()] || "";
    refTitle.innerHTML = `
      <span>מסכת ${p.masechet || ""} • ${loc}</span>
      ${sederHeb ? `<span class="academic-pill" style="font-size:0.75rem; margin-right:0.5rem; font-weight:normal;">${sederHeb}</span>` : ""}
      ${p.matched ? `<span class="academic-pill gold" style="font-size:0.75rem; font-weight:normal;">התאמה לשם: ${p.matched}</span>` : ""}
    `;
  }

  // Sefaria Link
  if (sefariaLink) {
    if (p.sefaria_ref) {
      const cleanRef = p.sefaria_ref.replace("Steinsaltz on ", "");
      const sefariaUrl = `https://www.sefaria.org/${encodeURIComponent(cleanRef)}`;
      sefariaLink.href = sefariaUrl;
      sefariaLink.style.display = "inline-flex";
    } else {
      sefariaLink.style.display = "none";
    }
  }

  // Snippet with Hebrew prefix-aware name highlighting and authority keywords
  if (textDisplay) {
    const highlighted = highlightNameInText(p.snippet, p.matched);
    textDisplay.innerHTML = highlighted;
  }

  // Dual Scale Scores Badges (Raw 0-3 vs Thesis Normalized 0, 0.25, 0.5, 1.0)
  if (scoresContainer) {
    scoresContainer.innerHTML = `
      <span class="score-badge intellectual" title="סולם גולמי: ${p.Intellectual}/3 • סולם התזה המנורמל: ${p.Intellectual_norm}">
        📘 אינטלקטואלי: <strong>${p.Intellectual_norm}</strong> <small style="opacity:0.75;">(גולמי: ${p.Intellectual}/3)</small>
      </span>
      <span class="score-badge institutional" title="סולם גולמי: ${p.Institutional}/3 • סולם התזה המנורמל: ${p.Institutional_norm}">
        🏛️ מוסדי: <strong>${p.Institutional_norm}</strong> <small style="opacity:0.75;">(גולמי: ${p.Institutional}/3)</small>
      </span>
      <span class="score-badge external" title="פוליטי: ${p.Political}/3, אריסטוקרטי: ${p.Aristocratic}/3 • סולם התזה המנורמל: ${p.External_norm}">
        👑 חיצוני ושררה: <strong>${p.External_norm}</strong> <small style="opacity:0.75;">(פוליטי: ${p.Political}, אריסטוקרטי: ${p.Aristocratic})</small>
      </span>
    `;
  }

  // Halakhic Activity Badge
  if (halakhicContainer) {
    const isAct = p.Halakhic_Activity === 1;
    halakhicContainer.innerHTML = `
      <span class="academic-pill" style="color: ${isAct ? "var(--c-institutional)" : "var(--slate-500)"}; border-color: ${isAct ? "var(--c-institutional)" : "var(--slate-300)"}; background: ${isAct ? "var(--c-institutional-bg)" : "var(--slate-100)"}; font-weight:700;">
        ${isAct ? "⚖️ פסיקה אקטיבית (1)" : "👤 נוכחות ברקע / סביל (0)"}
      </span>
    `;
  }

  // Model Reasoning Box with Structured Academic Citation
  if (reasoningDisplay) {
    reasoningDisplay.innerHTML = p.Reasoning 
      ? `<em>&ldquo;${escapeHtml(p.Reasoning)}&rdquo;</em>`
      : "לא צוין נימוק ברשומת המקור.";
  }

  if (window.lucide) window.lucide.createIcons();
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function showPassageInViewer(filename, passageId) {
  // 1. Switch to Tab 2
  const tabBtn = document.querySelector('.tab-btn[data-tab="tab-viewer"]');
  if (tabBtn) tabBtn.click();

  // 2. Set dataset key
  currentDatasetKey = filename;

  // 3. Ensure supplementary toggle is on if this is a supplementary figure
  const toggleSupp = document.getElementById("toggle-supplementary-desiim");
  const isSupp = SUMMARY_DATA.supplementary_nesiim && SUMMARY_DATA.supplementary_nesiim.some((s) => s.filename === filename);
  if (isSupp && toggleSupp && !toggleSupp.checked) {
    toggleSupp.checked = true;
    setupPatriarchChips();
  }

  // 4. Update chip buttons styling
  document.querySelectorAll(".chip-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-filename") === filename);
  });

  // 5. Reset filters to avoid hiding the passage
  const corpusSelect = document.getElementById("viewer-corpus-select");
  const sederSelect = document.getElementById("viewer-seder-select");
  const axisSelect = document.getElementById("viewer-axis-select");
  const searchInput = document.getElementById("viewer-search-input");
  if (corpusSelect) corpusSelect.value = "all";
  if (sederSelect) sederSelect.value = "all";
  if (axisSelect) axisSelect.value = "all";
  if (searchInput) searchInput.value = "";

  currentPassages = PASSAGES_DATA[filename] || [];
  filteredPassages = [...currentPassages];

  if (passageId != null) {
    const idx = filteredPassages.findIndex((p) => p.id === passageId);
    currentIndex = idx >= 0 ? idx : 0;
  } else {
    currentIndex = 0;
  }

  renderCurrentPassage();

  // 6. Smooth scroll to viewer card
  const viewerCard = document.getElementById("passage-text-display");
  if (viewerCard) {
    viewerCard.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}


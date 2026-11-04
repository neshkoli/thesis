// Tab 3: Quantitative Findings, Tables & Dynamic Charts
// Implements Phase 5 of the Patriarchate Taxonomy Research Website

import { SUMMARY_DATA } from "../data/summary_data.js";
import { PASSAGES_DATA } from "../data/default_data.js";
import { renderThesisChart, renderComparatorChart } from "./charts.js";
import { showPassageInViewer } from "./tab-viewer.js";

let currentChartMode = "chart-intellectual";

// Table sorting states
let table84Sort = { col: "order", dir: "asc" };
let table82Sort = { col: "order", dir: "asc" };

export function initTabFindings() {
  renderProofCards();
  setupTables();
  setupChartSwitcher();
  setupComparator();
  renderActiveChart();
}

function renderProofCards() {
  const container = document.getElementById("proof-cards-container");
  if (!container || !SUMMARY_DATA.proof_cards) return;

  container.innerHTML = "";
  SUMMARY_DATA.proof_cards.forEach((c) => {
    const card = document.createElement("div");
    card.className = "proof-card";
    card.style.setProperty("--card-border-color", c.color);

    card.innerHTML = `
      <div>
        <div class="proof-card-top">
          <span class="academic-pill" style="color: ${c.color}; border-color: ${c.color}40; background: ${c.color}15;">
            ${c.badge}
          </span>
        </div>
        <div class="proof-stat" style="color: ${c.color};">${c.stat}</div>
        <div class="proof-subtitle">${c.subtitle}</div>
      </div>
      <div class="proof-desc">${c.description}</div>
    `;
    container.appendChild(card);
  });
}

function setupTables() {
  const toggleSupp = document.getElementById("toggle-tables-supp");
  if (toggleSupp) {
    toggleSupp.addEventListener("change", () => {
      renderTable84();
      renderTable82();
    });
  }

  // Setup click listeners for Table 8.4 sortable headers
  const ths84 = document.querySelectorAll("#table-8-4-display th.sortable-th");
  ths84.forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.getAttribute("data-col");
      if (table84Sort.col === col) {
        table84Sort.dir = table84Sort.dir === "asc" ? "desc" : "asc";
      } else {
        table84Sort.col = col;
        table84Sort.dir = col === "order" || col === "display_name" ? "asc" : "desc";
      }
      renderTable84();
    });
  });

  // Setup click listeners for Table 8.2 sortable headers
  const ths82 = document.querySelectorAll("#table-8-2-display th.sortable-th");
  ths82.forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.getAttribute("data-col");
      if (table82Sort.col === col) {
        table82Sort.dir = table82Sort.dir === "asc" ? "desc" : "asc";
      } else {
        table82Sort.col = col;
        table82Sort.dir = col === "order" || col === "display_name" ? "asc" : "desc";
      }
      renderTable82();
    });
  });

  // Setup CSV exports
  const btnExport84 = document.getElementById("btn-export-table-8-4");
  if (btnExport84) {
    btnExport84.addEventListener("click", () => {
      const rows = getTable84Data();
      exportToCsv("table_8_4_findings.csv", [
        ["דור", "דמות הנשיא", "סמכות אינטלקטואלית (%)", "סמכות מוסדית (%)", "הנהגה חיצונית (%)", "סך קטעים"],
        ...rows.map((r) => [
          r.generation,
          r.display_name,
          r.intellectual_pct,
          r.institutional_pct,
          r.external_pct,
          r.total_quotes
        ])
      ]);
    });
  }

  const btnExport82 = document.getElementById("btn-export-table-8-2");
  if (btnExport82) {
    btnExport82.addEventListener("click", () => {
      const rows = getTable82Data();
      exportToCsv("table_8_2_corpus_breakdown.csv", [
        ["דמות הנשיא", "בבלי", "ירושלמי", "סה״כ", "אחוז בבלי", "אחוז ירושלמי", "יחס בבלי לירושלמי"],
        ...rows.map((r) => [
          r.display_name,
          r.bavli,
          r.yerushalmi,
          r.total,
          `${r.bavli_pct}%`,
          `${r.yerushalmi_pct}%`,
          `${(r.bavli / (r.yerushalmi || 1)).toFixed(2)} : 1`
        ])
      ]);
    });
  }

  renderTable84();
  renderTable82();
}

function getTable84Data() {
  const toggleSupp = document.getElementById("toggle-tables-supp");
  const showSupp = toggleSupp ? toggleSupp.checked : false;

  let list = [...SUMMARY_DATA.thesis_table_8_4];
  if (showSupp && SUMMARY_DATA.hillel_table_entry) {
    list.unshift(SUMMARY_DATA.hillel_table_entry);
  }

  list.sort((a, b) => {
    let va = a[table84Sort.col];
    let vb = b[table84Sort.col];

    if (typeof va === "string") {
      const cmp = va.localeCompare(vb, "he");
      return table84Sort.dir === "asc" ? cmp : -cmp;
    }

    if (va < vb) return table84Sort.dir === "asc" ? -1 : 1;
    if (va > vb) return table84Sort.dir === "asc" ? 1 : -1;
    return 0;
  });

  return list;
}

function renderTable84() {
  const tbody = document.querySelector("#table-8-4-display tbody");
  if (!tbody) return;

  // Update header arrows
  document.querySelectorAll("#table-8-4-display th.sortable-th").forEach((th) => {
    const col = th.getAttribute("data-col");
    const icon = th.querySelector(".sort-icon");
    if (col === table84Sort.col) {
      th.classList.add(table84Sort.dir === "asc" ? "sorted-asc" : "sorted-desc");
      if (icon) icon.innerText = table84Sort.dir === "asc" ? " ▲" : " ▼";
    } else {
      th.classList.remove("sorted-asc", "sorted-desc");
      if (icon) icon.innerText = "";
    }
  });

  const list = getTable84Data();
  tbody.innerHTML = "";

  list.forEach((row) => {
    const tr = document.createElement("tr");

    // Heatmap cell backgrounds
    const bgIntel = `background-color: rgba(37, 99, 235, ${Math.min(0.28, Math.max(0.06, (row.intellectual_pct / 100) * 0.3))}); font-weight: 700; color: #1e3a8a;`;
    const bgInst = `background-color: rgba(5, 150, 105, ${Math.min(0.28, Math.max(0.06, (row.institutional_pct / 100) * 0.6))}); font-weight: 700; color: #065f46;`;
    const bgExt = `background-color: rgba(139, 92, 246, ${Math.min(0.35, Math.max(0.08, (row.external_pct / 100) * 0.95))}); font-weight: 700; color: #581c87;`;

    tr.innerHTML = `
      <td><strong>${row.generation}</strong></td>
      <td>
        <strong>${row.display_name}</strong>
        ${row.is_supplementary ? `<span class="academic-pill" style="font-size:0.65rem; margin-right:0.35rem;">הערת שוליים 4</span>` : ""}
      </td>
      <td style="${bgIntel}">${row.intellectual_pct.toFixed(1)}%</td>
      <td style="${bgInst}">${row.institutional_pct.toFixed(1)}%</td>
      <td style="${bgExt}">${row.external_pct.toFixed(1)}%</td>
      <td>${row.total_quotes}</td>
    `;
    tbody.appendChild(tr);
  });
}

function getTable82Data() {
  const toggleSupp = document.getElementById("toggle-tables-supp");
  const showSupp = toggleSupp ? toggleSupp.checked : false;

  let list = [...SUMMARY_DATA.thesis_table_8_2];
  if (!showSupp) {
    // Show only the 8 official thesis rows (exclude Hillel from default Table 8.2 view)
    list = list.filter((r) => r.nasi_name !== "הלל הזקן");
  }

  list.sort((a, b) => {
    let va = a[table82Sort.col];
    let vb = b[table82Sort.col];

    if (table82Sort.col === "ratio") {
      va = a.bavli / (a.yerushalmi || 1);
      vb = b.bavli / (b.yerushalmi || 1);
    }

    if (typeof va === "string") {
      const cmp = va.localeCompare(vb, "he");
      return table82Sort.dir === "asc" ? cmp : -cmp;
    }

    if (va < vb) return table82Sort.dir === "asc" ? -1 : 1;
    if (va > vb) return table82Sort.dir === "asc" ? 1 : -1;
    return 0;
  });

  return list;
}

function renderTable82() {
  const tbody = document.querySelector("#table-8-2-display tbody");
  if (!tbody) return;

  // Update header arrows
  document.querySelectorAll("#table-8-2-display th.sortable-th").forEach((th) => {
    const col = th.getAttribute("data-col");
    const icon = th.querySelector(".sort-icon");
    if (col === table82Sort.col) {
      th.classList.add(table82Sort.dir === "asc" ? "sorted-asc" : "sorted-desc");
      if (icon) icon.innerText = table82Sort.dir === "asc" ? " ▲" : " ▼";
    } else {
      th.classList.remove("sorted-asc", "sorted-desc");
      if (icon) icon.innerText = "";
    }
  });

  const list = getTable82Data();
  tbody.innerHTML = "";

  list.forEach((row) => {
    const tr = document.createElement("tr");
    const ratio = (row.bavli / (row.yerushalmi || 1)).toFixed(2);
    tr.innerHTML = `
      <td>
        <strong>${row.display_name}</strong>
        ${!row.is_included ? `<span class="academic-pill" style="font-size:0.65rem; margin-right:0.35rem;">${row.exclusion_reason}</span>` : ""}
      </td>
      <td>${row.bavli} (${row.bavli_pct}%)</td>
      <td>${row.yerushalmi} (${row.yerushalmi_pct}%)</td>
      <td><strong>${row.total}</strong></td>
      <td><strong>${ratio} : 1</strong></td>
    `;
    tbody.appendChild(tr);
  });
}

function setupChartSwitcher() {
  const buttons = document.querySelectorAll("#chart-mode-buttons button");
  const titleEl = document.getElementById("current-chart-title");
  const descEl = document.getElementById("current-chart-desc");

  const meta = {
    "chart-intellectual": {
      title: "גרף 1: התפלגות הסמכות האינטלקטואלית-תורנית לאורך שושלת הנשיאות",
      desc: "מעקב לאורך שבעת הנשיאים על ציר הסמכות התורנית: שיא בימי רבי (91.7%) וצניחה חדה בתקופת האמוראים (42.8%)."
    },
    "chart-institutional": {
      title: "גרף 2: התפלגות הסמכות המוסדית-חקיקתית לאורך שושלת הנשיאות",
      desc: "מעקב לאורך שבעת הנשיאים על ציר התקנות והסנהדרין: שליטה בבית שני (43.9% אצל רבן גמליאל הזקן) וירידה הדרגתית."
    },
    "chart-external": {
      title: "גרף 3: התפלגות ההנהגה חיצונית-מעמדית ושררה לאורך שושלת הנשיאות",
      desc: "הוכחת התיזה המרכזית: נוכחות מזערית בתקופת המשנה (2.4%–2.9%) אל מול זינוק דרמטי פי 14.4 אצל רבי יהודה נשיאה (34.6%)."
    },
    "chart-periods": {
      title: "גרף 4: שינוי סממני השררה בין שתי התקופות ההיסטוריות",
      desc: "השוואה מאקרו-היסטורית: תקופה א' (התבססות ועיצוב: 92.0% פנימי) מול תקופה ב' (ממלכתיות והפרדת רשויות: 29.6% חיצוני)."
    },
    "chart-stacked": {
      title: "תצוגה משולבת: התפלגות שלושת צירי הסמכות (100% Stacked Bar)",
      desc: "מבט פנורמי על שלושת כובעי המנהיגות על ציר הזמן מבית שני ועד שלהי תקופת האמוראים."
    },
    "chart-reversal": {
      title: "גרף 5: היפוך תפקידים (תורה מול שררה - Scissors Effect)",
      desc: "הצטלבות צירי ההנהגה: קריסת ההובלה התורנית־מדרשית מול זינוק תפקידי השררה והייצוג השלטוני."
    }
  };

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-secondary");
      });
      btn.classList.remove("btn-secondary");
      btn.classList.add("btn-primary");

      currentChartMode = btn.getAttribute("data-chart");
      if (titleEl && meta[currentChartMode]) titleEl.innerText = meta[currentChartMode].title;
      if (descEl && meta[currentChartMode]) descEl.innerText = meta[currentChartMode].desc;

      renderActiveChart();
    });
  });
}

function renderActiveChart() {
  renderThesisChart(
    "thesisMainChart",
    currentChartMode,
    SUMMARY_DATA.thesis_table_8_4,
    SUMMARY_DATA.thesis_periods_macro
  );
}

function getFilenameForNasi(nasiName) {
  const c = SUMMARY_DATA.canonical_nesiim.find((x) => x.nasi_name === nasiName);
  if (c) return c.filename;
  const s = SUMMARY_DATA.supplementary_nesiim.find((x) => x.nasi_name === nasiName);
  if (s) return s.filename;
  return "";
}

function getRepresentativePassage(filename, biasPref) {
  const passages = PASSAGES_DATA[filename] || [];
  if (passages.length === 0) return null;

  if (biasPref === "ext") {
    const cand = passages.find((p) => (p.External >= 2 || p.External_norm >= 0.5) && p.Reasoning && p.snippet.length > 40);
    if (cand) return cand;
  }
  if (biasPref === "inst") {
    const cand = passages.find((p) => (p.Institutional >= 2 || p.Institutional_norm >= 0.5) && p.Reasoning && p.snippet.length > 40);
    if (cand) return cand;
  }
  const cand = passages.find((p) => (p.Intellectual >= 2 || p.Intellectual_norm >= 0.5) && p.Reasoning && p.snippet.length > 40);
  return cand || passages[0];
}

function setupComparator() {
  const selA = document.getElementById("comparator-select-a");
  const selB = document.getElementById("comparator-select-b");
  const resultsContainer = document.getElementById("comparator-results-container");
  const passagesContainer = document.getElementById("comparator-passages-container");
  if (!selA || !selB || !resultsContainer) return;

  const nesiim = SUMMARY_DATA.thesis_table_8_4;
  selA.innerHTML = "";
  selB.innerHTML = "";

  nesiim.forEach((n, idx) => {
    selA.innerHTML += `<option value="${n.nasi_name}" ${idx === 4 ? "selected" : ""}>${n.display_name} (${n.generation})</option>`;
    selB.innerHTML += `<option value="${n.nasi_name}" ${idx === 6 ? "selected" : ""}>${n.display_name} (${n.generation})</option>`;
  });

  function updateComparison() {
    const nA = nesiim.find((x) => x.nasi_name === selA.value) || nesiim[4];
    const nB = nesiim.find((x) => x.nasi_name === selB.value) || nesiim[6];

    const deltaIntel = (nB.intellectual_pct - nA.intellectual_pct).toFixed(1);
    const deltaInst = (nB.institutional_pct - nA.institutional_pct).toFixed(1);
    const deltaExt = (nB.external_pct - nA.external_pct).toFixed(1);

    resultsContainer.innerHTML = `
      <div class="grid-3" style="margin-top: 1rem;">
        <div class="anchor-box" style="border-top: 3px solid var(--c-intellectual);">
          <div style="font-size: 0.8rem; color: var(--slate-500);">סמכות אינטלקטואלית־תורנית</div>
          <div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 0.35rem;">
            <span><strong>${nA.display_name}:</strong> ${nA.intellectual_pct}%</span>
            <span><strong>${nB.display_name}:</strong> ${nB.intellectual_pct}%</span>
          </div>
          <div style="font-size: 0.8rem; font-weight: 700; margin-top: 0.35rem; color: ${deltaIntel >= 0 ? "var(--c-institutional)" : "var(--c-danger)"};">
            פער: ${deltaIntel >= 0 ? "+" : ""}${deltaIntel}%
          </div>
        </div>

        <div class="anchor-box" style="border-top: 3px solid var(--c-institutional);">
          <div style="font-size: 0.8rem; color: var(--slate-500);">סמכות מוסדית־חקיקתית</div>
          <div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 0.35rem;">
            <span><strong>${nA.display_name}:</strong> ${nA.institutional_pct}%</span>
            <span><strong>${nB.display_name}:</strong> ${nB.institutional_pct}%</span>
          </div>
          <div style="font-size: 0.8rem; font-weight: 700; margin-top: 0.35rem; color: ${deltaInst >= 0 ? "var(--c-institutional)" : "var(--c-danger)"};">
            פער: ${deltaInst >= 0 ? "+" : ""}${deltaInst}%
          </div>
        </div>

        <div class="anchor-box" style="border-top: 3px solid var(--c-external);">
          <div style="font-size: 0.8rem; color: var(--slate-500);">הנהגה חיצונית ושררה</div>
          <div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 0.35rem;">
            <span><strong>${nA.display_name}:</strong> ${nA.external_pct}%</span>
            <span><strong>${nB.display_name}:</strong> ${nB.external_pct}%</span>
          </div>
          <div style="font-size: 0.8rem; font-weight: 700; margin-top: 0.35rem; color: ${deltaExt >= 0 ? "var(--c-external)" : "var(--slate-500)"};">
            פער: ${deltaExt >= 0 ? "+" : ""}${deltaExt}% (שינוי דפוס מהותי)
          </div>
        </div>
      </div>
    `;

    // Render multi-dimensional mini comparison chart
    renderComparatorChart("comparatorMiniChart", nA, nB);

    // Render representative textual proof cards
    if (passagesContainer) {
      const fileA = getFilenameForNasi(nA.nasi_name);
      const fileB = getFilenameForNasi(nB.nasi_name);
      const prefA = nA.external_pct > 20 ? "ext" : (nA.institutional_pct > 30 ? "inst" : "intel");
      const prefB = nB.external_pct > 20 ? "ext" : (nB.institutional_pct > 30 ? "inst" : "intel");

      const pA = getRepresentativePassage(fileA, prefA);
      const pB = getRepresentativePassage(fileB, prefB);

      passagesContainer.innerHTML = `
        ${renderEvidenceCard(nA.display_name, fileA, pA)}
        ${renderEvidenceCard(nB.display_name, fileB, pB)}
      `;

      // Attach click listeners to open in Tab 2 Viewer
      passagesContainer.querySelectorAll(".btn-open-in-viewer").forEach((btn) => {
        btn.addEventListener("click", () => {
          const fn = btn.getAttribute("data-filename");
          const pid = parseInt(btn.getAttribute("data-id"), 10);
          showPassageInViewer(fn, pid);
        });
      });
    }

    if (window.lucide) window.lucide.createIcons();
  }

  selA.addEventListener("change", updateComparison);
  selB.addEventListener("change", updateComparison);
  updateComparison();
}

function renderEvidenceCard(patriarchName, filename, passage) {
  if (!passage) {
    return `<div class="comparator-proof-card"><p>לא נמצא קטע מייצג.</p></div>`;
  }

  const snippetShort = passage.snippet.length > 170
    ? passage.snippet.slice(0, 170) + "..."
    : passage.snippet;

  let loc = passage.corpus === "Bavli"
    ? `דף ${passage.daf || ""}`
    : `פרק ${passage.perek_number || ""}, הלכה ${passage.halacha_number || ""}`;

  return `
    <div class="comparator-proof-card">
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
          <span style="font-weight: 700; color: var(--slate-800); font-size: 0.9rem;">
            קטע מייצג: ${patriarchName}
          </span>
          <span class="academic-pill" style="font-size: 0.75rem;">
            ${passage.corpus === "Bavli" ? "בבלי" : "ירושלמי"} • מסכת ${passage.masechet} ${loc}
          </span>
        </div>

        <div class="proof-quote">
          &ldquo;${snippetShort}&rdquo;
        </div>

        <div style="display: flex; gap: 0.35rem; flex-wrap: wrap; margin-bottom: 0.75rem;">
          <span class="score-badge intellectual" style="font-size: 0.75rem;">אינטלקטואלי: ${passage.Intellectual_norm}</span>
          <span class="score-badge institutional" style="font-size: 0.75rem;">מוסדי: ${passage.Institutional_norm}</span>
          <span class="score-badge external" style="font-size: 0.75rem;">חיצוני: ${passage.External_norm}</span>
        </div>
      </div>

      <button class="btn btn-secondary btn-sm btn-open-in-viewer" data-filename="${filename}" data-id="${passage.id}" style="width: 100%; justify-content: center; gap: 0.35rem;">
        <i data-lucide="external-link" style="width: 14px; height: 14px;"></i>
        <span>עיין בקטע זה בלשונית המקורות</span>
      </button>
    </div>
  `;
}

function exportToCsv(filename, rows) {
  const csvContent = "\uFEFF" + rows.map((e) => e.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

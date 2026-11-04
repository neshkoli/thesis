// Tab 1: Methodology, Theoretical Background & Prompts Explorer
// Implements Phase 3 of the Patriarchate Taxonomy Research Website

import { PROMPTS_DATA } from "../data/prompts_data.js";

// Detailed annotated methodological breakdowns for each prompt
const PROMPT_ANNOTATIONS = {
  "prompt-taxonomy": {
    objective: "סיווג טקסונומי של תחומי הפעלת הכוח של הנשיא ורמת האקטיביות ההלכתית",
    scale_explanation: `
      <strong>סולם הניקוד המדורג (0–3 בפרומפט שהומר ל-0, 0.25, 0.5, 1.0 בתזה):</strong>
      <ul style="padding-right: 1.25rem; margin-top: 0.35rem; font-size: 0.85rem;">
        <li><code>0</code> (לא קיים כלל בתזה): אין בטקסט כל עדות או רמז לסמכות זו.</li>
        <li><code>1</code> (0.25 בתזה): רמז עקיף, משני או שולי בלבד.</li>
        <li><code>2</code> (0.5 בתזה): נוכחות בינונית וברורה בהקשר האירוע.</li>
        <li><code>3</code> (1.0 בתזה): זהו מוקד הקטע ועיקר הפעולה המתוארת של הנשיא.</li>
      </ul>
    `,
    rules: [
      {
        title: "📘 סמכות אינטלקטואלית־תורנית (Intellectual)",
        desc: "הנשיא כחכם המוסר מסורת קדומה, דורש דרשה בציבור, מנהל משא ומתן תלמודי או פוסק הלכה מכוח למדנותו וסברתו העצמית."
      },
      {
        title: "🏛️ סמכות מוסדית־חקיקתית (Institutional)",
        desc: "הנשיא כראש בית הדין והסנהדרין: התקנת תקנות ציבוריות לתיקון החברה ('מפני תיקון העולם'), מינוי דיינים, קידוש החודש ועיבור השנה."
      },
      {
        title: "👑 איחוד סמכות פוליטית ואריסטוקרטית למדד 'הנהגה חיצונית ושררה'",
        desc: "בקורפוס הגולמי, מופעים בודדים של מגעים עם רומא בלבד או גינוני שררה בלבד היו דלילים יחסית. איחוד שני המדדים לציר מאוחד יצר מדד סטטיסטי יציב ומהימן של עוצמת המעמד החיצוני של הנשיא."
      },
      {
        title: "⚖️ מדד אקטיביות הלכתית (0 או 1)",
        desc: "הבחנה בין נשיא הפוסק, מלמד או מורה הלכה בפועל (1) לבין נשיא המוזכר כדמות רקע היסטורית, נוכח פסיבי או שואל שאלה גרידא (0)."
      }
    ]
  },
  "prompt-gamliel": {
    objective: "זיהוי היסטורי ודאי (Disambiguation) בין ארבעת הנשיאים שנקראו 'רבן גמליאל'",
    scale_explanation: `
      <strong>עקרון העל: 'מעביר השמועה מול גיבור המעשה':</strong>
      הפרדה מוחלטת בין החכם המצטט את המעשה (למשל 'אמר רב יהודה אמר רב') לבין גיבורי המעשה (הנשיא ובני שיחו). הזיהוי נקבע לפי דור גיבור המעשה בלבד.
    `,
    rules: [
      {
        title: "1. רבן גמליאל הזקן (הראשון)",
        desc: "פעל בימי הבית השני (שלהי תקופת בית הורדוס). עוגנים: התואר 'הזקן', אזכור הר הבית, לשכת הגזית, ירושלים, איגרות לתפוצות ערב החורבן, וציטוטים מפי תלמידי בית שמאי והלל."
      },
      {
        title: "2. רבן גמליאל דיבנה (השני)",
        desc: "פעל לאחר החורבן (דור יבנה). עוגנים: רשת חכמי יבנה (ר' יהושע, ר' אליעזר, ר' עקיבא, ר' טרפון, ר' אלעזר בן עזריה), טבי עבדו, ספינות לרומא, הדחה מן הנשיאות וקידוש החודש ביבנה."
      },
      {
        title: "3. רבן גמליאל ברבי (השלישי)",
        desc: "בנו של רבי יהודה הנשיא (דור המעבר לאמוראים). עוגנים: התואר 'ברבי' / 'בר רבי', שיח עם אחיו ר' שמעון ברבי, אזכור רב ושמואל, וצוואת אביו רבי יהודה הנשיא."
      },
      {
        title: "4. רבן גמליאל המאוחר (שלהי תקופת האמוראים)",
        desc: "נשיאים מאוחרים בטבריה. עוגנים: אינטראקציה עם אמוראי ארץ ישראל המאוחרים (כגון רבי אבהו, רבי אמי, רבי יונה). נמצאו 7 קטעים בלבד שהוחרגו מהמדד הסטטיסטי עקב מיעוט מופעים."
      }
    ]
  },
  "prompt-rashbag": {
    objective: "הבחנה היסטורית בין רשב\"ג הראשון (ערב החורבן) לרשב\"ג השני (דור אושא)",
    scale_explanation: `
      <strong>כלל האצבע התלמודי:</strong>
      כמעט כל אזכור סתמי של 'רבן שמעון בן גמליאל אומר' במחלוקת הלכתית שגרתית בתלמוד מתייחס לרשב"ג השני (דור אושא). רשב"ג הראשון מופיע כמעט תמיד בסיפורים היסטוריים על המקדש והמרד.
    `,
    rules: [
      {
        title: "1. רבן שמעון בן גמליאל הראשון (הזקן)",
        desc: "נשיא ערב החורבן ומהנהגת המרד הגדול בירושלים. עוגנים: ירושלים, הר הבית, בית המקדש, הוזלת קורבנות יולדות ('מעשה שעמדו קינין בירושלים בדינרי זהב'), שמחת בית השואבה וישיבה עם רבן יוחנן בן זכאי."
      },
      {
        title: "2. רבן שמעון בן גמליאל השני (מאושא)",
        desc: "שיקם את הנשיאות באושא לאחר גזירות אדריאנוס ומרד בר כוכבא. עוגנים: חכמי דור אושא (ר' מאיר, ר' נתן, ר' יוסי, ר' יהודה), בנו רבי יהודה הנשיא המכנהו 'אבא', ומאות מחלוקות הלכתיות בדיני ממונות וגיטין."
      }
    ]
  }
};

export function initTabPrompts() {
  renderPipelineCard();
  renderPromptsList();
  renderValidationCard();
}

function renderPipelineCard() {
  const container = document.getElementById("pane-tab-methodology");
  if (!container) return;

  // Check if pipeline card already exists, if not insert before prompts
  let pipelineEl = document.getElementById("pipeline-details-card");
  if (pipelineEl) return; // already rendered

  pipelineEl = document.createElement("div");
  pipelineEl.id = "pipeline-details-card";
  pipelineEl.className = "card";
  pipelineEl.style.borderRight = "4px solid var(--c-institutional)";

  pipelineEl.innerHTML = `
    <div class="card-header">
      <h3>
        <i data-lucide="workflow" style="width: 18px; height: 18px; color: var(--c-institutional);"></i>
        צינור איסוף המקורות והכנת הנתונים (Text Extraction & Processing Pipeline)
      </h3>
      <span class="academic-pill">2,215 קטעים נקיים</span>
    </div>
    <div class="card-body">
      <div class="grid-4" style="margin-bottom: 1.25rem;">
        
        <div class="anchor-box" style="border-top: 3px solid #2563eb;">
          <div style="font-size: 0.75rem; font-weight: 700; color: #2563eb; margin-bottom: 0.25rem;">שלב 1: שאיבת הקורפוס</div>
          <h4 style="font-size: 0.9rem;">חיפוש שמות דיגיטלי</h4>
          <p style="font-size: 0.8rem; color: var(--slate-600);">חיפוש ממוחשב של כל שמות הנשיאים על כלל הווריאציות (כגון 'רבי יהודה נשיאה', 'ר' יודן נשייא') במאגרי הבבלי והירושלמי.</p>
        </div>

        <div class="anchor-box" style="border-top: 3px solid #059669;">
          <div style="font-size: 0.75rem; font-weight: 700; color: #059669; margin-bottom: 0.25rem;">שלב 2: שילוב ביאור עברי</div>
          <h4 style="font-size: 0.9rem;">שטיינזלץ ור' מאיר כהן</h4>
          <p style="font-size: 0.8rem; color: var(--slate-600);">סיווג על גבי טקסט מקור בארמית הניב דיוק נמוך. שילוב הביאור בסוגריים מרובעות העלה את דיוק ההבנה של מודל השפה לאין ערוך.</p>
        </div>

        <div class="anchor-box" style="border-top: 3px solid #d97706;">
          <div style="font-size: 0.75rem; font-weight: 700; color: #d97706; margin-bottom: 0.25rem;">שלב 3: חלון 90 מילים ואיחוד</div>
          <h4 style="font-size: 0.9rem;">דה-דופליקציה מובנית</h4>
          <p style="font-size: 0.8rem; color: var(--slate-600);">חילוץ מקטע של כ-90 מילים (15 לפני השם ו-75 לאחריו). מופעים חוזרים של אותה אישיות באותו מקטע אוחדו לרשומה בודדת.</p>
        </div>

        <div class="anchor-box" style="border-top: 3px solid #8b5cf6;">
          <div style="font-size: 0.75rem; font-weight: 700; color: #8b5cf6; margin-bottom: 0.25rem;">שלב 4: בקרת איכות ותיקוף</div>
          <h4 style="font-size: 0.9rem;">מדגם ידני של 10%</h4>
          <p style="font-size: 0.8rem; color: var(--slate-600);">בדיקת תוקף ידנית על מדגם אקראי של 220+ קטעים להבטחת מהימנות ועקביות הסיווג לפני הרצת האגרגציה המלאה.</p>
        </div>

      </div>

      <div style="background: var(--slate-50); padding: 0.85rem 1rem; border-radius: var(--radius-md); border: 1px solid var(--slate-200); font-size: 0.85rem; color: var(--slate-700);">
        <strong>שקיפות הנתונים:</strong> כלל המקורות המנותחים, הנימוקים שנפלטו מהמודל, וציוני הסמכות פתוחים לעיון פרטני בלשונית <em>'2. עיון במקורות וברשומות ההוכחה'</em>.
      </div>
    </div>
  `;

  // Find the prompts list container card and insert pipeline card right before it
  const promptsCard = document.querySelector("#prompts-list-container")?.closest(".card");
  if (promptsCard && promptsCard.parentNode) {
    promptsCard.parentNode.insertBefore(pipelineEl, promptsCard);
  }
}

function renderPromptsList() {
  const container = document.getElementById("prompts-list-container");
  if (!container || !PROMPTS_DATA || !PROMPTS_DATA.prompts) return;

  container.innerHTML = "";

  PROMPTS_DATA.prompts.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "prompt-card";
    card.style.marginBottom = "1.5rem";

    const annotations = PROMPT_ANNOTATIONS[p.id] || null;

    let rulesHtml = "";
    if (annotations && annotations.rules) {
      rulesHtml = annotations.rules
        .map(
          (r) => `
          <div style="background: var(--white); border: 1px solid var(--slate-200); border-radius: var(--radius-sm); padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
            <div style="font-size: 0.875rem; font-weight: 700; color: var(--slate-800); margin-bottom: 0.2rem;">${r.title}</div>
            <div style="font-size: 0.825rem; color: var(--slate-600); line-height: 1.45;">${r.desc}</div>
          </div>
        `
        )
        .join("");
    }

    card.innerHTML = `
      <div class="prompt-card-header" style="background: var(--slate-50); border-bottom: 1px solid var(--slate-200);">
        <div style="display: flex; align-items: center; gap: 0.65rem;">
          <span class="academic-pill gold">${p.badge}</span>
          <strong style="font-size: 1rem; color: var(--slate-900);">${p.title}</strong>
        </div>
        
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <div class="prompt-tab-switch" style="display: flex; background: var(--slate-200); border-radius: var(--radius-sm); padding: 2px;">
            <button class="btn btn-sm btn-prompt-view active" data-view="annotations" data-id="${p.id}" style="padding: 0.2rem 0.6rem; font-size: 0.75rem; background: var(--white); border-radius: 4px; border: none; font-weight: 700; cursor: pointer;">
              ניתוח והנחיות
            </button>
            <button class="btn btn-sm btn-prompt-view" data-view="raw" data-id="${p.id}" style="padding: 0.2rem 0.6rem; font-size: 0.75rem; background: none; border-radius: 4px; border: none; font-weight: 600; cursor: pointer; color: var(--slate-600);">
              נוסח מלא (Markdown)
            </button>
          </div>

          <button class="btn btn-secondary btn-sm btn-copy-prompt" data-prompt-id="${p.id}">
            <i data-lucide="copy" style="width: 13px; height: 13px;"></i>
            <span>העתק נוסח</span>
          </button>
        </div>
      </div>

      <div style="padding: 0.85rem 1.25rem; background: #fafafa; border-bottom: 1px solid var(--slate-200); font-size: 0.875rem; color: var(--slate-700);">
        <strong>מטרת הפרומפט:</strong> ${p.description}
      </div>

      <!-- View 1: Annotated Breakdown View (Default) -->
      <div class="prompt-view-pane prompt-view-annotations" id="view-annotations-${p.id}" style="padding: 1.25rem; background: var(--slate-50);">
        ${annotations ? `
          <div style="margin-bottom: 1rem; font-size: 0.875rem; color: var(--slate-700); background: var(--white); padding: 0.85rem; border-radius: var(--radius-sm); border: 1px solid var(--slate-200);">
            ${annotations.scale_explanation}
          </div>
          <div style="margin-bottom: 0.5rem; font-size: 0.85rem; font-weight: 700; color: var(--slate-800);">קריטריונים וכללי הכרעה מובנים:</div>
          ${rulesHtml}
        ` : ""}
      </div>

      <!-- View 2: Raw Markdown Code View -->
      <div class="prompt-view-pane prompt-view-raw" id="view-raw-${p.id}" style="display: none;">
        <pre class="prompt-code-container" style="max-height: 380px;"><code>${escapeHtml(p.content)}</code></pre>
      </div>
    `;

    container.appendChild(card);
  });

  // Attach view toggle listeners
  container.querySelectorAll(".btn-prompt-view").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pid = btn.getAttribute("data-id");
      const targetView = btn.getAttribute("data-view");
      const card = btn.closest(".prompt-card");

      card.querySelectorAll(".btn-prompt-view").forEach((b) => {
        b.classList.remove("active");
        b.style.background = "none";
        b.style.color = "var(--slate-600)";
        b.style.fontWeight = "600";
      });
      btn.classList.add("active");
      btn.style.background = "var(--white)";
      btn.style.color = "var(--slate-900)";
      btn.style.fontWeight = "700";

      const paneAnnotations = card.querySelector(`#view-annotations-${pid}`);
      const paneRaw = card.querySelector(`#view-raw-${pid}`);

      if (targetView === "annotations") {
        if (paneAnnotations) paneAnnotations.style.display = "block";
        if (paneRaw) paneRaw.style.display = "none";
      } else {
        if (paneAnnotations) paneAnnotations.style.display = "none";
        if (paneRaw) paneRaw.style.display = "block";
      }
    });
  });

  // Attach copy listeners
  container.querySelectorAll(".btn-copy-prompt").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pid = btn.getAttribute("data-prompt-id");
      const found = PROMPTS_DATA.prompts.find((x) => x.id === pid);
      if (found && found.content) {
        navigator.clipboard.writeText(found.content).then(() => {
          const originalText = btn.innerHTML;
          btn.innerHTML = `<i data-lucide="check" style="width: 13px; height: 13px; color: var(--c-institutional);"></i> <span>הועתק בהצלחה!</span>`;
          if (window.lucide) window.lucide.createIcons();
          setTimeout(() => {
            btn.innerHTML = originalText;
            if (window.lucide) window.lucide.createIcons();
          }, 2000);
        });
      }
    });
  });

  if (window.lucide) window.lucide.createIcons();
}

function renderValidationCard() {
  const container = document.getElementById("pane-tab-methodology");
  if (!container) return;

  if (document.getElementById("reproducibility-validation-card")) return;

  const card = document.createElement("div");
  card.id = "reproducibility-validation-card";
  card.className = "card";
  card.style.borderRight = "4px solid var(--c-intellectual)";

  card.innerHTML = `
    <div class="card-header">
      <h3>
        <i data-lucide="check-circle-2" style="width: 18px; height: 18px; color: var(--c-intellectual);"></i>
        בקרת איכות ותיקוף מדעי (Scientific Validation & Reproducibility)
      </h3>
      <span class="academic-pill">מהימנות 95%+</span>
    </div>
    <div class="card-body methodology-narrative">
      <div class="grid-3" style="margin-bottom: 1rem;">
        
        <div class="anchor-box">
          <h4><i data-lucide="clipboard-check" style="width: 15px; height: 15px; color: var(--c-institutional);"></i> מדגם ידני אקראי (10%)</h4>
          <p>כ-220 קטעים נדגמו באקראי ונבדקו ע״י חוקר אנושי לבחינת תאימות הסיווג לטקסט המקורי. הפערים נותחו וההנחיות לפרומפט שויפו בהתאם.</p>
        </div>

        <div class="anchor-box">
          <h4><i data-lucide="sliders" style="width: 15px; height: 15px; color: var(--c-intellectual);"></i> הגדרות דטרמיניסטיות</h4>
          <p>הפקת התוצאות במודל נעשתה תחת סכמת JSON קשיחה (Structured Outputs) וטמפרטורה נמוכה למזעור הזיות (Hallucinations) והבטחת שחזוריות.</p>
        </div>

        <div class="anchor-box">
          <h4><i data-lucide="git-merge" style="width: 15px; height: 15px; color: var(--c-external);"></i> שילוב איכותני-כמותי</h4>
          <p>הכלי הכמותי אינו תחליף לעין החוקר, אלא משמש כ'עוזר מחקר דיגיטלי' המאפשר מיפוי שיטתי, אחיד ונטול הטיות של קורפוס עתיר היקף.</p>
        </div>

      </div>

      <p style="font-size: 0.85rem; color: var(--slate-600); margin-bottom: 0;">
        לעיון בכלל הרשומות, הניקוד המפורט ומשפטי הנימוק של כל קטע תלמודי, עבור ללשונית 
        <a href="#viewer" style="color: var(--c-intellectual); font-weight: 700; text-decoration: underline;">2. עיון במקורות וברשומות ההוכחה</a>.
      </p>
    </div>
  `;

  container.appendChild(card);
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ניתוח תזת המעבר בהנהגת הנשיאות:
מהנהגה פנימית (רוחנית-מוסדית) להנהגה חיצונית (אריסטוקרטית-פוליטית)

סקריפט זה מבצע:
1. חישוב שיטת "הכובע הדומיננטי" (Dominant Hat) עבור 4 צירי הסמכות
   (Intellectual, Institutional, Political, Aristocratic), כולל חלוקת נקודות שווה בתיקו.
2. חישוב מגמות היפוך תפקידים לאורך ציר הזמן (שמות הנשיאים):
   ממוצע אקטיביות הלכתית (Halakhic Activity) אל מול ממוצע סמכות אריסטוקרטית (Aristocratic).
3. בחינת התיזה המרכזית: השוואת הנהגה פנימית (רוחנית-מוסדית) מול הנהגה חיצונית (אריסטוקרטית-פוליטית).
4. יצירת 3 קובצי CSV מעוצבים התואמים לפתיחה מיידית באקסל (utf-8-sig).
5. הפקת 3 גרפים נפרדים באיכות אקדמית גבוהה (300 DPI) + דשבורד משולב.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from bidi.algorithm import get_display


# סדר כרונולוגי קפדני של 8 הנשיאים
NESIIM_ORDER = [
    {"order": 1, "nasi": "הלל", "display": "הלל הזקן", "generation": "סוף ימי הבית השני"},
    {"order": 2, "nasi": "רבן גמליאל הזקן", "display": "רבן גמליאל הזקן", "generation": "דור 1 לתנאים"},
    {"order": 3, "nasi": "רבן שמעון בן גמליאל הראשון", "display": "רשב\"ג הראשון", "generation": "ערב החורבן"},
    {"order": 4, "nasi": "רבן גמליאל דיבנה", "display": "רבן גמליאל דיבנה", "generation": "דור 2 לתנאים (יבנה)"},
    {"order": 5, "nasi": "רבן שמעון בן גמליאל השני", "display": "רשב\"ג השני", "generation": "דור 3 לתנאים (אושא)"},
    {"order": 6, "nasi": "רבי יהודה הנשיא", "display": "רבי יהודה הנשיא", "generation": "דור 4-5 לתנאים"},
    {"order": 7, "nasi": "רבן גמליאל ברבי", "display": "רבן גמליאל ברבי", "generation": "דור 1 לאמוראים"},
    {"order": 8, "nasi": "רבי יהודה נשיאה", "display": "רבי יהודה נשיאה", "generation": "דור 2 לאמוראים (טבריה)"}
]

AUTHORITY_AXES = ["Intellectual", "Institutional", "Political", "Aristocratic"]

COLORS = {
    "Intellectual": "#1F4E79",    # כחול עמוק / אינטלקטואלי
    "Institutional": "#2E75B6",   # כחול מוסדי
    "Political": "#E37222",       # כתום פוליטי
    "Aristocratic": "#C00000",    # אדום/ארגמן אריסטוקרטי
    "Halakhic": "#0E6251",        # ירוק-טורקיז עמוק לאקטיביות הלכתית
    "Internal": "#1F4E79",        # הנהגה פנימית
    "External": "#C00000"         # הנהגה חיצונית
}


def fix_heb(text: str) -> str:
    """החזרת מחרוזת נקייה (ב-matplotlib 3.11+ עיצוב RTL/HarfBuzz מתבצע באופן טבעי ומדויק)."""
    return str(text)


def setup_plot_style():
    """הגדרת פונטים וסגנון אקדמי נקי."""
    plt.rcParams.update({
        'font.sans-serif': ['Arial', 'Helvetica', 'Arial Hebrew', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'figure.facecolor': 'white',
        'axes.facecolor': '#FAFAFA',
        'axes.edgecolor': '#D0D0D0',
        'axes.linewidth': 0.8,
        'grid.color': '#E5E5E5',
        'grid.linestyle': '--',
        'grid.linewidth': 0.6,
        'grid.alpha': 0.75
    })


def load_normalized_data(folder_path: str) -> pd.DataFrame:
    """טעינת כל קובצי ה-CSV המנורמלים של הנשיאים ואיחודם."""
    dfs = []
    for item in NESIIM_ORDER:
        expected_filename = f"{item['nasi']}_normalized.csv"
        file_path = os.path.join(folder_path, expected_filename)
        
        if not os.path.exists(file_path):
            candidates = glob.glob(os.path.join(folder_path, f"*{item['nasi']}*.csv"))
            candidates = [c for c in candidates if "all_nesiim" not in c and "summary" not in c]
            if candidates:
                file_path = candidates[0]
            else:
                print(f"אזהרה: לא נמצא קובץ עבור {item['nasi']}")
                continue

        df = pd.read_csv(file_path)
        # סינון שורות סיכום היסטוריות אם קיימות
        if "corpus" in df.columns:
            df = df[~df["corpus"].astype(str).str.upper().isin(["TOTAL", "RATIO", "SUMMARY", "AVERAGE"])].copy()

        # וידוא מטא-דאטה עקבי
        df["Chronological_Order"] = item["order"]
        df["Nasi"] = item["nasi"]
        df["Display_Name"] = item["display"]
        df["Generation"] = item["generation"]

        # המרת עמודות למספרים
        for ax in AUTHORITY_AXES:
            df[ax] = pd.to_numeric(df[ax], errors='coerce').fillna(0.0)

        if "Halakhic_Activity" in df.columns:
            df["Halakhic_Activity"] = pd.to_numeric(df["Halakhic_Activity"], errors='coerce')
        else:
            df["Halakhic_Activity"] = np.nan

        dfs.append(df)

    if not dfs:
        raise RuntimeError("לא נמצאו קובצי נתונים לטעינה!")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values("Chronological_Order").reset_index(drop=True)
    return combined


def calculate_dominant_hats(df: pd.DataFrame) -> pd.DataFrame:
    """
    חישוב שיטת הכובע הדומיננטי:
    עבור כל ציטוט, מציאת הציון המרבי מבין 4 עמודות הסמכות.
    רק העמודה המנצחת מקבלת 1.0 נקודה.
    במקרה של תיקו, הנקודה מחולקת שווה בשווה (למשל 0.5 לכל אחת משתיים, 0.33 לשלוש).
    אם כל הציונים הם 0 (ציטוט ללא סמכות מנהיגותית), כל העמודות מקבלות 0.
    """
    def allocate_dominant(row):
        scores = [row[ax] for ax in AUTHORITY_AXES]
        max_val = max(scores)
        if max_val == 0.0:
            return [0.0, 0.0, 0.0, 0.0]
        ties = [1.0 if s == max_val else 0.0 for s in scores]
        tie_count = sum(ties)
        return [t / tie_count for t in ties]

    allocated = df.apply(allocate_dominant, axis=1, result_type='expand')
    for i, ax in enumerate(AUTHORITY_AXES):
        df[f"{ax}_dominant"] = allocated[i]

    return df


def build_dominant_hat_summary(df: pd.DataFrame) -> pd.DataFrame:
    """יצירת טבלת סיכום של הכובע הדומיננטי לפי נשיא."""
    rows = []
    for item in NESIIM_ORDER:
        sub = df[df["Chronological_Order"] == item["order"]]
        total_quotes = len(sub)

        # סכומי נקודות הכובע הדומיננטי
        dom_counts = {ax: sub[f"{ax}_dominant"].sum() for ax in AUTHORITY_AXES}
        total_dom_points = sum(dom_counts.values())

        # חישוב אחוזים מתוך 100%
        dom_pcts = {}
        for ax in AUTHORITY_AXES:
            dom_pcts[ax] = (dom_counts[ax] / total_dom_points * 100.0) if total_dom_points > 0 else 0.0

        rows.append({
            "סדר כרונולוגי": item["order"],
            "נשיא": item["nasi"],
            "שם תצוגה": item["display"],
            "תקופה/דור": item["generation"],
            "סך ציטוטים בקורפוס": total_quotes,
            "ציטוטים בעלי סמכות דומיננטית": round(total_dom_points, 1),
            "אינטלקטואלי (ניקוד דומיננטי)": round(dom_counts["Intellectual"], 2),
            "מוסדי (ניקוד דומיננטי)": round(dom_counts["Institutional"], 2),
            "פוליטי (ניקוד דומיננטי)": round(dom_counts["Political"], 2),
            "אריסטוקרטי (ניקוד דומיננטי)": round(dom_counts["Aristocratic"], 2),
            "אינטלקטואלי (%)": round(dom_pcts["Intellectual"], 2),
            "מוסדי (%)": round(dom_pcts["Institutional"], 2),
            "פוליטי (%)": round(dom_pcts["Political"], 2),
            "אריסטוקרטי (%)": round(dom_pcts["Aristocratic"], 2)
        })

    return pd.DataFrame(rows)


def build_role_reversal_summary(df: pd.DataFrame, dom_summary: pd.DataFrame) -> pd.DataFrame:
    """
    יצירת טבלת סיכום להיפוך תפקידים:
    השוואת אקטיביות הלכתית מול סמכות אריסטוקרטית לאורך זמן.
    """
    rows = []
    for item in NESIIM_ORDER:
        sub = df[df["Chronological_Order"] == item["order"]]
        dom_row = dom_summary[dom_summary["סדר כרונולוגי"] == item["order"]].iloc[0]

        hal_valid = sub["Halakhic_Activity"].dropna()
        hal_mean_pct = hal_valid.mean() * 100.0 if len(hal_valid) > 0 else 0.0
        
        aris_raw_mean = sub["Aristocratic"].mean()
        aris_norm_mean = (sub["Aristocratic_normalized"].mean() * 100.0) if "Aristocratic_normalized" in sub.columns else np.nan
        aris_dom_pct = dom_row["אריסטוקרטי (%)"]

        rows.append({
            "סדר כרונולוגי": item["order"],
            "נשיא": item["nasi"],
            "שם תצוגה": item["display"],
            "תקופה/דור": item["generation"],
            "סך ציטוטים": len(sub),
            "ציטוטים עם סיווג הלכתי": len(hal_valid),
            "אקטיביות הלכתית (ממוצע באחוזים)": round(hal_mean_pct, 2),
            "אריסטוקרטי (כובע דומיננטי %)": round(aris_dom_pct, 2),
            "אריסטוקרטי (ממוצע מנורמל %)": round(aris_norm_mean, 2) if not np.isnan(aris_norm_mean) else None,
            "אריסטוקרטי (ציון ממוצע גולמי 0-3)": round(aris_raw_mean, 3)
        })

    return pd.DataFrame(rows)


def build_internal_vs_external_summary(dom_summary: pd.DataFrame) -> pd.DataFrame:
    """
    בחינת התיזה המרכזית:
    הנהגה פנימית (רוחנית-מוסדית = Intellectual + Institutional)
    לעומת הנהגה חיצונית (אריסטוקרטית-פוליטית = Aristocratic + Political).
    """
    rows = []
    for _, row in dom_summary.iterrows():
        internal_pct = row["אינטלקטואלי (%)"] + row["מוסדי (%)"]
        external_pct = row["פוליטי (%)"] + row["אריסטוקרטי (%)"]
        
        internal_pts = row["אינטלקטואלי (ניקוד דומיננטי)"] + row["מוסדי (ניקוד דומיננטי)"]
        external_pts = row["פוליטי (ניקוד דומיננטי)"] + row["אריסטוקרטי (ניקוד דומיננטי)"]

        rows.append({
            "סדר כרונולוגי": row["סדר כרונולוגי"],
            "נשיא": row["נשיא"],
            "שם תצוגה": row["שם תצוגה"],
            "תקופה/דור": row["תקופה/דור"],
            "סך ניקוד דומיננטי": row["ציטוטים בעלי סמכות דומיננטית"],
            "ניקוד פנימי (רוחנית-מוסדית)": round(internal_pts, 2),
            "ניקוד חיצוני (אריסטוקרטית-פוליטית)": round(external_pts, 2),
            "הנהגה פנימית - רוחנית-מוסדית (%)": round(internal_pct, 2),
            "הנהגה חיצונית - אריסטוקרטית-פוליטית (%)": round(external_pct, 2),
            "יחס פנימי/חיצוני": round(internal_pct / external_pct, 2) if external_pct > 0 else 999.0
        })

    return pd.DataFrame(rows)


# ==============================================================================
# פונקציות יצירת 3 הגרפים הנפרדים
# ==============================================================================

def plot_graph_1_dominant_hat_stacked_bar(dom_summary: pd.DataFrame, output_path: str):
    """
    גרף 1: התפלגות הכובע הדומיננטי (100% Stacked Bar Chart).
    מציג את התפלגות 4 כובעי הסמכות לפי נשיאים על בסיס הכובע שקיבל את הציון הגבוה ביותר.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 7))

    names = [fix_heb(n) for n in dom_summary["שם תצוגה"]]
    x = np.arange(len(names))
    width = 0.58

    intellectual = dom_summary["אינטלקטואלי (%)"].values
    institutional = dom_summary["מוסדי (%)"].values
    political = dom_summary["פוליטי (%)"].values
    aristocratic = dom_summary["אריסטוקרטי (%)"].values

    bottom = np.zeros(len(names))
    bars_data = [
        ("Intellectual", intellectual, COLORS["Intellectual"], "סמכות אינטלקטואלית-רוחנית (Intellectual)"),
        ("Institutional", institutional, COLORS["Institutional"], "סמכות מוסדית-תקנתית (Institutional)"),
        ("Political", political, COLORS["Political"], "סמכות פוליטית (Political)"),
        ("Aristocratic", aristocratic, COLORS["Aristocratic"], "סמכות אריסטוקרטית ושררה (Aristocratic)")
    ]

    for key, values, color, label in bars_data:
        rects = ax.bar(x, values, width, bottom=bottom, label=fix_heb(label),
                       color=color, edgecolor='white', linewidth=1.2, zorder=3)
        
        # כיתוב אחוזים בתוך המקטעים הגדולים מ-4%
        for i, (rect, val) in enumerate(zip(rects, values)):
            if val >= 4.0:
                ax.text(
                    rect.get_x() + rect.get_width() / 2.0,
                    bottom[i] + val / 2.0,
                    f"{val:.1f}%" if val < 90 else f"{val:.0f}%",
                    ha='center', va='center',
                    color="white" if key != "Political" else "#111111",
                    fontweight='bold', fontsize=9.5
                )
        bottom += values

    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax.set_ylabel(fix_heb("התפלגות יחסית של הכובע הדומיננטי"), fontsize=12, fontweight='bold', labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10.5, fontweight='bold', rotation=15)
    ax.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=12, fontweight='bold', labelpad=12)

    title_main = fix_heb("התפלגות צירי הסמכות בשושלת הנשיאות: שיטת 'הכובע הדומיננטי'")
    title_sub = fix_heb("שיוך כל ציטוט לקטגוריה הבלעדית שקיבלה את הציון המרבי (עם חלוקת נקודות במקרה של תיקו)")
    ax.set_title(f"{title_main}\n{title_sub}", fontsize=13, fontweight='bold', pad=15)

    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.28), ncol=2, frameon=True, fontsize=10)
    ax.grid(axis='y', zorder=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ גרף 1 (כובע דומיננטי 100%) נשמר בהצלחה: {output_path}")


def plot_graph_2_role_reversal_line_chart(trends_df: pd.DataFrame, output_path: str):
    """
    גרף 2: גרף מגמות - היפוך תפקידים לאורך ציר הזמן.
    מציג שני קווים: ממוצע אקטיביות הלכתית (Halakhic Activity) לעומת סמכות אריסטוקרטית (Aristocratic).
    """
    setup_plot_style()
    fig, ax1 = plt.subplots(figsize=(12, 7))

    names = [fix_heb(n) for n in trends_df["שם תצוגה"]]
    x = np.arange(len(names))

    y_halakhic = trends_df["אקטיביות הלכתית (ממוצע באחוזים)"].values
    y_aristocratic = trends_df["אריסטוקרטי (כובע דומיננטי %)"].values

    # קו 1: אקטיביות הלכתית
    line1 = ax1.plot(
        x, y_halakhic,
        color=COLORS["Halakhic"],
        linewidth=3.0,
        marker='o',
        markersize=9,
        markerfacecolor='white',
        markeredgecolor=COLORS["Halakhic"],
        markeredgewidth=2.8,
        label=fix_heb("אקטיביות הלכתית - Halakhic Activity (%)"),
        zorder=5
    )
    ax1.fill_between(x, y_halakhic, 0, color=COLORS["Halakhic"], alpha=0.10, zorder=2)

    # כיתוב ערכים לקו ההלכתי
    for xi, yi in zip(x, y_halakhic):
        ax1.annotate(
            f"{yi:.1f}%",
            (xi, yi),
            textcoords="offset points",
            xytext=(0, 8),
            ha='center',
            fontweight='bold',
            fontsize=9.5,
            color=COLORS["Halakhic"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=COLORS["Halakhic"], lw=0.8, alpha=0.95)
        )

    # קו 2: סמכות אריסטוקרטית (כובע דומיננטי באחוזים)
    line2 = ax1.plot(
        x, y_aristocratic,
        color=COLORS["Aristocratic"],
        linewidth=3.0,
        linestyle='--',
        marker='s',
        markersize=9,
        markerfacecolor='white',
        markeredgecolor=COLORS["Aristocratic"],
        markeredgewidth=2.8,
        label=fix_heb("סמכות אריסטוקרטית ושררה - Aristocratic (%)"),
        zorder=5
    )
    ax1.fill_between(x, y_aristocratic, 0, color=COLORS["Aristocratic"], alpha=0.10, zorder=2)

    # כיתוב ערכים לקו האריסטוקרטי
    for xi, yi in zip(x, y_aristocratic):
        offset_y = 9 if yi > 15 else -16
        ax1.annotate(
            f"{yi:.1f}%",
            (xi, yi),
            textcoords="offset points",
            xytext=(0, offset_y),
            ha='center',
            fontweight='bold',
            fontsize=9.5,
            color=COLORS["Aristocratic"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=COLORS["Aristocratic"], lw=0.8, alpha=0.95)
        )

    # הדגשת אזור ההיפוך בדורות המאוחרים (אמוראים)
    ax1.axvspan(5.5, 7.5, color='#FADBD8', alpha=0.35, zorder=1)
    ax1.text(6.5, 96, fix_heb("אזור ההיפוך:\nצניחה הלכתית וזינוק בשררה"),
             ha='center', va='top', fontsize=10, fontweight='bold', color='#78281F',
             bbox=dict(boxstyle="round,pad=0.35", fc="#FDEDEC", ec="#E6B0AA", lw=0.8))

    ax1.set_ylim(-2, 105)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax1.set_ylabel(fix_heb("שיעור באחוזים (%)"), fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=10.5, fontweight='bold', rotation=15)
    ax1.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=12, fontweight='bold', labelpad=12)

    title_main = fix_heb("גרף מגמות: היפוך תפקידים בשושלת הנשיאות לאורך ציר הזמן")
    title_sub = fix_heb("צניחה חדה בפסיקה הלכתית מול נסיקה של גינוני שררה ומעמד אריסטוקרטי בדורות המאוחרים")
    ax1.set_title(f"{title_main}\n{title_sub}", fontsize=13, fontweight='bold', pad=15)

    ax1.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='#D0D0D0', fontsize=10)
    ax1.grid(True, zorder=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ גרף 2 (מגמות היפוך תפקידים) נשמר בהצלחה: {output_path}")


def plot_graph_3_internal_vs_external_leadership(int_ext_df: pd.DataFrame, output_path: str):
    """
    גרף 3: הנהגה פנימית (רוחנית-מוסדית) מול הנהגה חיצונית (אריסטוקרטית-פוליטית).
    מבחן התזה הישיר: האם שושלת הנשיאות נדדה ממוקד פנים-קהילתי למוקד חוץ-שלטוני?
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 7))

    names = [fix_heb(n) for n in int_ext_df["שם תצוגה"]]
    x = np.arange(len(names))
    width = 0.55

    internal = int_ext_df["הנהגה פנימית - רוחנית-מוסדית (%)"].values
    external = int_ext_df["הנהגה חיצונית - אריסטוקרטית-פוליטית (%)"].values

    # עמודה מוערמת: פנימית בתחתית, חיצונית בחלק העליון
    rects1 = ax.bar(x, internal, width, label=fix_heb("הנהגה פנימית: רוחנית-מוסדית (Intellectual + Institutional)"),
                    color="#2E75B6", edgecolor='white', lw=1.2, zorder=3)
    rects2 = ax.bar(x, external, width, bottom=internal, label=fix_heb("הנהגה חיצונית: אריסטוקרטית-פוליטית (Aristocratic + Political)"),
                    color="#C00000", edgecolor='white', lw=1.2, zorder=3)

    # כיתוב אחוזים
    for i in range(len(names)):
        # פנימית
        ax.text(x[i], internal[i] / 2.0, f"{internal[i]:.1f}%",
                ha='center', va='center', color='white', fontweight='bold', fontsize=10)
        # חיצונית
        if external[i] >= 3.0:
            ax.text(x[i], internal[i] + external[i] / 2.0, f"{external[i]:.1f}%",
                    ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # קו מפריד ב-50%
    ax.axhline(50, color='#888888', linestyle=':', lw=1.2, zorder=2)
    ax.text(7.6, 50, fix_heb("50%"), va='center', fontsize=9, color='#666666')

    # חץ מגמה להנהגה החיצונית בדורות המאוחרים
    ax.annotate(
        fix_heb("עלייה דרמטית בשררה החיצונית\n(מ-1.6% אצל רבי ל-35.4% בנשיאה)"),
        xy=(7, 85),
        xytext=(4.8, 92),
        arrowprops=dict(facecolor='#922B21', edgecolor='#922B21', arrowstyle='->', lw=1.8),
        fontsize=10,
        fontweight='bold',
        color='#922B21',
        bbox=dict(boxstyle="round,pad=0.3", fc="#FDEDEC", ec="#E6B0AA", lw=0.8)
    )

    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax.set_ylabel(fix_heb("התפלגות יחסית (100%)"), fontsize=12, fontweight='bold', labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10.5, fontweight='bold', rotation=15)
    ax.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=12, fontweight='bold', labelpad=12)

    title_main = fix_heb("מבחן התיזה: מעבר מהנהגה פנימית (רוחנית-מוסדית) להנהגה חיצונית (אריסטוקרטית-פוליטית)")
    title_sub = fix_heb("התפלגות מודל המנהיגות לאורך 8 דורות בשושלת בית הלל")
    ax.set_title(f"{title_main}\n{title_sub}", fontsize=13, fontweight='bold', pad=15)

    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=1, frameon=True, fontsize=10)
    ax.grid(axis='y', zorder=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ גרף 3 (הנהגה פנימית מול חיצונית) נשמר בהצלחה: {output_path}")


def plot_combined_thesis_dashboard(dom_summary: pd.DataFrame, trends_df: pd.DataFrame, int_ext_df: pd.DataFrame, output_path: str):
    """דשבורד מחקרי משולב המציג את שלושת הגרפים יחדיו בפאנל אקדמי יוקרתי."""
    setup_plot_style()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(13, 16), sharex=True)

    names = [fix_heb(n) for n in dom_summary["שם תצוגה"]]
    x = np.arange(len(names))
    width = 0.55

    # פאנל 1: 4 כובעים דומיננטיים
    intellectual = dom_summary["אינטלקטואלי (%)"].values
    institutional = dom_summary["מוסדי (%)"].values
    political = dom_summary["פוליטי (%)"].values
    aristocratic = dom_summary["אריסטוקרטי (%)"].values

    bottom = np.zeros(len(names))
    bars_data = [
        ("Intellectual", intellectual, COLORS["Intellectual"], "אינטלקטואלי"),
        ("Institutional", institutional, COLORS["Institutional"], "מוסדי"),
        ("Political", political, COLORS["Political"], "פוליטי"),
        ("Aristocratic", aristocratic, COLORS["Aristocratic"], "אריסטוקרטי")
    ]
    for key, values, color, label in bars_data:
        rects = ax1.bar(x, values, width, bottom=bottom, label=fix_heb(label), color=color, edgecolor='white', lw=1, zorder=3)
        for i, (rect, val) in enumerate(zip(rects, values)):
            if val >= 5.0:
                ax1.text(rect.get_x() + rect.get_width()/2.0, bottom[i] + val/2.0, f"{val:.0f}%",
                         ha='center', va='center', color='white' if key != 'Political' else '#111',
                         fontweight='bold', fontsize=8.5)
        bottom += values

    ax1.set_ylim(0, 100)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax1.set_ylabel(fix_heb("כובע דומיננטי (100%)"), fontsize=10.5, fontweight='bold')
    ax1.set_title(fix_heb("א. התפלגות 4 צירי הסמכות לפי 'שיטת הכובע הדומיננטי'"), fontsize=11.5, fontweight='bold', loc='right')
    ax1.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), frameon=True, fontsize=9)
    ax1.grid(axis='y', zorder=0)

    # פאנל 2: היפוך תפקידים
    y_hal = trends_df["אקטיביות הלכתית (ממוצע באחוזים)"].values
    y_aris = trends_df["אריסטוקרטי (כובע דומיננטי %)"].values

    ax2.plot(x, y_hal, color=COLORS["Halakhic"], lw=2.6, marker='o', markersize=7.5, mfc='white', mew=2.4,
             label=fix_heb("אקטיביות הלכתית (%)"), zorder=4)
    ax2.plot(x, y_aris, color=COLORS["Aristocratic"], lw=2.6, linestyle='--', marker='s', markersize=7.5, mfc='white', mew=2.4,
             label=fix_heb("סמכות אריסטוקרטית (%)"), zorder=4)
    ax2.fill_between(x, y_hal, 0, color=COLORS["Halakhic"], alpha=0.08, zorder=2)
    ax2.fill_between(x, y_aris, 0, color=COLORS["Aristocratic"], alpha=0.08, zorder=2)
    ax2.axvspan(5.5, 7.5, color='#FADBD8', alpha=0.35, zorder=1)

    for xi, yi in zip(x, y_hal):
        ax2.annotate(f"{yi:.0f}%", (xi, yi), textcoords="offset points", xytext=(0, 6),
                     ha='center', fontweight='bold', fontsize=8.5, color=COLORS["Halakhic"],
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=COLORS["Halakhic"], lw=0.6))
    for xi, yi in zip(x, y_aris):
        offset = 6 if yi > 15 else -12
        ax2.annotate(f"{yi:.0f}%", (xi, yi), textcoords="offset points", xytext=(0, offset),
                     ha='center', fontweight='bold', fontsize=8.5, color=COLORS["Aristocratic"],
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=COLORS["Aristocratic"], lw=0.6))

    ax2.set_ylim(-2, 105)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax2.set_ylabel(fix_heb("שיעור באחוזים"), fontsize=10.5, fontweight='bold')
    ax2.set_title(fix_heb("ב. מגמת היפוך תפקידים: אקטיביות הלכתית מול סמכות אריסטוקרטית"), fontsize=11.5, fontweight='bold', loc='right')
    ax2.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), frameon=True, fontsize=9)
    ax2.grid(True, zorder=0)

    # פאנל 3: פנימית מול חיצונית
    internal = int_ext_df["הנהגה פנימית - רוחנית-מוסדית (%)"].values
    external = int_ext_df["הנהגה חיצונית - אריסטוקרטית-פוליטית (%)"].values

    ax3.bar(x, internal, width, label=fix_heb("הנהגה פנימית (רוחנית-מוסדית)"), color="#2E75B6", edgecolor='white', lw=1, zorder=3)
    ax3.bar(x, external, width, bottom=internal, label=fix_heb("הנהגה חיצונית (אריסטוקרטית-פוליטית)"), color="#C00000", edgecolor='white', lw=1, zorder=3)

    for i in range(len(names)):
        ax3.text(x[i], internal[i]/2.0, f"{internal[i]:.0f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)
        if external[i] >= 4.0:
            ax3.text(x[i], internal[i] + external[i]/2.0, f"{external[i]:.0f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)

    ax3.set_ylim(0, 100)
    ax3.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax3.set_ylabel(fix_heb("התפלגות יחסית (100%)"), fontsize=10.5, fontweight='bold')
    ax3.set_title(fix_heb("ג. מבחן התיזה: מעבר מהנהגה פנימית להנהגה חיצונית"), fontsize=11.5, fontweight='bold', loc='right')
    ax3.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), frameon=True, fontsize=9)
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, fontsize=10, fontweight='bold', rotation=15)
    ax3.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=11, fontweight='bold', labelpad=8)
    ax3.grid(axis='y', zorder=0)

    fig.suptitle(fix_heb("דשבורד מחקרי מקיף: תיזת הטרנספורמציה במוסד הנשיאות"), fontsize=14, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ דשבורד מחקרי משולב נשמר בהצלחה: {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ניתוח כמותי של תיזת הנשיאות: שיטת הכובע הדומיננטי ומגמות ההיפוך")
    parser.add_argument("--input-dir", type=str, default="taxonomy/classified-results/normalized_output", help="תיקיית קלט המכילה את 8 קובצי הנשיאים המנורמלים")
    parser.add_argument("--output-dir", type=str, default=None, help="תיקיית יעד לקובצי ה-CSV והגרפים")
    parser.add_argument("--plots", action="store_true", help="יצירת גרפים ב-matplotlib (ברירת מחדל: רק קובצי CSV)")
    args = parser.parse_args()

    input_folder = os.path.abspath(args.input_dir)
    output_folder = os.path.abspath(args.output_dir) if args.output_dir else input_folder

    print("=" * 80)
    print("▶ מתחיל ניתוח כמותי של תיזת הנשיאות: שיטת הכובע הדומיננטי ומגמות ההיפוך")
    print(f"▶ קריאת נתונים מתיקייה: {input_folder}")
    print(f"▶ שמירת קובצי CSV בתיקייה: {output_folder}")
    print("=" * 80)

    # 1. טעינת הנתונים
    df = load_normalized_data(input_folder)
    print(f"✓ נטענו בהצלחה {len(df)} שורות מ-8 קובצי הנשיאים.")

    # 2. חישוב הכובע הדומיננטי
    df = calculate_dominant_hats(df)
    
    # 3. יצירת טבלאות הסיכום
    dom_summary = build_dominant_hat_summary(df)
    role_reversal_summary = build_role_reversal_summary(df, dom_summary)
    int_ext_summary = build_internal_vs_external_summary(dom_summary)

    # 4. שמירת קובצי CSV ייעודיים לאקסל (קידוד utf-8-sig התומך בעברית ללא ג'יבריש)
    csv1_path = os.path.join(output_folder, "dominant_hat_summary.csv")
    csv2_path = os.path.join(output_folder, "role_reversal_trends.csv")
    csv3_path = os.path.join(output_folder, "internal_vs_external_leadership.csv")

    dom_summary.to_csv(csv1_path, index=False, encoding='utf-8-sig')
    role_reversal_summary.to_csv(csv2_path, index=False, encoding='utf-8-sig')
    int_ext_summary.to_csv(csv3_path, index=False, encoding='utf-8-sig')

    print(f"\n✓ נשמר קובץ אקסל 1 (הכובע הדומיננטי): {os.path.basename(csv1_path)}")
    print(f"✓ נשמר קובץ אקסל 2 (היפוך תפקידים - מגמות): {os.path.basename(csv2_path)}")
    print(f"✓ נשמר קובץ אקסל 3 (מבחן התזה - הנהגה פנימית מול חיצונית): {os.path.basename(csv3_path)}")

    # 5. יצירת גרפים במידה וסופק הדגל --plots
    if args.plots:
        g1_path = os.path.join(output_folder, "graph1_dominant_hat_stacked_bar.png")
        g2_path = os.path.join(output_folder, "graph2_role_reversal_line_chart.png")
        g3_path = os.path.join(output_folder, "graph3_internal_vs_external_leadership.png")
        g_dash_path = os.path.join(output_folder, "graph_thesis_dashboard_combined.png")

        plot_graph_1_dominant_hat_stacked_bar(dom_summary, g1_path)
        plot_graph_2_role_reversal_line_chart(role_reversal_summary, g2_path)
        plot_graph_3_internal_vs_external_leadership(int_ext_summary, g3_path)
        plot_combined_thesis_dashboard(dom_summary, role_reversal_summary, int_ext_summary, g_dash_path)

    # 6. הדפסת סיכום מספרי ברור למסוף
    print("\n" + "=" * 90)
    print("טבלה 1: התפלגות הכובע הדומיננטי (%)")
    print(dom_summary[["סדר כרונולוגי", "שם תצוגה", "אינטלקטואלי (%)", "מוסדי (%)", "פוליטי (%)", "אריסטוקרטי (%)"]].to_string(index=False))

    print("\n" + "=" * 90)
    print("טבלה 2: היפוך תפקידים - הלכה מול אריסטוקרטיה")
    print(role_reversal_summary[["סדר כרונולוגי", "שם תצוגה", "אקטיביות הלכתית (ממוצע באחוזים)", "אריסטוקרטי (כובע דומיננטי %)", "אריסטוקרטי (ציון ממוצע גולמי 0-3)"]].to_string(index=False))

    print("\n" + "=" * 90)
    print("טבלה 3: מבחן התיזה - הנהגה פנימית לעומת חיצונית (%)")
    print(int_ext_summary[["סדר כרונולוגי", "שם תצוגה", "הנהגה פנימית - רוחנית-מוסדית (%)", "הנהגה חיצונית - אריסטוקרטית-פוליטית (%)", "יחס פנימי/חיצוני"]].to_string(index=False))
    print("=" * 90)
    print("\n✓ קובצי ה-CSV עודכנו ונוצרו בהצלחה מלאה!")


if __name__ == "__main__":
    main()

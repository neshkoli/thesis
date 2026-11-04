#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ניתוח כמותי של צירי הסמכות והאקטיביות ההלכתית בקרב נשיאי הסנהדרין לאורך הדורות
מתודולוגיית "שיטת המשקל המובהק" (Thresholding & Row Normalization)

מטרת המחקר:
בחינת התיזה ההיסטורית-סוציולוגית בדבר מעבר הדרגתי מסמכות אינטלקטואלית/מוסדית (בתחילת השושלת)
לסמכות פוליטית/אריסטוקרטית (בסופה), לצד צניחה חדה באקטיביות ההלכתית בדורות המאוחרים.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from bidi.algorithm import get_display


def fix_heb(text: str) -> str:
    """
    עיבוד טקסט עברי כך שיוצג בצורה טבעית ותקנית במטפלוטליב (RTL).
    """
    lines = str(text).split('\n')
    return '\n'.join(get_display(line) for line in lines)




# רשימת 8 הנשיאים לפי סדר כרונולוגי קפדני
NESIIM_METADATA = [
    {
        "order": 1,
        "filename": "הלל_classified.csv",
        "nasi_name": "הלל",
        "display_name": "הלל הזקן",
        "generation": "סוף ימי הבית השני"
    },
    {
        "order": 2,
        "filename": "רבן_גמליאל_הזקן_classified.csv",
        "nasi_name": "רבן גמליאל הזקן",
        "display_name": "רבן גמליאל הזקן",
        "generation": "דור 1 לתנאים"
    },
    {
        "order": 3,
        "filename": "רבן_שמעון_בן_גמליאל_הראשון_classified.csv",
        "nasi_name": "רבן שמעון בן גמליאל הראשון",
        "display_name": "רשב\"ג הראשון",
        "generation": "ערב החורבן"
    },
    {
        "order": 4,
        "filename": "רבן_גמליאל_דיבנה_classified.csv",
        "nasi_name": "רבן גמליאל דיבנה",
        "display_name": "רבן גמליאל דיבנה",
        "generation": "דור 2 לתנאים (יבנה)"
    },
    {
        "order": 5,
        "filename": "רבן_שמעון_בן_גמליאל_השני_classified.csv",
        "nasi_name": "רבן שמעון בן גמליאל השני",
        "display_name": "רשב\"ג השני",
        "generation": "דור 3 לתנאים (אושא)"
    },
    {
        "order": 6,
        "filename": "רבי_יהודה_הנשיא_classified.csv",
        "nasi_name": "רבי יהודה הנשיא",
        "display_name": "רבי יהודה הנשיא",
        "generation": "דור 4-5 לתנאים (חותם המשנה)"
    },
    {
        "order": 7,
        "filename": "רבן_גמליאל_ברבי_classified.csv",
        "nasi_name": "רבן גמליאל ברבי",
        "display_name": "רבן גמליאל ברבי",
        "generation": "דור 1 לאמוראים"
    },
    {
        "order": 8,
        "filename": "רבי_יהודה_נשיאה_classified.csv",
        "nasi_name": "רבי יהודה נשיאה",
        "display_name": "רבי יהודה נשיאה",
        "generation": "דור 2 לאמוראים (טבריה)"
    }
]

AUTHORITY_AXES = ["Intellectual", "Institutional", "Political", "Aristocratic"]

# פלטת צבעים אקדמית יוקרתית בעלת ניגודיות גבוהה
COLORS = {
    "Intellectual": "#1F4E79",   # כחול עמוק / אינטלקטואלי
    "Institutional": "#2E75B6",  # כחול-אפור מוסדי
    "Political": "#E37222",      # כתום-ענבר פוליטי
    "Aristocratic": "#C00000",   # ארגמן/שני אריסטוקרטי
    "Halakhic": "#0E6251"        # טורקיז-יער כהה לאקטיביות הלכתית
}


def find_input_directory() -> str:
    """איתור אוטומטי של תיקיית הקבצים classified-results."""
    candidates = [
        "taxonomy/classified-results",
        "classified-results",
        "../taxonomy/classified-results",
        "../../taxonomy/classified-results"
    ]
    for c in candidates:
        if os.path.isdir(c) and any(os.path.exists(os.path.join(c, m["filename"])) for m in NESIIM_METADATA):
            return os.path.abspath(c)
    return os.path.abspath("taxonomy/classified-results")


def process_individual_file(file_path: str, nasi_info: dict) -> pd.DataFrame:
    """
    טעינת קובץ CSV של נשיא בודד, ניקוי שורות סיכום היסטוריות (TOTAL/RATIO),
    וביצוע סינון רעשים ונרמול שורות.
    """
    df = pd.read_csv(file_path)
    
    # סינון שורות סיכום שקיימות לעיתים בסוף הקובץ המקורי
    if "corpus" in df.columns:
        df = df[~df["corpus"].astype(str).str.upper().isin(["TOTAL", "RATIO", "SUMMARY", "AVERAGE"])].copy()
    
    # 1. הוספת עמודות מטא-דאטה וסדר כרונולוגי
    df["Nasi"] = nasi_info["nasi_name"]
    df["Display_Name"] = nasi_info["display_name"]
    df["Chronological_Order"] = nasi_info["order"]
    df["Generation"] = nasi_info["generation"]

    # 2. סינון רעשי רקע (Thresholding):
    # החלפת כל ערך ששווה ל-1 בערך 0; ערכים 2 ו-3 נשמרים כפי שהם
    for ax in AUTHORITY_AXES:
        if ax in df.columns:
            val_numeric = pd.to_numeric(df[ax], errors="coerce").fillna(0.0)
            df[f"{ax}_raw"] = val_numeric
            df[f"{ax}_thresholded"] = val_numeric.apply(lambda v: 0.0 if v == 1.0 else float(v))
        else:
            df[f"{ax}_raw"] = 0.0
            df[f"{ax}_thresholded"] = 0.0

    # 3. נרמול שורות (Row Normalization):
    # סכום 4 הצירים לאחר הסינון. אם > 0 מחלקים בסכום (כך שסכום השורה בדיוק 1.0), אחרת 0.0.
    thresholded_cols = [f"{ax}_thresholded" for ax in AUTHORITY_AXES]
    row_sum = df[thresholded_cols].sum(axis=1)
    df["Distinct_Authority_Sum"] = row_sum
    df["Has_Distinct_Authority"] = (row_sum > 0).astype(int)

    for ax in AUTHORITY_AXES:
        df[f"{ax}_normalized"] = np.where(
            row_sum > 0,
            df[f"{ax}_thresholded"] / row_sum,
            0.0
        )

    # וידוא עמודת Halakhic_Activity נומרית
    if "Halakhic_Activity" in df.columns:
        df["Halakhic_Activity_Numeric"] = pd.to_numeric(df["Halakhic_Activity"], errors="coerce")
    else:
        df["Halakhic_Activity_Numeric"] = np.nan

    return df


def aggregate_results(dfs: list) -> tuple:
    """
    4. אגרגציה לפי נשיא (לפי הסדר הכרונולוגי):
    - חישוב ממוצע 4 צירי הסמכות המנורמלים (באחוזים)
    - חישוב התפלגות יחסית (100% סך סמכות) עבור גרף העמודות המוערמות
    - 5. חישוב ממוצע אקטיביות הלכתית
    """
    combined_df = pd.concat(dfs, ignore_index=True)
    summary_rows = []

    for info in NESIIM_METADATA:
        nasi = info["nasi_name"]
        sub = combined_df[combined_df["Nasi"] == nasi]
        total_quotes = len(sub)
        distinct_quotes = int(sub["Has_Distinct_Authority"].sum())
        distinct_ratio = (distinct_quotes / total_quotes * 100.0) if total_quotes > 0 else 0.0

        # ממוצע הצירים המנורמלים בכלל הציטוטים
        norm_means = {
            ax: sub[f"{ax}_normalized"].mean() * 100.0 for ax in AUTHORITY_AXES
        }
        total_authority_share = sum(norm_means.values())

        # התפלגות יחסית (הסכום של 4 הצירים הוא בדיוק 100%)
        rel_shares = {}
        for ax in AUTHORITY_AXES:
            if total_authority_share > 0:
                rel_shares[ax] = (norm_means[ax] / total_authority_share) * 100.0
            else:
                rel_shares[ax] = 0.0

        # אקטיביות הלכתית (ממוצע נומרי באחוזים)
        halakhic_mean = sub["Halakhic_Activity_Numeric"].mean() * 100.0
        halakhic_valid_count = int(sub["Halakhic_Activity_Numeric"].notna().sum())

        row = {
            "סדר כרונולוגי": info["order"],
            "נשיא": info["nasi_name"],
            "שם תצוגה": info["display_name"],
            "תקופה/דור": info["generation"],
            "סך מקורות": total_quotes,
            "מקורות בעלי משקל מובהק": distinct_quotes,
            "שיעור מקורות מובהקים (%)": distinct_ratio,
            "אינטלקטואלי (ממוצע %)": norm_means["Intellectual"],
            "מוסדי (ממוצע %)": norm_means["Institutional"],
            "פוליטי (ממוצע %)": norm_means["Political"],
            "אריסטוקרטי (ממוצע %)": norm_means["Aristocratic"],
            "אינטלקטואלי (יחסי 100%)": rel_shares["Intellectual"],
            "מוסדי (יחסי 100%)": rel_shares["Institutional"],
            "פוליטי (יחסי 100%)": rel_shares["Political"],
            "אריסטוקרטי (יחסי 100%)": rel_shares["Aristocratic"],
            "אקטיביות הלכתית (%)": halakhic_mean,
            "מקורות עם דירוג הלכתי": halakhic_valid_count
        }
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    return summary_df, combined_df


def setup_plot_style():
    """הגדרת סגנון אקדמי נקי לגרפים."""
    plt.rcParams.update({
        'font.sans-serif': ['Arial', 'Arial Hebrew', 'DejaVu Sans', 'Helvetica'],
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
        'grid.alpha': 0.7
    })


def plot_stacked_bar_chart(summary_df: pd.DataFrame, output_path: str):
    """
    6א. גרף עמודות מוערמות (100% Stacked Bar Chart)
    המציג את התפלגות 4 צירי הסמכות עבור כל נשיא לאורך ציר הדורות.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 7.5))

    names = [fix_heb(n) for n in summary_df["שם תצוגה"]]
    x = np.arange(len(names))
    width = 0.62

    # נתונים באחוזים (הסכום של כל עמודה הוא בדיוק 100%)
    intellectual = summary_df["אינטלקטואלי (יחסי 100%)"].values
    institutional = summary_df["מוסדי (יחסי 100%)"].values
    political = summary_df["פוליטי (יחסי 100%)"].values
    aristocratic = summary_df["אריסטוקרטי (יחסי 100%)"].values

    bottom = np.zeros(len(names))

    bar_configs = [
        ("Intellectual", intellectual, COLORS["Intellectual"], "סמכות אינטלקטואלית"),
        ("Institutional", institutional, COLORS["Institutional"], "סמכות מוסדית"),
        ("Political", political, COLORS["Political"], "סמכות פוליטית"),
        ("Aristocratic", aristocratic, COLORS["Aristocratic"], "סמכות אריסטוקרטית")
    ]

    for key, values, color, label in bar_configs:
        rects = ax.bar(
            x, values, width,
            bottom=bottom,
            label=fix_heb(label),
            color=color,
            edgecolor='white',
            linewidth=1.2,
            zorder=3
        )
        
        # כיתוב אחוזים על גבי כל מקטע בגרף (אם המקטע גדול מ-4.2%)
        for i, (rect, val) in enumerate(zip(rects, values)):
            if val >= 4.2:
                y_pos = bottom[i] + val / 2.0
                text_color = "white" if key in ["Intellectual", "Aristocratic", "Institutional"] else "#111111"
                ax.text(
                    rect.get_x() + rect.get_width() / 2.0,
                    y_pos,
                    f"{val:.1f}%",
                    ha='center', va='center',
                    color=text_color,
                    fontweight='bold',
                    fontsize=9.5
                )

        bottom += values

    # עיצוב צירים וכותרות
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10.5, fontweight='bold', rotation=15)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax.set_ylabel(fix_heb("התפלגות יחסית של צירי הסמכות המובהקים"), fontsize=12, fontweight='bold', labelpad=12)
    ax.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=12, fontweight='bold', labelpad=12)

    t1 = fix_heb("התפתחות צירי הסמכות בשושלת הנשיאים - שיטת המשקל המובהק")
    t2 = fix_heb("מעבר מסמכות אינטלקטואלית/מוסדית לסמכות אריסטוקרטית ופוליטית לאורך הדורות")
    ax.set_title(f"{t1}\n{t2}", fontsize=13.5, fontweight='bold', pad=16)

    # מקרא מעוצב
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.16),
        ncol=4,
        frameon=True,
        facecolor='white',
        edgecolor='#CCCCCC',
        fontsize=10
    )

    ax.grid(axis='y', zorder=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ גרף עמודות מוערמות נשמר בהצלחה: {output_path}")


def plot_halakhic_activity_line(summary_df: pd.DataFrame, output_path: str):
    """
    6ב. גרף קווי (Line Chart) המציג את אחוז ה-Halakhic Activity
    לאורך ציר הדורות הכרונולוגי.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(11, 6.5))

    names = [fix_heb(n) for n in summary_df["שם תצוגה"]]
    x = np.arange(len(names))
    y = summary_df["אקטיביות הלכתית (%)"].values

    # קו רציף מעוצב עם הדגשת מגמה
    ax.plot(
        x, y,
        color=COLORS["Halakhic"],
        linewidth=2.8,
        marker='o',
        markersize=9,
        markerfacecolor='white',
        markeredgecolor=COLORS["Halakhic"],
        markeredgewidth=2.6,
        zorder=4,
        label=fix_heb("שיעור האקטיביות ההלכתית (%)")
    )

    # הצללה עדינה תחת הקו
    ax.fill_between(x, y, 0, color=COLORS["Halakhic"], alpha=0.12, zorder=2)

    # כיתוב ערכים מעל הנקודות
    for i, (xi, yi) in enumerate(zip(x, y)):
        offset_y = 4.0 if yi < 90 else -7.0
        va = 'bottom' if offset_y > 0 else 'top'
        ax.annotate(
            f"{yi:.1f}%",
            (xi, yi),
            textcoords="offset points",
            xytext=(0, offset_y),
            ha='center',
            va=va,
            fontweight='bold',
            fontsize=10.5,
            color="#111111",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#D0D0D0", lw=0.6, alpha=0.9)
        )

    # עיצוב צירים וכותרות
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10.5, fontweight='bold', rotation=15)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax.set_ylabel(fix_heb("אחוז האקטיביות ההלכתית"), fontsize=12, fontweight='bold', labelpad=12)
    ax.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=12, fontweight='bold', labelpad=12)

    t1 = fix_heb("מגמת האקטיביות ההלכתית בשושלת נשיאי הסנהדרין")
    t2 = fix_heb("צניחה חדה בפעילות ההלכתית המעשית בדורות המאוחרים (אמוראי ארץ ישראל)")
    ax.set_title(f"{t1}\n{t2}", fontsize=13.5, fontweight='bold', pad=16)

    # הדגשת הצניחה בסוף השושלת
    ax.axvspan(5.5, 7.5, color='#FADBD8', alpha=0.35, zorder=1, label=fix_heb("ירידה מובהקת בדורות המאוחרים"))

    ax.legend(
        loc='lower left',
        frameon=True,
        facecolor='white',
        edgecolor='#CCCCCC',
        fontsize=10
    )

    ax.grid(True, zorder=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ גרף אקטיביות הלכתית נשמר בהצלחה: {output_path}")


def plot_combined_dashboard(summary_df: pd.DataFrame, output_path: str):
    """
    תרשים משולב (דשבורד מחקרי כפול) הכולל הן את העמודות המוערמות
    והן את קו האקטיביות ההלכתית על גבי אותו ציר כרונולוגי - אידיאלי לתזה.
    """
    setup_plot_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 11), sharex=True, gridspec_kw={'height_ratios': [1.3, 1]})

    names = [fix_heb(n) for n in summary_df["שם תצוגה"]]
    x = np.arange(len(names))
    width = 0.58

    # 1. עמודות מוערמות בחלק העליון
    intellectual = summary_df["אינטלקטואלי (יחסי 100%)"].values
    institutional = summary_df["מוסדי (יחסי 100%)"].values
    political = summary_df["פוליטי (יחסי 100%)"].values
    aristocratic = summary_df["אריסטוקרטי (יחסי 100%)"].values
    bottom = np.zeros(len(names))

    bar_configs = [
        ("Intellectual", intellectual, COLORS["Intellectual"], "סמכות אינטלקטואלית"),
        ("Institutional", institutional, COLORS["Institutional"], "סמכות מוסדית"),
        ("Political", political, COLORS["Political"], "סמכות פוליטית"),
        ("Aristocratic", aristocratic, COLORS["Aristocratic"], "סמכות אריסטוקרטית")
    ]

    for key, values, color, label in bar_configs:
        rects = ax1.bar(x, values, width, bottom=bottom, label=fix_heb(label), color=color, edgecolor='white', lw=1, zorder=3)
        for i, (rect, val) in enumerate(zip(rects, values)):
            if val >= 4.5:
                ax1.text(
                    rect.get_x() + rect.get_width() / 2.0,
                    bottom[i] + val / 2.0,
                    f"{val:.0f}%",
                    ha='center', va='center',
                    color="white" if key != "Political" else "#111111",
                    fontweight='bold', fontsize=9
                )
        bottom += values

    ax1.set_ylim(0, 100)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax1.set_ylabel(fix_heb("התפלגות יחסית של צירי הסמכות"), fontsize=11, fontweight='bold')
    ax1.set_title(fix_heb("א. התפלגות צירי הסמכות לאורך הדורות (100% Stacked Bar)"), fontsize=12, fontweight='bold', loc='right')
    ax1.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), frameon=True, fontsize=9.5)
    ax1.grid(axis='y', zorder=0)

    # 2. קו אקטיביות הלכתית בחלק התחתון
    y_hal = summary_df["אקטיביות הלכתית (%)"].values
    ax2.plot(x, y_hal, color=COLORS["Halakhic"], lw=2.5, marker='s', markersize=8, mfc='white', mew=2.5, zorder=4)
    ax2.fill_between(x, y_hal, 0, color=COLORS["Halakhic"], alpha=0.15, zorder=2)

    for xi, yi in zip(x, y_hal):
        ax2.annotate(f"{yi:.1f}%", (xi, yi), textcoords="offset points", xytext=(0, 6),
                     ha='center', fontweight='bold', fontsize=9.5,
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#D0D0D0", lw=0.5))

    ax2.set_ylim(0, 105)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax2.set_ylabel(fix_heb("אקטיביות הלכתית (%)"), fontsize=11, fontweight='bold')
    ax2.set_title(fix_heb("ב. שיעור האקטיביות ההלכתית לאורך הדורות"), fontsize=12, fontweight='bold', loc='right')
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, fontsize=10.5, fontweight='bold', rotation=15)
    ax2.set_xlabel(fix_heb("סדר כרונולוגי של שושלת הנשיאים"), fontsize=11, fontweight='bold', labelpad=8)
    ax2.grid(True, zorder=0)

    main_sup = fix_heb("דשבורד מחקרי: דינמיקת הסמכות וההלכה בשושלת נשיאי הסנהדרין")
    fig.suptitle(main_sup, fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ תרשים משולב (דשבורד כפול) נשמר בהצלחה: {output_path}")


def print_summary_table(summary_df: pd.DataFrame):
    """הדפסה מעוצבת של טבלת הנתונים המסכמת."""
    print("\n" + "=" * 115)
    print("                 טבלת סיכום מחקרית: התפלגות צירי הסמכות והאקטיביות ההלכתית בשושלת הנשיאים")
    print("                                      מתודולוגיית 'שיטת המשקל המובהק'")
    print("=" * 115)
    
    display_cols = [
        "סדר כרונולוגי", "נשיא", "סך מקורות", "מקורות בעלי משקל מובהק",
        "אינטלקטואלי (יחסי 100%)", "מוסדי (יחסי 100%)", "פוליטי (יחסי 100%)", "אריסטוקרטי (יחסי 100%)",
        "אקטיביות הלכתית (%)"
    ]
    formatted = summary_df[display_cols].copy()
    for col in ["אינטלקטואלי (יחסי 100%)", "מוסדי (יחסי 100%)", "פוליטי (יחסי 100%)", "אריסטוקרטי (יחסי 100%)", "אקטיביות הלכתית (%)"]:
        formatted[col] = formatted[col].apply(lambda v: f"{v:6.2f}%")
        
    print(formatted.to_string(index=False))
    print("=" * 115)
    print("דגשים מתודולוגיים:")
    print("1. סינון רעשי רקע (Thresholding): ערכי 1 הוחלפו ב-0; ערכים מובהקים (2 ו-3) נשמרו.")
    print("2. נרמול שורות (Row Normalization): כל שורה חולקה בסך הסמכות המובהקת שבה (סכום כל שורה = 100%).")
    print("3. העמודות 'יחסי 100%' מציגות את החלק היחסי המדויק של כל ציר סמכות מתוך סך הסמכות של אותו נשיא.\n")


def main():
    parser = argparse.ArgumentParser(description="עיבוד נתוני סיווג הנשיאים לפי שיטת המשקל המובהק")
    parser.add_argument("--input-dir", type=str, default=None, help="נתיב לתיקיית classified-results")
    parser.add_argument("--output-dir", type=str, default=None, help="נתיב לתיקיית שמירת הפלטים")
    args = parser.parse_args()

    input_dir = args.input_dir or find_input_directory()
    if not os.path.exists(input_dir):
        print(f"שגיאה: תיקיית הקלט לא נמצאה: {input_dir}")
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(input_dir, "normalized_output")
    os.makedirs(output_dir, exist_ok=True)

    print(f"▶ קריאת נתונים מתיקייה: {input_dir}")
    print(f"▶ שמירת קבצים חדשים בתיקייה: {output_dir}\n")

    processed_dfs = []
    
    # 1. קריאת ועיבוד כל קובץ בנפרד
    for info in NESIIM_METADATA:
        filename = info["filename"]
        file_path = os.path.join(input_dir, filename)
        if not os.path.exists(file_path):
            print(f"אזהרה: הקובץ {filename} חסר בתיקייה!")
            continue

        df_proc = process_individual_file(file_path, info)
        processed_dfs.append(df_proc)

        # יצירת קובץ CSV חדש ומנורמל עבור כל נשיא
        out_individual_csv = os.path.join(output_dir, f"{info['nasi_name']}_normalized.csv")
        df_proc.to_csv(out_individual_csv, index=False, encoding='utf-8-sig')
        print(f"✓ נוצר קובץ מנורמל חדש: {os.path.basename(out_individual_csv)} ({len(df_proc)} שורות)")

    if not processed_dfs:
        print("שגיאה: לא נטענו קבצים כלל.")
        sys.exit(1)

    # 4 & 5. אגרגציה וחישוב אקטיביות הלכתית
    summary_df, combined_df = aggregate_results(processed_dfs)

    # שמירת קובץ מאוחד של כל הציטוטים מכל הנשיאים
    all_quotes_path = os.path.join(output_dir, "all_nesiim_distinct_normalized.csv")
    combined_df.to_csv(all_quotes_path, index=False, encoding='utf-8-sig')
    print(f"\n✓ נוצר קובץ נתונים מקיף מאוחד: {os.path.basename(all_quotes_path)}")

    # שמירת טבלת הסיכום ב-CSV
    summary_csv_path = os.path.join(output_dir, "nasi_authority_and_halakha_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False, encoding='utf-8-sig')
    print(f"✓ נשמרה טבלת הסיכום המספרית: {os.path.basename(summary_csv_path)}")

    # הדפסת הטבלה למסוף
    print_summary_table(summary_df)

    # 6. יצירת הגרפים האקדמיים
    stacked_bar_path = os.path.join(output_dir, "nasi_authority_stacked_bar_100pct.png")
    halakhic_line_path = os.path.join(output_dir, "nasi_halakhic_activity_line_chart.png")
    combined_dash_path = os.path.join(output_dir, "nasi_research_dashboard_combined.png")

    plot_stacked_bar_chart(summary_df, stacked_bar_path)
    plot_halakhic_activity_line(summary_df, halakhic_line_path)
    plot_combined_dashboard(summary_df, combined_dash_path)

    print("\n עיבוד הנתונים והפקת הגרפים הושלמו בהצלחה מלאה!")


if __name__ == "__main__":
    main()

// Chart.js visualizations for Patriarchate Thesis Website
// Faithful rendering of Graphs 1, 2, 3, 4, Stacked Bar & Role Reversal from Thesis Chapter 8

let mainChartInstance = null;
let comparatorChartInstance = null;

const COLORS = {
  intellectual: "#2563eb",   // Scholarly blue
  institutional: "#059669",  // Emerald green
  external: "#8b5cf6",       // Regal purple
  gold: "#d97706",
  slate: "#475569"
};

export function renderThesisChart(canvasId, chartType, tableData, macroData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (mainChartInstance) {
    mainChartInstance.destroy();
    mainChartInstance = null;
  }

  // Common labels (7 canonical Nesi'im)
  const labels = tableData.map((d) => d.display_name);

  // Common Chart.js RTL options
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        rtl: true,
        textDirection: "rtl",
        labels: {
          font: { family: "Assistant", size: 13, weight: "bold" },
          padding: 15
        }
      },
      tooltip: {
        rtl: true,
        textDirection: "rtl",
        titleFont: { family: "Assistant", size: 14, weight: "bold" },
        bodyFont: { family: "Assistant", size: 13 },
        padding: 12,
        callbacks: {
          label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y ?? ctx.parsed}%`
        }
      }
    },
    scales: {
      x: {
        ticks: { font: { family: "Assistant", size: 12, weight: "bold" } },
        grid: { display: false }
      },
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (val) => `${val}%`,
          font: { family: "Assistant", size: 12 }
        },
        grid: { color: "#f1f5f9" }
      }
    }
  };

  if (chartType === "chart-intellectual") {
    // GRAPH 1: Intellectual Authority Distribution
    mainChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "סמכות אינטלקטואלית־תורנית (%)",
            data: tableData.map((d) => d.intellectual_pct),
            borderColor: COLORS.intellectual,
            backgroundColor: "rgba(37, 99, 235, 0.12)",
            borderWidth: 3.5,
            pointBackgroundColor: COLORS.intellectual,
            pointRadius: 6,
            pointHoverRadius: 8,
            fill: true,
            tension: 0.25
          }
        ]
      },
      options: baseOptions
    });
  } else if (chartType === "chart-institutional") {
    // GRAPH 2: Institutional Authority Distribution
    mainChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "סמכות מוסדית־חקיקתית (%)",
            data: tableData.map((d) => d.institutional_pct),
            borderColor: COLORS.institutional,
            backgroundColor: "rgba(5, 150, 105, 0.12)",
            borderWidth: 3.5,
            pointBackgroundColor: COLORS.institutional,
            pointRadius: 6,
            pointHoverRadius: 8,
            fill: true,
            tension: 0.25
          }
        ]
      },
      options: baseOptions
    });
  } else if (chartType === "chart-external") {
    // GRAPH 3: External / Aristocratic & Political Authority Surge
    mainChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "הנהגה חיצונית־מעמדית ושררה (%)",
            data: tableData.map((d) => d.external_pct),
            borderColor: COLORS.external,
            backgroundColor: "rgba(139, 92, 246, 0.15)",
            borderWidth: 3.5,
            pointBackgroundColor: COLORS.external,
            pointRadius: 6,
            pointHoverRadius: 8,
            fill: true,
            tension: 0.25
          }
        ]
      },
      options: baseOptions
    });
  } else if (chartType === "chart-periods") {
    // GRAPH 4: Macro Periods Comparison (Period A vs Period B)
    const pA = macroData.period_a;
    const pB = macroData.period_b;

    mainChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["תקופה א': התבססות ועיצוב (הלל עד רבי)", "תקופה ב': ממלכתיות והפרדת רשויות (ר\"ג ברבי ור\"י נשיאה)"],
        datasets: [
          {
            label: "הנהגה פנימית (רוחנית-מוסדית)",
            data: [pA.internal_pct, pB.internal_pct],
            backgroundColor: COLORS.intellectual,
            borderRadius: 6
          },
          {
            label: "הנהגה חיצונית ושררה",
            data: [pA.external_pct, pB.external_pct],
            backgroundColor: COLORS.external,
            borderRadius: 6
          }
        ]
      },
      options: {
        ...baseOptions,
        scales: {
          ...baseOptions.scales,
          x: {
            ticks: { font: { family: "Assistant", size: 12, weight: "bold" } }
          }
        }
      }
    });
  } else if (chartType === "chart-stacked") {
    // 100% Stacked Bar Synthesis
    mainChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "סמכות אינטלקטואלית־תורנית",
            data: tableData.map((d) => d.intellectual_pct),
            backgroundColor: COLORS.intellectual
          },
          {
            label: "סמכות מוסדית־חקיקתית",
            data: tableData.map((d) => d.institutional_pct),
            backgroundColor: COLORS.institutional
          },
          {
            label: "הנהגה חיצונית־מעמדית",
            data: tableData.map((d) => d.external_pct),
            backgroundColor: COLORS.external
          }
        ]
      },
      options: {
        ...baseOptions,
        scales: {
          x: {
            stacked: true,
            ticks: { font: { family: "Assistant", size: 12, weight: "bold" } }
          },
          y: {
            stacked: true,
            max: 100,
            ticks: { callback: (val) => `${val}%` }
          }
        }
      }
    });
  } else if (chartType === "chart-reversal") {
    // CHART 6: Role Reversal / The Scissors Effect (תורה מול שררה)
    mainChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "סמכות אינטלקטואלית־תורנית (%)",
            data: tableData.map((d) => d.intellectual_pct),
            borderColor: COLORS.intellectual,
            backgroundColor: "rgba(37, 99, 235, 0.08)",
            borderWidth: 3,
            pointBackgroundColor: COLORS.intellectual,
            pointRadius: 5,
            tension: 0.2
          },
          {
            label: "הנהגה חיצונית ושררה (%)",
            data: tableData.map((d) => d.external_pct),
            borderColor: COLORS.external,
            backgroundColor: "rgba(139, 92, 246, 0.08)",
            borderWidth: 3,
            pointBackgroundColor: COLORS.external,
            pointRadius: 5,
            tension: 0.2
          }
        ]
      },
      options: {
        ...baseOptions,
        plugins: {
          ...baseOptions.plugins,
          tooltip: {
            ...baseOptions.plugins.tooltip,
            callbacks: {
              afterBody: (items) => {
                if (items.length >= 2) {
                  const diff = Math.abs(items[0].parsed.y - items[1].parsed.y).toFixed(1);
                  return `פער בין תורה לשררה: ${diff}%`;
                }
                return "";
              }
            }
          }
        }
      }
    });
  }
}

export function renderComparatorChart(canvasId, personA, personB) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (comparatorChartInstance) {
    comparatorChartInstance.destroy();
    comparatorChartInstance = null;
  }

  const categories = [
    "סמכות אינטלקטואלית",
    "סמכות מוסדית",
    "הנהגה חיצונית ושררה"
  ];

  comparatorChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: categories,
      datasets: [
        {
          label: personA.display_name,
          data: [personA.intellectual_pct, personA.institutional_pct, personA.external_pct],
          backgroundColor: "rgba(37, 99, 235, 0.85)",
          borderColor: "#2563eb",
          borderWidth: 1.5,
          borderRadius: 4
        },
        {
          label: personB.display_name,
          data: [personB.intellectual_pct, personB.institutional_pct, personB.external_pct],
          backgroundColor: "rgba(139, 92, 246, 0.85)",
          borderColor: "#8b5cf6",
          borderWidth: 1.5,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          rtl: true,
          textDirection: "rtl",
          labels: {
            font: { family: "Assistant", size: 12, weight: "bold" },
            padding: 12
          }
        },
        tooltip: {
          rtl: true,
          textDirection: "rtl",
          titleFont: { family: "Assistant", size: 13, weight: "bold" },
          bodyFont: { family: "Assistant", size: 12 },
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y}%`
          }
        }
      },
      scales: {
        x: {
          ticks: { font: { family: "Assistant", size: 11, weight: "bold" } },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (val) => `${val}%`,
            font: { family: "Assistant", size: 11 }
          },
          grid: { color: "#f1f5f9" }
        }
      }
    }
  });
}

/**
 * Amrapali Student Portal - Inventory & TQM Management Suite
 * Q14 Navigation Engine & Interactive Calculations
 *
 * Student: Ritik Kumar (Roll No: 2520301005, B.Tech CSE 5th Sem, Sec C)
 * Subject: BBAT104 Fundamental of Total Quality Management
 */

document.addEventListener("DOMContentLoaded", () => {
  initKeyboardNavigation();
  initTableFilter();
  initTQMTabs();
  initCalculators();
  initModals();
  initCharts();
});

// ============================================================================
// 1. Q14 KEYBOARD NAVIGATION (Target 5: Hotkey Shortcuts + F1 Help)
// ============================================================================

function initKeyboardNavigation() {
  document.addEventListener("keydown", (e) => {
    // If user is typing inside an input or textarea, don't trigger hotkeys
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
      if (e.key === "Escape") {
        closeAllModals();
      }
      return;
    }

    // F1 or Shift + ? -> Open Shortcuts Help Modal
    if (e.key === "F1" || (e.key === "?" && e.shiftKey)) {
      e.preventDefault();
      openModal("modal-shortcuts");
      return;
    }

    // Escape closes modals
    if (e.key === "Escape") {
      closeAllModals();
      return;
    }

    // Alt + Key combinations
    if (e.altKey) {
      switch (e.key.toLowerCase()) {
        case "h":
          e.preventDefault();
          window.location.href = "/";
          break;
        case "p":
          e.preventDefault();
          window.location.href = "/products";
          break;
        case "m":
          e.preventDefault();
          window.location.href = "/stock";
          break;
        case "s":
          e.preventDefault();
          window.location.href = "/suppliers";
          break;
        case "q":
          e.preventDefault();
          window.location.href = "/tqm";
          break;
        case "c":
          e.preventDefault();
          window.location.href = "/calculators";
          break;
        case "i":
          e.preventDefault();
          window.location.href = "/inspections";
          break;
        case "r":
          e.preventDefault();
          window.location.href = "/reports";
          break;
        case "v":
          e.preventDefault();
          window.location.href = "/viva-guide";
          break;
        case "u":
          e.preventDefault();
          window.location.href = "/profile";
          break;
        case "x":
          e.preventDefault();
          window.location.href = "/admin/members";
          break;
      }
    }
  });
}

// ============================================================================
// 2. LIVE TABLE FILTER / SEARCH (Instant 0-click responsiveness)
// ============================================================================

function initTableFilter() {
  const searchInputs = document.querySelectorAll(".table-search-input");
  searchInputs.forEach((input) => {
    const tableId = input.getAttribute("data-target-table");
    const table = document.getElementById(tableId);
    if (!table) return;

    input.addEventListener("input", () => {
      const query = input.value.toLowerCase().trim();
      const rows = table.querySelectorAll("tbody tr");

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  });
}

// ============================================================================
// 3. TQM 7 QC TOOLS TAB SWITCHER
// ============================================================================

function initTQMTabs() {
  const tabBtns = document.querySelectorAll(".tqm-tab-btn");
  if (!tabBtns.length) return;

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");

      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tqm-tab-pane").forEach((pane) => {
        pane.classList.remove("active");
      });

      btn.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add("active");
      }

      // If switching to pareto chart tab, trigger chart update
      if (targetId === "tab-pareto" && window.paretoChartInstance) {
        window.paretoChartInstance.update();
      }
    });
  });
}

// ============================================================================
// 4. INDUSTRY CALCULATORS (EOQ & RPN Risk Matrix)
// ============================================================================

function initCalculators() {
  // Live EOQ Calculator
  const eoqInputs = document.querySelectorAll(".eoq-calc-input");
  if (eoqInputs.length) {
    eoqInputs.forEach((inp) => {
      inp.addEventListener("input", updateEOQCalculation);
    });
    updateEOQCalculation();
  }

  // Live RPN Calculator in FMEA
  const rpnSliders = document.querySelectorAll(".rpn-calc-slider");
  if (rpnSliders.length) {
    rpnSliders.forEach((s) => {
      s.addEventListener("input", updateRPNCalculation);
    });
    updateRPNCalculation();
  }
}

function updateEOQCalculation() {
  const demandInp = document.getElementById("eoq-demand");
  const orderCostInp = document.getElementById("eoq-order-cost");
  const holdCostInp = document.getElementById("eoq-hold-cost");
  const leadTimeInp = document.getElementById("eoq-lead-time");
  const serviceLevelInp = document.getElementById("eoq-service-level");

  if (!demandInp || !orderCostInp || !holdCostInp) return;

  const D = Math.max(1, parseFloat(demandInp.value) || 0);
  const S = Math.max(0.1, parseFloat(orderCostInp.value) || 0);
  const H = Math.max(0.01, parseFloat(holdCostInp.value) || 0);
  const L = Math.max(0, parseFloat(leadTimeInp ? leadTimeInp.value : 7) || 0);
  const serviceLevel = parseFloat(serviceLevelInp ? serviceLevelInp.value : 95) || 95;

  const eoq = Math.sqrt((2 * D * S) / H);
  const roundedEOQ = Math.round(eoq);
  const ordersPerYear = (D / eoq).toFixed(1);
  const cycleDays = Math.round(365 / (D / eoq));
  const annualOrderCost = ((D / eoq) * S).toFixed(2);
  const annualHoldCost = ((eoq / 2) * H).toFixed(2);
  const totalCost = (parseFloat(annualOrderCost) + parseFloat(annualHoldCost)).toFixed(2);

  // Z-value
  const zMap = { 90: 1.28, 95: 1.645, 98: 2.05, 99: 2.33 };
  const z = zMap[serviceLevel] || 1.645;
  const dailyDemand = D / 365;
  const safetyStock = Math.round(z * 2.0 * Math.sqrt(Math.max(1, L)));
  const rop = Math.round(dailyDemand * L + safetyStock);

  setText("out-eoq", roundedEOQ.toLocaleString());
  setText("out-orders-year", ordersPerYear);
  setText("out-cycle-days", `${cycleDays} days`);
  setText("out-order-cost", `₹${annualOrderCost}`);
  setText("out-hold-cost", `₹${annualHoldCost}`);
  setText("out-total-cost", `₹${totalCost}`);
  setText("out-safety-stock", `${safetyStock} units`);
  setText("out-rop", `${rop} units`);
}

function updateRPNCalculation() {
  const sInp = document.getElementById("fmea-sev");
  const oInp = document.getElementById("fmea-occ");
  const dInp = document.getElementById("fmea-det");
  const rpnOut = document.getElementById("fmea-rpn-display");
  const riskBadge = document.getElementById("fmea-risk-badge");

  if (!sInp || !oInp || !dInp || !rpnOut) return;

  const s = parseInt(sInp.value) || 1;
  const o = parseInt(oInp.value) || 1;
  const d = parseInt(dInp.value) || 1;
  const rpn = s * o * d;

  rpnOut.textContent = rpn;
  setText("fmea-sev-val", s);
  setText("fmea-occ-val", o);
  setText("fmea-det-val", d);

  if (riskBadge) {
    riskBadge.className = "badge";
    if (rpn >= 150) {
      riskBadge.classList.add("badge-danger");
      riskBadge.textContent = "CRITICAL RISK (RPN ≥ 150) - Immediate Mitigating Action Required";
    } else if (rpn >= 100) {
      riskBadge.classList.add("badge-warning");
      riskBadge.textContent = "HIGH RISK (RPN 100-149) - Standard Operating Procedure Needed";
    } else if (rpn >= 60) {
      riskBadge.classList.add("badge-info");
      riskBadge.textContent = "MODERATE RISK (RPN 60-99) - Routine Process Monitoring";
    } else {
      riskBadge.classList.add("badge-success");
      riskBadge.textContent = "LOW RISK (RPN < 60) - Acceptable Process Control";
    }
  }
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ============================================================================
// 5. MODAL MANAGEMENT
// ============================================================================

function initModals() {
  document.querySelectorAll("[data-open-modal]").forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute("data-open-modal");
      openModal(modalId);
    });
  });

  document.querySelectorAll(".modal-close, .btn-modal-cancel").forEach((btn) => {
    btn.addEventListener("click", () => {
      closeAllModals();
    });
  });

  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        closeAllModals();
      }
    });
  });
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add("active");
  }
}

function closeAllModals() {
  document.querySelectorAll(".modal-backdrop").forEach((m) => {
    m.classList.remove("active");
  });
}

// ============================================================================
// 6. CHART.JS VISUALIZATIONS (Pareto, ABC Stratification, Category)
// ============================================================================

function initCharts() {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js not loaded, skipping charts initialization.");
    return;
  }

  // 1. Dual-Axis Pareto Chart
  const paretoCanvas = document.getElementById("paretoChartCanvas");
  if (paretoCanvas && window.PARETO_DATA) {
    const labels = window.PARETO_DATA.map((d) => d.defect_type);
    const frequencies = window.PARETO_DATA.map((d) => d.frequency);
    const cumulative = window.PARETO_DATA.map((d) => d.cumulative_pct);

    window.paretoChartInstance = new Chart(paretoCanvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Cumulative % (Pareto Curve)",
            data: cumulative,
            type: "line",
            borderColor: "#dc2626",
            backgroundColor: "rgba(220, 38, 38, 0.1)",
            borderWidth: 2.5,
            pointBackgroundColor: "#dc2626",
            pointRadius: 4,
            yAxisID: "yCumulative",
            tension: 0.2,
          },
          {
            label: "Defect Frequency (Count)",
            data: frequencies,
            backgroundColor: labels.map((_, i) =>
              cumulative[i] <= 80 ? "#0b3d91" : "#94a3b8"
            ),
            borderRadius: 4,
            yAxisID: "yFrequency",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top" },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => {
                if (ctx.datasetIndex === 0) {
                  return ctx.raw <= 80
                    ? "★ Vital Few (80% Root Cause)"
                    : "Useful Many";
                }
              },
            },
          },
        },
        scales: {
          x: {
            ticks: { maxRotation: 45, minRotation: 30, font: { size: 11 } },
            grid: { display: false },
          },
          yFrequency: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Defect Frequency" },
            beginAtZero: true,
          },
          yCumulative: {
            type: "linear",
            position: "right",
            title: { display: true, text: "Cumulative Percentage (%)" },
            min: 0,
            max: 105,
            grid: { drawOnChartArea: false },
            ticks: {
              callback: (val) => `${val}%`,
            },
          },
        },
      },
    });
  }

  // 2. ABC Inventory Distribution Doughnut
  const abcCanvas = document.getElementById("abcChartCanvas");
  if (abcCanvas && window.ABC_SUMMARY) {
    const labels = ["Class A (Vital 70%)", "Class B (Moderate 20%)", "Class C (Bulk 10%)"];
    const values = [
      window.ABC_SUMMARY.A.value,
      window.ABC_SUMMARY.B.value,
      window.ABC_SUMMARY.C.value,
    ];

    new Chart(abcCanvas, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: ["#dc2626", "#d97706", "#16a34a"],
            borderWidth: 2,
            borderColor: "#ffffff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ₹${ctx.raw.toLocaleString()}`,
            },
          },
        },
      },
    });
  }

  // 3. Category Share Chart
  const catCanvas = document.getElementById("categoryChartCanvas");
  if (catCanvas && window.CATEGORY_DATA) {
    new Chart(catCanvas, {
      type: "pie",
      data: {
        labels: window.CATEGORY_DATA.map((c) => c.category),
        datasets: [
          {
            data: window.CATEGORY_DATA.map((c) => c.total_units),
            backgroundColor: ["#0b3d91", "#00a6d6", "#16a34a", "#f59e0b", "#8b5cf6"],
            borderWidth: 2,
            borderColor: "#ffffff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
        },
      },
    });
  }
}

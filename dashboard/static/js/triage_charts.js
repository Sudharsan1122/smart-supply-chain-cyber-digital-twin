/**
 * triage_charts.js — Per-Rule F1 and Global Metrics Real-Time Charts
 */
(function () {
    "use strict";

    const REFRESH_MS = 5000;
    let rulesChart = null;
    let globalChart = null;

    // Buffer for time-series line chart
    const historyData = {
        labels: [],
        precision: [],
        recall: [],
        f1: [],
    };

    function initRulesChart() {
        const ctx = document.getElementById("rulesF1Chart");
        if (!ctx) return;

        rulesChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: [
                    "RULE-001", "RULE-002", "RULE-003", "RULE-004", "RULE-005",
                    "RULE-006", "RULE-007", "RULE-008", "RULE-009", "ML-ANOMALY"
                ],
                datasets: [{
                    label: "F1 Score",
                    data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: "rgba(185, 28, 28, 0.7)",
                    borderColor: "#ff4d4f",
                    borderWidth: 1.5,
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 400 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` F1: ${ctx.parsed.x.toFixed(3)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 1.0,
                        ticks: { color: "#8b949e" },
                        grid: { color: "#21262d" }
                    },
                    y: {
                        ticks: { color: "#c9d1d9", font: { family: "monospace", size: 11 } },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    function initGlobalChart() {
        const ctx = document.getElementById("globalMetricsChart");
        if (!ctx) return;

        // Initialize with initial timestamps
        const now = new Date();
        for (let i = 9; i >= 0; i--) {
            const t = new Date(now.getTime() - i * REFRESH_MS);
            historyData.labels.push(t.toLocaleTimeString());
            historyData.precision.push(null);
            historyData.recall.push(null);
            historyData.f1.push(null);
        }

        globalChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: historyData.labels,
                datasets: [
                    {
                        label: "Precision",
                        data: historyData.precision,
                        borderColor: "#388bfd",
                        backgroundColor: "rgba(56, 139, 253, 0.1)",
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 3,
                    },
                    {
                        label: "Recall",
                        data: historyData.recall,
                        borderColor: "#a371f7",
                        backgroundColor: "rgba(163, 113, 247, 0.1)",
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 3,
                    },
                    {
                        label: "F1 Score",
                        data: historyData.f1,
                        borderColor: "#ff4d4f",
                        backgroundColor: "rgba(255, 77, 79, 0.15)",
                        borderWidth: 2.5,
                        tension: 0.3,
                        pointRadius: 4,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 400 },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: "#c9d1d9", boxWidth: 12, padding: 14 }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 1.05,
                        ticks: { color: "#8b949e" },
                        grid: { color: "#21262d" }
                    },
                    x: {
                        ticks: { color: "#8b949e", font: { size: 10 } },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    async function updateRules() {
        try {
            const res = await fetch("/live/triage/rules").then(r => r.json());
            const rules = res.rules || [];
            if (!rulesChart) return;

            const map = {};
            rules.forEach(r => {
                map[r.rule_id] = r.f1 || 0;
            });

            const labels = rulesChart.data.labels;
            const vals = labels.map(l => map[l] !== undefined ? map[l] : 0);
            rulesChart.data.datasets[0].data = vals;
            rulesChart.update();
        } catch (e) {
            console.warn("Failed to fetch triage rules metrics", e);
        }
    }

    async function updateGlobalMetrics() {
        try {
            const data = await fetch("/live/triage").then(r => r.json());
            const m = data.metrics || {};

            // Update KPI counters in DOM
            const elTotal = document.getElementById("kpi-total-triaged");
            const elP = document.getElementById("kpi-precision");
            const elR = document.getElementById("kpi-recall");
            const elF1 = document.getElementById("kpi-f1");

            if (elTotal && m.total !== undefined) elTotal.innerText = m.total;
            if (elP && m.precision !== undefined) elP.innerText = Number(m.precision).toFixed(2);
            if (elR && m.recall !== undefined) elR.innerText = Number(m.recall).toFixed(2);
            if (elF1 && m.f1 !== undefined) elF1.innerText = Number(m.f1).toFixed(2);

            // Update Confusion Matrix
            const cmTp = document.getElementById("cm-tp");
            const cmFp = document.getElementById("cm-fp");
            const cmFn = document.getElementById("cm-fn");
            const cmTn = document.getElementById("cm-tn");
            if (cmTp && m.tp !== undefined) cmTp.innerText = m.tp;
            if (cmFp && m.fp !== undefined) cmFp.innerText = m.fp;
            if (cmFn && m.fn !== undefined) cmFn.innerText = m.fn;
            if (cmTn && m.tn !== undefined) cmTn.innerText = m.tn;

            // Push to line chart buffer
            if (globalChart) {
                const nowStr = new Date().toLocaleTimeString();
                historyData.labels.push(nowStr);
                historyData.precision.push(m.precision || 0);
                historyData.recall.push(m.recall || 0);
                historyData.f1.push(m.f1 || 0);

                if (historyData.labels.length > 20) {
                    historyData.labels.shift();
                    historyData.precision.shift();
                    historyData.recall.shift();
                    historyData.f1.shift();
                }

                globalChart.data.labels = historyData.labels;
                globalChart.data.datasets[0].data = historyData.precision;
                globalChart.data.datasets[1].data = historyData.recall;
                globalChart.data.datasets[2].data = historyData.f1;
                globalChart.update();
            }
        } catch (e) {
            console.warn("Failed to fetch global triage metrics", e);
        }
    }

    function boot() {
        initRulesChart();
        initGlobalChart();
        updateRules();
        updateGlobalMetrics();
        setInterval(() => {
            updateRules();
            updateGlobalMetrics();
        }, REFRESH_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();

/**
 * live_charts.js — Real-time Chart.js rendering for the Live Fleet dashboard.
 * Supports dynamic filtering by window (minutes), severity, and asset type.
 */
window.liveCharts = (function () {
    "use strict";

    let riskChart = null;
    let detectionsChart = null;
    let isInitialized = false;

    let currentFilters = {
        window: "30",
        severity: "",
        type: ""
    };

    const PALETTE = [
        { border: "#f85149", bg: "rgba(248, 81, 73, 0.15)" },   // Red / danger
        { border: "#d29922", bg: "rgba(210, 153, 34, 0.15)" },  // Amber / warning
        { border: "#58a6ff", bg: "rgba(88, 166, 255, 0.15)" },  // Blue / primary
        { border: "#a371f7", bg: "rgba(163, 113, 247, 0.15)" }, // Purple
        { border: "#3fb950", bg: "rgba(63, 185, 80, 0.15)" },   // Green
    ];

    function initRiskChart(ctx) {
        if (!ctx) return;
        riskChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 400 },
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: "#e6edf3", boxWidth: 12, padding: 10, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: "#161b22",
                        titleColor: "#e6edf3",
                        bodyColor: "#8b949e",
                        borderColor: "#30363d",
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#8b949e", maxTicksLimit: 10, font: { size: 10 } },
                        grid: { color: "#21262d" }
                    },
                    y: {
                        min: 0,
                        suggestedMax: 70,
                        ticks: { color: "#8b949e", font: { size: 10 } },
                        grid: { color: "#21262d" }
                    }
                }
            }
        });
    }

    function initDetectionsChart(ctx) {
        if (!ctx) return;
        detectionsChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Detections",
                        data: [],
                        backgroundColor: "#f0883e",
                        borderRadius: 3,
                        maxBarThickness: 16
                    },
                    {
                        label: "IOCs",
                        data: [],
                        backgroundColor: "#bc8cff",
                        borderRadius: 3,
                        maxBarThickness: 16
                    },
                    {
                        label: "Telemetry (x0.01)",
                        data: [],
                        type: "line",
                        borderColor: "#58a6ff",
                        backgroundColor: "rgba(88, 166, 255, 0.1)",
                        fill: true,
                        tension: 0.25,
                        pointRadius: 2,
                        yAxisID: "y1"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 350 },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: "#e6edf3", boxWidth: 12, padding: 10, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: "#161b22",
                        titleColor: "#e6edf3",
                        bodyColor: "#8b949e",
                        borderColor: "#30363d",
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#8b949e", maxTicksLimit: 10, font: { size: 10 } },
                        grid: { color: "#21262d" }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: "#8b949e", font: { size: 10 }, precision: 0 },
                        grid: { color: "#21262d" }
                    },
                    y1: {
                        position: "right",
                        beginAtZero: true,
                        display: false,
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }

    function init() {
        const riskCanvas = document.getElementById("risk-chart");
        const detCanvas = document.getElementById("detections-chart");
        if (riskCanvas) initRiskChart(riskCanvas.getContext("2d"));
        if (detCanvas) initDetectionsChart(detCanvas.getContext("2d"));
        isInitialized = true;
        update();
    }

    function setFilters(filters) {
        currentFilters = Object.assign(currentFilters, filters);
    }

    async function update() {
        if (!isInitialized) return;
        try {
            const query = new URLSearchParams({
                window: currentFilters.window || "30",
                severity: currentFilters.severity || "",
                type: currentFilters.type || ""
            });

            const resp = await fetch("/live/charts?" + query.toString());
            if (!resp.ok) return;
            const data = await resp.json();
            const timestamps = data.timestamps || [];

            // 1. Update Risk Line Chart
            if (riskChart && data.risk_history) {
                const assets = data.risk_history.assets || [];
                const series = data.risk_history.series || {};

                riskChart.data.labels = timestamps;
                riskChart.data.datasets = assets.map((asset, idx) => {
                    const color = PALETTE[idx % PALETTE.length];
                    return {
                        label: asset,
                        data: series[asset] || [],
                        borderColor: color.border,
                        backgroundColor: color.bg,
                        tension: 0.3,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        fill: false
                    };
                });
                riskChart.update("none");
            }

            // 2. Update Detections & IOCs Activity Bar Chart
            if (detectionsChart) {
                detectionsChart.data.labels = timestamps;
                detectionsChart.data.datasets[0].data = data.detections || [];
                detectionsChart.data.datasets[1].data = data.iocs || [];
                // Scale telemetry by 0.01 for compact dual-axis representation
                detectionsChart.data.datasets[2].data = (data.telemetry || []).map(v => Math.round(v * 0.01));
                detectionsChart.update("none");
            }
        } catch (err) {
            console.warn("Error updating live charts:", err);
        }
    }

    return {
        init: init,
        update: update,
        setFilters: setFilters
    };
})();

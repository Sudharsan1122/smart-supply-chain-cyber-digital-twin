/**
 * dashboard.js — Real-Time Live Monitoring & Polling Controller
 * Manages targeted AJAX updates, auto-scrolling events, filter listeners, and report export.
 */
(function () {
    "use strict";

    const cfg = window.DASHBOARD || { activeTab: "live", refreshSeconds: 3 };
    const REFRESH_MS = (cfg.refreshSeconds || 3) * 1000;
    const knownEventIds = new Set();

    function setStatus(online) {
        const badge = document.getElementById("live-badge");
        if (badge) {
            const dot = badge.querySelector(".dot");
            if (online) {
                badge.style.color = "#3fb950";
                badge.style.borderColor = "rgba(63, 185, 80, 0.3)";
                badge.style.background = "rgba(35, 134, 54, 0.15)";
                if (dot) dot.style.background = "#3fb950";
            } else {
                badge.style.color = "#f85149";
                badge.style.borderColor = "rgba(248, 81, 73, 0.3)";
                badge.style.background = "rgba(248, 81, 73, 0.15)";
                if (dot) dot.style.background = "#f85149";
            }
        }
    }

    function animateUpdate(el, newValue) {
        if (!el) return;
        const current = el.textContent.trim();
        if (current !== String(newValue).trim()) {
            el.textContent = newValue;
            el.classList.remove("updating");
            void el.offsetWidth; // trigger reflow
            el.classList.add("updating");
        }
    }

    // -----------------------------------------------------------------------
    // Feature 5: Download Report as JSON
    // -----------------------------------------------------------------------
    async function downloadReport() {
        const btn = document.getElementById("download-report");
        if (!btn) return;
        btn.disabled = true;
        btn.textContent = "Generating...";
        try {
            const [summary, charts, events, topology] = await Promise.all([
                fetch("/live/summary").then(r => r.json()).catch(() => ({})),
                fetch("/live/charts").then(r => r.json()).catch(() => ({})),
                fetch("/live/events").then(r => r.json()).catch(() => ([])),
                fetch("/live/topology").then(r => r.json()).catch(() => ({})),
            ]);
            const report = {
                project: "Smart Supply Chain Cyber Digital Twin",
                generated_at: new Date().toISOString(),
                version: "1.0.0",
                summary,
                charts,
                events,
                topology
            };
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `sscdt-report-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Failed to generate report:", err);
            alert("Could not generate report. Please try again.");
        } finally {
            btn.disabled = false;
            btn.textContent = "Download Report";
        }
    }

    // -----------------------------------------------------------------------
    // Feature 4: Global Filter Bar Listeners
    // -----------------------------------------------------------------------
    function initFilterBar() {
        const winSelect = document.getElementById("filter-window");
        const sevSelect = document.getElementById("filter-severity");
        const typeSelect = document.getElementById("filter-type");

        function onFilterChange() {
            const windowVal = winSelect ? winSelect.value : "30";
            const severityVal = sevSelect ? sevSelect.value : "";
            const typeVal = typeSelect ? typeSelect.value : "";

            if (window.liveCharts && window.liveCharts.setFilters) {
                window.liveCharts.setFilters({
                    window: windowVal,
                    severity: severityVal,
                    type: typeVal
                });
                window.liveCharts.update();
            }
        }

        if (winSelect) winSelect.addEventListener("change", onFilterChange);
        if (sevSelect) sevSelect.addEventListener("change", onFilterChange);
        if (typeSelect) typeSelect.addEventListener("change", onFilterChange);
    }

    // -----------------------------------------------------------------------
    // Feature 2: Close Detail Panel
    // -----------------------------------------------------------------------
    function initDetailPanel() {
        const closeBtn = document.getElementById("panel-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                const panel = document.getElementById("detail-panel");
                if (panel) panel.classList.remove("open");
            });
        }
    }

    // -----------------------------------------------------------------------
    // Tab: Live Fleet
    // -----------------------------------------------------------------------
    async function refreshLiveTab() {
        try {
            const resp = await fetch("/live/summary");
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            setStatus(true);

            // 1. KPI counters
            animateUpdate(document.getElementById("kpi-assets"), (data.twin && data.twin.nodes) || 0);
            animateUpdate(document.getElementById("kpi-edges"), (data.twin && data.twin.edges) || 0);

            const mqttEl = document.getElementById("kpi-mqtt");
            if (mqttEl) {
                const isMqtt = !!(data.mqtt && data.mqtt.connected);
                animateUpdate(mqttEl, isMqtt ? "connected" : "offline");
                mqttEl.className = "kpi-value " + (isMqtt ? "good" : "bad");
            }

            const dbEl = document.getElementById("kpi-db");
            if (dbEl) {
                const dbStatus = (data.ready && data.ready.checks && data.ready.checks.database) || "unknown";
                animateUpdate(dbEl, dbStatus);
                dbEl.className = "kpi-value " + (dbStatus === "connected" ? "good" : "bad");
            }

            const twinEl = document.getElementById("kpi-twin");
            if (twinEl) {
                const twinStatus = (data.ready && data.ready.checks && data.ready.checks.twin) || "ready";
                animateUpdate(twinEl, twinStatus);
                twinEl.className = "kpi-value good";
            }

            // 2. Top 10 Risk Table
            const riskTbody = document.getElementById("risk-table-body");
            if (riskTbody && Array.isArray(data.risk_top)) {
                if (data.risk_top.length === 0) {
                    riskTbody.innerHTML = '<tr><td colspan="6" class="muted">No risk scores computed yet.</td></tr>';
                } else {
                    riskTbody.innerHTML = data.risk_top.map((a, idx) => {
                        const score = Number(a.score || 0).toFixed(1);
                        let badgeClass = "safe";
                        if (score >= 75) badgeClass = "danger";
                        else if (score >= 50) badgeClass = "warn";
                        else if (score >= 25) badgeClass = "info";

                        const factors = Object.entries(a.factors || {})
                            .filter(([_, v]) => v > 0.1)
                            .map(([k, v]) => `<span class="factor-chip">${k}: ${Number(v).toFixed(1)}</span>`)
                            .join(" ");

                        const scoredAt = (a.scored_at || "").replace("T", " ").slice(0, 19);

                        return `
                            <tr>
                                <td>${idx + 1}</td>
                                <td class="mono font-bold">${a.asset_id}</td>
                                <td><span class="pill">${a.asset_type}</span></td>
                                <td><span class="badge ${badgeClass}">${score}</span></td>
                                <td class="small muted">${factors || '---'}</td>
                                <td class="muted small">${scoredAt || '---'}</td>
                            </tr>
                        `;
                    }).join("");
                }
            }

            // 3. State Summary Chips & Asset Grid
            const stateChips = document.getElementById("state-summary-chips");
            if (stateChips && data.state_summary && data.state_summary.by_state) {
                stateChips.innerHTML = Object.entries(data.state_summary.by_state)
                    .map(([s, count]) => `<span class="chip" data-state="${s}">${s}: <b>${count}</b></span>`)
                    .join(" ");
            }

            if (data.asset_states) {
                Object.entries(data.asset_states).forEach(([aid, st]) => {
                    const card = document.getElementById("asset-card-" + aid);
                    if (card) {
                        const badge = card.querySelector(".asset-state-badge");
                        if (badge && st.state) {
                            badge.textContent = st.state;
                            badge.className = "badge state-" + st.state + " asset-state-badge";
                        }
                    }
                });
            }

        } catch (err) {
            console.warn("Failed to refresh live summary:", err);
            setStatus(false);
        }

        // 4. Feature 3: Auto-scroll event stream
        await refreshLiveEvents();

        // 5. Update Charts & Topology
        if (window.liveCharts) window.liveCharts.update();
        if (window.liveTopology) window.liveTopology.update();
    }

    // -----------------------------------------------------------------------
    // Feature 3: Auto-Scroll Event Stream with Prepend & Slide-In Animation
    // -----------------------------------------------------------------------
    async function refreshLiveEvents() {
        const list = document.getElementById("events-list");
        if (!list) return;

        try {
            const resp = await fetch("/live/events");
            if (!resp.ok) return;
            const events = await resp.json();
            if (!Array.isArray(events) || events.length === 0) return;

            const badge = document.getElementById("event-count-badge");
            if (badge) badge.textContent = events.length + " Events";

            const isInitial = knownEventIds.size === 0;

            // Events arrive sorted newest first. Reverse to prepend in order.
            const toPrepend = [];
            events.forEach(e => {
                if (!knownEventIds.has(e.id)) {
                    knownEventIds.add(e.id);
                    toPrepend.push(e);
                }
            });

            toPrepend.reverse().forEach(e => {
                const li = document.createElement("li");
                li.className = "event-row" + (isInitial ? "" : " new");
                li.dataset.id = e.id;
                const ts = (e.timestamp || "").replace("T", " ").slice(0, 19);

                li.innerHTML = `
                    <span class="badge sev-${e.severity}">${e.severity}</span>
                    <span class="mono event-type">${e.event_type}</span>
                    <span class="event-desc">${e.description || 'Event logged'}</span>
                    <span class="muted small event-time">${ts}</span>
                `;

                const empty = list.querySelector(".empty-state");
                if (empty) list.removeChild(empty);

                list.prepend(li);

                if (!isInitial) {
                    setTimeout(() => li.classList.remove("new"), 500);
                }
            });

            // Keep list bounded to 25 items
            while (list.children.length > 25) {
                list.removeChild(list.lastChild);
            }

        } catch (err) {
            console.warn("Failed to refresh live events:", err);
        }
    }

    // -----------------------------------------------------------------------
    // Tab: Attack Stories
    // -----------------------------------------------------------------------
    async function refreshStoriesTab() {
        const tbody = document.getElementById("stories-table-body");
        if (!tbody) return;

        try {
            const resp = await fetch("/live/stories");
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const stories = await resp.json();
            setStatus(true);

            const badge = document.getElementById("stories-count-badge");
            if (badge) badge.textContent = stories.length + " Stories";

            if (stories.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="muted">No attack stories recorded yet.</td></tr>';
            } else {
                tbody.innerHTML = stories.map(s => {
                    const started = (s.created_at || "").replace("T", " ").slice(0, 19);
                    return `
                        <tr>
                            <td class="mono small">${(s.attack_id || '').slice(0, 16)}</td>
                            <td class="font-bold">${s.title || 'Untitled'}</td>
                            <td><span class="badge state-${s.status}">${s.status}</span></td>
                            <td class="muted small">${started || '---'}</td>
                        </tr>
                    `;
                }).join("");
            }
        } catch (err) {
            console.warn("Failed to refresh stories:", err);
            setStatus(false);
        }
    }

    // -----------------------------------------------------------------------
    // Tab: Threat Intel
    // -----------------------------------------------------------------------
    async function refreshThreatIntelTab() {
        const tbody = document.getElementById("iocs-table-body");
        if (!tbody) return;

        try {
            const resp = await fetch("/live/threat-intel");
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            setStatus(true);

            animateUpdate(document.getElementById("kpi-total-iocs"), (data.summary && data.summary.total) || 0);
            animateUpdate(document.getElementById("kpi-enriched-iocs"), (data.cache && data.cache.enriched_iocs) || 0);
            animateUpdate(document.getElementById("kpi-unenriched-iocs"), (data.cache && data.cache.unenriched_iocs) || 0);

            const chips = document.getElementById("ioc-chips");
            if (chips && data.summary && data.summary.by_type) {
                chips.innerHTML = Object.entries(data.summary.by_type)
                    .map(([t, count]) => `<span class="chip">${t}: <b>${count}</b></span>`)
                    .join(" ");
            }

            const iocs = data.iocs || [];
            const badge = document.getElementById("iocs-count-badge");
            if (badge) badge.textContent = iocs.length + " Indicators";

            if (iocs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="muted">No threat indicators extracted yet.</td></tr>';
            } else {
                tbody.innerHTML = iocs.map(i => {
                    const lastSeen = (i.last_seen || "").replace("T", " ").slice(0, 19);
                    let confHtml = '<span class="muted">---</span>';
                    if (i.confidence !== null && i.confidence !== undefined) {
                        const conf = Number(i.confidence);
                        const cClass = conf >= 0.7 ? "danger" : conf >= 0.4 ? "warn" : "safe";
                        confHtml = `<span class="badge ${cClass}">${conf.toFixed(2)}</span>`;
                    }

                    return `
                        <tr>
                            <td class="mono small font-bold">${i.value}</td>
                            <td><span class="pill">${i.ioc_type}</span></td>
                            <td class="small">${i.source || 'telemetry'}</td>
                            <td>${confHtml}</td>
                            <td class="muted small">${lastSeen || '---'}</td>
                        </tr>
                    `;
                }).join("");
            }
        } catch (err) {
            console.warn("Failed to refresh threat intel:", err);
            setStatus(false);
        }
    }

    // -----------------------------------------------------------------------
    // Tab: Triage
    // -----------------------------------------------------------------------
    async function refreshTriageTab() {
        const tbody = document.getElementById("triage-table-body");
        if (!tbody) return;

        try {
            const resp = await fetch("/live/triage");
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            setStatus(true);

            const m = data.metrics || {};
            animateUpdate(document.getElementById("kpi-total-triaged"), m.total || 0);
            animateUpdate(document.getElementById("kpi-precision"), Number(m.precision || 0).toFixed(2));
            animateUpdate(document.getElementById("kpi-recall"), Number(m.recall || 0).toFixed(2));
            animateUpdate(document.getElementById("kpi-f1"), Number(m.f1 || 0).toFixed(2));

            animateUpdate(document.getElementById("cm-tp"), m.tp || 0);
            animateUpdate(document.getElementById("cm-fp"), m.fp || 0);
            animateUpdate(document.getElementById("cm-fn"), m.fn || 0);
            animateUpdate(document.getElementById("cm-tn"), m.tn || 0);

            const recent = data.recent || [];
            const badge = document.getElementById("triage-count-badge");
            if (badge) badge.textContent = recent.length + " Records";

            if (recent.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="muted">No triage decisions recorded yet.</td></tr>';
            } else {
                tbody.innerHTML = recent.map(t => {
                    const vClass = t.verdict === 'TP' ? 'safe' : t.verdict === 'FP' ? 'warn' : 'info';
                    const conf = t.confidence !== null && t.confidence !== undefined ? Number(t.confidence).toFixed(2) : '---';
                    return `
                        <tr>
                            <td class="mono small">${t.detection_id}</td>
                            <td class="mono small">${t.rule_id || 'ML-model'}</td>
                            <td><span class="badge sev-${t.severity}">${t.severity}</span></td>
                            <td><span class="badge ${vClass}">${t.verdict}</span></td>
                            <td>${conf}</td>
                        </tr>
                    `;
                }).join("");
            }
        } catch (err) {
            console.warn("Failed to refresh triage:", err);
            setStatus(false);
        }
    }

    // -----------------------------------------------------------------------
    // Master Dispatcher & Poller
    // -----------------------------------------------------------------------
    function poll() {
        const tab = cfg.activeTab || "live";
        if (tab === "live") {
            refreshLiveTab();
        } else if (tab === "stories") {
            refreshStoriesTab();
        } else if (tab === "threat-intel") {
            refreshThreatIntelTab();
        } else if (tab === "triage") {
            refreshTriageTab();
        }
    }

    // Initial Execution
    document.addEventListener("DOMContentLoaded", () => {
        const downloadBtn = document.getElementById("download-report");
        if (downloadBtn) {
            downloadBtn.addEventListener("click", downloadReport);
        }

        if (cfg.activeTab === "live") {
            initFilterBar();
            initDetailPanel();
            if (window.liveCharts) window.liveCharts.init();
            if (window.liveTopology) window.liveTopology.init();
        }
        poll();
        setInterval(poll, REFRESH_MS);
    });

})();

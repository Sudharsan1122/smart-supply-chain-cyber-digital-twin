/**
 * live_topology.js — Interactive D3 force-directed digital twin topology visualization.
 * Supports zoom, pan, drag-and-drop, hover tooltips, and click-to-detail sidebar panel.
 */
window.liveTopology = (function () {
    "use strict";

    let simulation = null;
    let svg = null;
    let g = null;
    let nodeGroup = null;
    let linkGroup = null;
    let nodesData = [];
    let linksData = [];
    let isInitialized = false;

    const TYPE_COLORS = {
        "TRUCK": "#3fb950",
        "WAREHOUSE": "#58a6ff",
        "VEHICLE_GATEWAY": "#d29922",
        "API_GATEWAY": "#a371f7",
        "APPLICATION": "#bc8cff",
        "AUTH_SYSTEM": "#f85149",
        "DATABASE": "#79c0ff",
        "SENSOR": "#39c5cf"
    };

    function getNodeColor(d) {
        return TYPE_COLORS[d.asset_type] || "#8b949e";
    }

    function getNodeRadius(d) {
        const base = 8;
        const riskBonus = Math.min(14, (d.risk_score || 0) * 0.22);
        return base + riskBonus;
    }

    function getNodeStroke(d) {
        if ((d.risk_score || 0) >= 50) return "#f85149";
        if ((d.risk_score || 0) >= 25) return "#d29922";
        return "#21262d";
    }

    function onNodeClick(event, d) {
        event.stopPropagation();
        const panel = document.getElementById("detail-panel");
        if (!panel) return;
        panel.classList.add("open");

        const idEl = panel.querySelector(".panel-asset-id");
        const typeEl = panel.querySelector(".panel-type");
        const nameEl = panel.querySelector(".panel-name");
        const stateEl = panel.querySelector(".panel-state");
        const healthEl = panel.querySelector(".panel-health");
        const riskEl = panel.querySelector(".panel-risk");
        const detEl = panel.querySelector(".panel-detection");
        const neighEl = panel.querySelector(".panel-neighbors");

        if (idEl) idEl.textContent = d.asset_id;
        if (typeEl) typeEl.textContent = d.asset_type;
        if (nameEl) nameEl.textContent = d.name || "Loading...";
        if (stateEl) stateEl.textContent = d.state || "—";
        if (healthEl) healthEl.textContent = "—";
        if (riskEl) riskEl.textContent = (d.risk_score || 0).toFixed(1);
        if (detEl) detEl.textContent = "Loading detection info...";
        if (neighEl) neighEl.textContent = "Loading topology hierarchy...";

        Promise.all([
            fetch(`/live/asset/${d.asset_id}`).then(r => r.json()).catch(() => ({})),
            fetch(`/live/risk/${d.asset_id}`).then(r => r.json()).catch(() => ({})),
        ]).then(([asset, risk]) => {
            if (idEl) idEl.textContent = asset.asset_id || d.asset_id;
            if (typeEl) typeEl.textContent = asset.asset_type || d.asset_type;
            if (nameEl) nameEl.textContent = asset.name || "—";

            const st = (asset.state && asset.state.state) || d.state || "unknown";
            const hl = (asset.state && asset.state.health) || "good";
            if (stateEl) {
                stateEl.textContent = st;
                stateEl.className = "badge state-" + st + " panel-state";
            }
            if (healthEl) {
                healthEl.textContent = hl;
                healthEl.className = "pill asset-health health-" + hl + " panel-health";
            }

            const score = Number(risk.score !== undefined ? risk.score : (d.risk_score || 0)).toFixed(1);
            if (riskEl) {
                riskEl.textContent = score;
                let rClass = "safe";
                if (score >= 75) rClass = "danger";
                else if (score >= 50) rClass = "warn";
                else if (score >= 25) rClass = "info";
                riskEl.className = "badge " + rClass + " panel-risk";
            }

            const det = asset.latest_detection;
            if (detEl) {
                if (det) {
                    detEl.innerHTML = `<span class="badge sev-${det.severity}">${det.severity}</span> <b>${det.rule_id || 'DET'}</b>: ${det.description || 'Anomaly detected'}`;
                } else {
                    detEl.textContent = "No recent detections";
                }
            }

            const graph = asset.graph || {};
            const parents = (graph.parents || []).join(", ") || "None";
            const children = (graph.children || []).join(", ") || "None";
            if (neighEl) {
                neighEl.innerHTML = `Parents: <b>${parents}</b><br>Children: <b>${children}</b>`;
            }
        });
    }

    function init() {
        const svgEl = document.getElementById("topology-svg");
        if (!svgEl || !window.d3) return;

        const width = svgEl.clientWidth || 600;
        const height = svgEl.clientHeight || 360;

        svg = d3.select("#topology-svg")
            .attr("viewBox", [0, 0, width, height]);

        svg.selectAll("*").remove();

        g = svg.append("g");
        svg.call(d3.zoom()
            .scaleExtent([0.3, 3])
            .on("zoom", (event) => g.attr("transform", event.transform)));

        linkGroup = g.append("g").attr("class", "links");
        nodeGroup = g.append("g").attr("class", "nodes");

        simulation = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.asset_id).distance(55))
            .force("charge", d3.forceManyBody().strength(-110))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => getNodeRadius(d) + 5));

        isInitialized = true;
        render();
    }

    async function render() {
        if (!isInitialized) return;
        try {
            const resp = await fetch("/live/topology");
            if (!resp.ok) return;
            const data = await resp.json();

            const rawNodes = data.nodes || [];
            const rawEdges = data.edges || [];

            const nodeMap = new Map(nodesData.map(n => [n.asset_id, n]));
            nodesData = rawNodes.map(d => {
                const old = nodeMap.get(d.asset_id);
                return {
                    ...d,
                    x: old ? old.x : undefined,
                    y: old ? old.y : undefined,
                    vx: old ? old.vx : undefined,
                    vy: old ? old.vy : undefined
                };
            });

            const assetSet = new Set(nodesData.map(n => n.asset_id));
            linksData = rawEdges
                .filter(e => assetSet.has(e.source) && assetSet.has(e.target))
                .map(e => ({ ...e }));

            // Update Links
            const links = linkGroup.selectAll("line")
                .data(linksData, d => `${d.source}-${d.target}`);

            links.exit().remove();
            const linksEnter = links.enter().append("line")
                .attr("stroke", "#30363d")
                .attr("stroke-width", 1.5)
                .attr("stroke-opacity", 0.7);

            const allLinks = linksEnter.merge(links);

            // Update Nodes
            const tooltip = document.getElementById("topology-tooltip");
            const nodes = nodeGroup.selectAll("g.node")
                .data(nodesData, d => d.asset_id);

            nodes.exit().remove();

            const nodesEnter = nodes.enter().append("g")
                .attr("class", "node")
                .style("cursor", "pointer")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            nodesEnter.append("circle");
            nodesEnter.append("text")
                .attr("dy", -12)
                .attr("text-anchor", "middle")
                .attr("fill", "#8b949e")
                .attr("font-size", "9px")
                .attr("font-family", "monospace");

            const allNodes = nodesEnter.merge(nodes);

            allNodes.select("circle")
                .transition().duration(300)
                .attr("r", d => getNodeRadius(d))
                .attr("fill", d => getNodeColor(d))
                .attr("stroke", d => getNodeStroke(d))
                .attr("stroke-width", d => (d.risk_score >= 25 ? 2.5 : 1));

            allNodes.select("text")
                .text(d => d.asset_id);

            // Hover interactions & Click-to-Detail
            allNodes
                .on("mouseover", (event, d) => {
                    if (!tooltip) return;
                    tooltip.innerHTML = `
                        <div class="tooltip-id"><strong>${d.asset_id}</strong> (${d.asset_type})</div>
                        <div>Name: ${d.name || '---'}</div>
                        <div>State: <span class="badge state-${d.state}">${d.state}</span></div>
                        <div>Risk: <span class="badge ${d.risk_score >= 50 ? 'danger' : d.risk_score >= 25 ? 'warn' : 'safe'}">${d.risk_score.toFixed(1)}</span></div>
                        <div class="small muted" style="margin-top:4px;">Click to view full asset details</div>
                    `;
                    tooltip.style.opacity = "1";
                    tooltip.style.left = (event.offsetX + 15) + "px";
                    tooltip.style.top = (event.offsetY - 10) + "px";
                })
                .on("mousemove", (event) => {
                    if (!tooltip) return;
                    tooltip.style.left = (event.offsetX + 15) + "px";
                    tooltip.style.top = (event.offsetY - 10) + "px";
                })
                .on("mouseout", () => {
                    if (tooltip) tooltip.style.opacity = "0";
                })
                .on("click", onNodeClick);

            // Update Simulation
            simulation.nodes(nodesData);
            simulation.force("link").links(linksData);
            simulation.alpha(0.3).restart();

            simulation.on("tick", () => {
                allLinks
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                allNodes
                    .attr("transform", d => `translate(${d.x},${d.y})`);
            });

        } catch (err) {
            console.warn("Error rendering live topology:", err);
        }
    }

    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    return {
        init: init,
        update: render
    };
})();

/**
 * blast_radius_viz.js — D3 Force-Directed Blast Radius Graph
 */
(function () {
    "use strict";

    function depthColor(depth, isSource) {
        if (isSource || depth === 0) return "#b91c1c"; // Crimson
        if (depth === 1) return "#ea580c";             // Orange
        if (depth === 2) return "#d97706";             // Amber
        return "#10b981";                              // Emerald
    }

    window.renderBlastRadius = function (data, containerId) {
        const svg = d3.select(containerId);
        if (svg.empty()) return;

        svg.selectAll("*").remove();

        const el = svg.node();
        const width = el.clientWidth || 800;
        const height = el.clientHeight || 480;

        if (!data || !data.source_asset_id) {
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "#8b949e")
                .attr("font-size", "14px")
                .text("No blast radius data available.");
            return;
        }

        const sourceId = data.source_asset_id;
        const impacted = data.impacted || [];

        // Build Nodes
        const nodeMap = {};
        const nodes = [];

        // Source node
        const sourceNode = {
            id: sourceId,
            asset_id: sourceId,
            depth: 0,
            impact_score: 100,
            isSource: true,
            radius: 26,
        };
        nodeMap[sourceId] = sourceNode;
        nodes.push(sourceNode);

        // Impacted nodes
        impacted.forEach(imp => {
            const aid = imp.asset_id;
            if (!nodeMap[aid]) {
                const r = Math.max(14, Math.min(30, (imp.impact_score || 30) / 3 + 8));
                const n = {
                    id: aid,
                    asset_id: aid,
                    depth: imp.depth || 1,
                    impact_score: imp.impact_score || 0,
                    isSource: false,
                    path: imp.path || [sourceId, aid],
                    radius: r,
                };
                nodeMap[aid] = n;
                nodes.push(n);
            }
        });

        // Build Links based on path or direct connection to parent
        const links = [];
        impacted.forEach(imp => {
            const path = imp.path || [sourceId, imp.asset_id];
            for (let i = 0; i < path.length - 1; i++) {
                const u = path[i];
                const v = path[i + 1];
                if (nodeMap[u] && nodeMap[v]) {
                    const linkKey = `${u}->${v}`;
                    if (!links.some(l => l.key === linkKey)) {
                        links.push({ source: u, target: v, key: linkKey, depth: imp.depth });
                    }
                }
            }
        });

        // If no links constructed, connect all impacted directly to source
        if (links.length === 0 && impacted.length > 0) {
            impacted.forEach(imp => {
                links.push({ source: sourceId, target: imp.asset_id, depth: imp.depth });
            });
        }

        // SVG main group with zoom
        const g = svg.append("g");

        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
        svg.call(zoom);

        // Tooltip
        let tooltip = d3.select("#blast-tooltip");
        if (tooltip.empty()) {
            tooltip = d3.select("body").append("div")
                .attr("id", "blast-tooltip")
                .attr("class", "blast-tooltip");
        }

        // Force Simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(d => d.depth * 55 + 50))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.radius + 16));

        // Draw Links
        const link = g.append("g")
            .attr("class", "blast-links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke", "#30363d")
            .attr("stroke-width", 2)
            .attr("stroke-dasharray", d => d.depth > 1 ? "4,4" : null);

        // Draw Nodes
        const node = g.append("g")
            .attr("class", "blast-nodes")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Node Circles
        node.append("circle")
            .attr("r", d => d.radius)
            .attr("fill", d => depthColor(d.depth, d.isSource))
            .attr("stroke", d => d.isSource ? "#ff4d4f" : "#ffffff")
            .attr("stroke-width", d => d.isSource ? 3 : 1.5)
            .attr("stroke-opacity", 0.9)
            .attr("cursor", "pointer")
            .style("filter", d => d.isSource ? "drop-shadow(0 0 8px rgba(185, 28, 28, 0.8))" : null);

        // Node Labels
        node.append("text")
            .attr("dy", d => d.radius + 14)
            .attr("text-anchor", "middle")
            .attr("fill", "#e6edf3")
            .attr("font-size", "11px")
            .attr("font-family", "ui-monospace, monospace")
            .attr("font-weight", d => d.isSource ? "bold" : "normal")
            .text(d => d.id);

        // Tooltip & Click Handlers
        node.on("mouseover", (event, d) => {
            tooltip.style("display", "block")
                .html(`
                    <div style="font-weight: bold; margin-bottom: 2px;">${d.id} ${d.isSource ? "(Root Target)" : ""}</div>
                    <div>Depth Level: <span style="color: #58a6ff;">${d.depth}</span></div>
                    <div>Impact Score: <span style="color: #f85149;">${d.isSource ? "100.0" : Number(d.impact_score).toFixed(1)}%</span></div>
                    ${d.path ? `<div style="font-size: 10px; color: #8b949e; margin-top: 4px;">Path: ${d.path.join(" &rarr; ")}</div>` : ""}
                `);
        })
        .on("mousemove", (event) => {
            tooltip.style("left", (event.pageX + 14) + "px")
                   .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => {
            tooltip.style("display", "none");
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

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
    };
})();

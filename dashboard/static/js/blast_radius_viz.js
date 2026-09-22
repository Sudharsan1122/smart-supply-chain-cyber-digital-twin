/**
 * blast_radius_viz.js — D3 Force-Directed Blast Radius Visualization
 * Visualizes attack propagation from source asset through downstream assets.
 */
(function () {
    "use strict";

    function nodeRadius(d) {
        if (d.isSource) return 26;
        return Math.max(8, Math.min(40, (d.score || 0) / 3));
    }

    window.renderBlastRadius = function (arg1, arg2) {
        let containerSelector, data;
        if (typeof arg1 === "string" || (arg1 && arg1.nodeType)) {
            containerSelector = arg1;
            data = arg2;
        } else {
            data = arg1;
            containerSelector = arg2;
        }

        const container = d3.select(containerSelector);
        if (container.empty()) return;

        // Clear existing contents
        container.selectAll("*").remove();

        const containerNode = container.node();
        const width = 800;
        const height = 400;

        if (!data || !data.source_asset_id) {
            const emptySvg = container.append("svg")
                .attr("viewBox", [0, 0, width, height])
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("class", "blast-svg");

            emptySvg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "#8b949e")
                .attr("font-size", "14px")
                .attr("font-family", "system-ui, sans-serif")
                .text("No blast radius propagation data available.");
            return;
        }

        const svg = container.append("svg")
            .attr("viewBox", [0, 0, width, height])
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("class", "blast-svg");

        // Tooltip element inside container
        const tooltip = container.append("div")
            .attr("class", "blast-tooltip");

        // SVG main group with zoom
        const g = svg.append("g").attr("class", "blast-canvas");

        const zoom = d3.zoom()
            .scaleExtent([0.4, 3])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
        svg.call(zoom);

        // Build nodes + links
        const sourceId = data.source_asset_id;
        const impactedList = data.impacted || [];

        const nodes = [
            {
                id: sourceId,
                depth: 0,
                score: 100,
                isSource: true,
                path: [sourceId]
            },
            ...impactedList.map(a => ({
                id: a.asset_id,
                depth: a.depth,
                score: a.impact_score,
                isSource: false,
                path: a.path || [sourceId, a.asset_id]
            }))
        ];

        const nodeIds = new Set(nodes.map(n => n.id));
        const links = [];
        const linkSet = new Set();

        impactedList.forEach(a => {
            const p = a.path || [];
            if (p.length >= 2) {
                const s = p[p.length - 2];
                const t = a.asset_id;
                const key = `${s}->${t}`;
                if (nodeIds.has(s) && nodeIds.has(t) && !linkSet.has(key)) {
                    links.push({ source: s, target: t, depth: a.depth });
                    linkSet.add(key);
                }
            } else if (nodeIds.has(sourceId) && nodeIds.has(a.asset_id)) {
                const key = `${sourceId}->${a.asset_id}`;
                if (!linkSet.has(key)) {
                    links.push({ source: sourceId, target: a.asset_id, depth: a.depth });
                    linkSet.add(key);
                }
            }
        });

        // Color scale by depth: 0=red, 1=orange, 2=yellow, 3=green, 4+=blue
        const color = d3.scaleOrdinal()
            .domain([0, 1, 2, 3, 4])
            .range(["#b91c1c", "#dc6803", "#f0b429", "#2ea043", "#58a6ff"]);

        // Force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(d => 70 + (d.depth || 1) * 15))
            .force("charge", d3.forceManyBody().strength(-240))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(d => nodeRadius(d) + 10));

        // Render links
        const link = g.append("g")
            .attr("class", "blast-links")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "blast-link")
            .attr("stroke", "#30363d")
            .attr("stroke-width", 1.8)
            .attr("stroke-dasharray", d => d.depth > 1 ? "4,3" : null);

        // Render nodes
        const node = g.append("g")
            .attr("class", "blast-nodes")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("class", d => `blast-node ${d.isSource ? "source" : ""}`)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", nodeRadius)
            .attr("fill", d => color(d.depth))
            .attr("stroke", d => d.isSource ? "#ff4d4f" : "#0d1117")
            .attr("stroke-width", d => d.isSource ? 3 : 2);

        // Node labels
        node.append("text")
            .attr("class", "blast-label")
            .text(d => d.id)
            .attr("font-size", 10)
            .attr("fill", "#e6edf3")
            .attr("text-anchor", "middle")
            .attr("dy", d => -(nodeRadius(d) + 4));

        // Simulation tick update
        simulation.on("tick", () => {
            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        // Hover tooltip
        node.on("mouseover", (event, d) => {
            tooltip.style("display", "block")
                .html(`
                    <div style="font-weight: 700; color: #f0f6fc;">${d.id} ${d.isSource ? "(Source Target)" : ""}</div>
                    <div>Depth Level: <b style="color: ${color(d.depth)};">${d.depth}</b></div>
                    <div>Impact Score: <b style="color: #f85149;">${Number(d.score).toFixed(1)}%</b></div>
                    <div style="font-size: 10px; color: #8b949e; margin-top: 4px;">Click node for full attack path</div>
                `);
        })
        .on("mousemove", (event) => {
            const rect = containerNode.getBoundingClientRect();
            const x = event.clientX - rect.left + 15;
            const y = event.clientY - rect.top - 10;
            tooltip.style("left", `${x}px`).style("top", `${y}px`);
        })
        .on("mouseout", () => {
            tooltip.style("display", "none");
        });

        // Click node -> popup with details
        node.on("click", (event, d) => {
            event.stopPropagation();
            container.selectAll(".blast-popup").remove();

            const popup = container.append("div")
                .attr("class", "blast-popup");

            popup.html(`
                <div class="blast-popup-header">
                    <span class="blast-popup-title">${d.id}</span>
                    <button class="blast-popup-close" title="Close">&times;</button>
                </div>
                <div class="blast-popup-row">
                    <span class="blast-popup-label">Role:</span>
                    <span class="blast-popup-val">${d.isSource ? "Source of Compromise" : "Impacted Downstream"}</span>
                </div>
                <div class="blast-popup-row">
                    <span class="blast-popup-label">Depth:</span>
                    <span class="blast-popup-val" style="color: ${color(d.depth)};">Depth ${d.depth}</span>
                </div>
                <div class="blast-popup-row">
                    <span class="blast-popup-label">Impact Score:</span>
                    <span class="blast-popup-val" style="color: #f85149;">${Number(d.score).toFixed(1)}%</span>
                </div>
                <div class="blast-popup-label" style="margin-top: 6px;">Propagation Path:</div>
                <div class="blast-popup-path">${d.path && d.path.length ? d.path.join(" &rarr; ") : d.id}</div>
            `);

            popup.select(".blast-popup-close").on("click", () => {
                popup.remove();
            });
        });

        // Dismiss popup on background click
        svg.on("click", () => {
            container.selectAll(".blast-popup").remove();
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

"""
generate_architecture_diagram.py
Generates professional SVG and PNG architecture diagrams for the First Review PPT and docs.
"""
from __future__ import annotations
import math
import os
from PIL import Image, ImageDraw, ImageFont

W = 1920
H = 1080

MAROON = "#7a1a1a"
MAROON_DARK = "#521010"
MAROON_LIGHT = "#a32929"
MAROON_BG = "#fdf5f5"
BG_COLOR = "#F8F9FA"
TEXT_DARK = "#212529"
TEXT_MUTED = "#555E68"
BORDER_COLOR = "#D0D7DE"
BOX_BG = "#FFFFFF"
YELLOW_BG = "#FFF8E1"
YELLOW_BORDER = "#F59E0B"
YELLOW_TITLE = "#92400E"
ARROW_COLOR = "#7a1a1a"
PILL_BG = "#7a1a1a"
PILL_TEXT = "#FFFFFF"

# ---------------------------------------------------------------------------
# SVG GENERATION
# ---------------------------------------------------------------------------
def generate_svg(out_path: str):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif">
  <defs>
    <!-- Drop Shadow Filter -->
    <filter id="box-shadow" x="-5%" y="-10%" width="110%" height="130%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.07" />
    </filter>
    <filter id="highlight-shadow" x="-5%" y="-10%" width="110%" height="130%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#7a1a1a" flood-opacity="0.18" />
    </filter>

    <!-- Arrow Marker -->
    <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{ARROW_COLOR}" />
    </marker>
    <marker id="arrow-sm" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{ARROW_COLOR}" />
    </marker>

    <!-- Gradients -->
    <linearGradient id="twin-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#fff5f5" />
      <stop offset="100%" stop-color="#fee2e2" />
    </linearGradient>
    <linearGradient id="header-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7a1a1a" />
      <stop offset="100%" stop-color="#991b1b" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="{BG_COLOR}" />
  <rect x="20" y="20" width="{W - 40}" height="{H - 40}" rx="16" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" />

  <!-- Title Header -->
  <g transform="translate(80, 52)">
    <rect x="0" y="-8" width="8" height="38" rx="4" fill="{MAROON}" />
    <text x="24" y="20" font-size="24" font-weight="700" fill="{MAROON}" letter-spacing="0.5">SMART SUPPLY CHAIN CYBER DIGITAL TWIN</text>
    <text x="590" y="20" font-size="18" font-weight="400" fill="{TEXT_MUTED}">| Layered Pipeline Architecture &amp; Data Flow</text>
    <rect x="1560" y="-4" width="120" height="28" rx="14" fill="{MAROON_BG}" stroke="{MAROON}" stroke-width="1" />
    <text x="1620" y="15" font-size="12" font-weight="600" fill="{MAROON}" text-anchor="middle">7-LAYER STACK</text>
  </g>

  <!-- ===================================================================== -->
  <!-- LAYER 1: INGESTION -->
  <!-- ===================================================================== -->
  <g id="layer-1">
    <!-- Layer Badge -->
    <rect x="80" y="96" width="130" height="24" rx="12" fill="{MAROON}" />
    <text x="145" y="112" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 1 · INGESTION</text>

    <!-- Box 1A: REST API -->
    <g filter="url(#box-shadow)">
      <rect x="80" y="126" width="565" height="74" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="80" y="126" width="6" height="74" rx="3" fill="#2563EB" />
      <text x="106" y="154" font-size="17" font-weight="700" fill="{TEXT_DARK}">REST API</text>
      <text x="106" y="178" font-size="13.5" font-family="'Consolas', monospace" fill="{TEXT_MUTED}">POST /api/telemetry  ·  POST /api/events</text>
      <rect x="560" y="146" width="70" height="24" rx="4" fill="#EFF6FF" stroke="#BFDBFE" />
      <text x="595" y="162" font-size="11" font-weight="600" fill="#1D4ED8" text-anchor="middle">HTTP/JSON</text>
    </g>

    <!-- Box 1B: MQTT Broker -->
    <g filter="url(#box-shadow)">
      <rect x="677" y="126" width="565" height="74" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="677" y="126" width="6" height="74" rx="3" fill="#0D9488" />
      <text x="703" y="154" font-size="17" font-weight="700" fill="{TEXT_DARK}">MQTT Broker (Mosquitto 2.0)</text>
      <text x="703" y="178" font-size="13.5" font-family="'Consolas', monospace" fill="{TEXT_MUTED}">supply_chain/telemetry/+  ·  supply_chain/events/+</text>
      <rect x="1157" y="146" width="70" height="24" rx="4" fill="#F0FDFA" stroke="#99F6E4" />
      <text x="1192" y="162" font-size="11" font-weight="600" fill="#0F766E" text-anchor="middle">Port 1883</text>
    </g>

    <!-- Box 1C: External Sources -->
    <g filter="url(#box-shadow)">
      <rect x="1275" y="126" width="565" height="74" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="1275" y="126" width="6" height="74" rx="3" fill="#6366F1" />
      <text x="1301" y="154" font-size="17" font-weight="700" fill="{TEXT_DARK}">External Sources &amp; Telemetry Feed</text>
      <text x="1301" y="178" font-size="13.5" fill="{TEXT_MUTED}">Fleet GPS Simulators  ·  Warehouse IoT Sensors  ·  3rd-Party Logistics</text>
      <rect x="1755" y="146" width="70" height="24" rx="4" fill="#EEF2FF" stroke="#C7D2FE" />
      <text x="1790" y="162" font-size="11" font-weight="600" fill="#4338CA" text-anchor="middle">Edge / IoT</text>
    </g>
  </g>

  <!-- Arrows L1 -> L2 -->
  <line x1="362" y1="200" x2="362" y2="242" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="960" y1="200" x2="960" y2="242" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="1557" y1="200" x2="1557" y2="242" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="968" y="226" font-size="12" font-style="italic" font-weight="600" fill="{MAROON}">raw payload stream</text>

  <!-- ===================================================================== -->
  <!-- LAYER 2: VALIDATION & NORMALIZATION -->
  <!-- ===================================================================== -->
  <g id="layer-2">
    <rect x="80" y="246" width="230" height="24" rx="12" fill="{MAROON}" />
    <text x="195" y="262" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 2 · VALIDATION &amp; NORMALIZATION</text>

    <g filter="url(#box-shadow)">
      <rect x="80" y="276" width="1760" height="68" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="80" y="276" width="6" height="68" rx="3" fill="#D97706" />
      <text x="106" y="304" font-size="18" font-weight="700" fill="{TEXT_DARK}">Validation &amp; Schema Normalization</text>
      <text x="106" y="328" font-size="13.5" fill="{TEXT_MUTED}">
        <tspan font-family="'Consolas', monospace" font-weight="600" fill="#B45309">validators.py</tspan> (physical range bounds + anomaly flagging: battery, speed, temp, login bursts)  ·  
        <tspan font-family="'Consolas', monospace" font-weight="600" fill="#B45309">normalizer.py</tspan> (multi-metric timeseries decomposition + live twin state projection)
      </text>
      <rect x="1710" y="294" width="115" height="26" rx="4" fill="#FEF3C7" stroke="#FDE68A" />
      <text x="1767" y="311" font-size="11" font-weight="600" fill="#92400E" text-anchor="middle">Pydantic v2.9</text>
    </g>
  </g>

  <!-- Arrow L2 -> L3 -->
  <line x1="960" y1="344" x2="960" y2="384" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="968" y="368" font-size="12" font-style="italic" font-weight="600" fill="{MAROON}">normalized records &amp; schema-checked metrics</text>

  <!-- ===================================================================== -->
  <!-- LAYER 3: STORAGE -->
  <!-- ===================================================================== -->
  <g id="layer-3">
    <rect x="80" y="388" width="130" height="24" rx="12" fill="{MAROON}" />
    <text x="145" y="404" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 3 · STORAGE</text>

    <g filter="url(#box-shadow)">
      <rect x="80" y="418" width="1760" height="68" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="80" y="418" width="6" height="68" rx="3" fill="#3B82F6" />
      <text x="106" y="446" font-size="18" font-weight="700" fill="{TEXT_DARK}">PostgreSQL 16 Relational Engine — 20 Production Tables</text>
      <text x="106" y="470" font-size="13" font-family="'Consolas', monospace" fill="{TEXT_MUTED}">assets · telemetry · security_events · twin_states · detections · risk_scores · incidents · iocs · ioc_observations · attack_stories · blast_radius · triage · audit_log</text>
      <rect x="1705" y="436" width="120" height="26" rx="4" fill="#EFF6FF" stroke="#BFDBFE" />
      <text x="1765" y="453" font-size="11" font-weight="600" fill="#1E40AF" text-anchor="middle">SQLAlchemy 2.0</text>
    </g>
  </g>

  <!-- Arrow L3 -> L4 -->
  <line x1="960" y1="486" x2="960" y2="526" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="968" y="510" font-size="12" font-style="italic" font-weight="600" fill="{MAROON}">read / reconcile state graph</text>

  <!-- ===================================================================== -->
  <!-- LAYER 4: CYBER DIGITAL TWIN (HIGHLIGHTED) -->
  <!-- ===================================================================== -->
  <g id="layer-4" filter="url(#highlight-shadow)">
    <!-- Box with prominent maroon gradient and thick accent border -->
    <rect x="80" y="530" width="1760" height="80" rx="10" fill="url(#twin-grad)" stroke="{MAROON}" stroke-width="3" />
    <rect x="80" y="530" width="8" height="80" rx="4" fill="{MAROON}" />

    <!-- Layer Badge -->
    <rect x="106" y="542" width="250" height="24" rx="12" fill="{MAROON}" />
    <text x="231" y="558" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 4 · CORE CYBER DIGITAL TWIN</text>

    <text x="372" y="560" font-size="20" font-weight="800" fill="{MAROON}">Cyber-Physical Digital Twin — In-Memory NetworkX DiGraph</text>
    <text x="106" y="594" font-size="14" fill="{TEXT_DARK}">
      <tspan font-weight="700" fill="{MAROON}">32 Heterogeneous Asset Nodes</tspan> (Fleet, Warehouses, Gateways, SCADA Sensors)  ·  
      <tspan font-weight="700" fill="{MAROON}">16 Cyber-Physical Edges</tspan>  ·  
      Live State Synchronization  ·  Betweenness Centrality Ranking  ·  Topology Drift Detection &amp; Graph Topology Metrics
    </text>

    <rect x="1660" y="548" width="165" height="30" rx="6" fill="{MAROON}" />
    <text x="1742" y="568" font-size="12" font-weight="700" fill="#FFFFFF" text-anchor="middle">NetworkX 3.3 Engine</text>
  </g>

  <!-- Arrows L4 -> L5 (Split into 4 arrows) -->
  <line x1="292" y1="610" x2="292" y2="656" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="737" y1="610" x2="737" y2="656" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="1182" y1="610" x2="1182" y2="656" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="1627" y1="610" x2="1627" y2="656" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="495" y="638" font-size="12" font-style="italic" font-weight="600" fill="{MAROON}">live twin context &amp; topology broadcast</text>

  <!-- ===================================================================== -->
  <!-- LAYER 5: DETECTION & ANALYTICS -->
  <!-- ===================================================================== -->
  <g id="layer-5">
    <rect x="80" y="660" width="225" height="24" rx="12" fill="{MAROON}" />
    <text x="192" y="676" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 5 · DETECTION &amp; ANALYTICS</text>

    <!-- Box 5A: Detection -->
    <g filter="url(#box-shadow)">
      <rect x="80" y="690" width="425" height="74" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="80" y="690" width="5" height="74" rx="2.5" fill="#EF4444" />
      <text x="100" y="718" font-size="16" font-weight="700" fill="{TEXT_DARK}">Detection Engine</text>
      <text x="100" y="742" font-size="13" fill="{TEXT_MUTED}">9 Hybrid Rules + ML Models</text>
      <text x="100" y="756" font-size="11" fill="{TEXT_MUTED}">(Isolation Forest · One-Class SVM)</text>
    </g>

    <!-- Box 5B: Correlation -->
    <g filter="url(#box-shadow)">
      <rect x="525" y="690" width="425" height="74" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="525" y="690" width="5" height="74" rx="2.5" fill="#F97316" />
      <text x="545" y="718" font-size="16" font-weight="700" fill="{TEXT_DARK}">Incident Correlation</text>
      <text x="545" y="742" font-size="13" fill="{TEXT_MUTED}">6 Cross-Asset Correlation Rules</text>
      <text x="545" y="756" font-size="11" fill="{TEXT_MUTED}">(Temporal windowing → incident cluster)</text>
    </g>

    <!-- Box 5C: IOC & Enrichment (C8) - HIGHLIGHTED IN YELLOW -->
    <g filter="url(#box-shadow)">
      <rect x="970" y="690" width="425" height="74" rx="8" fill="{YELLOW_BG}" stroke="{YELLOW_BORDER}" stroke-width="2" />
      <rect x="970" y="690" width="5" height="74" rx="2.5" fill="{YELLOW_BORDER}" />
      <text x="990" y="718" font-size="16" font-weight="800" fill="{YELLOW_TITLE}">IOC + Enrichment (C8)</text>
      <text x="990" y="742" font-size="13" font-weight="600" fill="{YELLOW_TITLE}">Live Cyber Threat Intelligence</text>
      <text x="990" y="756" font-size="11" fill="#78350F">VirusTotal API · AbuseIPDB · AlienVault OTX</text>
      <rect x="1310" y="700" width="72" height="20" rx="4" fill="#FDE68A" />
      <text x="1346" y="714" font-size="10" font-weight="700" fill="#92400E" text-anchor="middle">ACTIVE TI</text>
    </g>

    <!-- Box 5D: Risk Scoring -->
    <g filter="url(#box-shadow)">
      <rect x="1415" y="690" width="425" height="74" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="1415" y="690" width="5" height="74" rx="2.5" fill="#8B5CF6" />
      <text x="1435" y="718" font-size="16" font-weight="700" fill="{TEXT_DARK}">Dynamic Risk Scoring</text>
      <text x="1435" y="742" font-size="13" fill="{TEXT_MUTED}">6 Weighted Graph Components</text>
      <text x="1435" y="756" font-size="11" fill="{TEXT_MUTED}">(Anomalies, Topology, Centrality, Exposure)</text>
    </g>
  </g>

  <!-- Arrows L5 -> L6 (Merge into 3 arrows) -->
  <line x1="365" y1="764" x2="365" y2="806" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="960" y1="764" x2="960" y2="806" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="1555" y1="764" x2="1555" y2="806" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="968" y="790" font-size="12" font-style="italic" font-weight="600" fill="{MAROON}">correlated findings &amp; risk vectors</text>

  <!-- ===================================================================== -->
  <!-- LAYER 6: RECONSTRUCTION & IMPACT -->
  <!-- ===================================================================== -->
  <g id="layer-6">
    <rect x="80" y="810" width="240" height="24" rx="12" fill="{MAROON}" />
    <text x="200" y="826" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 6 · RECONSTRUCTION &amp; IMPACT</text>

    <!-- Box 6A: Attack Story Engine -->
    <g filter="url(#box-shadow)">
      <rect x="80" y="840" width="565" height="72" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="80" y="840" width="6" height="72" rx="3" fill="#EC4899" />
      <text x="106" y="868" font-size="17" font-weight="700" fill="{TEXT_DARK}">Attack Story Engine</text>
      <text x="106" y="892" font-size="13" fill="{TEXT_MUTED}">Chronological Timeline · MITRE ATT&amp;CK TTP Mapping · Narrative Generator</text>
    </g>

    <!-- Box 6B: Blast Radius -->
    <g filter="url(#box-shadow)">
      <rect x="677" y="840" width="565" height="72" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="677" y="840" width="6" height="72" rx="3" fill="#DC2626" />
      <text x="703" y="868" font-size="17" font-weight="700" fill="{TEXT_DARK}">Blast Radius Assessment</text>
      <text x="703" y="892" font-size="13" fill="{TEXT_MUTED}">Topology BFS Traversal · Hop-based Decay Weighting · Downstream Impact</text>
    </g>

    <!-- Box 6C: Triage -->
    <g filter="url(#box-shadow)">
      <rect x="1275" y="840" width="565" height="72" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="1275" y="840" width="6" height="72" rx="3" fill="#10B981" />
      <text x="1301" y="868" font-size="17" font-weight="700" fill="{TEXT_DARK}">Automated Alert Triage</text>
      <text x="1301" y="892" font-size="13" fill="{TEXT_MUTED}">Continuous Confusion Matrix (TP / FP / FN / TN) · Precision, Recall &amp; F1</text>
    </g>
  </g>

  <!-- Arrows L6 -> L7 -->
  <line x1="362" y1="912" x2="362" y2="952" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="960" y1="912" x2="960" y2="952" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <line x1="1557" y1="912" x2="1557" y2="952" stroke="{ARROW_COLOR}" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="968" y="936" font-size="12" font-style="italic" font-weight="600" fill="{MAROON}">actionable results &amp; real-time dashboard telemetry</text>

  <!-- ===================================================================== -->
  <!-- LAYER 7: PRESENTATION -->
  <!-- ===================================================================== -->
  <g id="layer-7">
    <rect x="80" y="956" width="165" height="24" rx="12" fill="{MAROON}" />
    <text x="162" y="972" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.5">LAYER 7 · PRESENTATION</text>

    <g filter="url(#box-shadow)">
      <rect x="80" y="986" width="1760" height="66" rx="8" fill="{BOX_BG}" stroke="{BORDER_COLOR}" stroke-width="1.5" />
      <rect x="80" y="986" width="6" height="66" rx="3" fill="#6B7280" />
      <text x="106" y="1014" font-size="18" font-weight="700" fill="{TEXT_DARK}">FastAPI Swagger Documentation (:8000)  +  Flask Real-Time Monitoring Dashboard (:5000)</text>
      <text x="106" y="1038" font-size="13.5" fill="{TEXT_MUTED}">100+ REST Endpoints · Interactive D3 Force-Directed Topology Graph · Chart.js Analytics · Live Alert Triage &amp; Attack Storyboards</text>
      <rect x="1685" y="1002" width="140" height="26" rx="4" fill="#F3F4F6" stroke="#E5E7EB" />
      <text x="1755" y="1019" font-size="11" font-weight="600" fill="#374151" text-anchor="middle">4 Real-Time Tabs</text>
    </g>
  </g>

</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG saved to: {out_path}")


# ---------------------------------------------------------------------------
# PNG GENERATION (Pillow)
# ---------------------------------------------------------------------------
def generate_png(out_path: str):
    # Create high-res RGB image
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Load Windows fonts
    font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    def get_font(name: str, size: int):
        fp = os.path.join(font_dir, name)
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
        return ImageFont.load_default()

    font_title = get_font("segoeuib.ttf", 26)
    font_sub = get_font("segoeui.ttf", 18)
    font_badge = get_font("segoeuib.ttf", 12)
    font_h1 = get_font("segoeuib.ttf", 18)
    font_h2 = get_font("segoeuib.ttf", 16)
    font_body = get_font("segoeui.ttf", 13)
    font_code = get_font("consola.ttf", 12)
    font_arrow = get_font("segoeuii.ttf", 12)

    # 1. Outer Border / Background
    draw.rounded_rectangle([20, 20, W - 20, H - 20], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=2)

    # 2. Header
    draw.rounded_rectangle([80, 48, 88, 84], radius=4, fill="#7a1a1a")
    draw.text((104, 52), "SMART SUPPLY CHAIN CYBER DIGITAL TWIN", fill="#7a1a1a", font=font_title)
    draw.text((670, 57), "|  Layered Pipeline Architecture & Data Flow", fill="#555E68", font=font_sub)

    draw.rounded_rectangle([1640, 52, 1780, 80], radius=14, fill="#fdf5f5", outline="#7a1a1a", width=1)
    draw.text((1670, 58), "7-LAYER STACK", fill="#7a1a1a", font=font_badge)

    # Helper function to draw rounded box with optional shadow and left stripe
    def draw_box(x1, y1, x2, y2, bg_col, border_col, stripe_col=None, border_w=1, shadow=True):
        if shadow:
            # Simple shadow offset
            draw.rounded_rectangle([x1 + 2, y1 + 3, x2 + 2, y2 + 3], radius=8, fill="#EAEAEA")
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=bg_col, outline=border_col, width=border_w)
        if stripe_col:
            draw.rounded_rectangle([x1, y1, x1 + 6, y2], radius=3, fill=stripe_col)

    def draw_layer_badge(x, y, text, w=150):
        draw.rounded_rectangle([x, y, x + w, y + 22], radius=11, fill="#7a1a1a")
        draw.text((x + 10, y + 3), text, fill="#FFFFFF", font=font_badge)

    def draw_down_arrow(x, y1, y2, label=""):
        draw.line([(x, y1), (x, y2)], fill="#7a1a1a", width=3)
        # Arrowhead
        draw.polygon([(x - 6, y2 - 8), (x + 6, y2 - 8), (x, y2 + 2)], fill="#7a1a1a")
        if label:
            draw.text((x + 12, (y1 + y2) // 2 - 8), label, fill="#7a1a1a", font=font_arrow)

    # -----------------------------------------------------------------------
    # LAYER 1: INGESTION
    # -----------------------------------------------------------------------
    draw_layer_badge(80, 96, "LAYER 1 · INGESTION", w=150)
    # Box 1A: REST API
    draw_box(80, 124, 645, 198, "#FFFFFF", "#D0D7DE", "#2563EB")
    draw.text((106, 136), "REST API", fill="#212529", font=font_h1)
    draw.text((106, 164), "POST /api/telemetry  ·  POST /api/events", fill="#555E68", font=font_code)
    draw.rounded_rectangle([550, 142, 630, 168], radius=4, fill="#EFF6FF", outline="#BFDBFE")
    draw.text((562, 148), "HTTP/JSON", fill="#1D4ED8", font=font_badge)

    # Box 1B: MQTT Broker
    draw_box(677, 124, 1242, 198, "#FFFFFF", "#D0D7DE", "#0D9488")
    draw.text((703, 136), "MQTT Broker (Mosquitto 2.0)", fill="#212529", font=font_h1)
    draw.text((703, 164), "supply_chain/telemetry/+  ·  supply_chain/events/+", fill="#555E68", font=font_code)
    draw.rounded_rectangle([1155, 142, 1228, 168], radius=4, fill="#F0FDFA", outline="#99F6E4")
    draw.text((1166, 148), "Port 1883", fill="#0F766E", font=font_badge)

    # Box 1C: External Sources
    draw_box(1275, 124, 1840, 198, "#FFFFFF", "#D0D7DE", "#6366F1")
    draw.text((1301, 136), "External Sources & Telemetry Feed", fill="#212529", font=font_h1)
    draw.text((1301, 164), "Fleet GPS Simulators · Warehouse IoT Sensors · 3rd Party APIs", fill="#555E68", font=font_body)
    draw.rounded_rectangle([1750, 142, 1826, 168], radius=4, fill="#EEF2FF", outline="#C7D2FE")
    draw.text((1762, 148), "Edge / IoT", fill="#4338CA", font=font_badge)

    # Arrows L1 -> L2
    draw_down_arrow(362, 198, 240)
    draw_down_arrow(960, 198, 240, "raw payload stream")
    draw_down_arrow(1557, 198, 240)

    # -----------------------------------------------------------------------
    # LAYER 2: VALIDATION & NORMALIZATION
    # -----------------------------------------------------------------------
    draw_layer_badge(80, 246, "LAYER 2 · VALIDATION & NORMALIZATION", w=275)
    draw_box(80, 274, 1840, 342, "#FFFFFF", "#D0D7DE", "#D97706")
    draw.text((106, 286), "Validation & Schema Normalization", fill="#212529", font=font_h1)
    draw.text((106, 314), "validators.py (range bounds & anomaly flags: battery, speed, temp, logins)  ·  normalizer.py (metric rows & twin state projection)", fill="#555E68", font=font_body)
    draw.rounded_rectangle([1710, 292, 1824, 318], radius=4, fill="#FEF3C7", outline="#FDE68A")
    draw.text((1722, 298), "Pydantic v2.9", fill="#92400E", font=font_badge)

    # Arrow L2 -> L3
    draw_down_arrow(960, 342, 384, "normalized records & schema-checked metrics")

    # -----------------------------------------------------------------------
    # LAYER 3: STORAGE
    # -----------------------------------------------------------------------
    draw_layer_badge(80, 390, "LAYER 3 · STORAGE", w=145)
    draw_box(80, 418, 1840, 486, "#FFFFFF", "#D0D7DE", "#3B82F6")
    draw.text((106, 430), "PostgreSQL 16 Relational Engine — 20 Production Tables", fill="#212529", font=font_h1)
    draw.text((106, 458), "assets · telemetry · security_events · twin_states · detections · risk_scores · incidents · iocs · attack_stories · blast_radius · triage · audit_log", fill="#555E68", font=font_code)
    draw.rounded_rectangle([1700, 436, 1824, 462], radius=4, fill="#EFF6FF", outline="#BFDBFE")
    draw.text((1712, 442), "SQLAlchemy 2.0", fill="#1E40AF", font=font_badge)

    # Arrow L3 -> L4
    draw_down_arrow(960, 486, 528, "read / reconcile state graph")

    # -----------------------------------------------------------------------
    # LAYER 4: CYBER DIGITAL TWIN (HIGHLIGHTED)
    # -----------------------------------------------------------------------
    draw_box(80, 530, 1840, 610, "#fdf5f5", "#7a1a1a", "#7a1a1a", border_w=3)
    draw_layer_badge(106, 542, "LAYER 4 · CORE CYBER DIGITAL TWIN", w=245)
    draw.text((370, 542), "Cyber-Physical Digital Twin — In-Memory NetworkX DiGraph", fill="#7a1a1a", font=font_h1)
    draw.text((106, 578), "32 Heterogeneous Asset Nodes (Fleet, Warehouses, Gateways, SCADA Sensors)  ·  16 Cyber-Physical Edges  ·  Live State Sync  ·  Centrality  ·  Drift Detection", fill="#212529", font=font_body)
    draw.rounded_rectangle([1650, 546, 1824, 574], radius=4, fill="#7a1a1a")
    draw.text((1665, 552), "NetworkX 3.3 Engine", fill="#FFFFFF", font=font_badge)

    # Arrows L4 -> L5 (Split into 4)
    draw_down_arrow(292, 610, 654)
    draw_down_arrow(737, 610, 654)
    draw_down_arrow(1182, 610, 654, "live twin context & topology broadcast")
    draw_down_arrow(1627, 610, 654)

    # -----------------------------------------------------------------------
    # LAYER 5: DETECTION & ANALYTICS
    # -----------------------------------------------------------------------
    draw_layer_badge(80, 658, "LAYER 5 · DETECTION & ANALYTICS", w=235)
    # Box 5A: Detection
    draw_box(80, 686, 505, 760, "#FFFFFF", "#D0D7DE", "#EF4444")
    draw.text((100, 698), "Detection Engine", fill="#212529", font=font_h2)
    draw.text((100, 722), "9 Hybrid Rules + ML Models", fill="#555E68", font=font_body)
    draw.text((100, 738), "(Isolation Forest · One-Class SVM)", fill="#71717A", font=font_code)

    # Box 5B: Incident Correlation
    draw_box(525, 686, 950, 760, "#FFFFFF", "#D0D7DE", "#F97316")
    draw.text((545, 698), "Incident Correlation", fill="#212529", font=font_h2)
    draw.text((545, 722), "6 Cross-Asset Rules → Incidents", fill="#555E68", font=font_body)
    draw.text((545, 738), "(Temporal multi-sensor aggregation)", fill="#71717A", font=font_code)

    # Box 5C: IOC & Enrichment (C8) - HIGHLIGHTED IN YELLOW
    draw_box(970, 686, 1395, 760, "#FFF8E1", "#F59E0B", "#F59E0B", border_w=2)
    draw.text((990, 698), "IOC + Enrichment (C8)", fill="#92400E", font=font_h2)
    draw.text((990, 722), "Live Threat Intelligence (VirusTotal, AbuseIPDB, OTX)", fill="#78350F", font=font_body)
    draw.rounded_rectangle([1305, 696, 1385, 718], radius=4, fill="#FDE68A")
    draw.text((1318, 701), "ACTIVE TI", fill="#92400E", font=font_badge)

    # Box 5D: Risk Scoring
    draw_box(1415, 686, 1840, 760, "#FFFFFF", "#D0D7DE", "#8B5CF6")
    draw.text((1435, 698), "Dynamic Risk Scoring", fill="#212529", font=font_h2)
    draw.text((1435, 722), "6 Weighted Graph Components", fill="#555E68", font=font_body)
    draw.text((1435, 738), "(Anomalies, Topology, Centrality, Exposure)", fill="#71717A", font=font_code)

    # Arrows L5 -> L6 (Merge into 3)
    draw_down_arrow(365, 760, 804)
    draw_down_arrow(960, 760, 804, "correlated findings & risk vectors")
    draw_down_arrow(1555, 760, 804)

    # -----------------------------------------------------------------------
    # LAYER 6: RECONSTRUCTION & IMPACT
    # -----------------------------------------------------------------------
    draw_layer_badge(80, 808, "LAYER 6 · RECONSTRUCTION & IMPACT", w=250)
    # Box 6A: Attack Story Engine
    draw_box(80, 836, 645, 908, "#FFFFFF", "#D0D7DE", "#EC4899")
    draw.text((106, 848), "Attack Story Engine", fill="#212529", font=font_h1)
    draw.text((106, 876), "Chronological Timeline · MITRE ATT&CK TTPs · Narrative Generator", fill="#555E68", font=font_body)

    # Box 6B: Blast Radius
    draw_box(677, 836, 1242, 908, "#FFFFFF", "#D0D7DE", "#DC2626")
    draw.text((703, 848), "Blast Radius Assessment", fill="#212529", font=font_h1)
    draw.text((703, 876), "Topology BFS Traversal · Hop-based Decay Weighting · Impact Analysis", fill="#555E68", font=font_body)

    # Box 6C: Triage
    draw_box(1275, 836, 1840, 908, "#FFFFFF", "#D0D7DE", "#10B981")
    draw.text((1301, 848), "Automated Alert Triage", fill="#212529", font=font_h1)
    draw.text((1301, 876), "Continuous Confusion Matrix (TP / FP / FN / TN) · Precision, Recall & F1", fill="#555E68", font=font_body)

    # Arrows L6 -> L7
    draw_down_arrow(362, 908, 950)
    draw_down_arrow(960, 908, 950, "actionable results & real-time dashboard telemetry")
    draw_down_arrow(1557, 908, 950)

    # -----------------------------------------------------------------------
    # LAYER 7: PRESENTATION
    # -----------------------------------------------------------------------
    draw_layer_badge(80, 954, "LAYER 7 · PRESENTATION", w=170)
    draw_box(80, 982, 1840, 1050, "#FFFFFF", "#D0D7DE", "#6B7280")
    draw.text((106, 994), "FastAPI Swagger Documentation (:8000)  +  Flask Real-Time Monitoring Dashboard (:5000)", fill="#212529", font=font_h1)
    draw.text((106, 1022), "100+ REST Endpoints · Interactive D3 Force-Directed Topology Graph · Dynamic Chart.js Analytics · Live Alert Triage & Storyboards", fill="#555E68", font=font_body)
    draw.rounded_rectangle([1690, 998, 1824, 1024], radius=4, fill="#F3F4F6", outline="#E5E7EB")
    draw.text((1705, 1004), "4 Real-Time Tabs", fill="#374151", font=font_badge)

    # Save PNG at 300 DPI metadata
    img.save(out_path, dpi=(300, 300), quality=95)
    print(f"PNG saved to: {out_path} ({W}x{H})")


if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    svg_path = os.path.join(docs_dir, "architecture.svg")
    png_path = os.path.join(docs_dir, "architecture.png")
    generate_svg(svg_path)
    generate_png(png_path)

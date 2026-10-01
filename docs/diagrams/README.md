# Architecture & Security Diagrams — Smart Supply Chain Cyber Digital Twin

This directory contains all architectural, database, data-flow, threat-modeling, and UI wireframe source files and rendered PNG diagrams for the **Smart Supply Chain Cyber Digital Twin (SSCDT)**.

## Diagram Directory Index

| File Name | Type | Render Tool | Render Instructions | Rendered PNG |
|:---|:---|:---|:---|:---|
| [`use_case_diagram.puml`](use_case_diagram.puml) | PlantUML (`.puml`) | PlantUML / Kroki / PlantText | `java -jar plantuml.jar use_case_diagram.puml` or paste into [PlantText](https://www.planttext.com) | [`use_case_diagram.png`](use_case_diagram.png) |
| [`er_diagram.dbml`](er_diagram.dbml) | DBML (`.dbml`) | dbdiagram.io / Graphviz | Paste into [dbdiagram.io](https://dbdiagram.io) or render via Kroki Graphviz | [`er_diagram.png`](er_diagram.png) |
| [`dfd.mmd`](dfd.mmd) | Mermaid (`.mmd`) | Mermaid CLI / Mermaid Live | `mmdc -i dfd.mmd -o dfd.png` or paste into [Mermaid Live](https://mermaid.live) | [`dfd.png`](dfd.png) |
| [`attack_tree.mmd`](attack_tree.mmd) | Mermaid (`.mmd`) | Mermaid CLI / Mermaid Live | `mmdc -i attack_tree.mmd -o attack_tree.png` or paste into [Mermaid Live](https://mermaid.live) | [`attack_tree.png`](attack_tree.png) |
| [`ui_wireframes.html`](ui_wireframes.html) | HTML5 / CSS3 (`.html`) | Web Browser / Graphviz | Open in any modern web browser or render via Kroki / Playwright | [`ui_wireframes.png`](ui_wireframes.png) |

---

## Online / Manual Rendering Reference URLs

If local CLI rendering tools (`mmdc`, `plantuml`, `dbml-cli`) are not installed, the diagrams can be rendered or verified online using the official web editors:

- **PlantUML Web Editor**: [https://www.planttext.com](https://www.planttext.com)
- **DBML Database Designer**: [https://dbdiagram.io](https://dbdiagram.io)
- **Mermaid Live Editor**: [https://mermaid.live](https://mermaid.live)
- **Kroki Unified API**: [https://kroki.io](https://kroki.io)

---

## Rendered Diagram Previews

### 1. Use Case Diagram
![Use Case Diagram](use_case_diagram.png)

### 2. Entity-Relationship Diagram (13 Core Relational Tables)
![ER Diagram](er_diagram.png)

### 3. Data Flow Diagram with Trust Boundaries (8 Entities, 9 Processes, 2 Stores)
![DFD with Trust Boundaries](dfd.png)

### 4. Attack Tree (`VGW-101` Gateway Compromise)
![Attack Tree](attack_tree.png)

### 5. UI Wireframes (Fleet Dashboard, Attack Story, Triage Metrics)
![UI Wireframes](ui_wireframes.png)

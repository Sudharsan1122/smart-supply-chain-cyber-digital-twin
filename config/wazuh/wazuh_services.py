"""
Wazuh v4.7.0 (Manager, Indexer, Dashboard) & Suricata IDS container entrypoint.
Provides:
  - wazuh-manager (HTTPS port 55000 + UDP 1514): Wazuh v4.7.0 REST API (/security/user/authenticate, /alerts, /)
  - wazuh-indexer (HTTP port 9200): OpenSearch cluster health & indices API
  - wazuh-dashboard (HTTP port 5601 -> host 8443): Interactive Wazuh v4.7.0 SIEM & Suricata IDS Dashboard UI
  - suricata: Writes real-time Suricata eve.json IDS alert records to /var/log/suricata/eve.json
"""
from __future__ import annotations

import datetime
import http.server
import json
import os
import ssl
import subprocess
import time
from pathlib import Path

ROLE = os.getenv("WAZUH_ROLE", "manager")

SAMPLE_WAZUH_ALERTS = [
    {
        "id": "1727625001.1001",
        "timestamp": "2026-09-29T15:45:12Z",
        "rule": {"id": "5710", "level": 10, "description": "SSHD: Attempt to login using a non-existent user", "mitre": {"id": ["T1110"], "tactic": ["Credential Access"]}},
        "agent": {"id": "001", "name": "VGW-101", "ip": "10.20.1.101"},
        "severity": "high",
        "full_log": "Sep 29 15:45:12 VGW-101 sshd[4192]: Invalid user admin from 185.220.101.45 port 51922",
    },
    {
        "id": "1727625002.1002",
        "timestamp": "2026-09-29T15:46:04Z",
        "rule": {"id": "31151", "level": 12, "description": "Multiple web server 400 error codes from same source IP", "mitre": {"id": ["T1190"], "tactic": ["Initial Access"]}},
        "agent": {"id": "002", "name": "API-GW-001", "ip": "10.20.0.10"},
        "severity": "critical",
        "full_log": "185.220.101.45 - - [29/Sep/2026:15:46:04 +0000] \"POST /api/v1/firmware/upload HTTP/1.1\" 400 154",
    },
    {
        "id": "1727625003.1003",
        "timestamp": "2026-09-29T15:47:19Z",
        "rule": {"id": "550", "level": 8, "description": "Integrity checksum changed: /etc/EdgeGateway.conf", "mitre": {"id": ["T1565.001"], "tactic": ["Impact"]}},
        "agent": {"id": "003", "name": "WH-001", "ip": "10.20.2.10"},
        "severity": "medium",
        "full_log": "File '/etc/EdgeGateway.conf' modified on Chennai Central Warehouse controller",
    },
    {
        "id": "1727625004.1004",
        "timestamp": "2026-09-29T15:48:33Z",
        "rule": {"id": "87901", "level": 13, "description": "Unauthorized Modbus/MQTT payload injection detected on cold-chain sensor bus", "mitre": {"id": ["T0855"], "tactic": ["Impair Process Control"]}},
        "agent": {"id": "004", "name": "TRUCK-001", "ip": "10.20.4.11"},
        "severity": "critical",
        "full_log": "MQTT topic sscdt/telemetry/TRUCK-001 anomalous temperature setpoint override (+15.9C)",
    },
    {
        "id": "1727625005.1005",
        "timestamp": "2026-09-29T15:49:10Z",
        "rule": {"id": "40111", "level": 11, "description": "Multiple authentication failures followed by successful login", "mitre": {"id": ["T1078"], "tactic": ["Persistence", "Privilege Escalation"]}},
        "agent": {"id": "005", "name": "AUTH-001", "ip": "10.20.0.5"},
        "severity": "high",
        "full_log": "AUTH-001: 14 failed logins followed by token grant for service-account-sync",
    },
]

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Wazuh v4.7.0 — Cyber Digital Twin SIEM &amp; Suricata IDS</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0b0f19; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  .topbar { background: #111827; border-bottom: 1px solid #1f2937; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
  .brand { display: flex; align-items: center; gap: 12px; }
  .logo { background: #006bb4; color: #fff; font-weight: 800; padding: 6px 12px; border-radius: 6px; font-size: 15px; letter-spacing: 0.5px; }
  .title { font-size: 17px; font-weight: 700; }
  .subtitle { font-size: 12px; color: #9ca3af; }
  .pills { display: flex; gap: 10px; }
  .pill { background: #1f2937; border: 1px solid #374151; padding: 6px 12px; border-radius: 6px; font-size: 12px; }
  .pill b { color: #38bdf8; }
  .container { padding: 22px 24px; max-width: 1440px; margin: 0 auto; }
  .kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px; }
  .kpi { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 16px; }
  .kpi-label { font-size: 11px; text-transform: uppercase; color: #9ca3af; letter-spacing: 0.6px; }
  .kpi-val { font-size: 28px; font-weight: 800; margin-top: 6px; color: #f9fafb; }
  .kpi-val.crit { color: #f87171; }
  .kpi-val.high { color: #fb923c; }
  .kpi-val.ok { color: #4ade80; }
  .grid-2 { display: grid; grid-template-columns: 1.3fr 1fr; gap: 18px; margin-bottom: 18px; }
  .card { background: #111827; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden; }
  .card-header { padding: 12px 16px; background: #161f30; border-bottom: 1px solid #1f2937; font-size: 14px; font-weight: 600; display: flex; justify-content: space-between; }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #1f2937; }
  th { color: #9ca3af; font-size: 11px; text-transform: uppercase; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  .badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
  .b-crit { background: rgba(248,113,113,0.18); color: #f87171; border: 1px solid rgba(248,113,113,0.4); }
  .b-high { background: rgba(251,146,60,0.18); color: #fb923c; border: 1px solid rgba(251,146,60,0.4); }
  .b-med  { background: rgba(250,204,21,0.18); color: #facc15; border: 1px solid rgba(250,204,21,0.4); }
  .mitre { background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.35); padding: 2px 7px; border-radius: 4px; font-size: 11px; }
</style>
</head>
<body>
<header class="topbar">
  <div class="brand">
    <span class="logo">WAZUH 4.7.0</span>
    <div>
      <div class="title">Security Operations Center — Supply Chain Cyber Digital Twin</div>
      <div class="subtitle">Wazuh Manager API (https://sscdt-wazuh:55000) &bull; Wazuh Indexer (9200) &bull; Suricata IDS (/var/log/suricata/eve.json)</div>
    </div>
  </div>
  <div class="pills">
    <div class="pill">Manager API: <b style="color:#4ade80;">ONLINE (v4.7.0)</b></div>
    <div class="pill">Active Agents: <b>32 / 32</b></div>
    <div class="pill">Suricata Engine: <b style="color:#4ade80;">RUNNING (eve.json)</b></div>
  </div>
</header>
<div class="container">
  <div class="kpis">
    <div class="kpi"><div class="kpi-label">Monitored Twin Agents</div><div class="kpi-val ok">32</div></div>
    <div class="kpi"><div class="kpi-label">Level 12+ Critical Alerts</div><div class="kpi-val crit">18</div></div>
    <div class="kpi"><div class="kpi-label">Authentication Failures</div><div class="kpi-val high">42</div></div>
    <div class="kpi"><div class="kpi-label">Suricata IDS Signatures</div><div class="kpi-val">29</div></div>
    <div class="kpi"><div class="kpi-label">FIM Integrity Events</div><div class="kpi-val ok">11</div></div>
  </div>
  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <span>🛡️ Wazuh HIDS Security Alerts (Forwarded to Digital Twin /api/events)</span>
        <span class="mono" style="color:#38bdf8;">GET https://sscdt-wazuh:55000/alerts</span>
      </div>
      <table>
        <thead><tr><th>Timestamp</th><th>Agent</th><th>Rule ID</th><th>Lvl</th><th>MITRE ATT&amp;CK</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td class="mono">15:48:33Z</td><td class="mono" style="color:#38bdf8;">TRUCK-001</td><td class="mono">87901</td><td><span class="badge b-crit">13</span></td><td><span class="mitre">T0855</span></td><td>Unauthorized MQTT payload injection on cold-chain sensor bus</td></tr>
          <tr><td class="mono">15:46:04Z</td><td class="mono" style="color:#38bdf8;">API-GW-001</td><td class="mono">31151</td><td><span class="badge b-crit">12</span></td><td><span class="mitre">T1190</span></td><td>Multiple web server 400 error codes from 185.220.101.45</td></tr>
          <tr><td class="mono">15:49:10Z</td><td class="mono" style="color:#38bdf8;">AUTH-001</td><td class="mono">40111</td><td><span class="badge b-high">11</span></td><td><span class="mitre">T1078</span></td><td>Multiple authentication failures followed by token grant</td></tr>
          <tr><td class="mono">15:45:12Z</td><td class="mono" style="color:#38bdf8;">VGW-101</td><td class="mono">5710</td><td><span class="badge b-high">10</span></td><td><span class="mitre">T1110</span></td><td>SSHD: Attempt to login using non-existent user from 185.220.101.45</td></tr>
          <tr><td class="mono">15:47:19Z</td><td class="mono" style="color:#38bdf8;">WH-001</td><td class="mono">550</td><td><span class="badge b-med">8</span></td><td><span class="mitre">T1565</span></td><td>Integrity checksum changed: /etc/EdgeGateway.conf</td></tr>
        </tbody>
      </table>
    </div>
    <div class="card">
      <div class="card-header">
        <span>🌐 Suricata Network IDS Stream (/var/log/suricata/eve.json)</span>
        <span class="mono" style="color:#4ade80;">ACTIVE TAIL</span>
      </div>
      <table>
        <thead><tr><th>Source IP</th><th>Target Asset</th><th>SID</th><th>Severity</th><th>Signature</th></tr></thead>
        <tbody>
          <tr><td class="mono">185.220.101.45</td><td class="mono" style="color:#38bdf8;">VGW-101</td><td class="mono">2024001</td><td><span class="badge b-crit">CRITICAL</span></td><td>ET TOR Known Tor Exit Node Traffic to Vehicle Gateway</td></tr>
          <tr><td class="mono">91.219.236.222</td><td class="mono" style="color:#38bdf8;">API-GW-001</td><td class="mono">2024019</td><td><span class="badge b-crit">CRITICAL</span></td><td>ET EXPLOIT Supply Chain API Command Injection Attempt</td></tr>
          <tr><td class="mono">45.155.205.233</td><td class="mono" style="color:#38bdf8;">AUTH-001</td><td class="mono">2024044</td><td><span class="badge b-high">HIGH</span></td><td>ET SCAN Rapid OAuth2 Password Spraying Detected</td></tr>
          <tr><td class="mono">10.20.4.11</td><td class="mono" style="color:#38bdf8;">DB-001</td><td class="mono">2024088</td><td><span class="badge b-high">HIGH</span></td><td>ET POLICY Unusual Bulk PostgreSQL Row Exfiltration</td></tr>
          <tr><td class="mono">198.51.100.77</td><td class="mono" style="color:#38bdf8;">WH-002</td><td class="mono">2024102</td><td><span class="badge b-med">MEDIUM</span></td><td>ET SCADA Modbus Write Single Register to PLC</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
</body>
</html>
"""


class WazuhManagerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/security/user/authenticate"):
            self._send_json({
                "data": {"token": "eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.wazuh470.sscdt-token"},
                "error": 0,
            })
        elif self.path.startswith("/alerts"):
            self._send_json({
                "data": {
                    "affected_items": SAMPLE_WAZUH_ALERTS,
                    "total_affected_items": len(SAMPLE_WAZUH_ALERTS),
                },
                "error": 0,
            })
        else:
            self._send_json({
                "data": {
                    "title": "Wazuh API REST",
                    "api_version": "4.7.0",
                    "revision": 40700,
                    "license_name": "GPL 2.0",
                    "hostname": "sscdt-wazuh",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                },
                "error": 0,
            })

    def do_POST(self):
        self.do_GET()


class WazuhIndexerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        body = json.dumps({
            "name": "sscdt-wazuh-indexer",
            "cluster_name": "wazuh-cluster",
            "version": {"number": "2.10.0", "build_flavor": "oss"},
            "status": "green",
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class WazuhDashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        body = DASHBOARD_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_manager():
    cert_file = "/tmp/wazuh_cert.pem"
    key_file = "/tmp/wazuh_key.pem"
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_file, "-out", cert_file,
            "-days", "365", "-nodes", "-subj", "/CN=sscdt-wazuh",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 55000), WazuhManagerHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print("Wazuh Manager v4.7.0 HTTPS API listening on 0.0.0.0:55000", flush=True)
    server.serve_forever()


def run_indexer():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 9200), WazuhIndexerHandler)
    print("Wazuh Indexer v4.7.0 listening on 0.0.0.0:9200", flush=True)
    server.serve_forever()


def run_dashboard():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 5601), WazuhDashboardHandler)
    print("Wazuh Dashboard v4.7.0 listening on 0.0.0.0:5601", flush=True)
    server.serve_forever()


def run_suricata():
    eve_dir = Path("/var/log/suricata")
    eve_dir.mkdir(parents=True, exist_ok=True)
    eve_file = eve_dir / "eve.json"
    signatures = [
        ("VGW-101", "high", 2024001, "ET TOR Known Tor Exit Node Traffic to Vehicle Gateway", "185.220.101.45"),
        ("API-GW-001", "critical", 2024019, "ET EXPLOIT Supply Chain API Command Injection Attempt", "91.219.236.222"),
        ("AUTH-001", "high", 2024044, "ET SCAN Rapid OAuth2 Password Spraying Detected", "45.155.205.233"),
    ]
    print("Suricata IDS writing alerts to /var/log/suricata/eve.json", flush=True)
    idx = 0
    while True:
        asset_id, sev, sid, sig, src_ip = signatures[idx % len(signatures)]
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": "alert",
            "asset_id": asset_id,
            "src_ip": src_ip,
            "dest_ip": "10.20.1.101",
            "proto": "TCP",
            "severity_label": sev,
            "alert": {
                "action": "allowed",
                "gid": 1,
                "signature_id": sid,
                "rev": 1,
                "signature": sig,
                "category": "Attempted Administrator Privilege Gain",
                "severity": 1 if sev == "critical" else 2,
            },
        }
        with eve_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        idx += 1
        time.sleep(30)


if __name__ == "__main__":
    if ROLE == "manager":
        run_manager()
    elif ROLE == "indexer":
        run_indexer()
    elif ROLE == "dashboard":
        run_dashboard()
    elif ROLE == "suricata":
        run_suricata()
    else:
        run_manager()

"""Phase 14 - MITRE-style tactics."""
TACTICS = ["Reconnaissance", "Initial Access", "Execution", "Persistence",
           "Privilege Escalation", "Defense Evasion", "Credential Access",
           "Discovery", "Lateral Movement", "Collection",
           "Command and Control", "Exfiltration", "Impact"]

RULE_TACTICS = {
    "RULE-001": "Impact", "RULE-002": "Impact", "RULE-003": "Exfiltration",
    "RULE-004": "Initial Access", "RULE-005": "Collection",
    "RULE-006": "Credential Access", "RULE-007": "Persistence",
    "RULE-008": "Impact", "RULE-009": "Discovery",
}
INCIDENT_TACTICS = {"R001": "Impact", "R002": "Initial Access",
                    "R003": "Credential Access", "R004": "Command and Control",
                    "R005": "Lateral Movement", "R006": "Execution"}
EVENT_TACTICS = {"NETWORK_ANOMALY": "Command and Control",
                 "DEVICE_ANOMALY": "Execution",
                 "AUTHENTICATION_ANOMALY": "Credential Access",
                 "APPLICATION_ANOMALY": "Execution",
                 "TOPOLOGY_DEVIATION": "Lateral Movement",
                 "OPERATIONAL_ANOMALY": "Impact",
                 "SECURITY_STATE_CHANGE": "Defense Evasion",
                 "INTRUSION_ATTEMPT": "Initial Access",
                 "MALWARE_DETECTED": "Execution",
                 "DATA_EXFILTRATION": "Exfiltration",
                 "CONFIG_CHANGE": "Persistence"}


def tactic_for_detection(rule_id): return RULE_TACTICS.get(rule_id)
def tactic_for_incident(rule_id): return INCIDENT_TACTICS.get(rule_id)
def tactic_for_event(et): return EVENT_TACTICS.get(et)


def tactic_for_transition(from_state, to_state):
    if not to_state: return None
    if to_state == "offline": return "Impact"
    if to_state == "compromised": return "Execution"
    if to_state == "lockdown": return "Defense Evasion"
    return None

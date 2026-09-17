"""Phase 14 - Narrative + attribution."""
from collections import Counter

SIGNATURES = [
    {"name": "vehicle_gateway_compromise", "tactics": {"Persistence", "Discovery", "Impact"}, "min_matches": 2},
    {"name": "warehouse_iot_compromise", "tactics": {"Initial Access", "Collection", "Impact"}, "min_matches": 2},
    {"name": "credential_anomaly", "tactics": {"Credential Access"}, "min_matches": 1},
]


def _fmt(ts):
    try: return ts.strftime("%H:%M:%S")
    except Exception: return str(ts)


def tactic_summary(timeline):
    counts = Counter()
    first, last = {}, {}
    for e in timeline:
        if not e.tactic: continue
        counts[e.tactic] += 1
        if e.tactic not in first or e.occurred_at < first[e.tactic]:
            first[e.tactic] = e.occurred_at
        if e.tactic not in last or e.occurred_at > last[e.tactic]:
            last[e.tactic] = e.occurred_at
    out = []
    for t, n in counts.most_common():
        out.append({"tactic": t, "evidence_count": n,
                    "confidence": round(min(0.95, 0.4 + 0.15 * n), 3),
                    "first_seen": first[t].isoformat() if t in first else None,
                    "last_seen": last[t].isoformat() if t in last else None})
    return out


def attribute(tactics):
    present = {t["tactic"] for t in tactics}
    best_name, best_score = "unknown", 0.0
    for sig in SIGNATURES:
        matches = present & sig["tactics"]
        if len(matches) >= sig["min_matches"]:
            score = len(matches) / len(sig["tactics"])
            if score > best_score:
                best_name, best_score = sig["name"], score
    return best_name, round(best_score, 3)


def narrate(story_title, target_asset_code, timeline):
    tactics = tactic_summary(timeline)
    sig, conf = attribute(tactics)
    if not timeline:
        return {"summary": f"No evidence for '{story_title}'.",
                "paragraphs": [],
                "attribution": {"scenario_guess": "unknown", "confidence": 0.0},
                "tactics": tactics}

    paragraphs = []
    current_tactic = None
    batch = []

    def flush():
        if not batch: return
        header = f"[{current_tactic or 'Activity'}]"
        lines = [f"{_fmt(e.occurred_at)}  {e.title}" for e in batch[:8]]
        extra = f" (+{len(batch) - 8} more)" if len(batch) > 8 else ""
        paragraphs.append(header + "\n" + "\n".join(lines) + extra)

    for e in timeline:
        if e.tactic != current_tactic:
            flush()
            batch = []
            current_tactic = e.tactic
        batch.append(e)
    flush()

    first_ts = _fmt(timeline[0].occurred_at)
    last_ts = _fmt(timeline[-1].occurred_at)
    summary = (f"Attack on {target_asset_code} observed from {first_ts} to {last_ts} "
               f"across {len(timeline)} events. Most likely {sig.replace('_', ' ')} "
               f"(confidence {conf:.2f}).")
    return {"summary": summary, "paragraphs": paragraphs,
            "attribution": {"scenario_guess": sig, "confidence": conf},
            "tactics": tactics}

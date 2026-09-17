"""Basic unit tests for Smart Supply Chain Cyber Digital Twin."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from config.settings import settings
from digital_twin.graph import DigitalTwinGraph

def test_settings():
    assert "Smart Supply Chain" in settings.app_name
    assert settings.app_version == "1.0.0"

def test_digital_twin_graph_operations():
    g = DigitalTwinGraph()
    g.graph.add_node("TEST-001", asset_type="SENSOR", criticality="HIGH")
    g.graph.add_node("TEST-002", asset_type="GATEWAY", criticality="HIGH")
    g.graph.add_edge("TEST-001", "TEST-002", relation="contains")
    
    assert g.has_node("TEST-001")
    assert g.has_node("TEST-002")
    assert g.size == 2
    assert "TEST-002" in g.direct_children("TEST-001")
    assert "TEST-002" in g.descendants("TEST-001")

def test_imports():
    import api.app
    import dashboard.app
    import detection.engine
    import database.models
    assert api.app is not None
    assert dashboard.app is not None

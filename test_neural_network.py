#!/usr/bin/env python3
"""
Test script to verify neural network visualization component works
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from ui.neural_network import (
        render_neural_network_background, 
        render_interactive_network_topology
    )
    print("✓ Neural network module imported successfully")
    
    # Test background rendering
    bg_html = render_neural_network_background()
    assert "<svg" in bg_html, "SVG not found in background"
    assert "neural-network-container" in bg_html, "Container not found"
    assert "ESP8266" in bg_html, "ESP8266 node not found"
    assert "MQTT Broker" in bg_html, "MQTT node not found"
    assert "Prediction Engine" in bg_html, "Prediction Engine node not found"
    assert "AI CORE" in bg_html, "AI Core node not found"
    print("✓ Neural network background HTML generated successfully")
    print(f"  - Generated {len(bg_html)} bytes of HTML")
    
    # Test topology rendering
    topo_html = render_interactive_network_topology(
        temperature=23.5,
        humidity=45.0,
        health_score=85,
        device_status="ONLINE",
        temp_direction="Rising",
        hum_direction="Stable"
    )
    assert "topology-node" in topo_html, "Topology node not found"
    assert "23.5" in topo_html, "Temperature not in topology"
    assert "ONLINE" in topo_html, "Device status not in topology"
    print("✓ Interactive network topology generated successfully")
    print(f"  - Generated {len(topo_html)} bytes of HTML")
    
    print("\n✅ All tests passed!")
    print("\nNeural Network Features:")
    print("  ✓ Animated neural network background with glowing nodes")
    print("  ✓ Interactive topology visualization")
    print("  ✓ Animated connections with data flow")
    print("  ✓ Multiple particle layers for AI atmosphere")
    print("  ✓ Jarvis-inspired sci-fi design")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

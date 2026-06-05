"""
Neural Network Visualization Component - Jarvis-Inspired
Renders animated glowing neural network with nodes and connections
"""
import streamlit as st
import numpy as np
from datetime import datetime


def render_neural_network_background():
    """Render animated neural network as SVG background"""
    html = """
    <style>
    @keyframes nodeGlow {
        0%, 100% { r: 12px; filter: drop-shadow(0 0 8px rgba(56,189,248,0.6)); }
        50% { r: 14px; filter: drop-shadow(0 0 16px rgba(56,189,248,0.9)); }
    }
    
    @keyframes nodePulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }
    
    @keyframes connectionFlow {
        0% {
            stroke-dashoffset: 1000;
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            stroke-dashoffset: 0;
            opacity: 0;
        }
    }
    
    @keyframes connectionPulse {
        0%, 100% { stroke-width: 1px; opacity: 0.3; }
        50% { stroke-width: 2px; opacity: 0.8; }
    }
    
    @keyframes particleFloat {
        0%, 100% { 
            transform: translate(0, 0) scale(1);
            opacity: 0.1;
        }
        25% { 
            opacity: 0.4;
        }
        50% { 
            transform: translate(100px, -100px) scale(1.2);
            opacity: 0.6;
        }
        75% {
            opacity: 0.3;
        }
    }
    
    @keyframes particleFloat2 {
        0%, 100% { 
            transform: translate(0, 0) scale(1);
            opacity: 0.1;
        }
        25% { 
            opacity: 0.4;
        }
        50% { 
            transform: translate(-120px, 80px) scale(0.8);
            opacity: 0.5;
        }
        75% {
            opacity: 0.2;
        }
    }
    
    @keyframes particleFloat3 {
        0%, 100% { 
            transform: translate(0, 0) scale(1);
            opacity: 0.15;
        }
        50% { 
            transform: translate(80px, 120px) scale(1.1);
            opacity: 0.5;
        }
    }
    
    .neural-network-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        pointer-events: none;
        background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%);
        overflow: hidden;
    }
    
    .neural-svg {
        position: absolute;
        width: 100%;
        height: 100%;
        opacity: 0.7;
    }
    
    .network-particle {
        position: absolute;
        border-radius: 50%;
        filter: blur(1px);
    }
    
    .particle-1 {
        width: 6px;
        height: 6px;
        background: radial-gradient(circle, #38bdf8, rgba(56,189,248,0.2));
        animation: particleFloat 15s infinite ease-in-out;
    }
    
    .particle-2 {
        width: 4px;
        height: 4px;
        background: radial-gradient(circle, #22c55e, rgba(34,197,94,0.2));
        animation: particleFloat2 18s infinite ease-in-out;
    }
    
    .particle-3 {
        width: 5px;
        height: 5px;
        background: radial-gradient(circle, #a78bfa, rgba(167,139,250,0.2));
        animation: particleFloat3 20s infinite ease-in-out;
    }
    
    .particle-4 {
        width: 3px;
        height: 3px;
        background: radial-gradient(circle, #facc15, rgba(250,204,21,0.2));
        animation: particleFloat 16s infinite ease-in-out;
    }
    
    .particle-5 {
        width: 5px;
        height: 5px;
        background: radial-gradient(circle, #38bdf8, rgba(56,189,248,0.2));
        animation: particleFloat2 17s infinite ease-in-out;
    }
    
    .particle-6 {
        width: 4px;
        height: 4px;
        background: radial-gradient(circle, #22c55e, rgba(34,197,94,0.2));
        animation: particleFloat3 19s infinite ease-in-out;
    }
    </style>
    
    <div class="neural-network-container">
        <svg class="neural-svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
            <defs>
                <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
                
                <filter id="glow-strong">
                    <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>
            
            <!-- Background ambient particles -->
            <circle cx="200" cy="200" r="80" fill="none" stroke="rgba(56,189,248,0.1)" stroke-width="1"/>
            <circle cx="200" cy="200" r="120" fill="none" stroke="rgba(56,189,248,0.05)" stroke-width="1"/>
            
            <circle cx="1700" cy="800" r="100" fill="none" stroke="rgba(34,197,94,0.1)" stroke-width="1"/>
            <circle cx="1700" cy="800" r="150" fill="none" stroke="rgba(34,197,94,0.05)" stroke-width="1"/>
            
            <circle cx="960" cy="540" r="200" fill="none" stroke="rgba(167,139,250,0.08)" stroke-width="1"/>
            <circle cx="960" cy="540" r="300" fill="none" stroke="rgba(167,139,250,0.04)" stroke-width="1"/>
            
            <!-- Network Nodes - AI Components -->
            <!-- ESP8266 Node (Bottom Left) -->
            <g>
                <circle cx="300" cy="800" r="20" fill="rgba(56,189,248,0.2)" stroke="#38bdf8" stroke-width="2" filter="url(#glow)"/>
                <circle cx="300" cy="800" r="28" fill="none" stroke="rgba(56,189,248,0.4)" stroke-width="1" opacity="0.6"/>
                <text x="300" y="860" text-anchor="middle" fill="#38bdf8" font-size="14" font-weight="bold">ESP8266</text>
            </g>
            
            <!-- MQTT Broker Node (Bottom Middle) -->
            <g>
                <circle cx="960" cy="850" r="20" fill="rgba(34,197,94,0.2)" stroke="#22c55e" stroke-width="2" filter="url(#glow)"/>
                <circle cx="960" cy="850" r="28" fill="none" stroke="rgba(34,197,94,0.4)" stroke-width="1" opacity="0.6"/>
                <text x="960" y="910" text-anchor="middle" fill="#22c55e" font-size="14" font-weight="bold">MQTT Broker</text>
            </g>
            
            <!-- Prediction Engine Node (Top Right) -->
            <g>
                <circle cx="1650" cy="300" r="20" fill="rgba(250,204,21,0.2)" stroke="#facc15" stroke-width="2" filter="url(#glow)"/>
                <circle cx="1650" cy="300" r="28" fill="none" stroke="rgba(250,204,21,0.4)" stroke-width="1" opacity="0.6"/>
                <text x="1650" y="340" text-anchor="middle" fill="#facc15" font-size="14" font-weight="bold">Prediction</text>
                <text x="1650" y="360" text-anchor="middle" fill="#facc15" font-size="14" font-weight="bold">Engine</text>
            </g>
            
            <!-- AI Core Node (Top Middle) -->
            <g>
                <circle cx="960" cy="200" r="24" fill="rgba(167,139,250,0.3)" stroke="#a78bfa" stroke-width="3" filter="url(#glow-strong)"/>
                <circle cx="960" cy="200" r="32" fill="none" stroke="rgba(167,139,250,0.5)" stroke-width="1" opacity="0.7"/>
                <text x="960" y="210" text-anchor="middle" fill="#a78bfa" font-size="16" font-weight="bold">AI CORE</text>
            </g>
            
            <!-- ML Anomaly Detection Node (Top Left) -->
            <g>
                <circle cx="300" cy="300" r="18" fill="rgba(167,139,250,0.2)" stroke="#a78bfa" stroke-width="2" filter="url(#glow)"/>
                <circle cx="300" cy="300" r="26" fill="none" stroke="rgba(167,139,250,0.4)" stroke-width="1" opacity="0.6"/>
                <text x="300" y="345" text-anchor="middle" fill="#a78bfa" font-size="12" font-weight="bold">ML</text>
                <text x="300" y="360" text-anchor="middle" fill="#a78bfa" font-size="12" font-weight="bold">Anomaly</text>
            </g>
            
            <!-- Connections with flowing animation -->
            <!-- ESP8266 to MQTT -->
            <line x1="320" y1="800" x2="940" y2="850" stroke="url(#gradient1)" stroke-width="2" opacity="0.4" stroke-dasharray="1000" style="animation: connectionFlow 4s infinite ease-in"/>
            <line x1="320" y1="800" x2="940" y2="850" stroke="#38bdf8" stroke-width="1" opacity="0.2" style="animation: connectionPulse 3s infinite ease-in-out"/>
            
            <!-- MQTT to AI Core -->
            <line x1="960" y1="830" x2="960" y2="224" stroke="url(#gradient2)" stroke-width="2" opacity="0.4" stroke-dasharray="1000" style="animation: connectionFlow 4s infinite ease-in; animation-delay: 0.5s"/>
            <line x1="960" y1="830" x2="960" y2="224" stroke="#22c55e" stroke-width="1" opacity="0.2" style="animation: connectionPulse 3s infinite ease-in-out; animation-delay: 0.5s"/>
            
            <!-- AI Core to Prediction Engine -->
            <line x1="984" y1="224" x2="1626" y2="324" stroke="url(#gradient3)" stroke-width="2" opacity="0.4" stroke-dasharray="1000" style="animation: connectionFlow 4s infinite ease-in; animation-delay: 1s"/>
            <line x1="984" y1="224" x2="1626" y2="324" stroke="#facc15" stroke-width="1" opacity="0.2" style="animation: connectionPulse 3s infinite ease-in-out; animation-delay: 1s"/>
            
            <!-- AI Core to ML Anomaly -->
            <line x1="936" y1="224" x2="318" y2="318" stroke="url(#gradient4)" stroke-width="2" opacity="0.4" stroke-dasharray="1000" style="animation: connectionFlow 4s infinite ease-in; animation-delay: 1.5s"/>
            <line x1="936" y1="224" x2="318" y2="318" stroke="#a78bfa" stroke-width="1" opacity="0.2" style="animation: connectionPulse 3s infinite ease-in-out; animation-delay: 1.5s"/>
            
            <!-- ML Anomaly to MQTT -->
            <line x1="318" y1="318" x2="942" y2="830" stroke="url(#gradient5)" stroke-width="2" opacity="0.4" stroke-dasharray="1000" style="animation: connectionFlow 4s infinite ease-in; animation-delay: 2s"/>
            <line x1="318" y1="318" x2="942" y2="830" stroke="#38bdf8" stroke-width="1" opacity="0.2" style="animation: connectionPulse 3s infinite ease-in-out; animation-delay: 2s"/>
            
            <!-- Prediction Engine to MQTT -->
            <line x1="1630" y1="320" x2="980" y2="830" stroke="url(#gradient6)" stroke-width="2" opacity="0.4" stroke-dasharray="1000" style="animation: connectionFlow 4s infinite ease-in; animation-delay: 2.5s"/>
            <line x1="1630" y1="320" x2="980" y2="830" stroke="#22c55e" stroke-width="1" opacity="0.2" style="animation: connectionPulse 3s infinite ease-in-out; animation-delay: 2.5s"/>
            
            <defs>
                <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#38bdf8;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#22c55e;stop-opacity:0.2" />
                </linearGradient>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#22c55e;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#a78bfa;stop-opacity:0.2" />
                </linearGradient>
                <linearGradient id="gradient3" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#a78bfa;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#facc15;stop-opacity:0.2" />
                </linearGradient>
                <linearGradient id="gradient4" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#a78bfa;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#a78bfa;stop-opacity:0.2" />
                </linearGradient>
                <linearGradient id="gradient5" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#a78bfa;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#22c55e;stop-opacity:0.2" />
                </linearGradient>
                <linearGradient id="gradient6" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#facc15;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#22c55e;stop-opacity:0.2" />
                </linearGradient>
            </defs>
        </svg>
        
        <!-- Floating particles -->
        <div class="network-particle particle-1" style="top: 10%; left: 5%; animation-delay: 0s;"></div>
        <div class="network-particle particle-2" style="top: 15%; left: 85%; animation-delay: 1s;"></div>
        <div class="network-particle particle-3" style="top: 60%; left: 15%; animation-delay: 2s;"></div>
        <div class="network-particle particle-4" style="top: 70%; left: 80%; animation-delay: 3s;"></div>
        <div class="network-particle particle-5" style="top: 25%; left: 45%; animation-delay: 1.5s;"></div>
        <div class="network-particle particle-6" style="top: 75%; left: 50%; animation-delay: 2.5s;"></div>
    </div>
    """
    return html


def render_interactive_network_topology(temperature, humidity, health_score, device_status, 
                                       temp_direction="Stable", hum_direction="Stable"):
    """
    Render interactive network topology with animated data flow
    Shows real-time status of each component
    """
    html = f"""
    <div class="network-topology">
        <div class="topology-node">
            <div class="node-circle" style="border-color: #38bdf8; box-shadow: 0 0 20px rgba(56, 189, 248, 0.8);">
                📡
            </div>
            <div class="node-label">
                ESP8266
                <div class="node-status">{device_status}</div>
            </div>
        </div>
        
        <div class="connection-arrow">→</div>
        
        <div class="topology-node">
            <div class="node-circle" style="border-color: #22c55e; box-shadow: 0 0 20px rgba(34, 197, 94, 0.8);">
                🌐
            </div>
            <div class="node-label">
                MQTT Broker
                <div class="node-status">{temperature}°C</div>
            </div>
        </div>
        
        <div class="connection-arrow">→</div>
        
        <div class="topology-node">
            <div class="node-circle" style="border-color: #facc15; box-shadow: 0 0 20px rgba(250, 204, 21, 0.8);">
                🔮
            </div>
            <div class="node-label">
                Prediction
                <div class="node-status">{temp_direction}</div>
            </div>
        </div>
        
        <div class="connection-arrow">→</div>
        
        <div class="topology-node">
            <div class="node-circle" style="border-color: #a78bfa; box-shadow: 0 0 20px rgba(167, 139, 250, 0.8); border-width: 3px;">
                🧠
            </div>
            <div class="node-label">
                AI Core
                <div class="node-status">{health_score}/100</div>
            </div>
        </div>
    </div>
    """
    
    return html


def render_network_status_badge(component_name, status, value, color):
    """Render a glowing status badge for network components"""
    html = f"""
    <style>
    @keyframes badgeGlow {{
        0%, 100% {{ 
            box-shadow: 0 0 8px {color}60, inset 0 0 8px {color}20;
        }}
        50% {{ 
            box-shadow: 0 0 16px {color}80, inset 0 0 12px {color}40;
        }}
    }}
    
    .status-badge {{
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        border: 1px solid {color}40;
        background: rgba(15, 23, 42, 0.9);
        color: {color};
        font-weight: 600;
        font-size: 12px;
        animation: badgeGlow 2s infinite;
        margin: 4px;
        backdrop-filter: blur(10px);
    }}
    </style>
    
    <div class="status-badge">
        {component_name}: {value}
    </div>
    """
    return html

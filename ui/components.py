"""
UI Components - Reusable Streamlit components with enterprise styling
"""
import streamlit as st


def render_metric_card(title, value, metric_type='info', trend=None, delta=None):
    """Render a styled metric card with glassmorphism effect and neural glow"""
    color_map = {
        'info': '#3b82f6',
        'success': '#22c55e',
        'warning': '#facc15',
        'critical': '#ef4444'
    }
    color = color_map.get(metric_type, '#3b82f6')
    
    # Extract RGB values for glow
    color_rgb = color.lstrip('#')
    r, g, b = int(color_rgb[0:2], 16), int(color_rgb[2:4], 16), int(color_rgb[4:6], 16)
    
    html = f"""
    <style>
    @keyframes metricGlow {{
        0%, 100% {{ 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba({r},{g},{b},0.2);
            border-left-width: 4px;
        }}
        50% {{ 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 30px rgba({r},{g},{b},0.5);
            border-left-width: 6px;
        }}
    }}
    
    .metric-card-glow {{
        animation: metricGlow 3s ease-in-out infinite;
    }}
    </style>
    <div class="metric-card-glow" style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.6));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s ease;
        border-left: 4px solid {color};
    ">
        <p style="margin: 0; color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">{title}</p>
        <p style="margin: 10px 0 5px 0; color: #fff; font-size: 32px; font-weight: 800; text-shadow: 0 0 10px {color}60;">{value}</p>
        {f'<p style="margin: 0; color: {color}; font-size: 13px;">{trend}</p>' if trend else ''}
        {f'<p style="margin: 0; color: #6ee7b7; font-size: 12px;">Δ {delta}</p>' if delta else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_recommendation(priority, title, message, action, icon, color):
    """Render a styled recommendation card with neural glow"""
    priority_colors = {
        'critical': '#ef4444',
        'warning': '#facc15',
        'info': '#3b82f6',
        'success': '#22c55e'
    }
    bg_color = priority_colors.get(priority, '#3b82f6')
    rgb = get_rgb(bg_color)
    
    html = f"""
    <style>
    @keyframes recommendGlow {{
        0%, 100% {{ 
            box-shadow: 0 8px 32px rgba({rgb}, 0.15), 0 0 15px rgba({rgb}, 0.1);
            border-left-width: 4px;
        }}
        50% {{ 
            box-shadow: 0 8px 32px rgba({rgb}, 0.25), 0 0 25px rgba({rgb}, 0.2);
            border-left-width: 6px;
        }}
    }}
    
    .recommend-card-glow {{
        animation: recommendGlow 2.5s ease-in-out infinite;
    }}
    </style>
    <div class="recommend-card-glow" style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.7));
        backdrop-filter: blur(20px);
        border: 1px solid {bg_color}40;
        border-left: 4px solid {bg_color};
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
                <p style="margin: 0 0 8px 0; color: {bg_color}; font-weight: 700; font-size: 14px; text-shadow: 0 0 8px {bg_color}40;">
                    {title}
                </p>
                <p style="margin: 0 0 10px 0; color: #cbd5e1; font-size: 13px; line-height: 1.5;">
                    {message}
                </p>
                <button style="
                    background: {bg_color}20;
                    color: {bg_color};
                    border: 1px solid {bg_color}40;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                ">{action}</button>
            </div>
            <div style="font-size: 24px; margin-left: 16px;">{icon}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_health_score(score):
    """Render building health score gauge with neural glow"""
    if score >= 80:
        color = '#22c55e'
        status = 'Excellent'
    elif score >= 60:
        color = '#facc15'
        status = 'Good'
    elif score >= 40:
        color = '#f97316'
        status = 'Fair'
    else:
        color = '#ef4444'
        status = 'Poor'
    
    html = f"""
    <style>
    @keyframes healthGlow {{
        0%, 100% {{ box-shadow: 0 0 30px {color}40, 0 0 60px {color}20; }}
        50% {{ box-shadow: 0 0 40px {color}60, 0 0 80px {color}40; }}
    }}
    
    .health-gauge {{
        animation: healthGlow 3s ease-in-out infinite;
    }}
    </style>
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.6)); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.2);">
        <p style="margin: 0 0 15px 0; color: #9ca3af; font-size: 12px;">BUILDING HEALTH SCORE</p>
        <div class="health-gauge" style="
            width: 120px;
            height: 120px;
            margin: 0 auto 15px;
            border-radius: 50%;
            background: conic-gradient({color} {score}%, #1e293b 0%);
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background: #0f172a;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
            ">
                <p style="margin: 0; color: {color}; font-size: 32px; font-weight: 800; text-shadow: 0 0 10px {color}80;">{score}</p>
                <p style="margin: 5px 0 0 0; color: #64748b; font-size: 11px;">/ 100</p>
            </div>
        </div>
        <p style="margin: 0; color: {color}; font-weight: 700; font-size: 14px; text-shadow: 0 0 8px {color}40;">{status}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_rgb(hex_color):
    """Convert hex color to RGB for CSS"""
    hex_color = hex_color.lstrip('#')
    return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"


def render_prediction_card(metric, prediction_data):
    """Render a prediction card for a metric with neural glow"""
    if prediction_data.get('predicted_value') is None:
        return
    
    confidence = prediction_data.get('confidence', 0)
    trend = prediction_data.get('trend', 'unknown')
    risk = prediction_data.get('risk_level', 'unknown')
    current = prediction_data.get('current', 'N/A')
    predicted = prediction_data.get('predicted_value', 'N/A')
    
    metric_icons = {
        'co2': '💨',
        'temperature': '🌡️',
        'humidity': '💧',
        'power': '⚡'
    }
    
    html = f"""
    <style>
    @keyframes predictionGlow {{
        0%, 100% {{ 
            box-shadow: 0 0 15px rgba(56,189,248,0.1);
        }}
        50% {{ 
            box-shadow: 0 0 30px rgba(56,189,248,0.25);
        }}
    }}
    
    .prediction-card {{
        animation: predictionGlow 3s ease-in-out infinite;
    }}
    </style>
    <div class="prediction-card" style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.5));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
    ">
        <p style="margin: 0 0 10px 0; color: #9ca3af; font-size: 12px;">{metric_icons.get(metric, '📊')} {metric.upper()}</p>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="margin: 0; color: #cbd5e1; font-size: 12px;">Current</p>
                <p style="margin: 5px 0 0 0; color: #fff; font-size: 20px; font-weight: 700; text-shadow: 0 0 8px rgba(34,197,94,0.5);">{current}</p>
            </div>
            <div style="text-align: center; flex: 1;">
                <p style="margin: 0; color: {risk.split()[0]}; font-size: 14px;">{trend}</p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; color: #cbd5e1; font-size: 12px;">Predicted</p>
                <p style="margin: 5px 0 0 0; color: #fff; font-size: 20px; font-weight: 700; text-shadow: 0 0 8px rgba(34,197,94,0.5);">{predicted}</p>
            </div>
        </div>
        <div style="margin-top: 10px; background: #1e293b; border-radius: 6px; height: 4px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #3b82f6, #22c55e); height: 100%; width: {confidence}%;"></div>
        </div>
        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 11px; text-align: right;">{int(confidence)}% confidence</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

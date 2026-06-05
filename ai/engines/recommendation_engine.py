"""
Recommendation Engine - Generates intelligent suggestions based on room conditions
"""


class RecommendationEngine:
    """Generates prioritized recommendations for room optimization"""
    
    def __init__(self, co2_threshold=1000, temp_threshold=27, humidity_threshold=70, power_threshold=1200):
        self.co2_threshold = co2_threshold
        self.temp_threshold = temp_threshold
        self.humidity_threshold = humidity_threshold
        self.power_threshold = power_threshold
    
    def generate_recommendations(self, room_data, predictions, anomaly_status):
        """
        Generate intelligent recommendations based on current state and predictions
        
        Args:
            room_data: Current sensor readings
            predictions: Predictions from prediction engine
            anomaly_status: Current anomaly detection result
        
        Returns:
            List of recommendations sorted by priority
        """
        recommendations = []
        
        # Rule 1: CO2 Management
        if room_data['occupancy'] == 'Occupied':
            if room_data['co2'] > self.co2_threshold:
                recommendations.append({
                    'priority': 'critical',
                    'title': '🌬️ Ventilation Needed',
                    'message': f"CO2 at {room_data['co2']} ppm - Open windows or increase ventilation",
                    'action': 'Increase Air Exchange Rate',
                    'icon': '🔴',
                    'color': 'red'
                })
            elif predictions['co2'].get('risk_level') == '🟡 Warning':
                recommendations.append({
                    'priority': 'warning',
                    'title': '📈 CO2 Rising',
                    'message': f"Predicted CO2 spike ahead - {predictions['co2'].get('trend')}",
                    'action': 'Monitor CO2 levels',
                    'icon': '🟡',
                    'color': 'orange'
                })
        
        # Rule 2: Temperature Control
        if room_data['temperature'] > self.temp_threshold:
            if room_data['occupancy'] == 'Occupied':
                recommendations.append({
                    'priority': 'warning',
                    'title': '❄️ Temperature High',
                    'message': f"Temperature {room_data['temperature']}°C - Increase cooling",
                    'action': 'Lower Thermostat',
                    'icon': '🔴',
                    'color': 'red'
                })
        elif predictions['temperature'].get('trend') == '📈 Rising' and room_data['occupancy'] == 'Occupied':
            recommendations.append({
                'priority': 'info',
                'title': '🌡️ Temperature Rising',
                'message': f"Temperature expected to increase - Monitor comfort",
                'action': 'Prepare Cooling',
                'icon': '🟡',
                'color': 'orange'
            })
        
        # Rule 3: Humidity Management
        if room_data['humidity'] > self.humidity_threshold:
            recommendations.append({
                'priority': 'warning',
                'title': '💧 High Humidity',
                'message': f"Humidity {room_data['humidity']}% - May cause discomfort",
                'action': 'Increase Dehumidification',
                'icon': '🔴',
                'color': 'red'
            })
        
        # Rule 4: Energy Efficiency
        if room_data['occupancy'] == 'Empty' and room_data['power'] > self.power_threshold:
            recommendations.append({
                'priority': 'critical',
                'title': '⚡ Energy Waste',
                'message': f"Room empty but using {room_data['power']}W - Likely waste",
                'action': 'Reduce Power Consumption',
                'icon': '🔴',
                'color': 'red'
            })
        elif predictions['power'].get('trend') == '📈 Rising' and room_data['occupancy'] == 'Empty':
            recommendations.append({
                'priority': 'warning',
                'title': '📊 Power Increasing',
                'message': f"Power usage expected to increase while empty",
                'action': 'Investigate Power Draw',
                'icon': '🟡',
                'color': 'orange'
            })
        
        # Rule 5: Occupancy Insights
        if predictions['occupancy'].get('trend') == '📉 Likely to become empty':
            recommendations.append({
                'priority': 'info',
                'title': '👥 Room Likely Emptying',
                'message': f"Occupancy trend suggests room will soon be empty",
                'action': 'Prepare for Reduced Mode',
                'icon': '🔵',
                'color': 'blue'
            })
        elif predictions['occupancy'].get('trend') == '📈 More likely to be occupied' and room_data['occupancy'] == 'Empty':
            recommendations.append({
                'priority': 'info',
                'title': '📈 Activity Expected',
                'message': f"Pattern suggests increased occupancy coming",
                'action': 'Prepare Systems',
                'icon': '🔵',
                'color': 'blue'
            })
        
        # Rule 6: Anomaly Response
        if anomaly_status == 'Anomaly':
            recommendations.insert(0, {
                'priority': 'critical',
                'title': '🚨 Anomaly Detected',
                'message': f"Unusual sensor patterns detected - Investigate immediately",
                'action': 'Review Sensor Data',
                'icon': '🔴',
                'color': 'red'
            })
        
        # Rule 7: Comfort Optimization
        if (room_data['occupancy'] == 'Occupied' and 
            18 <= room_data['temperature'] <= 24 and 
            40 <= room_data['humidity'] <= 60 and 
            room_data['co2'] < 800):
            recommendations.append({
                'priority': 'success',
                'title': '✨ Optimal Conditions',
                'message': f"Room conditions are ideal for comfort and productivity",
                'action': 'Maintain Current Settings',
                'icon': '🟢',
                'color': 'green'
            })
        
        # Sort by priority
        priority_order = {'critical': 0, 'warning': 1, 'info': 2, 'success': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations[:5]  # Return top 5 recommendations

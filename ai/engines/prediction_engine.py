"""
Prediction Engine - Forecasts future room conditions using time-series analysis
"""
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta


class PredictionEngine:
    """Predicts future room conditions using historical data"""
    
    def __init__(self, lookback_minutes=20):
        """
        Args:
            lookback_minutes: How many minutes of history to use for predictions
        """
        self.lookback_minutes = lookback_minutes
    
    def predict_metric(self, historical_data, room_name, metric, minutes_ahead=10):
        """
        Predict a metric value for a specific room
        
        Args:
            historical_data: List of sensor readings from session_state.history
            room_name: Name of the room to predict for
            metric: Metric to predict (co2, temperature, humidity, power)
            minutes_ahead: How many minutes into the future to predict
        
        Returns:
            dict with predicted_value, confidence, trend, risk_level
        """
        # Filter data for this room
        room_data = [d for d in historical_data if d.get('room') == room_name]
        
        if len(room_data) < 3:
            return {
                'predicted_value': None,
                'confidence': 0,
                'trend': 'unknown',
                'risk_level': 'unknown',
                'message': 'Insufficient data'
            }
        
        # Extract metric values
        values = np.array([float(d.get(metric, 0)) for d in room_data[-self.lookback_minutes:]])
        
        if len(values) < 2:
            return {
                'predicted_value': None,
                'confidence': 0,
                'trend': 'unknown',
                'risk_level': 'unknown',
                'message': 'Insufficient data'
            }
        
        # Simple linear extrapolation with exponential weight
        x = np.arange(len(values))
        weights = np.exp(np.linspace(-1, 0, len(values)))  # Recent data weighted higher
        
        try:
            coeffs = np.polyfit(x, values, 1, w=weights)
            # Predict next value
            future_x = len(values) + (minutes_ahead / 2)  # 2 readings per minute
            predicted = float(np.polyval(coeffs, future_x))
            
            # Calculate confidence based on data variance
            recent_values = values[-5:]
            variance = np.var(recent_values)
            confidence = min(1.0, 1.0 - (variance / (np.mean(recent_values) + 1)))
            
            # Determine trend
            slope = coeffs[0]
            trend = self._get_trend(slope, metric)
            
            # Determine risk level
            risk_level = self._assess_risk(predicted, metric)
            
            return {
                'predicted_value': round(predicted, 1),
                'confidence': round(confidence * 100, 1),
                'trend': trend,
                'risk_level': risk_level,
                'slope': slope,
                'current': values[-1]
            }
        
        except Exception as e:
            return {
                'predicted_value': None,
                'confidence': 0,
                'trend': 'unknown',
                'risk_level': 'unknown',
                'error': str(e)
            }
    
    def _get_trend(self, slope, metric):
        """Classify trend as rising, stable, or falling"""
        threshold = {
            'co2': 5,
            'temperature': 0.1,
            'humidity': 2,
            'power': 50
        }.get(metric, 1)
        
        if slope > threshold:
            return '📈 Rising'
        elif slope < -threshold:
            return '📉 Falling'
        else:
            return '➡️ Stable'
    
    def _assess_risk(self, value, metric):
        """Assess risk level based on predicted value"""
        thresholds = {
            'co2': {'warning': 1000, 'critical': 1200},
            'temperature': {'warning': 27, 'critical': 30},
            'humidity': {'warning': 70, 'critical': 80},
            'power': {'warning': 2200, 'critical': 2800}
        }
        
        if metric not in thresholds:
            return 'unknown'
        
        t = thresholds[metric]
        if value >= t['critical']:
            return '🔴 Critical'
        elif value >= t['warning']:
            return '🟡 Warning'
        else:
            return '🟢 Normal'
    
    def predict_occupancy_trend(self, historical_data, room_name):
        """Predict if room is likely to have more or less occupancy"""
        room_data = [d for d in historical_data if d.get('room') == room_name]
        
        if len(room_data) < 5:
            return {'trend': 'unknown', 'confidence': 0}
        
        # Check recent occupancy pattern
        recent_occupancy = [1 if d.get('occupancy') == 'Occupied' else 0 
                           for d in room_data[-10:]]
        
        trend_value = sum(recent_occupancy[-5:]) - sum(recent_occupancy[:5])
        
        if trend_value > 1:
            return {'trend': '📈 More likely to be occupied', 'confidence': 70}
        elif trend_value < -1:
            return {'trend': '📉 Likely to become empty', 'confidence': 70}
        else:
            return {'trend': '➡️ Occupancy stable', 'confidence': 50}
    
    def get_all_predictions(self, historical_data, room_name, minutes_ahead=10):
        """Get predictions for all key metrics"""
        predictions = {}
        for metric in ['co2', 'temperature', 'humidity', 'power']:
            predictions[metric] = self.predict_metric(
                historical_data, room_name, metric, minutes_ahead
            )
        predictions['occupancy'] = self.predict_occupancy_trend(
            historical_data, room_name
        )
        return predictions

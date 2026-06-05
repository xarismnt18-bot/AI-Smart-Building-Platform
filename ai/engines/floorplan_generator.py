"""
Floorplan Generator - Creates interactive smart building floorplan visualization
"""
import plotly.graph_objects as go
import plotly.express as px


class FloorplanGenerator:
    """Generates interactive floorplan visualization"""
    
    # Room positions on floorplan (x, y coordinates)
    ROOM_POSITIONS = {
        'Main Office': {'x': 100, 'y': 300, 'width': 150, 'height': 120},
        'HR Office': {'x': 300, 'y': 300, 'width': 120, 'height': 120},
        'Conference Room': {'x': 100, 'y': 80, 'width': 180, 'height': 150},
        'Demo Room': {'x': 320, 'y': 80, 'width': 140, 'height': 150}
    }
    
    def __init__(self):
        self.status_colors = {
            'normal': '#22c55e',      # Green
            'warning': '#facc15',      # Yellow
            'critical': '#ef4444',     # Red
            'empty': '#64748b'         # Gray
        }
    
    def get_room_status(self, room_data):
        """Determine room status color based on conditions"""
        if room_data.get('ml_status') == 'Anomaly':
            return 'critical'
        elif room_data.get('alerts', 0) > 0:
            return 'critical'
        elif (room_data.get('co2', 0) > 1000 or 
              room_data.get('temperature', 0) > 27 or
              room_data.get('humidity', 0) > 70):
            return 'warning'
        elif room_data.get('occupancy') == 'Empty':
            return 'empty'
        else:
            return 'normal'
    
    def create_floorplan(self, current_df):
        """
        Create interactive SVG-based floorplan with color-coded rooms
        
        Args:
            current_df: DataFrame with current room data
        
        Returns:
            Plotly figure with interactive floorplan
        """
        if current_df.empty:
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add building background
        fig.add_shape(
            type='rect',
            x0=50, x1=500, y0=30, y1=450,
            line=dict(color='#334155', width=3),
            fillcolor='#0f172a',
            opacity=0.8,
            layer='below'
        )
        
        # Add rooms
        for room_name, pos in self.ROOM_POSITIONS.items():
            room_data = current_df[current_df['room'] == room_name]
            
            if room_data.empty:
                continue
            
            room_info = room_data.iloc[0]
            status = self.get_room_status(room_info)
            color = self.status_colors[status]
            
            # Add room rectangle
            fig.add_shape(
                type='rect',
                x0=pos['x'], x1=pos['x'] + pos['width'],
                y0=pos['y'], y1=pos['y'] + pos['height'],
                line=dict(color=color, width=3),
                fillcolor=color,
                opacity=0.3,
                name=room_name,
                layer='above'
            )
            
            # Add room label with hover info
            hover_text = self._get_hover_text(room_info)
            fig.add_annotation(
                x=pos['x'] + pos['width']/2,
                y=pos['y'] + pos['height']/2,
                text=f"<b>{room_name}</b><br>{room_info.get('occupancy', 'Unknown')}",
                showarrow=False,
                font=dict(size=12, color='#fff', family='Arial'),
                bgcolor=color,
                opacity=0.8,
                bordercolor=color,
                borderwidth=2,
                borderpad=4,
                hovertext=hover_text,
                hoverlabel=dict(bgcolor=color, bordercolor='#fff', font=dict(color='#fff'))
            )
            
            # Add status indicator (blinking effect via opacity)
            if status == 'critical':
                fig.add_shape(
                    type='circle',
                    x0=pos['x'] + pos['width'] - 20, x1=pos['x'] + pos['width'] - 5,
                    y0=pos['y'] + pos['height'] - 15, y1=pos['y'] + pos['height'],
                    line=dict(color='#ef4444', width=2),
                    fillcolor='#ef4444',
                    opacity=0.8
                )
        
        # Add legend
        legend_y = 420
        fig.add_annotation(
            x=50, y=legend_y,
            text='<b>Status Legend</b>',
            showarrow=False,
            font=dict(size=14, color='#fff'),
            xanchor='left'
        )
        
        legend_items = [
            ('🟢 Normal', '#22c55e'),
            ('🟡 Warning', '#facc15'),
            ('🔴 Critical', '#ef4444'),
            ('⚫ Empty', '#64748b')
        ]
        
        for i, (label, color) in enumerate(legend_items):
            fig.add_annotation(
                x=50, y=legend_y - 30 - (i * 25),
                text=label,
                showarrow=False,
                font=dict(size=11, color='#fff'),
                xanchor='left'
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': '<b>🏢 Smart Building Floorplan</b>',
                'font': {'size': 24, 'color': '#fff'},
                'x': 0.5,
                'xanchor': 'center'
            },
            paper_bgcolor='#0f172a',
            plot_bgcolor='#0f172a',
            xaxis=dict(
                range=[40, 520],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True
            ),
            yaxis=dict(
                range=[20, 460],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True
            ),
            hovermode='closest',
            margin=dict(l=20, r=20, t=80, b=20),
            height=500,
            font=dict(family='Arial, sans-serif', color='#fff'),
            showlegend=False
        )
        
        return fig
    
    def _get_hover_text(self, room_info):
        """Generate hover text for room"""
        text = f"<b>{room_info.get('room', 'Room')}</b><br>"
        text += f"CO2: {room_info.get('co2', 'N/A')} ppm<br>"
        text += f"Temp: {room_info.get('temperature', 'N/A')}°C<br>"
        text += f"Humidity: {room_info.get('humidity', 'N/A')}%<br>"
        text += f"Power: {room_info.get('power', 'N/A')} W<br>"
        text += f"Occupancy: {room_info.get('occupancy', 'Unknown')}<br>"
        text += f"Status: {room_info.get('ml_status', 'Unknown')}"
        return text
    
    def create_building_overview(self, current_df, history_df):
        """Create overview metrics for entire building"""
        if current_df.empty:
            return {}
        
        total_rooms = len(current_df)
        occupied_rooms = (current_df['occupancy'] == 'Occupied').sum()
        critical_alerts = (current_df['alerts'] > 0).sum()
        anomalies = (current_df['ml_status'] == 'Anomaly').sum()
        avg_co2 = current_df['co2'].mean()
        total_power = current_df['power'].sum()
        
        return {
            'total_rooms': total_rooms,
            'occupied_rooms': occupied_rooms,
            'occupancy_rate': f"{(occupied_rooms/total_rooms*100):.0f}%",
            'critical_alerts': critical_alerts,
            'anomalies': anomalies,
            'avg_co2': f"{avg_co2:.0f}",
            'total_power': f"{total_power:.0f}",
            'health_score': self._calculate_health_score(current_df)
        }
    
    def _calculate_health_score(self, current_df):
        """Calculate overall building health score 0-100"""
        if current_df.empty:
            return 0
        
        score = 100
        
        # Deduct for alerts
        alert_penalty = (current_df['alerts'].sum() / len(current_df)) * 10
        score -= alert_penalty
        
        # Deduct for anomalies
        anomaly_count = (current_df['ml_status'] == 'Anomaly').sum()
        anomaly_penalty = (anomaly_count / len(current_df)) * 15
        score -= anomaly_penalty
        
        # Deduct for high CO2
        high_co2 = (current_df['co2'] > 1000).sum()
        co2_penalty = (high_co2 / len(current_df)) * 10
        score -= co2_penalty
        
        # Deduct for high temperature
        high_temp = (current_df['temperature'] > 27).sum()
        temp_penalty = (high_temp / len(current_df)) * 5
        score -= temp_penalty
        
        return max(0, min(100, int(score)))

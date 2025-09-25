"""
Visualization module for COVID-19 Belgium Dashboard

This module contains all visualization functions including the Dash dashboard,
choropleth maps, and supporting utilities for interactive data exploration.
"""

import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging

import dash
from dash import dcc, html, Input, Output

from config import (
    DASHBOARD_CONFIG, VARIABLE_OPTIONS, COLOR_SCALES, VARIABLE_LABELS,
    HOVER_LABELS, FILE_PATHS, DATA_PROCESSING
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def iso_to_date(year: int, week: int) -> datetime:
    """
    Convert ISO year and week to date (Monday of that week).
    
    Args:
        year: ISO year
        week: ISO week number
        
    Returns:
        datetime: Monday of the specified week
    """
    # January 4th is always in the first ISO week
    jan4 = datetime(int(year), 1, 4)
    # Find Monday of first ISO week
    first_monday = jan4 - pd.Timedelta(days=jan4.weekday())
    # Calculate Monday of target week
    target_date = first_monday + pd.Timedelta(weeks=int(week) - 1)
    return target_date


def load_and_process_geospatial_data(data: pd.DataFrame, 
                                   shapefile_path: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Load and process Belgian shapefile data and merge with COVID data.
    
    Args:
        data: COVID data with municipality information
        shapefile_path: Path to Belgian municipalities shapefile
        
    Returns:
        gpd.GeoDataFrame: Merged geospatial data
    """
    if shapefile_path is None:
        # Try multiple possible locations for the shapefile
        possible_paths = [
            FILE_PATHS["shapefile"],  # Default: data_public/shapefiles/
            FILE_PATHS["shapefile"].parent.parent / "sh_statbel_statistical_sectors_20190101.shp",  # data_public/
            FILE_PATHS["shapefile"].parent / "sh_statbel_statistical_sectors_20190101.shp"  # shapefiles/
        ]
        
        shapefile_path = None
        for path in possible_paths:
            if path.exists():
                shapefile_path = str(path)
                logger.info(f"📍 Found shapefile at: {shapefile_path}")
                break
        
        if shapefile_path is None:
            logger.warning("⚠️ Shapefile not found locally, attempting to download...")
            
            # Try to download the shapefile
            from data_processing import download_and_extract_shapefile
            
            if download_and_extract_shapefile():
                # Re-check for shapefile after download
                for path in possible_paths:
                    if path.exists():
                        shapefile_path = str(path)
                        logger.info(f"✅ Using downloaded shapefile: {shapefile_path}")
                        break
            
            if shapefile_path is None:
                logger.error("❌ Could not find or download shapefile from any of these locations:")
                for path in possible_paths:
                    logger.error(f"   - {path}")
                raise FileNotFoundError(f"Belgian shapefile not found and download failed. Please manually place the shapefile in one of the expected locations.")
    
    logger.info("🗺️ Loading Belgium shapefile...")
    
    try:
        # Load the shapefile
        belgium_shapes = gpd.read_file(shapefile_path)
        logger.info(f"✅ Loaded {len(belgium_shapes)} geographic units")
        
        # Extract municipality codes
        belgium_shapes['MUNICIPALITY_NIS'] = belgium_shapes['CNIS5_2019'].astype(str).str[:5]
        belgium_shapes['MUNICIPALITY_NIS'] = pd.to_numeric(
            belgium_shapes['MUNICIPALITY_NIS'], errors='coerce'
        )
        
        # Aggregate to municipality level
        logger.info("🔧 Aggregating statistical sectors to municipalities...")
        belgium_municipalities = belgium_shapes.dissolve(
            by='MUNICIPALITY_NIS', aggfunc='first'
        ).reset_index()
        belgium_municipalities['NIS5'] = belgium_municipalities['MUNICIPALITY_NIS']
        
        logger.info(f"✅ Created {len(belgium_municipalities)} municipality polygons")
        
        # Merge with COVID data
        map_geo_data = belgium_municipalities.merge(data, on='NIS5', how='left')
        
        # Convert to WGS84 for web mapping
        if map_geo_data.crs != DATA_PROCESSING["coordinate_system"]:
            logger.info(f"🔄 Converting to {DATA_PROCESSING['coordinate_system']}...")
            map_geo_data = map_geo_data.to_crs(DATA_PROCESSING["coordinate_system"])
        
        # Optimize geometries
        logger.info("⚡ Optimizing geometries for faster rendering...")
        map_geo_data['geometry'] = map_geo_data['geometry'].simplify(
            tolerance=DATA_PROCESSING["geometry_simplification_tolerance"], 
            preserve_topology=True
        )
        
        # Calculate rates if needed
        if 'cases_per_1000' not in map_geo_data.columns and 'CASES' in map_geo_data.columns:
            map_geo_data['cases_per_1000'] = (
                map_geo_data['CASES'] / map_geo_data['POPULATION'] * 1000
            ).fillna(0)
        
        # Fill missing values
        for col in ['CASES', 'SI', 'POPULATION', 'vacc_pct']:
            if col in map_geo_data.columns:
                map_geo_data[col] = map_geo_data[col].fillna(0)
        
        logger.info(f"✅ Successfully merged: {len(map_geo_data)} records")
        return map_geo_data
        
    except Exception as e:
        logger.error(f"❌ Error loading shapefile: {e}")
        raise


def prepare_dashboard_data(geo_data: gpd.GeoDataFrame, 
                          filter_time_period: Optional[Tuple[datetime, datetime]] = None) -> Dict:
    """
    Prepare and optimize data for dashboard use.
    
    Args:
        geo_data: Geospatial data with COVID information
        filter_time_period: Optional tuple of (start_date, end_date) to filter data
        
    Returns:
        Dict: Prepared data including cached time periods and metadata
    """
    logger.info("🔧 Preparing dashboard data...")
    
    dashboard_data = geo_data.copy()
    
    # Filter time period if specified
    if filter_time_period and 'date' in dashboard_data.columns:
        start_date, end_date = filter_time_period
        dashboard_data = dashboard_data[
            (dashboard_data['date'] >= start_date) & 
            (dashboard_data['date'] <= end_date)
        ].copy()
        logger.info(f"Filtered to {len(dashboard_data)} records between {start_date} and {end_date}")
    
    # Identify time column and prepare time controls
    time_columns = [col for col in dashboard_data.columns 
                   if any(keyword in col.lower() for keyword in ['week', 'date', 'time'])]
    
    time_info = {
        'time_columns': time_columns,
        'time_column': time_columns[0] if time_columns else None,
        'unique_times': [],
        'time_range': [],
        'time_marks': {}
    }
    
    if time_columns:
        time_column = time_columns[0]
        unique_times = sorted([t for t in dashboard_data[time_column].unique() if pd.notna(t)])
        time_info['unique_times'] = unique_times
        time_info['time_range'] = list(range(len(unique_times)))
        time_info['time_marks'] = _create_adaptive_time_marks(unique_times)
    
    # Pre-process and cache all time periods for performance
    cached_data = {}
    cached_geojson = {}
    
    if time_info['time_column']:
        logger.info("⚡ Pre-processing data for all time periods...")
        for i, time_val in enumerate(time_info['unique_times']):
            time_data = dashboard_data[
                dashboard_data[time_info['time_column']] == time_val
            ].copy().reset_index(drop=True)
            
            # Convert dates to strings for JSON serialization
            time_data_for_json = time_data.copy()
            for col in time_data_for_json.columns:
                if time_data_for_json[col].dtype == 'datetime64[ns]':
                    time_data_for_json[col] = time_data_for_json[col].astype(str)
            
            # Pre-generate GeoJSON
            geojson_dict = json.loads(time_data_for_json.to_json())
            
            cached_data[i] = time_data
            cached_geojson[i] = geojson_dict
        
        logger.info("✅ All time periods pre-processed and cached!")
    
    return {
        'data': dashboard_data,
        'time_info': time_info,
        'cached_data': cached_data,
        'cached_geojson': cached_geojson,
        'essential_columns': [
            'NIS5', 'T_MUN_NL', 'T_PROVI_NL', 'date', 'CASES', 
            'SI', 'vacc_pct', 'POPULATION', 'geometry'
        ]
    }


def _create_adaptive_time_marks(unique_times: List) -> Dict[int, str]:
    """Create adaptive time marks based on the number of time periods."""
    total_periods = len(unique_times)
    time_marks = {}
    
    if total_periods <= 10:
        # Few periods: Show all
        for i, time_val in enumerate(unique_times):
            if hasattr(time_val, 'strftime'):
                time_marks[i] = time_val.strftime('%m-%d')
            else:
                # Format as "Week X" for week numbers
                time_marks[i] = f'Week {time_val}'
    
    elif total_periods <= 25:
        # Medium periods: Show every 2nd-3rd
        step = max(2, total_periods // 8)
        for i in range(0, total_periods, step):
            time_val = unique_times[i]
            if hasattr(time_val, 'strftime'):
                time_marks[i] = time_val.strftime('%m-%d')
            else:
                # Format as "Week X" for week numbers
                time_marks[i] = f'Week {time_val}'
        
        # Always include the last period
        if (total_periods - 1) not in time_marks:
            time_val = unique_times[-1]
            if hasattr(time_val, 'strftime'):
                time_marks[total_periods - 1] = time_val.strftime('%m-%d')
            else:
                # Format as "Week X" for week numbers
                time_marks[total_periods - 1] = f'Week {time_val}'
    
    else:
        # Many periods: Show monthly/quarterly marks
        step = max(total_periods // 8, 1)
        for i in range(0, total_periods, step):
            time_val = unique_times[i]
            if hasattr(time_val, 'strftime'):
                time_marks[i] = time_val.strftime('%b %Y')
            else:
                # Format as "Week X" for week numbers
                time_marks[i] = f'Week {time_val}'
    
    return time_marks


def create_choropleth_map(selected_var: str, time_value: int, 
                         prepared_data: Dict) -> Tuple[go.Figure, float, int]:
    """
    Create optimized choropleth map for selected variable and time period.
    
    Args:
        selected_var: Variable to visualize
        time_value: Index of time period to display
        prepared_data: Prepared dashboard data dictionary
        
    Returns:
        Tuple of (plotly figure, total value, number of data points)
    """
    logger.info(f"🔍 Creating map for variable: {selected_var}, time: {time_value}")
    
    # Use cached data if available
    cached_data = prepared_data['cached_data']
    cached_geojson = prepared_data['cached_geojson']
    time_info = prepared_data['time_info']
    
    if time_value in cached_data:
        plot_data = cached_data[time_value]
        geojson_dict = cached_geojson[time_value]
        
        if time_info['time_column']:
            selected_time = time_info['unique_times'][time_value]
            time_label = f" - {selected_time.strftime('%Y-%m-%d') if hasattr(selected_time, 'strftime') else selected_time}"
        else:
            time_label = ""
    else:
        plot_data = prepared_data['data']
        geojson_dict = json.loads(plot_data.to_json())
        time_label = " - All Time"
    
    try:
        # Find municipality name column
        hover_name_col = _find_municipality_name_column(plot_data)
        
        logger.info(f"🔍 Variable range: {plot_data[selected_var].min():.2f} - {plot_data[selected_var].max():.2f}")
        logger.info(f"🔍 Data points: {len(plot_data)}")
        
        # Create choropleth
        fig = px.choropleth_mapbox(
            plot_data,
            geojson=geojson_dict,
            locations=plot_data.index,
            color=selected_var,
            color_continuous_scale=COLOR_SCALES.get(selected_var, 'Viridis'),
            mapbox_style="carto-positron",
            zoom=DASHBOARD_CONFIG["map_zoom"],
            center=DASHBOARD_CONFIG["map_center"],
            opacity=0.7,
            labels=HOVER_LABELS,
            hover_name=hover_name_col
        )
        
        # Customize hover template
        hover_template = _create_hover_template()
        customdata = plot_data[['CASES', 'SI', 'vacc_pct', 'POPULATION']].values
        
        fig.update_traces(
            hovertemplate=hover_template,
            customdata=customdata,
            hovertext=plot_data[hover_name_col]
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f"{VARIABLE_LABELS.get(selected_var, selected_var)} - Belgium Municipalities{time_label}",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            height=DASHBOARD_CONFIG["map_height"],
            margin={"r":20,"t":80,"l":20,"b":20}
        )
        
        total_value = plot_data[selected_var].sum()
        logger.info(f"✅ Choropleth map created successfully! Total value: {total_value:.2f}")
        
        return fig, total_value, len(plot_data)
        
    except Exception as e:
        logger.error(f"❌ Choropleth creation failed: {e}")
        return _create_fallback_map(plot_data, selected_var, time_label)


def _find_municipality_name_column(data: pd.DataFrame) -> str:
    """Find the best column to use for municipality names in hover."""
    for col in ['T_MUN_NL', 'T_MUN_FR', 'T_NIS6_NL', 'MUNICIPALITY_NIS']:
        if col in data.columns and data[col].notna().any():
            return col
    
    # Fallback: create generic names
    data['municipality_name'] = 'Municipality ' + data.index.astype(str)
    return 'municipality_name'


def _create_hover_template() -> str:
    """Create standardized hover template for maps."""
    hover_template = "<b>%{hovertext}</b><br><br>"
    hover_template += "Cases: %{customdata[0]:,}<br>"
    hover_template += "Stringency Index (SI): %{customdata[1]:.1f}<br>"
    hover_template += "Vaccinations: %{customdata[2]:.1f}%<br>"
    hover_template += "Population: %{customdata[3]:,}<br>"
    hover_template += "<extra></extra>"
    return hover_template


def _create_fallback_map(data: pd.DataFrame, selected_var: str, time_label: str) -> Tuple[go.Figure, float, int]:
    """Create fallback scatter plot if choropleth fails."""
    try:
        logger.info("🔄 Creating fallback scatter plot...")
        data['lon'] = data.geometry.centroid.x
        data['lat'] = data.geometry.centroid.y
        
        hover_name_col = _find_municipality_name_column(data)
        
        fig = px.scatter_mapbox(
            data,
            lat='lat',
            lon='lon',
            color=selected_var,
            size=selected_var,
            color_continuous_scale=COLOR_SCALES.get(selected_var, 'Viridis'),
            mapbox_style="carto-positron",
            zoom=DASHBOARD_CONFIG["map_zoom"],
            center=DASHBOARD_CONFIG["map_center"],
            hover_name=hover_name_col,
            labels=HOVER_LABELS
        )
        
        fig.update_layout(
            title=f"Belgium COVID Data - {VARIABLE_LABELS.get(selected_var, selected_var)}{time_label} (Scatter Plot Fallback)",
            height=DASHBOARD_CONFIG["map_height"]
        )
        
        return fig, data[selected_var].sum(), len(data)
        
    except Exception as e2:
        logger.error(f"❌ Even fallback failed: {e2}")
        
        fig = go.Figure()
        fig.add_annotation(
            text=f"Map creation failed.<br><br>Error: {str(e2)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.9)"
        )
        fig.update_layout(title="Map Error", height=DASHBOARD_CONFIG["map_height"])
        return fig, 0, 0


def create_dashboard_app(prepared_data: Dict) -> dash.Dash:
    """
    Create and configure the Dash dashboard application.
    
    Args:
        prepared_data: Prepared dashboard data dictionary
        
    Returns:
        dash.Dash: Configured Dash application
    """
    logger.info("🎛️ Creating Dash application...")
    
    app = dash.Dash(__name__)
    time_info = prepared_data['time_info']
    
    # Create layout
    app.layout = html.Div([
        # Header
        html.Div([
            html.H1("🇧🇪 Belgium COVID-19 Interactive Dashboard", 
                    style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
            html.P("Interactive Choropleth Map of Belgian Municipalities with Time Control",
                   style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 18})
        ], style={'padding': '20px'}),
        
        # Controls Section
        html.Div([
            # Variable Selection
            html.Div([
                html.Label("📊 Select Variable:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                dcc.Dropdown(
                    id='variable-dropdown',
                    options=VARIABLE_OPTIONS,
                    value='CASES',
                    style={'marginBottom': 20}
                )
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            # Time Selection
            html.Div([
                html.Label("📅 Select Time Period:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                dcc.Slider(
                    id='time-slider',
                    min=0,
                    max=len(time_info['time_range'])-1 if time_info['time_range'] else 0,
                    value=0,
                    marks=time_info['time_marks'],
                    step=1,
                    included=False,
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block', 'paddingLeft': '20px'})
        ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px'}),
        
        # Statistics Section
        html.Div([
            html.Div(id='statistics-display', style={'textAlign': 'center', 'marginBottom': 20})
        ]),
        
        # Map Section
        html.Div([
            dcc.Graph(
                id='choropleth-map',
                style={'height': f"{DASHBOARD_CONFIG['map_height']}px"}
            )
        ], style={'padding': '0 20px'}),
        
        # Footer
        html.Div([
            html.P("Data: Sciensano, StatBel, Oxford COVID-19 Government Response Tracker",
                   style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': 12, 'marginTop': 20})
        ], style={'padding': '20px'})
    ], style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh'})
    
    # Register callbacks
    _register_callbacks(app, prepared_data)
    
    # Add CSS styles
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
            .stat-card {
                text-align: center;
                padding: 15px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                min-width: 120px;
            }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    logger.info("✅ Dash app created successfully!")
    return app


def _register_callbacks(app: dash.Dash, prepared_data: Dict):
    """Register dashboard callbacks."""
    @app.callback(
        [Output('choropleth-map', 'figure'),
         Output('statistics-display', 'children')],
        [Input('variable-dropdown', 'value'),
         Input('time-slider', 'value')]
    )
    def update_map(selected_variable: str, selected_time: int):
        """Update map and statistics based on user selections."""
        logger.info(f"🔄 Updating map for variable: {selected_variable}, time: {selected_time}")
        
        try:
            # Create map
            fig, total_value, data_points = create_choropleth_map(
                selected_variable, selected_time, prepared_data
            )
            
            # Create statistics
            stats_display = _create_statistics_display(
                selected_variable, selected_time, total_value, data_points, prepared_data
            )
            
            return fig, stats_display
            
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")
            
            error_fig = go.Figure()
            error_fig.add_annotation(text=f"Callback Error: {str(e)}", 
                                   x=0.5, y=0.5, showarrow=False)
            error_stats = html.Div([html.H3("Error", style={'color': 'red'})])
            
            return error_fig, error_stats


def _create_statistics_display(selected_variable: str, selected_time: int, 
                              total_value: float, data_points: int, 
                              prepared_data: Dict) -> html.Div:
    """Create statistics display for the dashboard."""
    var_labels = {
        'CASES': ('COVID-19 Cases', '🦠'),
        'SI': ('Stringency Index', '📊'),
        'vacc_pct': ('Vaccination %', '💉'),
        'POPULATION': ('Population', '👥')
    }
    
    label, emoji = var_labels.get(selected_variable, ('Value', '📊'))
    
    # Get current time period data
    cached_data = prepared_data['cached_data']
    time_info = prepared_data['time_info']
    
    if selected_time in cached_data:
        current_data = cached_data[selected_time]
        if time_info['time_column']:
            selected_time_value = time_info['unique_times'][selected_time]
            time_label = f" - {selected_time_value.strftime('%Y-%m-%d') if hasattr(selected_time_value, 'strftime') else selected_time_value}"
        else:
            time_label = ""
    else:
        current_data = prepared_data['data']
        time_label = ""
    
    mean_val = current_data[selected_variable].mean()
    max_val = current_data[selected_variable].max()
    
    # Format based on variable type
    if selected_variable == 'vacc_pct':
        total_display = f"{total_value/len(current_data):.1f}%"
        mean_display = f"{mean_val:.1f}%"
        max_display = f"{max_val:.1f}%"
    else:
        total_display = f"{total_value:.0f}"
        mean_display = f"{mean_val:.1f}"
        max_display = f"{max_val:.0f}"
    
    return html.Div([
        html.H3(f"{emoji} {label} Statistics{time_label}", 
               style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': 20}),
        html.Div([
            html.Div([
                html.H4(total_display, style={'margin': 0, 'color': '#e74c3c'}),
                html.P("Average" if selected_variable == 'vacc_pct' else "Total", style={'margin': 0})
            ], className='stat-card'),
            html.Div([
                html.H4(mean_display, style={'margin': 0, 'color': '#3498db'}),
                html.P("Mean", style={'margin': 0})
            ], className='stat-card'),
            html.Div([
                html.H4(max_display, style={'margin': 0, 'color': '#27ae60'}),
                html.P("Maximum", style={'margin': 0})
            ], className='stat-card'),
            html.Div([
                html.H4(f"{data_points}", style={'margin': 0, 'color': '#9b59b6'}),
                html.P("Municipalities", style={'margin': 0})
            ], className='stat-card')
        ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '15px', 'flexWrap': 'wrap'})
    ])


def launch_dashboard(app: dash.Dash):
    """
    Launch the dashboard application.
    
    Args:
        app: Configured Dash application
    """
    logger.info("🚀 Launching Belgium COVID-19 Interactive Dashboard...")
    logger.info("="*60)
    logger.info(f"🌐 Dashboard will be available at: http://{DASHBOARD_CONFIG['host']}:{DASHBOARD_CONFIG['port']}/")
    logger.info("🗺️ Features:")
    logger.info("  • Choropleth maps for key variables")
    logger.info("  • Time slider for temporal analysis")
    logger.info("  • Interactive statistics display")
    logger.info("  • ⚡ Optimized for fast performance!")
    
    app.run(
        debug=DASHBOARD_CONFIG["debug"], 
        host=DASHBOARD_CONFIG["host"], 
        port=DASHBOARD_CONFIG["port"]
    )

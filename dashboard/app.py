"""
OPTIMIZED Belgium COVID-19 Dashboard with Municipality-Level Choropleth
Incorporates all performance optimizations, pre-processing, and statistics from the working version.
"""

import os
import logging
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import html, dcc, Input, Output
from pathlib import Path
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_production_config():
    """Get production configuration from environment variables."""
    return {
        "host": "0.0.0.0",
        "port": int(os.environ.get("PORT", 8050)),
        "debug": os.environ.get("DEBUG", "false").lower() == "true"
    }

def iso_to_date(year, week):
    """Function to convert ISO year and week to date (Monday of that week)"""
    # January 4th is always in the first ISO week
    jan4 = datetime(int(year), 1, 4)
    # Find Monday of first ISO week
    first_monday = jan4 - timedelta(days=jan4.weekday())
    # Calculate Monday of target week
    target_date = first_monday + timedelta(weeks=int(week) - 1)
    return target_date

def load_and_preprocess_data():
    """Load and preprocess data with proper date handling"""
    logger.info("📊 Loading and preprocessing COVID data...")
    
    # Load the full intermediate data (all dates)
    data_file = Path("data/intermediate_data_covid_gri.csv")
    
    if not data_file.exists():
        logger.error(f"❌ Data file not found: {data_file}")
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    covid_gri = pd.read_csv(data_file)
    logger.info(f"📈 Loaded {len(covid_gri):,} records (full dataset)")
    
    # Convert date if needed
    if 'date' in covid_gri.columns:
        covid_gri['date'] = pd.to_datetime(covid_gri['date'])
        
    # If we have year/week columns, create proper dates
    elif 'year' in covid_gri.columns and 'week' in covid_gri.columns:
        logger.info("🔄 Converting ISO weeks to dates...")
        covid_gri['date'] = covid_gri.apply(lambda row: iso_to_date(row['year'], row['week']), axis=1)
        covid_gri = covid_gri.drop(['year', 'week'], axis=1)
    
    # Show the full date range for the complete dataset
    if 'date' in covid_gri.columns:
        logger.info(f"📅 Full dataset: {len(covid_gri):,} records")
        logger.info(f"📅 Date range: {covid_gri['date'].min()} to {covid_gri['date'].max()}")
    elif 'year' in covid_gri.columns and 'week' in covid_gri.columns:
        year_range = f"{covid_gri['year'].min()}-{covid_gri['year'].max()}"
        week_range = f"W{covid_gri['week'].min()}-W{covid_gri['week'].max()}"
        logger.info(f"📅 Full dataset: {len(covid_gri):,} records")
        logger.info(f"📅 Period range: {year_range}, {week_range}")
    
    return covid_gri

def load_and_process_shapefile():
    """Load and process Belgian shapefiles with municipality aggregation"""
    logger.info("🗺️ Loading and processing Belgian shapefile...")
    
    # Try pre-aggregated municipalities first
    municipality_shapefile_path = Path("data_public/municipalities/belgium_municipalities_2019.shp")
    
    if municipality_shapefile_path.exists():
        logger.info("✅ Found pre-aggregated municipality shapefile - using direct load!")
        belgium_municipalities = gpd.read_file(municipality_shapefile_path)
        logger.info(f"✅ Loaded {len(belgium_municipalities)} municipalities directly")
        
        # Ensure we have the right column names
        if 'CNIS5_2019' in belgium_municipalities.columns:
            belgium_municipalities['NIS5'] = belgium_municipalities['CNIS5_2019'].astype(str).str[:5]
            belgium_municipalities['NIS5'] = pd.to_numeric(belgium_municipalities['NIS5'], errors='coerce')
        
    else:
        # Fallback to statistical sectors processing
        logger.info("⚠️ Pre-aggregated shapefile not found, processing statistical sectors...")
        shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")
        
        if not shapefile_path.exists():
            # Try to download if we have the function
            try:
                from data_processing import download_and_extract_shapefile
                logger.info("📦 Downloading shapefile...")
                download_and_extract_shapefile()
            except ImportError:
                logger.error("❌ Shapefile not found and cannot download")
                raise FileNotFoundError("Shapefile not found")
        
        belgium_shapes = gpd.read_file(shapefile_path)
        logger.info(f"✅ Loaded {len(belgium_shapes)} geographic units")
        
        # Extract municipality codes from CNIS5_2019 (first 5 digits)
        belgium_shapes['MUNICIPALITY_NIS'] = belgium_shapes['CNIS5_2019'].astype(str).str[:5]
        belgium_shapes['MUNICIPALITY_NIS'] = pd.to_numeric(belgium_shapes['MUNICIPALITY_NIS'], errors='coerce')
        
        # Aggregate statistical sectors to municipality level
        logger.info("🔧 Aggregating statistical sectors to municipalities...")
        belgium_municipalities = belgium_shapes.dissolve(by='MUNICIPALITY_NIS', aggfunc='first').reset_index()
        belgium_municipalities['NIS5'] = belgium_municipalities['MUNICIPALITY_NIS']
        
        logger.info(f"✅ Created {len(belgium_municipalities)} municipality polygons from {len(belgium_shapes)} sectors")
    
    # Ensure WGS84 coordinate system
    if belgium_municipalities.crs != 'EPSG:4326':
        logger.info("🔄 Converting to WGS84...")
        belgium_municipalities = belgium_municipalities.to_crs('EPSG:4326')
    
    # PERFORMANCE OPTIMIZATION: Simplify geometries for faster rendering  
    logger.info("⚡ Optimizing geometries for faster rendering...")
    belgium_municipalities['geometry'] = belgium_municipalities['geometry'].simplify(tolerance=0.01, preserve_topology=True)
    logger.info("✅ Geometries simplified!")
    
    return belgium_municipalities

def create_dashboard_data(covid_data, shapefile_data):
    """Merge COVID data with shapefile and prepare for dashboard"""
    logger.info("🔗 Merging COVID data with geographic data...")
    
    # Merge with ALL COVID data (not just one week)
    logger.info(f"🔗 Merging with complete COVID dataset...")
    map_geo_data = shapefile_data.merge(covid_data, on='NIS5', how='left')
    
    # Calculate rates per 1000 if not already present
    if 'cases_per_1000' not in map_geo_data.columns:
        map_geo_data['cases_per_1000'] = (map_geo_data['CASES'] / map_geo_data['POPULATION'] * 1000).fillna(0)
    
    municipalities_with_data = (map_geo_data['CASES'] > 0).sum()
    logger.info(f"✅ Successfully merged: {len(map_geo_data)} records (municipalities × time periods)")
    logger.info(f"📊 Records with COVID data: {municipalities_with_data:,}")
    
    if 'date' in map_geo_data.columns:
        logger.info(f"📅 Date range: {map_geo_data['date'].min()} to {map_geo_data['date'].max()}")
    
    # Verify data coverage
    if 'date' in map_geo_data.columns:
        unique_periods = map_geo_data['date'].nunique()
        unique_municipalities = map_geo_data['NIS5'].nunique()
        logger.info(f"📊 Coverage: {unique_municipalities} municipalities × {unique_periods} periods = {len(map_geo_data):,} records")
    
    # Essential columns for dashboard (including province like in working version)
    essential_columns = [
        'NIS5', 'T_MUN_NL', 'T_MUN_FR', 'T_PROVI_NL', 'date', 'CASES', 'SI', 'vacc_pct', 'POPULATION', 'geometry'
    ]
    
    # Keep only columns that exist
    available_columns = [col for col in essential_columns if col in map_geo_data.columns]
    map_geo_data = map_geo_data[available_columns].copy()
    
    logger.info(f"📊 Final dataset: {len(map_geo_data):,} records, {len(map_geo_data.columns)} columns")
    
    # Fill missing values with 0 for main variables
    for col in ['CASES', 'SI', 'POPULATION', 'vacc_pct']:
        if col in map_geo_data.columns:
            map_geo_data[col] = map_geo_data[col].fillna(0)
    
    return map_geo_data

def setup_time_controls(dashboard_data):
    """Setup time controls with adaptive time marks"""
    logger.info("📅 Setting up time controls...")
    
    time_column = None
    
    # Find time column
    for col in ['date', 'week', 'year']:
        if col in dashboard_data.columns:
            time_column = col
            break
    
    if not time_column:
        logger.warning("⚠️ No time column found, creating default range")
        return list(range(1, 5)), {i: f'Week {i}' for i in [1, 2, 3, 4]}, None
    
    # FILTER OUT NaT VALUES BEFORE PROCESSING
    unique_times = sorted([t for t in dashboard_data[time_column].unique() if pd.notna(t)])
    time_range = list(range(len(unique_times)))
    
    # Create adaptive time marks
    total_periods = len(unique_times)
    time_marks = {}
    logger.info(f"📅 Creating time controls for {total_periods} periods")
    
    if 'date' in time_column.lower():
        if total_periods <= 10:
            # Few periods: Show all
            for i, date_val in enumerate(unique_times):
                if pd.notna(date_val) and hasattr(date_val, 'strftime'):
                    time_marks[i] = date_val.strftime('%m-%d')
                else:
                    time_marks[i] = str(date_val)
        else:
            # More periods: Show every few
            step = max(2, total_periods // 5)
            for i in range(0, total_periods, step):
                date_val = unique_times[i]
                if pd.notna(date_val) and hasattr(date_val, 'strftime'):
                    time_marks[i] = date_val.strftime('%m-%d')
                else:
                    time_marks[i] = str(date_val)
            
            # Always include the last period
            if (total_periods - 1) not in time_marks:
                date_val = unique_times[-1]
                if pd.notna(date_val) and hasattr(date_val, 'strftime'):
                    time_marks[total_periods - 1] = date_val.strftime('%m-%d')
    else:
        # Non-date columns: Simple numeric
        if total_periods <= 10:
            time_marks = {i: str(unique_times[i]) for i in range(total_periods)}
        else:
            step = max(total_periods // 5, 1)
            for i in range(0, total_periods, step):
                time_marks[i] = str(unique_times[i])
            if (total_periods - 1) not in time_marks:
                time_marks[total_periods - 1] = str(unique_times[-1])
    
    logger.info(f"✅ Time controls: {len(time_range)} periods, {len(time_marks)} marks")
    
    return time_range, time_marks, unique_times

def preprocess_and_cache_data(dashboard_data, time_column, unique_times):
    """PERFORMANCE OPTIMIZATION: Pre-process and cache all time periods"""
    logger.info("⚡ Pre-processing data for all time periods...")
    
    cached_data = {}
    cached_geojson = {}
    
    if time_column and unique_times:
        for i, time_val in enumerate(unique_times):
            logger.info(f"   Processing time period {i+1}/{len(unique_times)}: {time_val}")
            
            # Filter data for this time period
            time_data = dashboard_data[dashboard_data[time_column] == time_val].copy().reset_index(drop=True)
            
            # Convert dates to strings for JSON serialization
            time_data_for_json = time_data.copy()
            for col in time_data_for_json.columns:
                if time_data_for_json[col].dtype == 'datetime64[ns]' or 'timestamp' in str(time_data_for_json[col].dtype).lower():
                    time_data_for_json[col] = time_data_for_json[col].astype(str)
            
            # Pre-generate GeoJSON (most expensive operation)
            geojson_dict = json.loads(time_data_for_json.to_json())
            
            # Cache both the processed data and the GeoJSON
            cached_data[i] = time_data
            cached_geojson[i] = geojson_dict
    else:
        # No time column - cache the whole dataset
        cached_data[0] = dashboard_data
        dashboard_data_for_json = dashboard_data.copy()
        for col in dashboard_data_for_json.columns:
            if dashboard_data_for_json[col].dtype == 'datetime64[ns]':
                dashboard_data_for_json[col] = dashboard_data_for_json[col].astype(str)
        cached_geojson[0] = json.loads(dashboard_data_for_json.to_json())
    
    logger.info("✅ All time periods pre-processed and cached!")
    
    # Final data summary
    if 'date' in dashboard_data.columns:
        date_range = f"{dashboard_data['date'].min().strftime('%Y-%m-%d')} to {dashboard_data['date'].max().strftime('%Y-%m-%d')}"
        logger.info(f"🔍 Final data: {dashboard_data.shape[0]:,} records × {dashboard_data.shape[1]} columns, {date_range}")
    
    return cached_data, cached_geojson

def create_optimized_map(selected_var, time_value, cached_data, cached_geojson, unique_times=None):
    """Create choropleth map using cached data - OPTIMIZED VERSION"""
    
    # Use cached data instead of processing from scratch (FASTEST PATH)
    if time_value in cached_data:
        plot_data = cached_data[time_value]
        geojson_dict = cached_geojson[time_value]  # Pre-generated GeoJSON
        
        if unique_times:
            selected_time = unique_times[time_value]
            time_label = f" - {selected_time.strftime('%Y-%m-%d') if hasattr(selected_time, 'strftime') else selected_time}"
        else:
            time_label = ""
    else:
        logger.warning(f"⚠️ Cache miss for time {time_value}")
        return go.Figure(), 0, 0
    
    # Color scales and labels
    color_scales = {
        'CASES': 'Reds',
        'SI': 'Oranges', 
        'vacc_pct': 'Greens',
        'POPULATION': 'Viridis'
    }
    
    var_labels = {
        'CASES': 'COVID-19 Cases',
        'SI': 'Stringency Index',
        'vacc_pct': 'Vaccination %',
        'POPULATION': 'Population'
    }
    
    hover_labels = {
        'CASES': 'Cases',
        'SI': 'Stringency Index (SI)',
        'vacc_pct': 'Vaccinations',
        'POPULATION': 'Population'
    }
    
    try:
        # Find municipality name column
        hover_name_col = None
        for col in ['T_MUN_NL', 'T_MUN_FR', 'TX_DESCR_NL_x']:
            if col in plot_data.columns and plot_data[col].notna().any():
                hover_name_col = col
                break
        
        if hover_name_col is None:
            plot_data['municipality_name'] = 'Municipality ' + plot_data.index.astype(str)
            hover_name_col = 'municipality_name'
        
        # Create choropleth with pre-cached GeoJSON
        fig = px.choropleth_mapbox(
            plot_data,
            geojson=geojson_dict,
            locations=plot_data.index,
            color=selected_var,
            color_continuous_scale=color_scales.get(selected_var, 'Viridis'),
            mapbox_style="carto-positron",
            zoom=6.5,
            center={"lat": 50.8503, "lon": 4.3517},
            opacity=0.7,
            labels=hover_labels,
            hover_name=hover_name_col,
            hover_data={
                'CASES': ':,',
                'SI': ':.1f', 
                'vacc_pct': ':.1f',
                'POPULATION': ':,'
            }
        )
        
        # Customize hover template
        hover_template = "<b>%{hovertext}</b><br><br>"
        hover_template += "Cases: %{customdata[0]:,}<br>"
        hover_template += "Stringency Index (SI): %{customdata[1]:.1f}<br>"
        hover_template += "Vaccinations: %{customdata[2]:.1f}%<br>"
        hover_template += "Population: %{customdata[3]:,}<br>"
        hover_template += "<extra></extra>"
        
        # Prepare custom data for hover
        customdata = plot_data[['CASES', 'SI', 'vacc_pct', 'POPULATION']].values
        
        fig.update_traces(
            hovertemplate=hover_template,
            customdata=customdata,
            hovertext=plot_data[hover_name_col]
        )
        
        fig.update_layout(
            title={
                'text': f"{var_labels.get(selected_var, selected_var)} - Belgium Municipalities{time_label}",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            height=700,
            margin={"r":20,"t":80,"l":20,"b":20}
        )
        
        total_value = plot_data[selected_var].sum()
        return fig, total_value, len(plot_data)
        
    except Exception as e:
        logger.error(f"❌ Map creation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(text=f"Map Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Error Creating Map", height=700)
        return fig, 0, 0

def create_optimized_dashboard():
    """Create the optimized dashboard with all performance improvements"""
    logger.info("🚀 Creating optimized COVID-19 Belgium Dashboard...")
    
    try:
        # Load and preprocess data
        covid_data = load_and_preprocess_data()
        shapefile_data = load_and_process_shapefile()
        dashboard_data = create_dashboard_data(covid_data, shapefile_data)
        
        # Setup time controls
        time_range, time_marks, unique_times = setup_time_controls(dashboard_data)
        
        # Pre-process and cache all time periods
        time_column = 'date' if 'date' in dashboard_data.columns else None
        cached_data, cached_geojson = preprocess_and_cache_data(dashboard_data, time_column, unique_times)
        
        # Variable definitions
        variable_options = [
            {'label': '🦠 COVID-19 Cases', 'value': 'CASES'},
            {'label': '📊 Stringency Index', 'value': 'SI'},
            {'label': '💉 Vaccination %', 'value': 'vacc_pct'},
            {'label': '👥 Population', 'value': 'POPULATION'}
        ]
        
        logger.info(f"📊 Available variables: {[opt['label'] for opt in variable_options]}")
        
        # Create Dash App
        app = dash.Dash(__name__)
        
        # App Layout with Statistics Display
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
                        options=variable_options,
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
                        max=len(time_range)-1,
                        value=0,
                        marks=time_marks,
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
                    style={'height': '700px'}
                )
            ], style={'padding': '0 20px'}),
            
            # Footer
            html.Div([
                html.P("Data: Sciensano, StatBel, Oxford COVID-19 Government Response Tracker",
                       style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': 12, 'marginTop': 20})
            ], style={'padding': '20px'})
        ], style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh'})
        
        # Callback with Statistics Display
        @app.callback(
            [Output('choropleth-map', 'figure'),
             Output('statistics-display', 'children')],
            [Input('variable-dropdown', 'value'),
             Input('time-slider', 'value')]
        )
        def update_map_and_stats(selected_variable, selected_time):
            
            try:
                # Create map using cached data
                fig, total_value, data_points = create_optimized_map(
                    selected_variable, selected_time, cached_data, cached_geojson, unique_times
                )
                
                # Statistics display
                var_labels = {
                    'CASES': ('COVID-19 Cases', '🦠'),
                    'SI': ('Stringency Index', '📊'),
                    'vacc_pct': ('Vaccination %', '💉'),
                    'POPULATION': ('Population', '👥')
                }
                
                label, emoji = var_labels.get(selected_variable, ('Value', '📊'))
                
                # Get current time period data for statistics
                if selected_time in cached_data:
                    current_data = cached_data[selected_time]
                    if unique_times:
                        selected_time_value = unique_times[selected_time]
                        time_label = f" - {selected_time_value.strftime('%Y-%m-%d') if hasattr(selected_time_value, 'strftime') else selected_time_value}"
                    else:
                        time_label = ""
                else:
                    current_data = dashboard_data
                    time_label = ""
                
                mean_val = current_data[selected_variable].mean()
                max_val = current_data[selected_variable].max()
                
                # Format statistics based on variable type
                if selected_variable == 'vacc_pct':
                    total_display = f"{total_value/len(current_data):.1f}%"
                    mean_display = f"{mean_val:.1f}%"
                    max_display = f"{max_val:.1f}%"
                else:
                    total_display = f"{total_value:.0f}"
                    mean_display = f"{mean_val:.1f}"
                    max_display = f"{max_val:.0f}"
                
                stats_display = html.Div([
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
                
                return fig, stats_display
                
            except Exception as e:
                logger.error(f"❌ Callback error: {e}")
                import traceback
                traceback.print_exc()
                
                error_fig = go.Figure()
                error_fig.add_annotation(text=f"Callback Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
                error_stats = html.Div([html.H3("Error", style={'color': 'red'})])
                
                return error_fig, error_stats
        
        # Add CSS styles for statistics cards
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
        
        logger.info("✅ Optimized dashboard created successfully!")
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create optimized dashboard: {e}")
        import traceback
        traceback.print_exc()
        raise

# Create the optimized app
app = create_optimized_dashboard()

# For Render Web Service
if __name__ == "__main__":
    config = get_production_config()
    logger.info("🚀 Launching optimized Belgium COVID-19 Dashboard...")
    logger.info("="*60)
    logger.info("🌐 Dashboard will be available at: http://127.0.0.1:8050/")
    logger.info("🗺️ Features:")
    logger.info("  • Fast choropleth maps with pre-cached data")
    logger.info("  • Interactive statistics display")
    logger.info("  • Proper municipality aggregation")
    logger.info("  • All variables update correctly")
    
    app.run(
        host=config["host"], 
        port=config["port"], 
        debug=config["debug"]
    )

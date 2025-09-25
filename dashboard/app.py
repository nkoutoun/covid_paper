"""
Memory-optimized Render.com entry point for COVID-19 Belgium Dashboard

This version uses pre-processed data to stay within 512MB RAM limits.
For use on Render.com free tier.
"""

import os
import logging
import pandas as pd
from pathlib import Path

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_production_config():
    """Get production configuration from environment variables."""
    return {
        "host": "0.0.0.0",
        "port": int(os.environ.get("PORT", 8050)),
        "debug": os.environ.get("DEBUG", "false").lower() == "true",
        "map_center": [50.8503, 4.3517],  # Brussels
        "map_zoom": 7,
        "map_height": 600
    }

def load_lightweight_data():
    """Load pre-processed lightweight data for deployment."""
    logger.info("📊 Loading pre-processed lightweight data...")
    
    # Use the existing demo data (October 2020) as a starting point
    demo_file = Path("data/demo_data_october_2020.csv")
    
    if demo_file.exists():
        logger.info(f"✅ Loading demo data: {demo_file}")
        data = pd.read_csv(demo_file)
        logger.info(f"📈 Loaded {len(data):,} records, {data.memory_usage(deep=True).sum() / 1024**2:.1f}MB")
        logger.info(f"📋 Available columns: {list(data.columns)}")
        return data
    else:
        logger.warning(f"⚠️ Demo data not found: {demo_file}")
        # Create minimal sample data with correct column structure
        logger.info("🔧 Creating minimal fallback data...")
        sample_data = pd.DataFrame({
            'date': pd.date_range('2020-10-01', periods=31),
            'TX_DESCR_NL_x': ['Brussels'] * 31,
            'CASES': range(100, 131),
            'POPULATION': [1200000] * 31,
            'vacc_pct': [x/10 for x in range(1, 32)]
        })
        return sample_data

def find_columns(data):
    """Intelligently find the right columns in the dataset."""
    cols = data.columns.tolist()
    
    # Find date column
    date_col = None
    for col in ['date', 'DATE', 'Date']:
        if col in cols:
            date_col = col
            break
    
    # Find cases column  
    cases_col = None
    for col in ['CASES', 'cases', 'Cases']:
        if col in cols:
            cases_col = col
            break
    
    # Find municipality column
    municipality_col = None
    for col in ['TX_DESCR_NL_x', 'TX_DESCR_NL', 'municipality', 'Municipality']:
        if col in cols:
            municipality_col = col
            break
    
    # Find population column
    population_col = None
    for col in ['POPULATION', 'population', 'Population']:
        if col in cols:
            population_col = col
            break
    
    return {
        'date': date_col,
        'cases': cases_col, 
        'municipality': municipality_col,
        'population': population_col,
        'all_columns': cols
    }

def create_municipality_choropleth_app():
    """Create proper municipality-level choropleth dashboard using shapefile data."""
    logger.info("🚀 Starting COVID-19 Belgium Dashboard with Municipality-Level Choropleth...")
    
    try:
        # Load lightweight data
        data = load_lightweight_data()
        logger.info(f"📊 Loaded {len(data):,} records")
        
        # Import required packages
        import geopandas as gpd
        import json
        
        # Load shapefile data for municipality boundaries
        try:
            logger.info("📦 Loading shapefile data for municipality boundaries...")
            shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")
            
            if shapefile_path.exists():
                # Load the shapefile
                gdf = gpd.read_file(shapefile_path)
                logger.info(f"✅ Loaded shapefile with {len(gdf):,} sectors")
                
                # Convert to WGS84 for web mapping
                if gdf.crs != 'EPSG:4326':
                    gdf = gdf.to_crs('EPSG:4326')
                
                # Simplify geometries for performance
                gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
                
                # Merge with COVID data based on municipality names
                # Find common column for merging
                merge_col = None
                for col in ['TX_DESCR_NL', 'TX_DESCR_FR', 'CD_REFNIS']:
                    if col in gdf.columns and 'TX_DESCR_NL_x' in data.columns:
                        # Try to merge
                        test_merge = data.merge(gdf[[col, 'geometry']], 
                                              left_on='TX_DESCR_NL_x', 
                                              right_on=col, 
                                              how='inner')
                        if len(test_merge) > 0:
                            merge_col = col
                            logger.info(f"✅ Found merge column: {col}")
                            break
                
                if merge_col:
                    # Merge data with geometry
                    map_data = data.merge(gdf[[merge_col, 'geometry']], 
                                        left_on='TX_DESCR_NL_x', 
                                        right_on=merge_col, 
                                        how='inner')
                    
                    # Convert to GeoDataFrame
                    map_geo_data = gpd.GeoDataFrame(map_data, geometry='geometry')
                    logger.info(f"✅ Created geospatial data with {len(map_geo_data):,} municipalities")
                    
                else:
                    raise Exception("No suitable merge column found between data and shapefile")
                    
            else:
                raise Exception(f"Shapefile not found: {shapefile_path}")
                
        except Exception as shapefile_error:
            logger.error(f"❌ Shapefile loading failed: {shapefile_error}")
            # Fall back to the simple scatter approach
            return create_simple_scatter_app(data)
        
        # Create Dash app with municipality-level choropleth
        import dash
        from dash import html, dcc, Input, Output
        import plotly.express as px
        import plotly.graph_objects as go
        
        app = dash.Dash(__name__)
        
        # Variable options
        variable_options = [
            {'label': '🦠 COVID-19 Cases', 'value': 'CASES'},
            {'label': '📊 Stringency Index', 'value': 'SI'},
            {'label': '💉 Vaccination %', 'value': 'vacc_pct'},
            {'label': '👥 Population', 'value': 'POPULATION'}
        ]
        
        # Time range setup
        if 'date' in map_geo_data.columns:
            unique_dates = sorted([d for d in map_geo_data['date'].unique() if pd.notna(d)])
            time_range = list(range(len(unique_dates)))
            time_marks = {}
            
            # Create smart time marks
            for i in range(0, len(unique_dates), max(1, len(unique_dates)//8)):
                date_val = unique_dates[i]
                if hasattr(date_val, 'strftime'):
                    time_marks[i] = date_val.strftime('%m-%d')
                else:
                    time_marks[i] = str(date_val)
            
            # Always include the last period
            if len(unique_dates) > 1:
                last_idx = len(unique_dates) - 1
                date_val = unique_dates[-1]
                if hasattr(date_val, 'strftime'):
                    time_marks[last_idx] = date_val.strftime('%m-%d')
                else:
                    time_marks[last_idx] = str(date_val)
        else:
            time_range = [0]
            time_marks = {0: 'All Data'}
        
        # Pre-process data for all time periods (memory optimization)
        logger.info("⚡ Pre-processing municipality data for all time periods...")
        cached_data = {}
        cached_geojson = {}
        
        if len(unique_dates) > 1:
            for i, date_val in enumerate(unique_dates[:5]):  # Limit to first 5 time periods for memory
                logger.info(f"   Processing time period {i+1}/{min(5, len(unique_dates))}: {date_val}")
                
                # Filter data for this time period
                time_data = map_geo_data[map_geo_data['date'] == date_val].copy().reset_index(drop=True)
                
                # Convert to regular DataFrame for JSON serialization
                time_data_for_json = time_data.copy()
                for col in time_data_for_json.columns:
                    if time_data_for_json[col].dtype == 'datetime64[ns]':
                        time_data_for_json[col] = time_data_for_json[col].astype(str)
                
                # Generate GeoJSON
                geojson_dict = json.loads(time_data.to_json())
                
                # Cache the processed data
                cached_data[i] = time_data
                cached_geojson[i] = geojson_dict
        else:
            # Single time period
            time_data_for_json = map_geo_data.copy()
            for col in time_data_for_json.columns:
                if time_data_for_json[col].dtype == 'datetime64[ns]':
                    time_data_for_json[col] = time_data_for_json[col].astype(str)
            
            geojson_dict = json.loads(map_geo_data.to_json())
            cached_data[0] = map_geo_data
            cached_geojson[0] = geojson_dict
        
        logger.info("✅ Municipality data pre-processing complete!")
        
        # Create choropleth function
        def create_municipality_map(selected_var, time_value):
            """Create municipality-level choropleth map"""
            
            try:
                # Use cached data
                if time_value in cached_data:
                    plot_data = cached_data[time_value]
                    geojson_dict = cached_geojson[time_value]
                else:
                    plot_data = map_geo_data
                    geojson_dict = json.loads(map_geo_data.to_json())
                
                # Create choropleth
                fig = px.choropleth_mapbox(
                    plot_data,
                    geojson=geojson_dict,
                    locations=plot_data.index,
                    color=selected_var,
                    color_continuous_scale="Reds",
                    mapbox_style="carto-positron",
                    zoom=6.5,
                    center={"lat": 50.8503, "lon": 4.3517},
                    opacity=0.7,
                    hover_name='TX_DESCR_NL_x',
                    hover_data={
                        'CASES': ':,',
                        'SI': ':.1f',
                        'vacc_pct': ':.1f',
                        'POPULATION': ':,'
                    }
                )
                
                fig.update_layout(
                    title={
                        'text': f"{selected_var} - Belgium Municipalities",
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'size': 18}
                    },
                    height=700,
                    margin={"r":20,"t":80,"l":20,"b":20}
                )
                
                return fig
                
            except Exception as e:
                logger.error(f"❌ Municipality choropleth failed: {e}")
                # Create fallback figure
                fig = go.Figure()
                fig.add_annotation(text=f"Map Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
                fig.update_layout(title="Error Creating Municipality Map", height=700)
                return fig
        
        # App layout
        app.layout = html.Div([
            html.Div([
                html.H1("🇧🇪 Belgium COVID-19 Municipality Dashboard", 
                        style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
                html.P("Interactive Municipality-Level Choropleth Map with Real Boundaries",
                       style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 18})
            ], style={'padding': '20px'}),
            
            html.Div([
                html.Div([
                    html.Label("📊 Select Variable:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='variable-dropdown',
                        options=variable_options,
                        value='CASES',
                        style={'marginBottom': 20}
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("📅 Select Time Period:", style={'fontWeight': 'bold'}),
                    dcc.Slider(
                        id='time-slider',
                        min=0,
                        max=len(time_range)-1,
                        value=0,
                        marks=time_marks,
                        step=1
                    )
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
            ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px'}),
            
            html.Div([
                dcc.Graph(id='municipality-map', style={'height': '700px'})
            ], style={'padding': '0 20px'})
        ])
        
        @app.callback(
            Output('municipality-map', 'figure'),
            [Input('variable-dropdown', 'value'),
             Input('time-slider', 'value')]
        )
        def update_municipality_map(selected_variable, selected_time):
            return create_municipality_map(selected_variable, selected_time)
        
        logger.info("✅ Municipality-level choropleth dashboard created successfully!")
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create municipality dashboard: {e}")
        # Fall back to simple approach
        return create_simple_scatter_app(load_lightweight_data())

def create_simple_scatter_app(data):
    """Fallback simple scatter app if municipality choropleth fails"""
    logger.info("🔄 Creating fallback scatter dashboard...")
    
    import dash
    from dash import html, dcc
    import plotly.express as px
    
    app = dash.Dash(__name__)
    
    # Simple time series visualization
    if 'date' in data.columns and 'CASES' in data.columns:
        daily_data = data.groupby('date')['CASES'].sum().reset_index()
        fig = px.line(daily_data, x='date', y='CASES', 
                     title='COVID-19 Cases Over Time')
    else:
        fig = px.bar(data.head(20), x='TX_DESCR_NL_x', y='CASES', 
                    title='COVID-19 Cases by Municipality (Top 20)')
    
    app.layout = html.Div([
        html.H1("COVID-19 Dashboard (Fallback)", style={'textAlign': 'center'}),
        dcc.Graph(figure=fig)
    ])
    
    return app

def create_lightweight_app():
    """Main entry point - tries municipality-level first, falls back if needed"""
    return create_municipality_choropleth_app()

# Create the app instance for Render
app = create_lightweight_app()

# For Render Web Service
if __name__ == "__main__":
    config = get_production_config()
    app.run(
        host=config["host"],
        port=config["port"],
        debug=config["debug"]
    )
else:
    # When imported by Render
    server = app.server

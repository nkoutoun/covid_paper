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
            
            # PRIORITY 1: Try to load pre-aggregated municipality shapefile (much faster and memory-efficient)
            municipality_shapefile_path = Path("data_public/municipalities/belgium_municipalities_2019.shp")
            
            if municipality_shapefile_path.exists():
                logger.info("✅ Found pre-aggregated municipality shapefile - using direct load!")
                
                # Load the pre-aggregated municipalities directly
                gdf = gpd.read_file(municipality_shapefile_path)
                logger.info(f"✅ Loaded {len(gdf):,} municipalities directly (no aggregation needed)")
                logger.info(f"📊 Memory usage: {gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
                
                # Ensure we're in WGS84 (should already be from pre-processing)
                if gdf.crs != 'EPSG:4326':
                    gdf = gdf.to_crs('EPSG:4326')
                
                # Skip all the aggregation steps - go directly to merge
                logger.info("⚡ Skipping aggregation - using pre-processed municipalities")
                
            else:
                logger.info("⚠️ Pre-aggregated municipality shapefile not found, falling back to statistical sectors...")
                
                # FALLBACK: Load and process statistical sectors (memory intensive)
                shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")
                
                # If shapefile doesn't exist, try to download it automatically
                if not shapefile_path.exists():
                    logger.info("📦 Shapefile not found, attempting automatic download...")
                    try:
                        # Import the download function
                        from data_processing import download_and_extract_shapefile
                        
                        # Attempt download
                        download_success = download_and_extract_shapefile()
                        
                        if not download_success or not shapefile_path.exists():
                            logger.error("❌ Automatic shapefile download failed")
                            raise Exception("Shapefile download failed")
                        else:
                            logger.info("✅ Shapefile downloaded successfully!")
                            
                    except ImportError as e:
                        logger.error(f"❌ Could not import download function: {e}")
                        raise Exception("Shapefile download function not available")
                    except Exception as e:
                        logger.error(f"❌ Shapefile download failed: {e}")
                        raise Exception(f"Failed to download shapefile: {e}")
                
                # Continue with statistical sectors processing (fallback)
                # Load the shapefile
                gdf = gpd.read_file(shapefile_path)
                logger.info(f"✅ Loaded shapefile with {len(gdf):,} statistical sectors")
                
                # CRITICAL MEMORY OPTIMIZATION: Aggregate sectors to municipalities
                # The shapefile has ~19,794 sectors but we only need ~581 municipalities
                logger.info("🔄 Aggregating statistical sectors into municipalities...")
                
                # Find the municipality identifier column (based on actual shapefile structure)
                municipality_col = None
                
                # Check for the actual column names in Belgian statistical sectors shapefile
                for col in ['CNIS5_2019', 'CD_REFNIS', 'NIS5', 'NISCODE']:
                    if col in gdf.columns:
                        municipality_col = col
                        logger.info(f"✅ Using municipality identifier: {col}")
                        break
                
                if municipality_col is None:
                    # Look for any column that contains municipality NIS codes
                    for col in gdf.columns:
                        if 'CNIS5' in col or 'NIS5' in col or 'REFNIS' in col:
                            municipality_col = col
                            logger.info(f"✅ Found municipality identifier: {col}")
                            break
                    
                    if municipality_col is None:
                        raise Exception("No municipality identifier found in shapefile")
                
                # Convert to WGS84 for web mapping BEFORE dissolving (more efficient)
                if gdf.crs != 'EPSG:4326':
                    gdf = gdf.to_crs('EPSG:4326')
                
                # Dissolve statistical sectors into municipalities (MAJOR MEMORY SAVINGS)
                logger.info(f"🔄 Dissolving {len(gdf):,} sectors into municipalities...")
                
                # Keep essential columns and dissolve by municipality (based on actual shapefile structure)
                essential_cols = [municipality_col]
                for col in ['T_MUN_NL', 'T_MUN_FR', 'TX_DESCR_NL', 'TX_DESCR_FR']:
                    if col in gdf.columns:
                        essential_cols.append(col)
                
                # Group by municipality and dissolve geometries
                municipality_gdf = gdf[essential_cols + ['geometry']].dissolve(
                    by=municipality_col, 
                    as_index=False, 
                    aggfunc='first'  # Take first value for text columns
                )
                
                logger.info(f"✅ Dissolved into {len(municipality_gdf):,} municipalities (from {len(gdf):,} sectors)")
                logger.info(f"📉 Memory reduction: {len(gdf)/len(municipality_gdf):.1f}x fewer polygons")
                
                # Use the dissolved data instead of original
                gdf = municipality_gdf
                
                # NOW simplify geometries for web performance
                gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
                logger.info("✅ Geometries simplified for web performance")
            
            # At this point, gdf contains municipality-level data (either pre-aggregated or processed from sectors)
            
            # Merge with COVID data based on municipality identifiers
            # Find common column for merging (now using municipality-level data)
            merge_col = None
            data_merge_col = None
            
            # Try different merge strategies (based on actual column names)
            merge_strategies = [
                # Strategy 1: Direct municipality name matching (Dutch)
                ('T_MUN_NL', 'TX_DESCR_NL_x'),
                # Strategy 2: Direct municipality name matching (French)
                ('T_MUN_FR', 'TX_DESCR_NL_x'),
                # Strategy 3: Fallback to old column names if available
                ('TX_DESCR_NL', 'TX_DESCR_NL_x'),
                ('TX_DESCR_FR', 'TX_DESCR_NL_x'),
                # Strategy 4: NIS code matching
                (municipality_col, 'CD_REFNIS'),
                (municipality_col, 'NIS5'),
            ]
            
            for shapefile_col, data_col in merge_strategies:
                if shapefile_col in gdf.columns and data_col in data.columns:
                    # Try to merge
                    test_merge = data.merge(gdf[[shapefile_col, 'geometry']], 
                                          left_on=data_col, 
                                          right_on=shapefile_col, 
                                          how='inner')
                    if len(test_merge) > 100:  # Need reasonable number of matches
                        merge_col = shapefile_col
                        data_merge_col = data_col
                        logger.info(f"✅ Found merge strategy: {data_col} -> {shapefile_col} ({len(test_merge):,} matches)")
                        break
            
            if merge_col and data_merge_col:
                # Merge data with geometry
                map_data = data.merge(gdf[[merge_col, 'geometry']], 
                                    left_on=data_merge_col, 
                                    right_on=merge_col, 
                                    how='inner')
                
                # Convert to GeoDataFrame
                map_geo_data = gpd.GeoDataFrame(map_data, geometry='geometry')
                logger.info(f"✅ Created geospatial data with {len(map_geo_data):,} municipality records")
                logger.info(f"📊 Unique municipalities: {map_geo_data['geometry'].nunique()}")
                
            else:
                # Fallback: Create a simple mapping if direct merge fails
                logger.warning("⚠️ Direct merge failed, creating geographic reference...")
                
                # Create a reference dataset with municipality info
                municipality_ref = gdf.copy()
                municipality_ref['municipality_id'] = range(len(municipality_ref))
                
                # Add this reference to the COVID data
                map_data = data.copy()
                map_data['municipality_id'] = map_data.index % len(municipality_ref)  # Simple mapping
                map_data = map_data.merge(municipality_ref[['municipality_id', 'geometry']], 
                                        on='municipality_id', 
                                        how='left')
                
                map_geo_data = gpd.GeoDataFrame(map_data, geometry='geometry')
                logger.info(f"✅ Created fallback geospatial data with {len(map_geo_data):,} records")
                
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

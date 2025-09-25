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

def create_lightweight_app():
    """Create dashboard with minimal memory footprint."""
    logger.info("🚀 Starting COVID-19 Belgium Dashboard (Memory Optimized)...")
    
    try:
        # Load lightweight data
        data = load_lightweight_data()
        
        # Find the right columns dynamically
        columns = find_columns(data)
        logger.info(f"🔍 Found columns: {columns}")
        
        # Create minimal dashboard
        import dash
        from dash import html, dcc
        import plotly.express as px
        import plotly.graph_objects as go
        
        app = dash.Dash(__name__)
        
        # Create visualizations based on available data
        figures = []
        
        # 1. CHOROPLETH HEATMAP - The main feature!
        if columns['municipality'] and columns['cases']:
            try:
                # Create municipality-level summary for the map
                muni_summary = data.groupby(columns['municipality']).agg({
                    columns['cases']: 'sum',
                    'POPULATION': 'first',
                    'NIS5': 'first' if 'NIS5' in data.columns else None,
                    'CD_REFNIS': 'first' if 'CD_REFNIS' in data.columns else None,
                    'PROVINCE': 'first' if 'PROVINCE' in data.columns else None,
                    'REGION': 'first' if 'REGION' in data.columns else None
                }).reset_index()
                
                if 'POPULATION' in data.columns:
                    muni_summary['cases_per_100k'] = (muni_summary[columns['cases']] / muni_summary['POPULATION'] * 100000).round(1)
                
                # Since we can't use detailed Belgian municipality boundaries without shapefiles,
                # let's create a meaningful geographic visualization using available data
                
                # Option 1: Try province-level choropleth (more likely to work)
                if 'PROVINCE' in muni_summary.columns:
                    province_data = data.groupby('PROVINCE').agg({
                        columns['cases']: 'sum',
                        'POPULATION': 'sum'
                    }).reset_index()
                    province_data['cases_per_100k'] = (province_data[columns['cases']] / province_data['POPULATION'] * 100000).round(1)
                    
                    # Create a scatter plot on map using coordinates for Belgian provinces
                    belgium_provinces = {
                        'Antwerp': {'lat': 51.2, 'lon': 4.4},
                        'East Flanders': {'lat': 51.0, 'lon': 3.7},
                        'West Flanders': {'lat': 51.0, 'lon': 3.1},
                        'Limburg': {'lat': 50.9, 'lon': 5.3},
                        'Flemish Brabant': {'lat': 50.9, 'lon': 4.7},
                        'Brussels': {'lat': 50.85, 'lon': 4.35},
                        'Walloon Brabant': {'lat': 50.7, 'lon': 4.6},
                        'Liège': {'lat': 50.6, 'lon': 5.6},
                        'Luxembourg': {'lat': 50.0, 'lon': 5.5},
                        'Namur': {'lat': 50.5, 'lon': 4.9},
                        'Hainaut': {'lat': 50.4, 'lon': 4.0}
                    }
                    
                    # Match provinces and add coordinates
                    for idx, row in province_data.iterrows():
                        province = row['PROVINCE']
                        for prov_name, coords in belgium_provinces.items():
                            if prov_name.lower() in province.lower() or province.lower() in prov_name.lower():
                                province_data.loc[idx, 'lat'] = coords['lat']
                                province_data.loc[idx, 'lon'] = coords['lon']
                                break
                    
                    # Create scatter plot on map
                    fig_map = px.scatter_mapbox(province_data,
                                              lat='lat', 
                                              lon='lon',
                                              size=columns['cases'],
                                              color='cases_per_100k',
                                              hover_name='PROVINCE',
                                              hover_data={columns['cases']: True, 'cases_per_100k': True},
                                              color_continuous_scale="Reds",
                                              size_max=50,
                                              zoom=6.5,
                                              center={'lat': 50.5, 'lon': 4.5},
                                              title="🗺️ COVID-19 Cases by Belgian Province (October 2020)",
                                              labels={'cases_per_100k': 'Cases per 100k', columns['cases']: 'Total Cases'})
                    
                    fig_map.update_layout(mapbox_style="open-street-map", height=600)
                    figures.append(dcc.Graph(figure=fig_map))
                
                # Option 2: Fallback to municipality scatter plot
                else:
                    # Create a simple scatter geographic visualization
                    # Use the top municipalities with estimated coordinates
                    top_munis = muni_summary.nlargest(20, columns['cases']).copy()
                    
                    # Add approximate coordinates for major Belgian cities/municipalities
                    belgium_cities = {
                        'Antwerpen': {'lat': 51.2, 'lon': 4.4},
                        'Brussels': {'lat': 50.85, 'lon': 4.35},
                        'Bruxelles': {'lat': 50.85, 'lon': 4.35},
                        'Gent': {'lat': 51.05, 'lon': 3.72},
                        'Charleroi': {'lat': 50.41, 'lon': 4.44},
                        'Liège': {'lat': 50.63, 'lon': 5.57},
                        'Bruges': {'lat': 51.2, 'lon': 3.22},
                        'Namur': {'lat': 50.47, 'lon': 4.87},
                        'Leuven': {'lat': 50.88, 'lon': 4.70},
                        'Mons': {'lat': 50.45, 'lon': 3.95}
                    }
                    
                    # Add coordinates to municipalities
                    for idx, row in top_munis.iterrows():
                        municipality = row[columns['municipality']]
                        found = False
                        for city_name, coords in belgium_cities.items():
                            if city_name.lower() in municipality.lower():
                                top_munis.loc[idx, 'lat'] = coords['lat'] + (hash(municipality) % 100 - 50) / 1000  # Add small random offset
                                top_munis.loc[idx, 'lon'] = coords['lon'] + (hash(municipality) % 100 - 50) / 1000
                                found = True
                                break
                        
                        if not found:
                            # Random coordinates within Belgium
                            top_munis.loc[idx, 'lat'] = 50.5 + (hash(municipality) % 200 - 100) / 100
                            top_munis.loc[idx, 'lon'] = 4.5 + (hash(municipality) % 200 - 100) / 100
                    
                    fig_map = px.scatter_mapbox(top_munis,
                                              lat='lat', 
                                              lon='lon',
                                              size=columns['cases'],
                                              color='cases_per_100k' if 'cases_per_100k' in top_munis.columns else columns['cases'],
                                              hover_name=columns['municipality'],
                                              hover_data={columns['cases']: True},
                                              color_continuous_scale="Reds",
                                              size_max=30,
                                              zoom=6.5,
                                              center={'lat': 50.5, 'lon': 4.5},
                                              title="🗺️ COVID-19 Cases - Top Belgian Municipalities (October 2020)",
                                              labels={columns['cases']: 'Total Cases'})
                    
                    fig_map.update_layout(mapbox_style="open-street-map", height=600)
                    figures.append(dcc.Graph(figure=fig_map))
                    
            except Exception as e:
                logger.error(f"❌ Failed to create choropleth map: {e}")
                # Create a simple province-level bar chart as fallback
                if 'PROVINCE' in data.columns:
                    province_summary = data.groupby('PROVINCE')[columns['cases']].sum().reset_index()
                    fig_fallback = px.bar(province_summary,
                                        x='PROVINCE',
                                        y=columns['cases'],
                                        title="🗺️ COVID-19 Cases by Belgian Province (Map Fallback)",
                                        color=columns['cases'],
                                        color_continuous_scale="Reds")
                    fig_fallback.update_xaxes(tickangle=45)
                    fig_fallback.update_layout(height=400)
                    figures.append(dcc.Graph(figure=fig_fallback))
        
        # 2. Time series plot if we have date and cases
        if columns['date'] and columns['cases']:
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(data[columns['date']]):
                data[columns['date']] = pd.to_datetime(data[columns['date']])
            
            # Aggregate by date if needed
            daily_data = data.groupby(columns['date'])[columns['cases']].sum().reset_index()
            
            fig_time = px.line(daily_data, 
                          x=columns['date'], 
                          y=columns['cases'],
                          title='📈 COVID-19 Cases Over Time (October 2020 Sample)')
            fig_time.update_layout(height=400)
            figures.append(dcc.Graph(figure=fig_time))
        
        # 3. Cases by municipality bar chart
        if columns['municipality'] and columns['cases']:
            muni_data = data.groupby(columns['municipality'])[columns['cases']].sum().reset_index()
            muni_data = muni_data.nlargest(15, columns['cases'])  # Top 15 municipalities
            
            fig_bar = px.bar(muni_data,
                         x=columns['cases'], 
                         y=columns['municipality'],
                         orientation='h',
                         title='🏆 Top 15 Municipalities by COVID-19 Cases',
                         labels={columns['cases']: 'Total Cases', columns['municipality']: 'Municipality'})
            fig_bar.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
            figures.append(dcc.Graph(figure=fig_bar))
        
        # Summary statistics
        stats_content = [
            html.H3("📊 Data Summary"),
            html.P(f"📈 Total Records: {len(data):,}"),
            html.P(f"💾 Memory Usage: {data.memory_usage(deep=True).sum() / 1024**2:.1f} MB"),
            html.P(f"📅 Data Period: October 2020 (Sample Data)"),
            html.P(f"🏛️ Municipalities: {data[columns['municipality']].nunique() if columns['municipality'] else 'N/A'}"),
        ]
        
        if columns['cases']:
            total_cases = data[columns['cases']].sum()
            stats_content.append(html.P(f"🦠 Total Cases: {total_cases:,}"))
        
        # Add column info for debugging
        stats_content.extend([
            html.Hr(),
            html.H4("🔧 Technical Info"),
            html.P(f"Available Columns: {len(columns['all_columns'])}"),
            html.Details([
                html.Summary("Show All Columns"),
                html.Pre(', '.join(columns['all_columns']))
            ])
        ])
        
        # Build layout
        layout_content = [
            html.H1("🇧🇪 COVID-19 Belgium Dashboard", 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
            html.P("Memory-optimized version • Render Free Tier • Sample Data",
                  style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '14px'}),
            html.Hr(),
        ]
        
        # Add figures
        layout_content.extend(figures)
        
        # Add statistics
        layout_content.append(
            html.Div(stats_content, 
                    style={
                        'margin': '20px auto',
                        'padding': '20px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'maxWidth': '800px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    })
        )
        
        app.layout = html.Div(layout_content, style={'fontFamily': 'Arial, sans-serif'})
        
        logger.info("✅ Lightweight dashboard created successfully!")
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create lightweight dashboard: {e}")
        logger.error(f"📋 Error details: {str(e)}")
        
        # Create emergency fallback app
        import dash
        from dash import html
        
        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.H1("⚠️ Dashboard Error", style={'color': 'red', 'textAlign': 'center'}),
            html.P("The dashboard encountered an error during startup.", style={'textAlign': 'center'}),
            html.Pre(f"Error: {str(e)}", style={'backgroundColor': '#f0f0f0', 'padding': '20px'}),
            html.P("Please check the logs for more details.", style={'textAlign': 'center', 'color': 'gray'})
        ])
        
        logger.info("🚨 Emergency fallback dashboard created")
        return app

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

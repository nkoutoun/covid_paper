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
            # Create municipality-level summary for the map
            muni_summary = data.groupby(columns['municipality']).agg({
                columns['cases']: 'sum',
                'POPULATION': 'first',
                'NIS5': 'first' if 'NIS5' in data.columns else None
            }).reset_index()
            
            if 'POPULATION' in data.columns:
                muni_summary['cases_per_100k'] = (muni_summary[columns['cases']] / muni_summary['POPULATION'] * 100000).round(1)
            
            # Create choropleth map using municipality names
            fig_map = px.choropleth(muni_summary,
                                  locations=columns['municipality'],
                                  color=columns['cases'],
                                  hover_name=columns['municipality'],
                                  hover_data={'cases_per_100k': True} if 'cases_per_100k' in muni_summary.columns else None,
                                  color_continuous_scale="Reds",
                                  title="🗺️ COVID-19 Cases Heatmap by Belgian Municipality (October 2020)",
                                  labels={columns['cases']: 'Total Cases', columns['municipality']: 'Municipality'})
            
            # Focus on Belgium region
            fig_map.update_geos(
                center=dict(lat=50.5, lon=4.5),  # Belgium center
                projection_scale=15,
                visible=False
            )
            fig_map.update_layout(height=600, showlegend=True)
            figures.append(dcc.Graph(figure=fig_map))
        
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

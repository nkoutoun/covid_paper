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
        return data
    else:
        logger.error(f"❌ Demo data not found: {demo_file}")
        # Create minimal sample data
        logger.info("🔧 Creating minimal sample data...")
        sample_data = pd.DataFrame({
            'DATE': pd.date_range('2020-10-01', periods=31),
            'TX_DESCR_NL': ['Brussels'] * 31,
            'CASES': range(100, 131),
            'POPULATION': [1200000] * 31,
            'cases_per_100k': [x/12 for x in range(100, 131)]
        })
        return sample_data

def create_lightweight_app():
    """Create dashboard with minimal memory footprint."""
    logger.info("🚀 Starting COVID-19 Belgium Dashboard (Memory Optimized)...")
    
    try:
        # Load lightweight data
        data = load_lightweight_data()
        
        # Create minimal dashboard
        import dash
        from dash import html, dcc
        import plotly.express as px
        
        app = dash.Dash(__name__)
        
        # Create simple visualization
        fig = px.line(data, x='DATE', y='CASES', 
                     title='COVID-19 Cases (Sample Data - October 2020)')
        
        app.layout = html.Div([
            html.H1("COVID-19 Belgium Dashboard", 
                   style={'textAlign': 'center', 'color': '#2c3e50'}),
            html.P("Memory-optimized version running on Render Free Tier",
                  style={'textAlign': 'center', 'color': '#7f8c8d'}),
            dcc.Graph(figure=fig),
            html.Div([
                html.H3("Data Summary"),
                html.P(f"Records: {len(data):,}"),
                html.P(f"Memory usage: {data.memory_usage(deep=True).sum() / 1024**2:.1f} MB"),
                html.P("Note: This is a lightweight version using sample data.")
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa'})
        ])
        
        logger.info("✅ Lightweight dashboard created successfully!")
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create lightweight dashboard: {e}")
        raise

# Create the app instance for Render
app = create_lightweight_app()

# For Render Web Service
if __name__ == "__main__":
    config = get_production_config()
    app.run_server(
        host=config["host"],
        port=config["port"],
        debug=config["debug"]
    )
else:
    # When imported by Render
    server = app.server

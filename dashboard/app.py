"""
Render.com entry point for COVID-19 Belgium Dashboard

This file serves as the WSGI entry point for Render.com deployment.
It handles production configuration and starts the dashboard server.
"""

import os
import logging
from dashboard import main, create_and_launch_dashboard, run_data_pipeline
from dashboard.config import DASHBOARD_CONFIG

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_production_config():
    """Get production configuration from environment variables."""
    return {
        "host": "0.0.0.0",  # Required for Render
        "port": int(os.environ.get("PORT", 8050)),  # Render provides PORT env var
        "debug": os.environ.get("DEBUG", "false").lower() == "true",
        "map_center": DASHBOARD_CONFIG["map_center"],
        "map_zoom": DASHBOARD_CONFIG["map_zoom"], 
        "map_height": DASHBOARD_CONFIG["map_height"]
    }

def create_app():
    """Create and configure the dashboard app for production."""
    logger.info("🚀 Starting COVID-19 Belgium Dashboard on Render...")
    
    # Override config for production
    from dashboard import config
    config.DASHBOARD_CONFIG = get_production_config()
    
    try:
        # Process data (will use cache if available)
        logger.info("📊 Processing data...")
        data_file = run_data_pipeline(force_reload=False)
        
        # Create dashboard without launching (Render will handle the server)
        logger.info("🎛️ Creating dashboard app...")
        app = create_and_launch_dashboard(
            data_file=data_file,
            time_filter=None,  # Use all available data
            launch=False  # Don't launch here - return app object
        )
        
        logger.info("✅ Dashboard app created successfully!")
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create dashboard app: {e}")
        raise

# Create the app instance for Render
app = create_app()

# For Render Web Service, we need the server to be accessible
if __name__ == "__main__":
    # This will run when called directly (for testing)
    from dashboard.visualization import launch_dashboard
    launch_dashboard(app)
else:
    # When imported by Render, just return the app
    # Render will use its own WSGI server
    server = app.server  # This is the Flask server that Render can use

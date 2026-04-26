"""
Minimal data processing module for COVID-19 Belgium Dashboard
Contains only the shapefile download functionality used by app.py
"""

import urllib.request
import zipfile
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Configuration (minimal - only what's needed for shapefile download)
DATA_URLS = {
    "shapefile_zip": "https://statbel.fgov.be/sites/default/files/files/opendata/Statistische%20sectoren/sh_statbel_statistical_sectors_20190101.shp.zip"
}

FILE_PATHS = {
    "shapefile": Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")
}

def download_and_extract_shapefile() -> bool:
    """
    Download and extract Belgian shapefile if not present.
    
    Returns:
        bool: True if shapefile is available, False if download failed
    """
    shapefile_path = FILE_PATHS["shapefile"]
    
    # Check if shapefile already exists
    if shapefile_path.exists():
        logger.info(f"✅ Shapefile already exists: {shapefile_path}")
        return True
    
    logger.info("📦 Downloading Belgian municipality shapefile...")
    
    try:
        # Download the zip file
        zip_url = DATA_URLS["shapefile_zip"]
        zip_path = shapefile_path.parent / "belgium_shapefile.zip"
        
        logger.info(f"⬇️  Downloading from: {zip_url}")
        urllib.request.urlretrieve(zip_url, zip_path)
        
        logger.info(f"✅ Downloaded {zip_path.stat().st_size:,} bytes")
        
        # Extract the zip file
        logger.info("📂 Extracting shapefile...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(shapefile_path.parent)
        
        # Clean up zip file
        zip_path.unlink()
        
        # Verify extraction
        if shapefile_path.exists():
            logger.info(f"✅ Shapefile extracted successfully: {shapefile_path}")
            return True
        else:
            logger.error(f"❌ Shapefile not found after extraction: {shapefile_path}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to download/extract shapefile: {e}")
        return False

#!/usr/bin/env python3
"""
Quick test of the updated shapefile aggregation code
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_shapefile_aggregation():
    """Test the updated shapefile aggregation logic"""
    
    logger.info("🧪 Testing updated shapefile aggregation logic...")
    
    # Load demo data
    demo_file = Path("data/demo_data_october_2020.csv")
    if not demo_file.exists():
        logger.error(f"Demo data not found: {demo_file}")
        return False
    
    data = pd.read_csv(demo_file)
    logger.info(f"📊 Loaded {len(data):,} COVID records")
    
    # Load shapefile
    shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")
    if not shapefile_path.exists():
        logger.error(f"Shapefile not found: {shapefile_path}")
        return False
    
    try:
        # Load the shapefile
        gdf = gpd.read_file(shapefile_path)
        logger.info(f"✅ Loaded shapefile with {len(gdf):,} statistical sectors")
        
        # CRITICAL MEMORY OPTIMIZATION: Aggregate sectors to municipalities
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
        
        # Merge with COVID data based on municipality identifiers
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
            logger.info(f"💾 Final memory: {map_geo_data.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
            
            return True
        else:
            logger.error("❌ No successful merge strategy found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_shapefile_aggregation()
    if success:
        print("\n🎉 Updated code test PASSED! Ready to deploy.")
    else:
        print("\n❌ Updated code test FAILED. Need to fix before deploying.")

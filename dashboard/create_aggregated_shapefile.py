#!/usr/bin/env python3
"""
Create pre-aggregated municipality shapefile for Render deployment
This eliminates the need for memory-intensive processing on Render
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import time

print("🏛️ Creating Pre-Aggregated Municipality Shapefile")
print("="*55)

# Load the full statistical sectors shapefile
shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")

if not shapefile_path.exists():
    print(f"❌ Source shapefile not found: {shapefile_path}")
    print("Please make sure the full shapefile is downloaded first.")
    exit(1)

# Output path for aggregated municipalities
output_dir = Path("data_public/municipalities")
output_dir.mkdir(exist_ok=True)

output_shapefile = output_dir / "belgium_municipalities_2019.shp"

print(f"📦 Loading source shapefile: {shapefile_path}")
start_time = time.time()

try:
    # Load the full shapefile
    gdf = gpd.read_file(shapefile_path)
    load_time = time.time() - start_time
    
    print(f"✅ Loaded {len(gdf):,} statistical sectors in {load_time:.1f}s")
    print(f"📊 Original memory: {gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"📋 CRS: {gdf.crs}")
    
    # Convert to WGS84 for web mapping
    print("🌍 Converting to WGS84...")
    start_time = time.time()
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')
    convert_time = time.time() - start_time
    print(f"✅ CRS converted in {convert_time:.1f}s")
    
    # Aggregate to municipalities using CNIS5_2019
    print("🏛️ Aggregating sectors to municipalities...")
    start_time = time.time()
    
    # Keep essential columns for the aggregated shapefile
    essential_cols = ['CNIS5_2019', 'T_MUN_NL', 'T_MUN_FR']
    
    # Check which columns are actually available
    available_cols = [col for col in essential_cols if col in gdf.columns]
    print(f"📋 Available columns: {available_cols}")
    
    # Dissolve statistical sectors into municipalities
    municipality_gdf = gdf[available_cols + ['geometry']].dissolve(
        by='CNIS5_2019', 
        as_index=False, 
        aggfunc='first'  # Take first value for text columns
    )
    
    dissolve_time = time.time() - start_time
    
    print(f"✅ Aggregated to {len(municipality_gdf):,} municipalities in {dissolve_time:.1f}s")
    print(f"📉 Size reduction: {len(gdf)/len(municipality_gdf):.1f}x fewer polygons")
    print(f"📊 New memory: {municipality_gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Simplify geometries for web performance
    print("⚡ Simplifying geometries for web mapping...")
    start_time = time.time()
    municipality_gdf['geometry'] = municipality_gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
    simplify_time = time.time() - start_time
    print(f"✅ Geometries simplified in {simplify_time:.1f}s")
    print(f"📊 Final memory: {municipality_gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Save the aggregated shapefile
    print(f"💾 Saving aggregated shapefile: {output_shapefile}")
    start_time = time.time()
    
    municipality_gdf.to_file(output_shapefile)
    save_time = time.time() - start_time
    
    print(f"✅ Saved in {save_time:.1f}s")
    
    # Check file sizes
    shapefile_size = sum(f.stat().st_size for f in output_dir.glob("belgium_municipalities_2019.*"))
    print(f"📊 Aggregated shapefile size: {shapefile_size / 1024**2:.1f} MB")
    
    # Show sample of municipalities
    print(f"\n📋 Sample municipalities:")
    print("-" * 40)
    sample_data = municipality_gdf[['CNIS5_2019', 'T_MUN_NL', 'T_MUN_FR']].head(10)
    print(sample_data.to_string(index=False))
    
    print(f"\n🎯 SUMMARY:")
    print("-" * 40)
    print(f"✅ Input: {len(gdf):,} statistical sectors")
    print(f"✅ Output: {len(municipality_gdf):,} municipalities") 
    print(f"✅ File size: {shapefile_size / 1024**2:.1f} MB")
    print(f"✅ Memory usage: {municipality_gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"✅ Ready for Git commit: {'YES' if shapefile_size < 50*1024**2 else 'NO (too large)'}")
    
    # Test loading the saved file
    print(f"\n🧪 Testing saved shapefile...")
    test_gdf = gpd.read_file(output_shapefile)
    print(f"✅ Test load successful: {len(test_gdf):,} municipalities")
    
    print(f"\n🎉 Pre-aggregated municipality shapefile created successfully!")
    print(f"📁 Location: {output_shapefile}")
    print(f"🚀 Ready to commit to Git and deploy on Render!")

except Exception as e:
    print(f"❌ Error creating aggregated shapefile: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

#!/usr/bin/env python3
"""
Test municipality aggregation locally before deploying
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import time

print("🧪 Testing Municipality Aggregation Solution")
print("="*50)

# Load the shapefile
shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")

if not shapefile_path.exists():
    print(f"❌ Shapefile not found: {shapefile_path}")
    exit(1)

# Load shapefile
print("📦 Loading shapefile...")
start_time = time.time()
gdf = gpd.read_file(shapefile_path)
load_time = time.time() - start_time

print(f"✅ Loaded {len(gdf):,} statistical sectors in {load_time:.1f}s")
print(f"📊 Original memory: {gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
print(f"📋 CRS: {gdf.crs}")

# Convert to WGS84 for web mapping
print("\n🌍 Converting to WGS84...")
start_time = time.time()
if gdf.crs != 'EPSG:4326':
    gdf = gdf.to_crs('EPSG:4326')
convert_time = time.time() - start_time
print(f"✅ CRS converted in {convert_time:.1f}s")

# Test municipality aggregation using CNIS5_2019
print(f"\n🏛️ Aggregating sectors to municipalities...")
print(f"   Using column: CNIS5_2019 (municipality NIS codes)")

start_time = time.time()

# Keep essential columns for dissolving
essential_cols = ['CNIS5_2019', 'T_MUN_NL', 'T_MUN_FR']
available_cols = [col for col in essential_cols if col in gdf.columns]
print(f"   Available columns for dissolve: {available_cols}")

# Dissolve statistical sectors into municipalities
municipality_gdf = gdf[available_cols + ['geometry']].dissolve(
    by='CNIS5_2019', 
    as_index=False, 
    aggfunc='first'  # Take first value for text columns
)

dissolve_time = time.time() - start_time

print(f"✅ Dissolved into {len(municipality_gdf):,} municipalities in {dissolve_time:.1f}s")
print(f"📉 Memory reduction: {len(gdf)/len(municipality_gdf):.1f}x")
print(f"📊 New memory: {municipality_gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Simplify geometries
print(f"\n⚡ Simplifying geometries...")
start_time = time.time()
municipality_gdf['geometry'] = municipality_gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
simplify_time = time.time() - start_time
print(f"✅ Geometries simplified in {simplify_time:.1f}s")
print(f"📊 Final memory: {municipality_gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Show sample results
print(f"\n📋 Sample Municipality Data:")
print("-" * 30)
print(municipality_gdf[['CNIS5_2019', 'T_MUN_NL', 'T_MUN_FR']].head(10))

# Test merge with COVID data
print(f"\n🦠 Testing merge with COVID data...")
demo_data_path = Path("data/demo_data_october_2020.csv")

if demo_data_path.exists():
    covid_data = pd.read_csv(demo_data_path)
    print(f"✅ Loaded COVID data: {len(covid_data):,} records")
    print(f"📋 COVID columns: {list(covid_data.columns)}")
    
    # Try merging with different strategies
    merge_strategies = [
        ('T_MUN_NL', 'TX_DESCR_NL_x'),
        ('T_MUN_FR', 'TX_DESCR_NL_x'),
        ('CNIS5_2019', 'CD_REFNIS'),
        ('CNIS5_2019', 'NIS5'),
    ]
    
    for shapefile_col, covid_col in merge_strategies:
        if shapefile_col in municipality_gdf.columns and covid_col in covid_data.columns:
            print(f"\n🔗 Testing merge: {covid_col} -> {shapefile_col}")
            
            test_merge = covid_data.merge(
                municipality_gdf[[shapefile_col, 'geometry']], 
                left_on=covid_col, 
                right_on=shapefile_col, 
                how='inner'
            )
            
            match_rate = len(test_merge) / len(covid_data) * 100
            print(f"   Matches: {len(test_merge):,} / {len(covid_data):,} ({match_rate:.1f}%)")
            
            if match_rate > 50:  # Good match rate
                print(f"   ✅ Good merge strategy!")
                
                # Create final geospatial dataset
                final_gdf = gpd.GeoDataFrame(test_merge, geometry='geometry')
                print(f"   📊 Final geo data: {len(final_gdf):,} records")
                print(f"   💾 Final memory: {final_gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
                break
            else:
                print(f"   ❌ Poor match rate, trying next strategy...")
else:
    print("⚠️ No COVID data found for merge testing")

print(f"\n🎯 SUMMARY:")
print("-" * 30)
print(f"✅ Aggregation successful: {len(gdf):,} → {len(municipality_gdf):,}")
print(f"✅ Memory reduction: {gdf.memory_usage(deep=True).sum() / municipality_gdf.memory_usage(deep=True).sum():.1f}x")
print(f"✅ Processing time: {load_time + convert_time + dissolve_time + simplify_time:.1f}s total")
print(f"✅ Should fit in 512MB: {'YES' if municipality_gdf.memory_usage(deep=True).sum() / 1024**2 < 100 else 'NO'}")

print(f"\n🎉 Municipality aggregation test completed!")

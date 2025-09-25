#!/usr/bin/env python3
"""
Test script to inspect shapefile columns and test municipality aggregation
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

print("🔍 Inspecting Belgian Statistical Sectors Shapefile...")
print("="*60)

# Load the shapefile
shapefile_path = Path("data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp")

if not shapefile_path.exists():
    print(f"❌ Shapefile not found: {shapefile_path}")
    exit(1)

# Load and inspect
print("📦 Loading shapefile...")
gdf = gpd.read_file(shapefile_path)

print(f"✅ Loaded shapefile with {len(gdf):,} records")
print(f"📋 CRS: {gdf.crs}")
print(f"📊 Shape: {gdf.shape}")

print("\n🔍 AVAILABLE COLUMNS:")
print("-" * 40)
for i, col in enumerate(gdf.columns, 1):
    print(f"{i:2d}. {col}")

print(f"\n📊 SAMPLE DATA (first 3 records):")
print("-" * 40)
print(gdf.head(3))

print(f"\n🔍 MUNICIPALITY IDENTIFICATION ANALYSIS:")
print("-" * 40)

# Look for potential municipality identifier columns
potential_muni_cols = []

for col in gdf.columns:
    if col.upper() in ['CD_REFNIS', 'NIS5', 'NISCODE', 'CD_REFNIS_MUN', 'MUNICIP', 'COMMUNE']:
        potential_muni_cols.append(col)
        print(f"✅ Found potential municipality column: {col}")
        print(f"   Sample values: {gdf[col].head(5).tolist()}")
        print(f"   Unique values: {gdf[col].nunique():,}")
        print()

# Check if we can extract municipality codes from any numeric column
for col in gdf.columns:
    if gdf[col].dtype in ['int64', 'object']:
        # Try to convert to string and see if looks like NIS codes
        try:
            col_str = gdf[col].astype(str)
            if col_str.str.len().mode()[0] >= 5:  # Belgian NIS codes are typically 5+ digits
                sample_vals = col_str.head(5).tolist()
                if all(val.isdigit() or val.replace('.', '').isdigit() for val in sample_vals if pd.notna(val)):
                    print(f"🔍 Potential NIS code column: {col}")
                    print(f"   Sample values: {sample_vals}")
                    print(f"   Length mode: {col_str.str.len().mode()[0]}")
                    
                    # Try extracting municipality codes (first 5 digits)
                    if col_str.str.len().mode()[0] >= 5:
                        muni_codes = col_str.str[:5]
                        unique_munis = muni_codes.nunique()
                        print(f"   → Municipality codes (first 5): {unique_munis:,} unique")
                        print(f"   → Sample muni codes: {muni_codes.head(5).tolist()}")
                        
                        if unique_munis < len(gdf) and unique_munis > 100:
                            potential_muni_cols.append(f"{col}_MUNI_EXTRACTED")
                            print(f"   ✅ Good candidate for municipality extraction!")
                    print()
        except:
            pass

print(f"\n🎯 RECOMMENDED AGGREGATION STRATEGY:")
print("-" * 40)

if potential_muni_cols:
    print(f"Found {len(potential_muni_cols)} potential municipality identifier columns:")
    for col in potential_muni_cols:
        print(f"  - {col}")
else:
    print("❌ No obvious municipality identifiers found.")
    print("🔧 Will need to examine the data more carefully...")

print(f"\n🧪 MEMORY TEST:")
print("-" * 40)
print(f"Current shapefile memory: {gdf.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Test a simple grouping to see what happens
if len(potential_muni_cols) > 0:
    test_col = potential_muni_cols[0].replace('_MUNI_EXTRACTED', '')
    if test_col in gdf.columns:
        print(f"🧪 Testing aggregation with column: {test_col}")
        try:
            if '_MUNI_EXTRACTED' in potential_muni_cols[0]:
                # Extract municipality codes
                gdf['MUNI_CODE'] = gdf[test_col].astype(str).str[:5]
                group_col = 'MUNI_CODE'
            else:
                group_col = test_col
            
            print(f"   Grouping by: {group_col}")
            print(f"   Before: {len(gdf):,} sectors")
            
            # Count unique groups
            unique_groups = gdf[group_col].nunique()
            print(f"   After: {unique_groups:,} municipalities (estimated)")
            print(f"   Memory reduction: {len(gdf)/unique_groups:.1f}x")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")

print(f"\n✅ Analysis complete!")

#!/usr/bin/env python3
"""
Prepare COVID-19 Belgium Dashboard for Render.com deployment

This script creates a clean deployment directory with only essential files.
"""

import shutil
import os
from pathlib import Path

def prepare_deployment():
    """Create deployment-ready directory structure."""
    
    print("🚀 Preparing COVID-19 Belgium Dashboard for Render deployment...")
    
    # Define source and destination
    source_dir = Path.cwd()
    deploy_dir = source_dir.parent / "covid-dashboard-deploy"
    
    # Create clean deployment directory
    if deploy_dir.exists():
        print(f"📁 Removing existing deployment directory: {deploy_dir}")
        shutil.rmtree(deploy_dir)
    
    deploy_dir.mkdir(exist_ok=True)
    print(f"📁 Created deployment directory: {deploy_dir}")
    
    # Essential Python files to copy
    python_files = [
        "__init__.py",
        "main.py", 
        "app.py",
        "config.py",
        "data_processing.py",
        "visualization.py", 
        "utils.py"
    ]
    
    # Configuration and documentation files
    config_files = [
        "requirements.txt",
        "render.yaml",
        "setup.py",
        "LICENSE",
        "README.md",
        "DEPLOYMENT.md"
    ]
    
    # Copy Python source files
    print("\n📋 Copying Python source files...")
    for file in python_files:
        if (source_dir / file).exists():
            shutil.copy2(source_dir / file, deploy_dir / file)
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (not found)")
    
    # Copy configuration files
    print("\n📋 Copying configuration files...")
    for file in config_files:
        if (source_dir / file).exists():
            shutil.copy2(source_dir / file, deploy_dir / file)
            print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} (not found)")
    
    # Create data directories
    print("\n📋 Creating data directories...")
    (deploy_dir / "data").mkdir(exist_ok=True)
    (deploy_dir / "data_public").mkdir(exist_ok=True)
    (deploy_dir / "data_public" / "shapefiles").mkdir(exist_ok=True)
    print("  ✅ data/")
    print("  ✅ data_public/")
    print("  ✅ data_public/shapefiles/")
    
    # Copy essential data files only
    print("\n📋 Copying essential data files...")
    essential_data_files = [
        "data/population_by_NIS.xlsx",
        "data/si_be_muni_daily.xlsx"
    ]
    
    total_size = 0
    for file_path in essential_data_files:
        source_file = source_dir / file_path
        dest_file = deploy_dir / file_path
        
        if source_file.exists():
            shutil.copy2(source_file, dest_file)
            file_size = source_file.stat().st_size
            total_size += file_size
            print(f"  ✅ {file_path} ({file_size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (REQUIRED - not found!)")
    
    print(f"\n📊 Total essential data size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    
    # Create .gitignore for deployment
    print("\n📋 Creating deployment .gitignore...")
    gitignore_content = """# Large data files (auto-downloaded)
data_public/*.csv
data/*.csv

# Cache files
__pycache__/
*.pyc

# Environment
.env
.venv

# IDE
.vscode/
.idea/
"""
    
    with open(deploy_dir / ".gitignore", "w") as f:
        f.write(gitignore_content)
    print("  ✅ .gitignore")
    
    # Verify deployment structure
    print("\n🔍 Verifying deployment structure...")
    
    # Check essential files
    missing_files = []
    for file in python_files + ["requirements.txt", "render.yaml", "README.md"]:
        if not (deploy_dir / file).exists():
            missing_files.append(file)
    
    # Check essential data
    for file_path in essential_data_files:
        if not (deploy_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("  ❌ Missing essential files:")
        for file in missing_files:
            print(f"    - {file}")
        return False
    
    # Calculate deployment size
    deployment_size = sum(f.stat().st_size for f in deploy_dir.rglob('*') if f.is_file())
    print(f"  ✅ Total deployment size: {deployment_size:,} bytes ({deployment_size/1024/1024:.1f} MB)")
    
    print("\n✅ Deployment preparation complete!")
    print(f"📁 Deployment files ready in: {deploy_dir}")
    print("\n🚀 Next steps:")
    print("1. Initialize git repository in deployment directory")
    print("2. Push to GitHub")
    print("3. Connect to Render.com")
    print("4. Follow DEPLOYMENT.md guide")
    
    return True

if __name__ == "__main__":
    success = prepare_deployment()
    if not success:
        print("\n❌ Deployment preparation failed!")
        print("Please ensure all essential files are present before deploying.")
        exit(1)

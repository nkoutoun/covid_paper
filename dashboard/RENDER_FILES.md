# Files Needed for Render.com Deployment

## ✅ Essential Files (DEPLOY THESE - 2MB total)

### Python Source Code (Required)
```
__init__.py           # Package initialization  
main.py              # Main application logic
app.py               # Production entry point for Render ⭐ NEW
config.py            # Configuration settings
data_processing.py   # Data processing pipeline  
visualization.py     # Dashboard and visualization
utils.py            # Utility functions
```

### Configuration Files (Required)
```
requirements.txt     # Python dependencies
render.yaml         # Render.com configuration ⭐ NEW
README.md           # Documentation  
LICENSE             # MIT license
```

### Essential Data Files (Required - Small)
```
data/population_by_NIS.xlsx    # 1.3MB - Municipality population
data/si_be_muni_daily.xlsx     # 662KB - Oxford stringency data
```

### Helper Files (Optional but Recommended)
```
setup.py              # Package setup
DEPLOYMENT.md         # Deployment guide ⭐ NEW  
prepare_deployment.py # Deployment helper script ⭐ NEW
.gitignore           # Updated for deployment
```

## ❌ DO NOT Deploy These Files (167MB+ total)

### Large Auto-Downloaded Files
```
❌ data_public/COVID19BE_CASES_MUNI.csv        (58.5MB)
❌ data_public/COVID19BE_VACC_MUNI_CUM.csv     (107.6MB)
❌ data_public/shapefiles/*.shp|.dbf|.shx      (222MB - now auto-downloaded!)
```

### Generated/Cache Files  
```
❌ data/intermediate_data_covid_gri.csv        (24.9MB)
❌ data/demo_data_october_2020.csv             (750KB)
❌ __pycache__/ directories
```

### Development Files
```
❌ dashboard_code_original.ipynb               (has personal paths)
❌ INSTALL.md                                  (local setup only)
```

## 🚀 Quick Deployment Steps

### Option 1: Use Helper Script (Recommended)
```bash
cd dashboard
python prepare_deployment.py
# Creates ../covid-dashboard-deploy with only essential files
cd ../covid-dashboard-deploy  
git init
git add .
git commit -m "Initial dashboard deployment"
# Push to GitHub and connect to Render
```

### Option 2: Manual Selection
1. Create new directory
2. Copy files from ✅ Essential Files list above
3. Skip files from ❌ DO NOT Deploy list
4. Deploy to Render.com

## 📊 Size Comparison

| Category | Files | Size | Deploy? |
|----------|-------|------|---------|
| **Essential Python Code** | 7 files | ~50KB | ✅ Yes |
| **Essential Data Files** | 2 files | 2MB | ✅ Yes |  
| **Config & Docs** | 5 files | ~20KB | ✅ Yes |
| **Large CSV Files** | 2 files | 167MB | ❌ No (auto-downloaded) |
| **Shapefile** | 5 files | 222MB | ❌ No (optional) |
| **Cache Files** | 2 files | 25MB | ❌ No (regenerated) |

**Total for Deployment**: ~2MB  
**Total if included everything**: ~416MB

## 🎯 Render Configuration

**In render.yaml:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`
- Environment: Python 3.11

**The app.py file handles:**
- Production host/port configuration  
- Automatic data downloads
- Dashboard startup

## 💡 Pro Tips

1. **Test locally first**: Run `python app.py` to test production config
2. **Use free tier for testing**: Upgrade to starter plan for production
3. **Monitor build logs**: First deploy takes 5-10min for data downloads
4. **Essential files only**: Keep deployment lean for faster builds

## 🆘 Troubleshooting

**"Missing module" error**: Check requirements.txt includes all dependencies  
**"Port error"**: Ensure app.py uses production configuration  
**"Data not found"**: Verify the 2 essential data files are included  
**Large build**: Make sure you excluded the ❌ files above

---

**Ready to deploy?** You need **exactly 2MB** of essential files, not the full 416MB!

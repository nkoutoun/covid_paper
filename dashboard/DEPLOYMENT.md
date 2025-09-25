# Deployment Guide: COVID-19 Belgium Dashboard on Render.com

This guide explains how to deploy your dashboard to Render.com cloud hosting.

## 📋 Essential Files for Deployment

### ✅ **Required Files (Deploy These)**

**Python Source Code:**
- `__init__.py` - Package initialization
- `main.py` - Main application logic
- `app.py` - Production entry point for Render
- `config.py` - Configuration settings
- `data_processing.py` - Data processing pipeline
- `visualization.py` - Dashboard and visualization
- `utils.py` - Utility functions

**Configuration Files:**
- `requirements.txt` - Python dependencies
- `render.yaml` - Render.com service configuration
- `setup.py` - Package setup (optional)
- `LICENSE` - License file
- `README.md` - Documentation

**Essential Data Files (Small - 2MB total):**
- `data/population_by_NIS.xlsx` (1.3MB) - Municipality population data
- `data/si_be_muni_daily.xlsx` (662KB) - Oxford Stringency Index data

### ❌ **DO NOT Deploy These Files**

**Large Auto-Downloaded Files (389MB+ total):**
- `data_public/COVID19BE_CASES_MUNI.csv` (58.5MB)
- `data_public/COVID19BE_VACC_MUNI_CUM.csv` (107.6MB) 
- `data_public/shapefiles/*` (222MB total) - **Now auto-downloaded!**

**Generated/Cache Files:**
- `data/intermediate_data_covid_gri.csv` (24.9MB)
- `data/demo_data_october_2020.csv` (750KB)
- `__pycache__/` directories

**Development Files:**
- `dashboard_code_original.ipynb` (contains personal paths)
- `INSTALL.md` (local setup guide)
- `.gitignore` (already configured to exclude large files)

## 🚀 Deployment Steps

### 1. Prepare Your Repository

Create a clean repository with only essential files:

```bash
# Create new directory for deployment
mkdir covid-dashboard-deploy
cd covid-dashboard-deploy

# Copy essential Python files
cp *.py ../
cp requirements.txt render.yaml LICENSE README.md ../

# Copy essential data files only
mkdir data
cp data/population_by_NIS.xlsx data/
cp data/si_be_muni_daily.xlsx data/

# Create empty data_public directory (will be populated by app)
mkdir data_public
mkdir data_public/shapefiles
```

### 2. Deploy to Render

#### Option A: GitHub Integration (Recommended)
1. Push your repository to GitHub
2. Go to [Render.com](https://render.com)
3. Connect your GitHub account
4. Select "Web Service" 
5. Choose your repository
6. Render will automatically detect the `render.yaml` configuration

#### Option B: Manual Deployment  
1. Create account on [Render.com](https://render.com)
2. Create new "Web Service"
3. Upload your deployment files
4. Configure manually:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment**: Python 3.11

### 3. Configure Environment Variables

In Render dashboard, add these environment variables:
- `PYTHON_VERSION`: `3.11`
- `RENDER_DEPLOY`: `true`
- `DEBUG`: `false` (for production)

### 4. Monitor Deployment

**Expected Build Time**: 8-15 minutes
- Installing dependencies: ~2 minutes
- First data download: ~3-5 minutes (large COVID files)
- Shapefile download: ~3-5 minutes (222MB Belgian boundaries)
- Dashboard initialization: ~1-2 minutes

**Build Logs to Watch For:**
```
✅ Installing dependencies from requirements.txt
✅ Downloading COVID-19 data from Sciensano...
⚠️ Shapefile not found locally, attempting to download...
📦 Downloading Belgian municipality shapefile...
✅ Shapefile extracted successfully
✅ Processing data pipeline...
✅ Creating dashboard app...
✅ Dashboard ready at https://your-app.onrender.com
```

## 🔧 Production Configuration

The `app.py` file automatically handles production settings:

- **Host**: `0.0.0.0` (required for Render)
- **Port**: From `PORT` environment variable (Render provides this)
- **Debug**: `false` in production
- **Data Downloads**: Automatic on first run

## 📊 Data Handling in Production

### Automatic Downloads
- COVID cases and vaccination data download automatically from Sciensano APIs (~165MB)
- Belgian municipality shapefile downloads from StatBel (~222MB)
- Total automatic downloads on first run: ~389MB
- Subsequent runs use cached data

### Data Persistence
- Render provides persistent storage for processed data
- Cache files survive deployments
- Essential local files (population, Oxford data) are included in deployment

## ⚡ Performance Considerations

### Free Tier Limitations
- **RAM**: 512MB (may need starter plan for full dataset)
- **Sleep**: Apps sleep after 15min inactivity
- **Build Time**: 500 minutes/month

### Optimization Tips
- Use time filtering for better performance: `main(time_filter=('2020-10-01', '2020-12-31'))`
- Consider upgrading to Starter plan ($7/month) for better performance
- Monitor memory usage in Render logs

## 🐛 Troubleshooting

### Common Issues

#### Build Failures
**Issue**: `ModuleNotFoundError` 
**Solution**: Check `requirements.txt` includes all dependencies

**Issue**: Memory errors during build
**Solution**: Upgrade to Starter plan or use time filtering

#### Runtime Issues
**Issue**: Dashboard won't start
**Solution**: Check environment variables and port configuration

**Issue**: Data download fails
**Solution**: Verify internet access and Sciensano API availability

#### Performance Issues
**Issue**: Slow loading
**Solution**: Use demo mode or time filtering for smaller datasets

### Debug Mode
Enable debug logging by setting environment variable:
- `DEBUG`: `true`

## 📱 Accessing Your Dashboard

Once deployed, your dashboard will be available at:
`https://covid-belgium-dashboard.onrender.com`

**Features Available:**
- Interactive choropleth maps
- Time-based analysis controls
- Multiple variable selection
- Real-time statistics
- Responsive design for mobile/desktop

## 🔄 Updates and Maintenance

### Automatic Updates
- Render rebuilds automatically on git push (if using GitHub integration)
- Data refreshes automatically when force-reload is triggered

### Manual Updates
```bash
# To update data manually, trigger rebuild in Render dashboard
# Or add webhook for automatic data refresh
```

## 💰 Cost Estimation

**Free Tier**: $0/month
- Good for demos and testing
- 500 build minutes/month
- Apps sleep after 15min inactivity

**Starter Plan**: $7/month
- Recommended for production use
- Always-on service
- Better performance (1GB RAM)

## 🆘 Support

If you encounter issues:
1. Check Render build logs for error messages
2. Verify all essential files are included
3. Test locally with production configuration
4. Contact Render support for infrastructure issues

---

**Total Deployment Size**: ~2MB (essential files only)
**First Build Time**: ~5-10 minutes
**Subsequent Builds**: ~2-3 minutes

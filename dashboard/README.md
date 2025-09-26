# Belgium COVID-19 Interactive Dashboard

An interactive web dashboard for exploring COVID-19 data across Belgian municipalities with temporal analysis and geospatial visualization.

## ✨ Features

- **Interactive Municipality Map**: Choropleth visualization with real Belgian boundaries (581 municipalities)
- **Temporal Analysis**: Time slider covering 2019-2022 with adaptive time marks
- **Multiple Variables**: COVID-19 cases, stringency index, vaccination rates, population data
- **Real-time Statistics**: Dynamic statistics cards showing totals, means, and maximums
- **Responsive Design**: Optimized for web deployment with fast performance

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python app.py

# Open browser to http://localhost:8050
```

### Live Demo
Visit the deployed dashboard: https://covid-belgium-dashboard.onrender.com

## 📊 Data Sources

- **COVID-19 Cases**: Sciensano (Belgian Institute for Health) - Only publicly available data is shown. When daily cases are <5 for a municipality, we set them to be equal to 1 for data privacy reasons.
- **Vaccination Data**: Sciensano (Belgian Institute for Health)  
- **Geographic Boundaries**: StatBel (Belgian Statistics Office)
- **Government Response**: Oxford COVID-19 Government Response Tracker
- **Coverage**: 91K+ records across 581 municipalities (2019-2022)

## 🏗️ Architecture

```
dashboard/
├── app.py                    # Main Dash application
├── data_processing.py        # Shapefile download utilities
├── data/                     # COVID-19 dataset (91K records)
├── data_public/
│   └── municipalities/       # Pre-aggregated Belgian boundaries (1.1MB)
├── requirements.txt          # Python dependencies
└── render.yaml              # Deployment configuration
```

## 🛠️ Technical Details

- **Framework**: Dash + Plotly for interactive visualizations
- **Geospatial**: GeoPandas with optimized municipality boundaries
- **Performance**: Pre-cached data and geometry simplification
- **Memory**: <100MB total footprint for cloud deployment

## 🌍 Deployment

The dashboard is optimized for **Render.com** deployment:
- Automatic builds from Git commits
- Uses pre-processed data for fast startup
- Memory-optimized for free tier limits
- No external API dependencies

## 📈 Performance Optimizations

- Pre-aggregated shapefiles (from 19K sectors to 581 municipalities)
- Cached GeoJSON for all time periods
- Simplified geometries for web rendering
- Minimal dependencies (7 essential packages)
- Progressive data loading

## 🤝 Contributing

This dashboard was created for COVID-19 research analysis. For questions or contributions, please contact Nikolaos Koutounidis.

---
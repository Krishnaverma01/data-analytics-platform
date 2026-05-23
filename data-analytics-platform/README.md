# DataLens - Data Analytics Platform

## Project Overview
A comprehensive data analysis and visualization web application built with Python Flask backend and HTML/CSS/JS frontend.

## How to Run
```bash
cd /home/z/my-project/download/data-analytics-platform
python3 app.py
```
Then open http://localhost:5000 in your browser.

## Project Structure
```
data-analytics-platform/
├── app.py                    # Flask backend with all API endpoints
├── start.sh                  # Startup script
├── sample_data.csv           # Sample dataset for testing
├── templates/
│   └── index.html            # Main dashboard HTML
├── static/
│   ├── css/
│   │   └── style.css         # Soft white minimalist responsive CSS
│   └── js/
│       ├── app.js            # Main JS - connects frontend to Flask
│       └── charts.js         # Chart.js visualization module
└── utils/
    ├── __init__.py
    ├── analyzer.py           # Data analysis engine (ML, stats, predictions)
    └── report_generator.py   # PDF report generation
```

## Features
1. **Data Upload** - CSV, XLSX, JSON, TSV support with drag & drop
2. **Data Overview** - Shape, types, missing values, quality score
3. **Correlation Analysis** - Heatmap, strongest correlations, insights
4. **Distribution Analysis** - Histograms, box plots, normality tests, outlier detection
5. **Anomaly Detection** - Isolation Forest algorithm with deviation profiling
6. **Predictions** - Linear regression, polynomial, Random Forest, Gradient Boosting
7. **Problem Detection** - 7 types of data quality issues with severity levels
8. **Solutions** - Actionable fixes with step-by-step instructions
9. **Feature Engineering** - Temporal, interaction, aggregation, statistical features
10. **Clustering** - K-Means with PCA visualization, auto cluster detection
11. **PDF Report** - Complete downloadable analysis report

## Tech Stack
- Backend: Python 3, Flask, pandas, scikit-learn, matplotlib, reportlab
- Frontend: HTML5, CSS3, JavaScript (vanilla), Chart.js
- ML: Isolation Forest, Random Forest, Gradient Boosting, KMeans, PCA

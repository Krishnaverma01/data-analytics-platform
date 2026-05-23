#!/bin/bash
# DataLens Analytics Platform - Start Script

echo "=================================================="
echo "  DataLens - Data Analytics Platform"
echo "=================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check dependencies
python3 -c "import flask, pandas, sklearn, reportlab" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install flask flask-cors pandas scikit-learn matplotlib seaborn reportlab scipy openpyxl xlrd
fi

echo ""
echo "Starting server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")"
python3 app.py

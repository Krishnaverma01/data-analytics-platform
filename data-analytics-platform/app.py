"""
Data Analytics Platform - Flask Backend
A comprehensive data analysis and visualization web application.
"""
import os
import sys
import json
import uuid
import traceback
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS

# Add utils to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.analyzer import DataAnalyzer
from utils.report_generator import ReportGenerator


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy and pandas types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, (pd.Timestamp,)):
            return obj.isoformat()
        elif isinstance(obj, (pd.Timedelta,)):
            return str(obj)
        elif pd.isna(obj):
            return None
        return super().default(obj)


app = Flask(__name__)
app.secret_key = os.urandom(24)
# NumpyEncoder handled by _sanitize_for_json() below
# Allow cross-origin requests from any frontend host (needed for split hosting)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
REPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# In-memory session storage for analysis data
analysis_sessions = {}


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and parse CSV/Excel file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Read file based on extension
        filename = file.filename.lower()
        filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{file.filename}")
        file.save(filepath)

        try:
            if filename.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(filepath)
            elif filename.endswith(('.xlsx', '.xls')):
                import pandas as pd
                df = pd.read_excel(filepath)
            elif filename.endswith('.json'):
                import pandas as pd
                df = pd.read_json(filepath)
            elif filename.endswith('.tsv'):
                import pandas as pd
                df = pd.read_csv(filepath, sep='\t')
            else:
                os.remove(filepath)
                return jsonify({"error": "Unsupported file format. Please upload CSV, Excel, JSON, or TSV files."}), 400
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": f"Error reading file: {str(e)}"}), 400

        # Store in session
        analysis_sessions[session_id] = {
            "df": df,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "filepath": filepath
        }

        # Quick preview
        preview = df.head(20).fillna("N/A").to_dict(orient='records')
        columns = [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns]

        return jsonify({
            "session_id": session_id,
            "filename": file.filename,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "preview": preview,
            "column_info": columns
        })

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """Run complete data analysis."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session. Please upload data first."}), 400

        df = analysis_sessions[session_id]["df"]
        analyzer = DataAnalyzer(df)
        results = analyzer.get_full_analysis()

        # Store analyzer for subsequent requests
        analysis_sessions[session_id]["analyzer"] = analyzer
        analysis_sessions[session_id]["full_analysis"] = results

        # Also generate business insights
        business = analyzer.get_business_insights()
        results["business_insights"] = business

        return jsonify(_sanitize_for_json(results))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route('/api/analyze/overview', methods=['POST'])
def analyze_overview():
    """Get data overview only."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        df = analysis_sessions[session_id]["df"]
        analyzer = DataAnalyzer(df)
        return jsonify(_sanitize_for_json(analyzer.get_overview()))

    except Exception as e:
        return jsonify({"error": f"Overview analysis failed: {str(e)}"}), 500


@app.route('/api/analyze/correlations', methods=['POST'])
def analyze_correlations():
    """Get correlation analysis."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        return jsonify(_sanitize_for_json(analyzer.get_correlation_analysis()))

    except Exception as e:
        return jsonify({"error": f"Correlation analysis failed: {str(e)}"}), 500


@app.route('/api/analyze/distributions', methods=['POST'])
def analyze_distributions():
    """Get distribution analysis."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        return jsonify(_sanitize_for_json(analyzer.get_distribution_analysis()))

    except Exception as e:
        return jsonify({"error": f"Distribution analysis failed: {str(e)}"}), 500


@app.route('/api/analyze/anomalies', methods=['POST'])
def analyze_anomalies():
    """Get anomaly detection results."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        return jsonify(_sanitize_for_json(analyzer.detect_anomalies()))

    except Exception as e:
        return jsonify({"error": f"Anomaly detection failed: {str(e)}"}), 500


@app.route('/api/analyze/problems', methods=['POST'])
def analyze_problems():
    """Get problem detection results."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        problems = analyzer.detect_problems()
        solutions = analyzer.suggest_solutions(problems["problems"])
        return jsonify(_sanitize_for_json({"problems": problems, "solutions": solutions}))

    except Exception as e:
        return jsonify({"error": f"Problem detection failed: {str(e)}"}), 500


@app.route('/api/analyze/predictions', methods=['POST'])
def analyze_predictions():
    """Get ML predictions."""
    try:
        data = request.json
        session_id = data.get('session_id')
        target_col = data.get('target_column')
        periods = data.get('periods', 5)

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        return jsonify(_sanitize_for_json(analyzer.predict_future(target_col, periods)))

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route('/api/analyze/features', methods=['POST'])
def analyze_features():
    """Get feature engineering suggestions."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        return jsonify(_sanitize_for_json(analyzer.get_feature_suggestions()))

    except Exception as e:
        return jsonify({"error": f"Feature analysis failed: {str(e)}"}), 500


@app.route('/api/analyze/clustering', methods=['POST'])
def analyze_clustering():
    """Get clustering analysis."""
    try:
        data = request.json
        session_id = data.get('session_id')
        n_clusters = data.get('n_clusters')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        analyzer = _get_analyzer(session_id)
        return jsonify(_sanitize_for_json(analyzer.get_clustering_analysis(n_clusters)))

    except Exception as e:
        return jsonify({"error": f"Clustering analysis failed: {str(e)}"}), 500


@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    """Generate downloadable PDF report."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        # Get or run full analysis
        if "full_analysis" in analysis_sessions[session_id]:
            analysis = analysis_sessions[session_id]["full_analysis"]
        else:
            analyzer = _get_analyzer(session_id)
            analysis = analyzer.get_full_analysis()

        # Add predictions if available
        try:
            analyzer = _get_analyzer(session_id)
            predictions = analyzer.predict_future()
            analysis["predictions"] = predictions
        except Exception:
            pass

        # Add solutions
        try:
            if "problems" in analysis:
                analyzer = _get_analyzer(session_id)
                solutions = analyzer.suggest_solutions(analysis["problems"]["problems"])
                analysis["solutions"] = solutions
        except Exception:
            pass

        # Generate PDF
        filename = f"analysis_report_{session_id[:8]}.pdf"
        report_gen = ReportGenerator(analysis, filename)
        filepath = report_gen.generate()

        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": f"/api/report/download/{filename}"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500


@app.route('/api/report/download/<filename>')
def download_report(filename):
    """Download generated PDF report."""
    try:
        # Check in reports directory
        report_path = os.path.join(REPORT_FOLDER, filename)
        if os.path.exists(report_path):
            return send_file(report_path, as_attachment=True, download_name=filename)
        return jsonify({"error": "Report file not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500


@app.route('/api/columns', methods=['POST'])
def get_columns():
    """Get column info for prediction target selection."""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id not in analysis_sessions:
            return jsonify({"error": "Invalid session"}), 400

        df = analysis_sessions[session_id]["df"]
        analyzer = DataAnalyzer(df)
        numeric_cols = analyzer.numeric_cols
        categorical_cols = analyzer.categorical_cols

        return jsonify({
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "all_columns": list(df.columns)
        })

    except Exception as e:
        return jsonify({"error": f"Failed to get columns: {str(e)}"}), 500


def _sanitize_for_json(obj):
    """Deep convert numpy/pandas types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat() if not pd.isna(obj) else None
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    elif pd.isna(obj) if isinstance(obj, (float, int)) else False:
        return None
    return obj


def _get_analyzer(session_id):
    """Get or create analyzer for session."""
    if "analyzer" in analysis_sessions[session_id]:
        return analysis_sessions[session_id]["analyzer"]
    else:
        df = analysis_sessions[session_id]["df"]
        analyzer = DataAnalyzer(df)
        analysis_sessions[session_id]["analyzer"] = analyzer
        return analyzer


if __name__ == '__main__':
    print("=" * 50)
    print("  Data Analytics Platform")
    print("  Starting server on http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

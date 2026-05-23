"""
Data Analysis Engine - Core analytics, ML predictions, anomaly detection
"""
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest, RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')


class DataAnalyzer:
    """Comprehensive data analysis engine with ML capabilities."""

    def __init__(self, df):
        self.df = df.copy()
        self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        self._detect_datetime_columns()

    def _detect_datetime_columns(self):
        """Auto-detect datetime columns from string columns."""
        for col in self.categorical_cols[:]:
            sample = self.df[col].dropna().head(20)
            parsed = pd.to_datetime(sample, errors='coerce')
            if parsed.notna().mean() > 0.7:
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    self.categorical_cols.remove(col)
                    self.datetime_cols.append(col)
                except Exception:
                    pass

    def get_overview(self):
        """Generate comprehensive data overview."""
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_cells = int(self.df.isnull().sum().sum())
        duplicate_rows = int(self.df.duplicated().sum())

        overview = {
            "shape": {"rows": int(self.df.shape[0]), "columns": int(self.df.shape[1])},
            "total_cells": total_cells,
            "missing_cells": missing_cells,
            "missing_percentage": round((missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0,
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": round((duplicate_rows / self.df.shape[0]) * 100, 2) if self.df.shape[0] > 0 else 0,
            "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            "numeric_columns": len(self.numeric_cols),
            "categorical_columns": len(self.categorical_cols),
            "datetime_columns": len(self.datetime_cols),
            "column_details": []
        }

        for col in self.df.columns:
            col_info = {
                "name": col,
                "dtype": str(self.df[col].dtype),
                "non_null": int(self.df[col].notna().sum()),
                "null_count": int(self.df[col].isnull().sum()),
                "null_percentage": round((self.df[col].isnull().sum() / self.df.shape[0]) * 100, 2),
                "unique_count": int(self.df[col].nunique()),
                "is_numeric": col in self.numeric_cols,
                "is_categorical": col in self.categorical_cols,
                "is_datetime": col in self.datetime_cols,
            }
            if col in self.numeric_cols:
                desc = self.df[col].describe()
                col_info["stats"] = {
                    "mean": round(float(desc.get('mean', 0)), 4),
                    "std": round(float(desc.get('std', 0)), 4),
                    "min": round(float(desc.get('min', 0)), 4),
                    "q25": round(float(desc.get('25%', 0)), 4),
                    "q50": round(float(desc.get('50%', 0)), 4),
                    "q75": round(float(desc.get('75%', 0)), 4),
                    "max": round(float(desc.get('max', 0)), 4),
                    "skewness": round(float(self.df[col].skew()), 4) if self.df[col].notna().sum() > 2 else None,
                    "kurtosis": round(float(self.df[col].kurtosis()), 4) if self.df[col].notna().sum() > 2 else None,
                }
            elif col in self.categorical_cols:
                value_counts = self.df[col].value_counts().head(5)
                col_info["top_values"] = {str(k): int(v) for k, v in value_counts.items()}
            overview["column_details"].append(col_info)

        return overview

    def get_correlation_analysis(self):
        """Perform correlation analysis on numeric columns."""
        if len(self.numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns for correlation analysis"}

        corr_matrix = self.df[self.numeric_cols].corr()

        # Find strongest correlations
        correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                val = float(corr_matrix.iloc[i, j])
                if not np.isnan(val):
                    correlations.append({
                        "var1": corr_matrix.columns[i],
                        "var2": corr_matrix.columns[j],
                        "correlation": round(val, 4),
                        "strength": self._interpret_correlation(val),
                        "direction": "positive" if val > 0 else "negative"
                    })

        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "correlation_matrix": {
                "columns": self.numeric_cols,
                "values": [[round(float(corr_matrix.iloc[i, j]), 4) for j in range(len(corr_matrix.columns))]
                           for i in range(len(corr_matrix.columns))]
            },
            "strongest_correlations": correlations[:10],
            "insights": self._generate_correlation_insights(correlations)
        }

    def _interpret_correlation(self, val):
        abs_val = abs(val)
        if abs_val >= 0.8:
            return "Very Strong"
        elif abs_val >= 0.6:
            return "Strong"
        elif abs_val >= 0.4:
            return "Moderate"
        elif abs_val >= 0.2:
            return "Weak"
        else:
            return "Very Weak"

    def _generate_correlation_insights(self, correlations):
        insights = []
        for c in correlations[:5]:
            if abs(c["correlation"]) >= 0.7:
                insights.append(
                    f"Strong {c['direction']} correlation ({c['correlation']}) between '{c['var1']}' and '{c['var2']}'. "
                    f"These variables are highly related and may indicate redundancy or a strong underlying pattern."
                )
            elif abs(c["correlation"]) >= 0.4:
                insights.append(
                    f"Moderate {c['direction']} correlation ({c['correlation']}) between '{c['var1']}' and '{c['var2']}'. "
                    f"There is a meaningful relationship worth investigating further."
                )
        if not insights:
            insights.append("No strong correlations found between numeric variables. Variables appear to be largely independent.")
        return insights

    def get_distribution_analysis(self):
        """Analyze distributions of numeric columns."""
        distributions = {}
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) < 3:
                continue

            # Histogram bins
            hist, bin_edges = np.histogram(data, bins=20)
            distributions[col] = {
                "histogram": {
                    "counts": [int(x) for x in hist],
                    "bins": [round(float(x), 4) for x in bin_edges]
                },
                "statistics": {
                    "mean": round(float(data.mean()), 4),
                    "median": round(float(data.median()), 4),
                    "mode": round(float(data.mode().iloc[0]), 4),
                    "std": round(float(data.std()), 4),
                    "variance": round(float(data.var()), 4),
                    "skewness": round(float(data.skew()), 4),
                    "kurtosis": round(float(data.kurtosis()), 4),
                    "range": round(float(data.max() - data.min()), 4),
                    "iqr": round(float(data.quantile(0.75) - data.quantile(0.25)), 4),
                },
                "distribution_shape": self._classify_distribution(data.skew(), data.kurtosis()),
                "outliers_iqr": self._detect_outliers_iqr(data),
                "normality_test": self._test_normality(data)
            }
        return distributions

    def _classify_distribution(self, skew, kurt):
        shape = []
        if abs(skew) < 0.5:
            shape.append("Symmetric")
        elif skew > 0:
            shape.append("Right-skewed")
        else:
            shape.append("Left-skewed")

        if kurt > 3:
            shape.append("Leptokurtic (heavy tails)")
        elif kurt < 3:
            shape.append("Platykurtic (light tails)")
        else:
            shape.append("Mesokurtic (normal-like)")

        return " | ".join(shape)

    def _detect_outliers_iqr(self, data):
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = data[(data < lower) | (data > upper)]
        return {
            "count": int(len(outliers)),
            "percentage": round((len(outliers) / len(data)) * 100, 2),
            "lower_bound": round(float(lower), 4),
            "upper_bound": round(float(upper), 4)
        }

    def _test_normality(self, data):
        if len(data) < 3:
            return {"test": "insufficient_data"}
        if len(data) > 5000:
            data = data.sample(5000, random_state=42)
        try:
            stat, p_value = stats.shapiro(data)
            return {
                "test": "Shapiro-Wilk",
                "statistic": round(float(stat), 6),
                "p_value": round(float(p_value), 6),
                "is_normal": p_value > 0.05
            }
        except Exception:
            return {"test": "failed"}

    def detect_anomalies(self):
        """Detect anomalies using Isolation Forest."""
        try:
            if len(self.numeric_cols) < 1:
                return {"error": "Need at least 1 numeric column for anomaly detection"}

            data = self.df[self.numeric_cols].dropna()
            if len(data) < 10:
                return {"error": "Need at least 10 rows for anomaly detection"}

            # Limit data size to prevent OOM on free hosting (512MB RAM)
            max_rows = 5000
            if len(data) > max_rows:
                data = data.sample(n=max_rows, random_state=42)

            contamination = min(0.1, max(0.01, 5 / len(data)))
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=50,
                max_samples='auto',
                n_jobs=1
            )
            predictions = iso_forest.fit_predict(data)
            anomaly_scores = iso_forest.decision_function(data)

            anomaly_mask = predictions == -1
            anomalies = data[anomaly_mask].copy()
            normal = data[~anomaly_mask].copy()

            anomaly_indices = data.index[anomaly_mask].tolist()

            # Analyze what makes anomalies different
            anomaly_profile = {}
            if len(anomalies) > 0:
                for col in self.numeric_cols:
                    anomaly_profile[col] = {
                        "normal_mean": round(float(normal[col].mean()), 4),
                        "anomaly_mean": round(float(anomalies[col].mean()), 4),
                        "deviation_pct": round(float(
                            abs(anomalies[col].mean() - normal[col].mean()) / max(abs(normal[col].mean()), 1e-10) * 100
                        ), 2)
                    }

            return {
                "total_anomalies": int(anomaly_mask.sum()),
                "anomaly_percentage": round(float(anomaly_mask.mean() * 100), 2),
                "anomaly_indices": anomaly_indices[:100],
                "anomaly_scores": [round(float(s), 4) for s in anomaly_scores[:100]],
                "anomaly_profile": anomaly_profile,
                "insights": self._generate_anomaly_insights(anomaly_mask.sum(), len(data), anomaly_profile)
            }
        except Exception as e:
            return {"error": f"Anomaly detection skipped: {str(e)}"}

    def _generate_anomaly_insights(self, n_anomalies, total, profile):
        insights = []
        pct = round((n_anomalies / total) * 100, 2)
        if pct > 10:
            insights.append(f"High anomaly rate ({pct}%). This could indicate significant data quality issues or genuinely unusual patterns requiring investigation.")
        elif pct > 5:
            insights.append(f"Moderate anomaly rate ({pct}%). Some data points deviate significantly from normal patterns.")
        else:
            insights.append(f"Low anomaly rate ({pct}%). Dataset is relatively consistent with few outliers.")

        top_deviations = sorted(profile.items(), key=lambda x: x[1]["deviation_pct"], reverse=True)[:3]
        for col, info in top_deviations:
            if info["deviation_pct"] > 20:
                insights.append(
                    f"Anomalies show {info['deviation_pct']}% deviation in '{col}' "
                    f"(normal: {info['normal_mean']}, anomaly: {info['anomaly_mean']}). "
                    f"This column is a key driver of anomalous behavior."
                )
        return insights

    def predict_future(self, target_col=None, periods=5):
        """Predict future values using ML models."""
        if len(self.numeric_cols) < 1:
            return {"error": "Need numeric columns for prediction"}

        if target_col is None:
            target_col = self.numeric_cols[-1]
        elif target_col not in self.numeric_cols:
            return {"error": f"Target column '{target_col}' not found or not numeric"}

        feature_cols = [c for c in self.numeric_cols if c != target_col]
        data = self.df[self.numeric_cols].dropna()

        if len(data) < 10:
            return {"error": "Need at least 10 rows for prediction"}

        results = {"target": target_col, "predictions": {}}

        # 1. Time-series-like trend prediction using index
        try:
            X = np.arange(len(data)).reshape(-1, 1)
            y = data[target_col].values

            # Linear Trend
            lr = LinearRegression()
            lr.fit(X, y)
            future_X = np.arange(len(data), len(data) + periods).reshape(-1, 1)
            lr_preds = lr.predict(future_X)

            results["predictions"]["linear_trend"] = {
                "model": "Linear Regression",
                "future_values": [round(float(v), 4) for v in lr_preds],
                "r2_score": round(float(r2_score(y, lr.predict(X))), 4),
                "trend": "increasing" if lr.coef_[0] > 0 else "decreasing",
                "slope": round(float(lr.coef_[0]), 4),
                "intercept": round(float(lr.intercept_), 4)
            }

            # Polynomial trend (degree 2)
            from sklearn.preprocessing import PolynomialFeatures
            poly = PolynomialFeatures(degree=2)
            X_poly = poly.fit_transform(X)
            lr_poly = LinearRegression()
            lr_poly.fit(X_poly, y)
            future_X_poly = poly.transform(future_X)
            poly_preds = lr_poly.predict(future_X_poly)

            results["predictions"]["polynomial_trend"] = {
                "model": "Polynomial Regression (degree 2)",
                "future_values": [round(float(v), 4) for v in poly_preds],
                "r2_score": round(float(r2_score(y, lr_poly.predict(X_poly))), 4)
            }
        except Exception as e:
            results["predictions"]["trend_error"] = str(e)

        # 2. Multi-feature prediction
        if len(feature_cols) >= 1:
            try:
                X_multi = data[feature_cols].values
                y_multi = data[target_col].values

                X_train, X_test, y_train, y_test = train_test_split(
                    X_multi, y_multi, test_size=0.2, random_state=42
                )

                # Random Forest
                rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
                rf.fit(X_train, y_train)
                rf_preds = rf.predict(X_test)
                rf_r2 = r2_score(y_test, rf_preds)

                feature_importance = sorted(
                    zip(feature_cols, rf.feature_importances_),
                    key=lambda x: x[1], reverse=True
                )

                results["predictions"]["random_forest"] = {
                    "model": "Random Forest Regressor",
                    "r2_score": round(float(rf_r2), 4),
                    "mae": round(float(mean_absolute_error(y_test, rf_preds)), 4),
                    "rmse": round(float(np.sqrt(mean_squared_error(y_test, rf_preds))), 4),
                    "feature_importance": [
                        {"feature": f, "importance": round(float(i), 4)} for f, i in feature_importance
                    ]
                }

                # Gradient Boosting
                gb = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
                gb.fit(X_train, y_train)
                gb_preds = gb.predict(X_test)
                gb_r2 = r2_score(y_test, gb_preds)

                results["predictions"]["gradient_boosting"] = {
                    "model": "Gradient Boosting Regressor",
                    "r2_score": round(float(gb_r2), 4),
                    "mae": round(float(mean_absolute_error(y_test, gb_preds)), 4),
                    "rmse": round(float(np.sqrt(mean_squared_error(y_test, gb_preds))), 4)
                }

                # Best model prediction for future
                best_model = rf if rf_r2 >= gb_r2 else gb
                best_name = "Random Forest" if rf_r2 >= gb_r2 else "Gradient Boosting"

                # Use recent feature patterns to simulate future
                recent_features = data[feature_cols].tail(periods).values
                if len(recent_features) < periods:
                    recent_features = np.vstack([recent_features] * ((periods // len(recent_features)) + 1))[:periods]
                future_preds = best_model.predict(recent_features)

                results["predictions"]["best_model_forecast"] = {
                    "model": best_name,
                    "future_values": [round(float(v), 4) for v in future_preds],
                    "r2_score": round(float(max(rf_r2, gb_r2)), 4)
                }

            except Exception as e:
                results["predictions"]["multi_feature_error"] = str(e)

        # Generate prediction insights
        results["insights"] = self._generate_prediction_insights(results)
        return results

    def _generate_prediction_insights(self, results):
        insights = []
        preds = results.get("predictions", {})

        if "linear_trend" in preds:
            lt = preds["linear_trend"]
            direction = "upward" if lt["trend"] == "increasing" else "downward"
            insights.append(
                f"The target variable '{results['target']}' shows a {direction} linear trend "
                f"(slope: {lt['slope']}, R²: {lt['r2_score']}). "
            )
            if lt["r2_score"] > 0.7:
                insights.append("The linear trend is strong and reliable for forecasting.")
            elif lt["r2_score"] > 0.4:
                insights.append("The linear trend is moderate; consider non-linear patterns.")
            else:
                insights.append("The linear trend is weak; the variable may be highly volatile or influenced by other factors.")

        if "random_forest" in preds:
            rf = preds["random_forest"]
            insights.append(
                f"Random Forest model achieves R² of {rf['r2_score']} with MAE of {rf['mae']}. "
            )
            if rf["feature_importance"]:
                top_feat = rf["feature_importance"][0]
                insights.append(
                    f"The most important predictor is '{top_feat['feature']}' "
                    f"(importance: {top_feat['importance']})."
                )

        return insights

    def detect_problems(self):
        """Detect data quality problems, issues, and mistakes."""
        problems = []

        # 1. Missing values
        missing = self.df.isnull().sum()
        for col in missing[missing > 0].index:
            pct = (missing[col] / self.df.shape[0]) * 100
            severity = "Critical" if pct > 50 else "High" if pct > 30 else "Medium" if pct > 10 else "Low"
            problems.append({
                "type": "Missing Values",
                "column": col,
                "severity": severity,
                "details": f"{int(missing[col])} missing values ({round(pct, 2)}%) in column '{col}'",
                "impact": "Missing data can bias analysis results and reduce model accuracy. Imputation or removal strategies needed.",
                "solution": self._suggest_missing_solution(col, pct)
            })

        # 2. Duplicate rows
        dup_count = int(self.df.duplicated().sum())
        if dup_count > 0:
            pct = (dup_count / self.df.shape[0]) * 100
            problems.append({
                "type": "Duplicate Rows",
                "column": "All",
                "severity": "High" if pct > 10 else "Medium" if pct > 5 else "Low",
                "details": f"{dup_count} duplicate rows found ({round(pct, 2)}% of data)",
                "impact": "Duplicate records inflate statistics and can lead to overfitting in ML models.",
                "solution": "Remove duplicate rows using df.drop_duplicates(). Investigate data collection process to prevent duplicates."
            })

        # 3. Outliers
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) < 10:
                continue
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_count = int(((data < lower) | (data > upper)).sum())
            if outlier_count > 0:
                pct = (outlier_count / len(data)) * 100
                severity = "High" if pct > 10 else "Medium" if pct > 5 else "Low"
                problems.append({
                    "type": "Outliers",
                    "column": col,
                    "severity": severity,
                    "details": f"{outlier_count} outliers in '{col}' ({round(pct, 2)}%) - values beyond [{round(float(lower), 4)}, {round(float(upper), 4)}]",
                    "impact": "Outliers can significantly distort statistical measures and model training.",
                    "solution": f"Consider capping values at the IQR bounds, using robust statistical methods, or investigating if these are genuine extreme values."
                })

        # 4. High cardinality categorical columns
        for col in self.categorical_cols:
            nunique = self.df[col].nunique()
            if nunique > 50:
                problems.append({
                    "type": "High Cardinality",
                    "column": col,
                    "severity": "Medium",
                    "details": f"Column '{col}' has {nunique} unique values",
                    "impact": "High cardinality features can cause dimensionality explosion with one-hot encoding and overfitting.",
                    "solution": "Consider grouping rare categories, using target encoding, or frequency encoding instead of one-hot encoding."
                })

        # 5. Constant or near-constant columns
        for col in self.df.columns:
            nunique = self.df[col].nunique()
            if nunique <= 1:
                problems.append({
                    "type": "Constant Column",
                    "column": col,
                    "severity": "Medium",
                    "details": f"Column '{col}' has only {nunique} unique value(s)",
                    "impact": "Constant columns provide no information for analysis or modeling.",
                    "solution": "Remove this column as it adds no value to the analysis."
                })
            elif nunique == 2 and self.df[col].value_counts().iloc[0] / self.df.shape[0] > 0.95:
                problems.append({
                    "type": "Near-Constant Column",
                    "column": col,
                    "severity": "Low",
                    "details": f"Column '{col}' is highly imbalanced with one value dominating >95%",
                    "impact": "Near-constant features provide little information and can cause model bias.",
                    "solution": "Consider removing or using specialized techniques for imbalanced data."
                })

        # 6. Data type issues
        for col in self.categorical_cols:
            sample = self.df[col].dropna().head(50)
            numeric_attempt = pd.to_numeric(sample, errors='coerce')
            if numeric_attempt.notna().mean() > 0.8:
                problems.append({
                    "type": "Data Type Mismatch",
                    "column": col,
                    "severity": "Medium",
                    "details": f"Column '{col}' is stored as text but appears to be numeric",
                    "impact": "Incorrect data types prevent proper numeric analysis and visualization.",
                    "solution": f"Convert column to numeric using pd.to_numeric(df['{col}'], errors='coerce')."
                })

        # 7. Skewed distributions
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) < 10:
                continue
            skewness = data.skew()
            if abs(skewness) > 2:
                problems.append({
                    "type": "Highly Skewed Distribution",
                    "column": col,
                    "severity": "Medium",
                    "details": f"Column '{col}' has skewness of {round(float(skewness), 2)} ({'right' if skewness > 0 else 'left'}-skewed)",
                    "impact": "Highly skewed data violates normality assumptions in many statistical tests and can degrade model performance.",
                    "solution": "Apply log transformation, Box-Cox transformation, or Yeo-Johnson transformation to normalize the distribution."
                })

        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        problems.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return {
            "total_problems": len(problems),
            "critical": sum(1 for p in problems if p["severity"] == "Critical"),
            "high": sum(1 for p in problems if p["severity"] == "High"),
            "medium": sum(1 for p in problems if p["severity"] == "Medium"),
            "low": sum(1 for p in problems if p["severity"] == "Low"),
            "problems": problems,
            "overall_score": max(0, min(100, 100 - problems.count(0) * 0 - sum(
                {"Critical": 15, "High": 8, "Medium": 4, "Low": 1}.get(p["severity"], 0) for p in problems
            )))
        }

    def _suggest_missing_solution(self, col, pct):
        if pct > 50:
            return f"Column '{col}' has over 50% missing values. Consider dropping this column entirely, or investigate the root cause of missing data."
        elif pct > 20:
            return f"Use advanced imputation (KNN imputer, iterative imputer) for '{col}'. Consider adding a missing indicator column to capture the pattern of missingness."
        else:
            return f"Simple imputation (mean/median for numeric, mode for categorical) should work for '{col}' given the low missing rate."

    def suggest_solutions(self, problems=None):
        """Generate actionable solutions and recommendations."""
        if problems is None:
            problems = self.detect_problems()["problems"]

        solutions = []

        for problem in problems:
            solution = {
                "problem_type": problem["type"],
                "column": problem["column"],
                "severity": problem["severity"],
                "solution": problem["solution"],
                "action_steps": self._get_action_steps(problem),
                "priority": self._get_priority(problem["severity"])
            }
            solutions.append(solution)

        # Add general recommendations
        solutions.extend(self._general_recommendations())

        return solutions

    def _get_action_steps(self, problem):
        ptype = problem["type"]
        col = problem["column"]
        steps = []

        if ptype == "Missing Values":
            steps = [
                f"1. Assess if missingness is random or systematic in '{col}'",
                f"2. If numeric: impute with median (robust to outliers)",
                f"3. If categorical: impute with mode or create 'Unknown' category",
                f"4. Consider adding a binary indicator column for missingness pattern",
                f"5. Validate imputation doesn't distort distribution significantly"
            ]
        elif ptype == "Duplicate Rows":
            steps = [
                "1. Review duplicate records to confirm they are true duplicates",
                "2. Check if duplicates are caused by join/merge operations",
                "3. Remove confirmed duplicates: df.drop_duplicates(inplace=True)",
                "4. Add unique constraints in data pipeline to prevent future duplicates"
            ]
        elif ptype == "Outliers":
            steps = [
                f"1. Investigate if outliers in '{col}' are genuine or data errors",
                f"2. For genuine outliers: use robust methods (median, IQR-based)",
                f"3. For error outliers: correct or remove them",
                f"4. Apply winsorization: cap at 5th/95th percentiles",
                f"5. Consider log transformation to reduce outlier impact"
            ]
        elif ptype == "High Cardinality":
            steps = [
                f"1. Analyze frequency distribution of '{col}'",
                f"2. Group categories appearing in <1% of data into 'Other'",
                f"3. Consider target encoding for supervised learning tasks",
                f"4. Use feature hashing for very high cardinality features"
            ]
        elif ptype == "Constant Column":
            steps = [
                f"1. Verify '{col}' is truly constant (check for hidden variations)",
                f"2. Drop the column if confirmed constant",
                f"3. Document removal in data pipeline"
            ]
        elif ptype == "Data Type Mismatch":
            steps = [
                f"1. Sample values from '{col}' to understand the format",
                f"2. Clean non-numeric characters if present",
                f"3. Convert: df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce')",
                f"4. Verify conversion didn't introduce unexpected NaN values"
            ]
        elif ptype == "Highly Skewed Distribution":
            steps = [
                f"1. Visualize the distribution of '{col}'",
                f"2. Try log transformation: df['{col}_log'] = np.log1p(df['{col}'])",
                f"3. Try Box-Cox or Yeo-Johnson for automatic optimization",
                f"4. Compare model performance with and without transformation"
            ]
        else:
            steps = ["1. Investigate the issue further", "2. Apply standard data cleaning techniques"]

        return steps

    def _get_priority(self, severity):
        priorities = {
            "Critical": {"level": "Immediate", "timeline": "Fix within 24 hours"},
            "High": {"level": "Urgent", "timeline": "Fix within 1 week"},
            "Medium": {"level": "Important", "timeline": "Address in next sprint"},
            "Low": {"level": "Nice to have", "timeline": "Backlog"}
        }
        return priorities.get(severity, {"level": "Unknown", "timeline": "TBD"})

    def _general_recommendations(self):
        recs = []

        # Feature engineering suggestions
        if len(self.datetime_cols) > 0:
            recs.append({
                "problem_type": "Feature Engineering",
                "column": ", ".join(self.datetime_cols),
                "severity": "Medium",
                "solution": "Extract temporal features from datetime columns (year, month, day, day_of_week, is_weekend, quarter).",
                "action_steps": [
                    "1. Extract date components: df['year'] = df[date_col].dt.year",
                    "2. Create cyclical features: sin/cos encoding for month/day",
                    "3. Calculate time since a reference date",
                    "4. Create rolling window features for time series"
                ],
                "priority": {"level": "Important", "timeline": "Address in next sprint"}
            })

        if len(self.numeric_cols) >= 2:
            recs.append({
                "problem_type": "Feature Engineering",
                "column": "Multiple numeric columns",
                "severity": "Low",
                "solution": "Create interaction features and polynomial features between important numeric columns.",
                "action_steps": [
                    "1. Identify top correlated feature pairs",
                    "2. Create ratio features: df['ratio'] = df[col_a] / df[col_b]",
                    "3. Create product features: df['product'] = df[col_a] * df[col_b]",
                    "4. Use sklearn PolynomialFeatures for systematic generation"
                ],
                "priority": {"level": "Nice to have", "timeline": "Backlog"}
            })

        # Clustering suggestion
        if len(self.numeric_cols) >= 2 and self.df.shape[0] >= 50:
            recs.append({
                "problem_type": "Pattern Discovery",
                "column": "All numeric",
                "severity": "Low",
                "solution": "Apply clustering (K-Means) to discover natural groupings in the data.",
                "action_steps": [
                    "1. Scale features using StandardScaler",
                    "2. Use elbow method to find optimal number of clusters",
                    "3. Fit KMeans and analyze cluster profiles",
                    "4. Use cluster labels as a feature for downstream models"
                ],
                "priority": {"level": "Nice to have", "timeline": "Backlog"}
            })

        return recs

    def get_feature_suggestions(self):
        """Suggest new features that can be engineered from existing data."""
        suggestions = []

        # DateTime features
        for col in self.datetime_cols:
            suggestions.append({
                "category": "Temporal",
                "source_column": col,
                "suggested_features": [
                    {"name": f"{col}_year", "description": "Extract year component", "type": "numeric"},
                    {"name": f"{col}_month", "description": "Extract month component", "type": "numeric"},
                    {"name": f"{col}_day_of_week", "description": "Extract day of week (0=Monday)", "type": "numeric"},
                    {"name": f"{col}_is_weekend", "description": "Binary flag for weekends", "type": "binary"},
                    {"name": f"{col}_quarter", "description": "Extract quarter (1-4)", "type": "numeric"},
                    {"name": f"{col}_days_since", "description": "Days since earliest date in column", "type": "numeric"},
                ]
            })

        # Numeric interaction features
        if len(self.numeric_cols) >= 2:
            top_pairs = []
            if len(self.numeric_cols) <= 10:
                corr = self.df[self.numeric_cols].corr().abs()
                for i in range(len(corr.columns)):
                    for j in range(i + 1, len(corr.columns)):
                        top_pairs.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))
                top_pairs.sort(key=lambda x: x[2], reverse=True)

            for col_a, col_b, _ in top_pairs[:5]:
                suggestions.append({
                    "category": "Interaction",
                    "source_column": f"{col_a} × {col_b}",
                    "suggested_features": [
                        {"name": f"{col_a}_{col_b}_ratio", "description": f"Ratio of {col_a} to {col_b}", "type": "numeric"},
                        {"name": f"{col_a}_{col_b}_product", "description": f"Product of {col_a} and {col_b}", "type": "numeric"},
                        {"name": f"{col_a}_{col_b}_diff", "description": f"Difference between {col_a} and {col_b}", "type": "numeric"},
                    ]
                })

        # Aggregation features for categorical columns
        for cat_col in self.categorical_cols[:5]:
            for num_col in self.numeric_cols[:5]:
                suggestions.append({
                    "category": "Aggregation",
                    "source_column": f"{cat_col} → {num_col}",
                    "suggested_features": [
                        {"name": f"{num_col}_mean_by_{cat_col}", "description": f"Mean of {num_col} grouped by {cat_col}", "type": "numeric"},
                        {"name": f"{num_col}_std_by_{cat_col}", "description": f"Std of {num_col} grouped by {cat_col}", "type": "numeric"},
                        {"name": f"{num_col}_rank_by_{cat_col}", "description": f"Rank of {num_col} within {cat_col} group", "type": "numeric"},
                    ]
                })

        # Statistical features
        for col in self.numeric_cols[:10]:
            suggestions.append({
                "category": "Statistical",
                "source_column": col,
                "suggested_features": [
                    {"name": f"{col}_zscore", "description": "Z-score normalized values", "type": "numeric"},
                    {"name": f"{col}_percentile", "description": "Percentile rank of each value", "type": "numeric"},
                    {"name": f"{col}_binned", "description": "Equal-width or equal-frequency bins", "type": "categorical"},
                    {"name": f"{col}_is_outlier", "description": "Binary flag for outlier values", "type": "binary"},
                ]
            })

        return {
            "total_suggestions": sum(len(s["suggested_features"]) for s in suggestions),
            "categories": list(set(s["category"] for s in suggestions)),
            "suggestions": suggestions
        }

    def get_clustering_analysis(self, n_clusters=None):
        """Perform clustering analysis on the data."""
        if len(self.numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns for clustering"}

        data = self.df[self.numeric_cols].dropna()
        if len(data) < 20:
            return {"error": "Need at least 20 rows for clustering"}

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(data)

        # Auto-determine optimal clusters using elbow method
        if n_clusters is None:
            max_k = min(10, len(data) // 5)
            if max_k < 2:
                max_k = 2
            inertias = []
            K_range = range(2, max_k + 1)
            for k in K_range:
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                km.fit(X_scaled)
                inertias.append(km.inertia_)

            # Find elbow using rate of change
            deltas = [inertias[i] - inertias[i + 1] for i in range(len(inertias) - 1)]
            if deltas:
                n_clusters = list(K_range)[np.argmax(deltas) + 1]
            else:
                n_clusters = 3

        # Fit final model
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)

        # PCA for visualization
        n_components = min(2, len(self.numeric_cols))
        pca = PCA(n_components=n_components)
        X_pca = pca.fit_transform(X_scaled)

        # Cluster profiles
        data_with_labels = data.copy()
        data_with_labels['cluster'] = labels

        profiles = {}
        for cluster_id in range(n_clusters):
            cluster_data = data_with_labels[data_with_labels['cluster'] == cluster_id]
            profile = {}
            for col in self.numeric_cols:
                profile[col] = {
                    "mean": round(float(cluster_data[col].mean()), 4),
                    "std": round(float(cluster_data[col].std()), 4),
                    "count": int(len(cluster_data))
                }
            profiles[f"cluster_{cluster_id}"] = profile

        return {
            "n_clusters": n_clusters,
            "cluster_sizes": {f"cluster_{i}": int((labels == i).sum()) for i in range(n_clusters)},
            "pca_coordinates": {
                "x": [round(float(v), 4) for v in X_pca[:, 0][:500]],
                "y": [round(float(v), 4) for v in X_pca[:, 1][:500]] if n_components > 1 else [],
                "labels": [int(l) for l in labels[:500]]
            },
            "explained_variance": [round(float(v), 4) for v in pca.explained_variance_ratio_],
            "cluster_profiles": profiles,
            "insights": self._generate_clustering_insights(profiles, n_clusters)
        }

    def _generate_clustering_insights(self, profiles, n_clusters):
        insights = []
        for cid, profile in profiles.items():
            size = list(profile.values())[0]["count"] if profile else 0
            # Find distinguishing features
            means = {col: info["mean"] for col, info in profile.items()}
            top_features = sorted(means.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
            feature_desc = ", ".join([f"{f}={m}" for f, m in top_features])
            insights.append(f"{cid}: {size} records, characterized by {feature_desc}")
        return insights

    def get_business_insights(self):
        """Generate practical business insights anyone can understand."""
        insights = {
            "summary": [],
            "top_items": {},
            "trends": {},
            "comparisons": {},
            "key_metrics": {},
            "recommendations": []
        }

        # ============ AUTO-DETECT BUSINESS COLUMNS ============
        money_keywords = ['revenue', 'sales', 'price', 'cost', 'profit', 'amount', 'total',
                          'payment', 'income', 'spend', 'spending', 'value', 'salary', 'wage',
                          'fee', 'discount', 'margin', 'turnover', 'bill', 'balance']
        quantity_keywords = ['quantity', 'qty', 'count', 'units', 'volume', 'num', 'number',
                             'stock', 'order', 'orders', 'items', 'pieces', 'amount']
        product_keywords = ['product', 'item', 'category', 'type', 'brand', 'model', 'sku',
                            'description', 'name', 'title', 'material', 'variant', 'sub_category',
                            'sub_category']
        customer_keywords = ['customer', 'client', 'buyer', 'user', 'member', 'account',
                             'company', 'supplier', 'vendor', 'store', 'region', 'city',
                             'country', 'state', 'location', 'branch', 'dealer']
        date_keywords = ['date', 'time', 'year', 'month', 'week', 'day', 'period',
                         'created', 'ordered', 'timestamp']

        def _find_col(keywords, col_list):
            for col in col_list:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                for kw in keywords:
                    if kw in col_lower:
                        return col
            return None

        money_col = _find_col(money_keywords, self.numeric_cols)
        qty_col = _find_col(quantity_keywords, self.numeric_cols)
        product_col = _find_col(product_keywords, self.categorical_cols)
        customer_col = _find_col(customer_keywords, self.categorical_cols)
        date_col = _find_col(date_keywords, self.datetime_cols + self.categorical_cols)

        # ============ OVERALL SUMMARY ============
        row_count = len(self.df)
        insights["summary"].append(f"Your dataset has {row_count:,} records with {len(self.df.columns)} data fields.")

        if money_col:
            total = self.df[money_col].sum()
            avg = self.df[money_col].mean()
            insights["summary"].append(f"Total {money_col.title()}: {total:,.2f}")
            insights["key_metrics"]["total_revenue"] = round(float(total), 2)
            insights["key_metrics"]["average_revenue"] = round(float(avg), 2)

        if product_col:
            n_products = self.df[product_col].nunique()
            insights["summary"].append(f"You have {n_products} unique {product_col.lower()} entries.")

        if customer_col:
            n_customers = self.df[customer_col].nunique()
            insights["summary"].append(f"You have {n_customers} unique {customer_col.lower()} entries.")

        # ============ TOP PRODUCTS / ITEMS ============
        if product_col and money_col:
            product_data = self.df.groupby(product_col)[money_col].agg(['sum', 'mean', 'count']).reset_index()
            product_data.columns = [product_col, 'total', 'average', 'count']
            product_data = product_data.sort_values('total', ascending=False)

            top_products = []
            for _, row in product_data.head(10).iterrows():
                pct = (row['total'] / self.df[money_col].sum()) * 100
                top_products.append({
                    "name": str(row[product_col]),
                    "total": round(float(row['total']), 2),
                    "average": round(float(row['average']), 2),
                    "count": int(row['count']),
                    "percentage": round(float(pct), 1)
                })
            insights["top_items"]["by_revenue"] = top_products

            # Insight text
            if top_products:
                top1 = top_products[0]
                insights["recommendations"].append(
                    f"Top performer: '{top1['name']}' generates {top1['percentage']}% of total {money_col.lower()} "
                    f"({top1['total']:,.2f}) with {top1['count']} transactions."
                )
                if len(top_products) >= 3:
                    top3_pct = sum(p['percentage'] for p in top_products[:3])
                    insights["recommendations"].append(
                        f"Your top 3 {product_col.lower()}s account for {top3_pct:.1f}% of all {money_col.lower()}."
                    )

        elif product_col and qty_col:
            product_data = self.df.groupby(product_col)[qty_col].agg(['sum', 'count']).reset_index()
            product_data.columns = [product_col, 'total_qty', 'transactions']
            product_data = product_data.sort_values('total_qty', ascending=False)

            top_products = []
            for _, row in product_data.head(10).iterrows():
                top_products.append({
                    "name": str(row[product_col]),
                    "quantity": round(float(row['total_qty']), 2),
                    "transactions": int(row['transactions'])
                })
            insights["top_items"]["by_quantity"] = top_products

        elif product_col:
            product_counts = self.df[product_col].value_counts().head(10)
            insights["top_items"]["by_frequency"] = [
                {"name": str(k), "count": int(v),
                 "percentage": round((v / len(self.df)) * 100, 1)}
                for k, v in product_counts.items()
            ]

        # ============ TOP CUSTOMERS / BUYERS ============
        if customer_col and money_col:
            customer_data = self.df.groupby(customer_col)[money_col].agg(['sum', 'mean', 'count']).reset_index()
            customer_data.columns = [customer_col, 'total', 'average', 'count']
            customer_data = customer_data.sort_values('total', ascending=False)

            top_customers = []
            for _, row in customer_data.head(10).iterrows():
                pct = (row['total'] / self.df[money_col].sum()) * 100
                top_customers.append({
                    "name": str(row[customer_col]),
                    "total": round(float(row['total']), 2),
                    "average": round(float(row['average']), 2),
                    "count": int(row['count']),
                    "percentage": round(float(pct), 1)
                })
            insights["top_items"]["by_customer"] = top_customers

            if top_customers:
                top_c = top_customers[0]
                insights["recommendations"].append(
                    f"Biggest buyer: '{top_c['name']}' has spent {top_c['total']:,.2f} "
                    f"across {top_c['count']} orders ({top_c['percentage']}% of total)."
                )

        elif customer_col:
            customer_counts = self.df[customer_col].value_counts().head(10)
            insights["top_items"]["by_customer_freq"] = [
                {"name": str(k), "count": int(v),
                 "percentage": round((v / len(self.df)) * 100, 1)}
                for k, v in customer_counts.items()
            ]

        # ============ TRENDS (OVER TIME) ============
        if date_col and money_col:
            try:
                df_copy = self.df.copy()
                df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
                df_copy = df_copy.dropna(subset=[date_col])
                df_copy = df_copy.sort_values(date_col)

                # Determine time grouping
                date_range = (df_copy[date_col].max() - df_copy[date_col].min()).days
                if date_range > 365:
                    group_col = df_copy[date_col].dt.to_period('M').astype(str)
                    period_label = "Monthly"
                elif date_range > 60:
                    group_col = df_copy[date_col].dt.to_period('W').astype(str)
                    period_label = "Weekly"
                else:
                    group_col = df_copy[date_col].dt.date.astype(str)
                    period_label = "Daily"

                trend_data = df_copy.groupby(group_col)[money_col].sum().reset_index()
                trend_data.columns = ['period', 'total']

                # Calculate trend direction
                if len(trend_data) >= 3:
                    first_half = trend_data['total'].iloc[:len(trend_data)//2].mean()
                    second_half = trend_data['total'].iloc[len(trend_data)//2:].mean()
                    change_pct = ((second_half - first_half) / max(abs(first_half), 1)) * 100

                    if change_pct > 5:
                        trend_dir = "increasing"
                        trend_emoji = "Up"
                    elif change_pct < -5:
                        trend_dir = "decreasing"
                        trend_emoji = "Down"
                    else:
                        trend_dir = "stable"
                        trend_emoji = "Stable"

                    insights["trends"]["direction"] = trend_dir
                    insights["trends"]["change_percent"] = round(float(change_pct), 1)
                    insights["recommendations"].append(
                        f"{money_col.title()} is {trend_dir} over time "
                        f"({'+'if change_pct > 0 else ''}{change_pct:.1f}% change from first half to second half)."
                    )

                insights["trends"]["data"] = {
                    "labels": [str(p) for p in trend_data['period'].tolist()[-20:]],
                    "values": [round(float(v), 2) for v in trend_data['total'].tolist()[-20:]],
                    "period_label": period_label
                }

                # Best and worst periods
                best_period = trend_data.loc[trend_data['total'].idxmax()]
                worst_period = trend_data.loc[trend_data['total'].idxmin()]
                insights["trends"]["best_period"] = {
                    "period": str(best_period['period']),
                    "value": round(float(best_period['total']), 2)
                }
                insights["trends"]["worst_period"] = {
                    "period": str(worst_period['period']),
                    "value": round(float(worst_period['total']), 2)
                }
                insights["recommendations"].append(
                    f"Best {period_label.lower()}: {best_period['period']} "
                    f"({best_period['total']:,.2f}). Worst: {worst_period['period']} ({worst_period['total']:,.2f})."
                )

            except Exception:
                pass

        elif date_col and qty_col:
            try:
                df_copy = self.df.copy()
                df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
                df_copy = df_copy.dropna(subset=[date_col])
                df_copy = df_copy.sort_values(date_col)

                date_range = (df_copy[date_col].max() - df_copy[date_col].min()).days
                if date_range > 365:
                    group_col = df_copy[date_col].dt.to_period('M').astype(str)
                    period_label = "Monthly"
                else:
                    group_col = df_copy[date_col].dt.to_period('W').astype(str)
                    period_label = "Weekly"

                trend_data = df_copy.groupby(group_col)[qty_col].sum().reset_index()
                trend_data.columns = ['period', 'total']

                if len(trend_data) >= 3:
                    first_half = trend_data['total'].iloc[:len(trend_data)//2].mean()
                    second_half = trend_data['total'].iloc[len(trend_data)//2:].mean()
                    change_pct = ((second_half - first_half) / max(abs(first_half), 1)) * 100

                    trend_dir = "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable"
                    insights["trends"]["direction"] = trend_dir
                    insights["trends"]["change_percent"] = round(float(change_pct), 1)

                insights["trends"]["data"] = {
                    "labels": [str(p) for p in trend_data['period'].tolist()[-20:]],
                    "values": [round(float(v), 2) for v in trend_data['total'].tolist()[-20:]],
                    "period_label": period_label
                }
            except Exception:
                pass

        # ============ CATEGORY COMPARISONS ============
        if product_col and money_col:
            # Revenue share pie data
            cat_data = self.df.groupby(product_col)[money_col].sum().sort_values(ascending=False)
            total = cat_data.sum()
            comparisons = []
            others_total = 0
            for i, (name, value) in enumerate(cat_data.items()):
                if i < 8:
                    comparisons.append({
                        "name": str(name),
                        "value": round(float(value), 2),
                        "percentage": round(float((value / total) * 100), 1)
                    })
                else:
                    others_total += value
            if others_total > 0:
                comparisons.append({
                    "name": "Others",
                    "value": round(float(others_total), 2),
                    "percentage": round(float((others_total / total) * 100), 1)
                })
            insights["comparisons"]["revenue_share"] = comparisons

        elif product_col:
            cat_counts = self.df[product_col].value_counts().head(10)
            total = cat_counts.sum()
            insights["comparisons"]["category_share"] = [
                {"name": str(k), "value": int(v),
                 "percentage": round((v / total) * 100, 1)}
                for k, v in cat_counts.items()
            ]

        # ============ GENERIC NUMERIC INSIGHTS (if no business columns detected) ============
        if not product_col and not customer_col and self.numeric_cols:
            # Top values for each numeric column
            for col in self.numeric_cols[:5]:
                col_data = self.df[col].dropna().sort_values(ascending=False)
                insights["key_metrics"][col] = {
                    "total": round(float(col_data.sum()), 2),
                    "average": round(float(col_data.mean()), 2),
                    "highest": round(float(col_data.iloc[0]), 2) if len(col_data) > 0 else 0,
                    "lowest": round(float(col_data.iloc[-1]), 2) if len(col_data) > 0 else 0,
                }

        # ============ DETECTED COLUMNS INFO ============
        insights["detected_columns"] = {
            "money": money_col,
            "quantity": qty_col,
            "product": product_col,
            "customer": customer_col,
            "date": date_col
        }

        # ============ ADD GENERIC RECOMMENDATIONS ============
        if not insights["recommendations"]:
            insights["recommendations"].append(
                "Upload data with columns like 'product', 'customer', 'revenue', 'date' "
                "to get the most actionable business insights."
            )

        if money_col and product_col:
            insights["recommendations"].append(
                f"Focus on growing your top {product_col.lower()}s — they drive most of your {money_col.lower()}."
            )

        return insights

    def get_full_analysis(self):
        """Run complete analysis pipeline."""
        return {
            "overview": self.get_overview(),
            "correlations": self.get_correlation_analysis(),
            "distributions": self.get_distribution_analysis(),
            "anomalies": self.detect_anomalies(),
            "problems": self.detect_problems(),
            "feature_suggestions": self.get_feature_suggestions(),
            "clustering": self.get_clustering_analysis()
        }

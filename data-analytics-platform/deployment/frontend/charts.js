/**
 * DataLens - Chart Module
 * Handles all Chart.js visualizations
 */

const ChartModule = {
    instances: {},

    // Color palette
    colors: {
        primary: '#4F46E5',
        primaryLight: '#818CF8',
        primaryLighter: '#C7D2FE',
        secondary: '#7C3AED',
        green: '#10B981',
        greenLight: '#6EE7B7',
        amber: '#F59E0B',
        amberLight: '#FCD34D',
        red: '#EF4444',
        redLight: '#FCA5A5',
        blue: '#3B82F6',
        blueLight: '#93C5FD',
        teal: '#14B8A6',
        pink: '#EC4899',
        orange: '#F97316',
        gray: '#94A3B8',
        grayLight: '#E2E8F0',
    },

    palette: [
        '#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#7C3AED',
        '#3B82F6', '#EC4899', '#14B8A6', '#F97316', '#8B5CF6',
        '#06B6D4', '#84CC16', '#E11D48', '#6366F1', '#D946EF'
    ],

    // Chart.js defaults
    defaults: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif', size: 12 },
                    color: '#475569',
                    usePointStyle: true,
                    padding: 16
                }
            },
            tooltip: {
                backgroundColor: '#1E293B',
                titleFont: { size: 13 },
                bodyFont: { size: 12 },
                padding: 12,
                cornerRadius: 8,
                displayColors: true,
            }
        },
        scales: {
            x: {
                grid: { color: '#F1F5F9', drawBorder: false },
                ticks: { font: { size: 11 }, color: '#94A3B8' }
            },
            y: {
                grid: { color: '#F1F5F9', drawBorder: false },
                ticks: { font: { size: 11 }, color: '#94A3B8' }
            }
        }
    },

    destroy(chartId) {
        if (this.instances[chartId]) {
            this.instances[chartId].destroy();
            delete this.instances[chartId];
        }
    },

    destroyAll() {
        Object.keys(this.instances).forEach(id => this.destroy(id));
    },

    // ============ COLUMN TYPES PIE CHART ============
    renderColumnTypes(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const numeric = data.numeric_columns || 0;
        const categorical = data.categorical_columns || 0;
        const datetime = data.datetime_columns || 0;

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Numeric', 'Categorical', 'Datetime'],
                datasets: [{
                    data: [numeric, categorical, datetime],
                    backgroundColor: [this.colors.primary, this.colors.amber, this.colors.green],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true } },
                    tooltip: this.defaults.plugins.tooltip
                }
            }
        });
    },

    // ============ QUALITY SCORE GAUGE ============
    renderQualityScore(canvasId, score) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const clampedScore = Math.max(0, Math.min(100, score));
        const color = clampedScore >= 80 ? this.colors.green : clampedScore >= 60 ? this.colors.amber : this.colors.red;

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Quality', 'Issues'],
                datasets: [{
                    data: [clampedScore, 100 - clampedScore],
                    backgroundColor: [color, '#F1F5F9'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                rotation: -90,
                circumference: 180,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            },
            plugins: [{
                id: 'qualityText',
                afterDraw(chart) {
                    const { ctx: c, width, height } = chart;
                    c.save();
                    c.font = 'bold 28px -apple-system, sans-serif';
                    c.fillStyle = color;
                    c.textAlign = 'center';
                    c.fillText(clampedScore + '%', width / 2, height - 20);
                    c.font = '12px -apple-system, sans-serif';
                    c.fillStyle = '#94A3B8';
                    c.fillText('Quality Score', width / 2, height - 2);
                    c.restore();
                }
            }]
        });
    },

    // ============ CORRELATION HEATMAP ============
    renderCorrelationHeatmap(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const cols = data.columns || [];
        const values = data.values || [];
        if (cols.length === 0) return;

        // For small matrices, use a custom matrix approach
        if (cols.length <= 15) {
            const labels = cols.map(c => c.length > 12 ? c.substring(0, 12) + '..' : c);
            const datasets = [];

            for (let i = 0; i < cols.length; i++) {
                for (let j = 0; j < cols.length; j++) {
                    const val = values[i][j];
                    datasets.push({
                        x: labels[j],
                        y: labels[i],
                        v: val
                    });
                }
            }

            this.instances[canvasId] = new Chart(ctx, {
                type: 'matrix',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Correlation',
                        data: datasets,
                        backgroundColor(ctx) {
                            const v = ctx.dataset.data[ctx.dataIndex]?.v || 0;
                            const alpha = Math.abs(v);
                            if (v > 0) return `rgba(79, 70, 229, ${alpha})`;
                            if (v < 0) return `rgba(239, 68, 68, ${alpha})`;
                            return '#F1F5F9';
                        },
                        borderColor: '#FFFFFF',
                        borderWidth: 1,
                        width: ({ chart }) => (chart.chartArea || {}).width / labels.length - 1,
                        height: ({ chart }) => (chart.chartArea || {}).height / labels.length - 1,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'category',
                            labels: labels,
                            ticks: { font: { size: 9 }, maxRotation: 45 },
                            grid: { display: false }
                        },
                        y: {
                            type: 'category',
                            labels: labels,
                            ticks: { font: { size: 9 } },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                title() { return ''; },
                                label(ctx) {
                                    const d = ctx.dataset.data[ctx.dataIndex];
                                    return d ? `${d.y} × ${d.x}: ${d.v.toFixed(3)}` : '';
                                }
                            }
                        }
                    }
                }
            });
        } else {
            // For larger matrices, just show bar chart of top correlations
            this._renderCorrelationBars(canvasId, cols, values);
        }
    },

    _renderCorrelationBars(canvasId, cols, values) {
        const correlations = [];
        for (let i = 0; i < cols.length; i++) {
            for (let j = i + 1; j < cols.length; j++) {
                correlations.push({
                    pair: `${cols[i].substring(0, 8)} × ${cols[j].substring(0, 8)}`,
                    value: values[i][j]
                });
            }
        }
        correlations.sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
        const top = correlations.slice(0, 15);

        const ctx = document.getElementById(canvasId);
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: top.map(c => c.pair),
                datasets: [{
                    label: 'Correlation',
                    data: top.map(c => c.value),
                    backgroundColor: top.map(c => c.value >= 0 ? this.colors.primary : this.colors.red),
                    borderRadius: 4
                }]
            },
            options: {
                ...this.defaults,
                indexAxis: 'y',
                scales: {
                    x: { ...this.defaults.scales.x, min: -1, max: 1 },
                    y: { ...this.defaults.scales.y, ticks: { font: { size: 10 } } }
                }
            }
        });
    },

    // ============ DISTRIBUTION HISTOGRAM ============
    renderDistribution(canvasId, colName, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const hist = data.histogram || {};
        const counts = hist.counts || [];
        const bins = hist.bins || [];

        if (counts.length === 0) return;

        const labels = bins.slice(0, -1).map((b, i) => {
            const mid = ((b + bins[i + 1]) / 2);
            return mid.toFixed(1);
        });

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: colName,
                    data: counts,
                    backgroundColor: this.colors.primaryLighter,
                    borderColor: this.colors.primary,
                    borderWidth: 1,
                    borderRadius: 4,
                    barPercentage: 0.95,
                    categoryPercentage: 0.95
                }]
            },
            options: {
                ...this.defaults,
                scales: {
                    x: { ...this.defaults.scales.x, title: { display: true, text: colName, font: { size: 11 } } },
                    y: { ...this.defaults.scales.y, title: { display: true, text: 'Frequency', font: { size: 11 } } }
                },
                plugins: {
                    ...this.defaults.plugins,
                    legend: { display: false }
                }
            }
        });
    },

    // ============ BOX PLOT (Simulated) ============
    renderBoxPlot(canvasId, colName, stats) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const { min, q25, q50, q75, max: mx } = stats;
        const iqr = q75 - q25;
        const whiskerLow = Math.max(min, q25 - 1.5 * iqr);
        const whiskerHigh = Math.min(mx, q75 + 1.5 * iqr);

        // Use floating bar to simulate box plot
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [colName],
                datasets: [
                    {
                        label: 'Lower Whisker',
                        data: [[whiskerLow, q25]],
                        backgroundColor: this.colors.grayLight,
                        borderColor: this.colors.gray,
                        borderWidth: 1,
                        barPercentage: 0.4,
                    },
                    {
                        label: 'Q1 - Q3 (IQR)',
                        data: [[q25, q75]],
                        backgroundColor: this.colors.primaryLighter,
                        borderColor: this.colors.primary,
                        borderWidth: 2,
                        barPercentage: 0.4,
                    },
                    {
                        label: 'Upper Whisker',
                        data: [[q75, whiskerHigh]],
                        backgroundColor: this.colors.grayLight,
                        borderColor: this.colors.gray,
                        borderWidth: 1,
                        barPercentage: 0.4,
                    }
                ]
            },
            options: {
                ...this.defaults,
                indexAxis: 'y',
                plugins: {
                    ...this.defaults.plugins,
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label(ctx) {
                                const v = ctx.raw;
                                if (Array.isArray(v)) return `${ctx.dataset.label}: ${v[0].toFixed(2)} - ${v[1].toFixed(2)}`;
                                return `${ctx.dataset.label}: ${v}`;
                            }
                        }
                    }
                },
                scales: {
                    x: { ...this.defaults.scales.x },
                    y: { ...this.defaults.scales.y }
                }
            },
            plugins: [{
                id: 'medianLine',
                afterDraw(chart) {
                    const { ctx: c, scales } = chart;
                    const yScale = scales.y;
                    const xScale = scales.x;
                    const yPos = yScale.getPixelForValue(0);
                    const xMed = xScale.getPixelForValue(q50);
                    c.save();
                    c.strokeStyle = '#EF4444';
                    c.lineWidth = 2;
                    c.beginPath();
                    c.moveTo(xMed, yPos - 20);
                    c.lineTo(xMed, yPos + 20);
                    c.stroke();
                    c.font = '10px sans-serif';
                    c.fillStyle = '#EF4444';
                    c.fillText(`Median: ${q50.toFixed(2)}`, xMed + 5, yPos - 24);
                    c.restore();
                }
            }]
        });
    },

    // ============ ANOMALY SCORE CHART ============
    renderAnomalyScores(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const scores = data.anomaly_scores || [];
        if (scores.length === 0) return;

        const labels = scores.map((_, i) => i + 1);
        const colors = scores.map(s => s < 0 ? this.colors.red : this.colors.primary);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Anomaly Score',
                    data: scores,
                    backgroundColor: colors.map(c => c + '40'),
                    borderColor: colors,
                    borderWidth: 1,
                    borderRadius: 2
                }]
            },
            options: {
                ...this.defaults,
                scales: {
                    x: { ...this.defaults.scales.x, title: { display: true, text: 'Data Point', font: { size: 11 } } },
                    y: { ...this.defaults.scales.y, title: { display: true, text: 'Score', font: { size: 11 } } }
                },
                plugins: {
                    ...this.defaults.plugins,
                    legend: { display: false }
                }
            }
        });
    },

    // ============ ANOMALY PROFILE CHART ============
    renderAnomalyProfile(canvasId, profile) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx || !profile) return;

        const cols = Object.keys(profile);
        const deviations = cols.map(c => profile[c].deviation_pct);
        const colors = deviations.map(d => d > 50 ? this.colors.red : d > 20 ? this.colors.amber : this.colors.green);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: cols.map(c => c.length > 15 ? c.substring(0, 15) + '..' : c),
                datasets: [{
                    label: 'Deviation %',
                    data: deviations,
                    backgroundColor: colors.map(c => c + '60'),
                    borderColor: colors,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                ...this.defaults,
                indexAxis: 'y',
                plugins: {
                    ...this.defaults.plugins,
                    legend: { display: false }
                }
            }
        });
    },

    // ============ PREDICTION CHART ============
    renderPredictions(canvasId, historicalData, predictions, label) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const histLen = historicalData.length;
        const histLabels = historicalData.map((_, i) => `T${i + 1}`);
        const predLabels = predictions.map((_, i) => `T${histLen + i + 1}`);
        const allLabels = [...histLabels, ...predLabels];

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: allLabels,
                datasets: [
                    {
                        label: 'Historical',
                        data: [...historicalData, ...new Array(predLabels.length).fill(null)],
                        borderColor: this.colors.primary,
                        backgroundColor: this.colors.primaryLighter,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        borderWidth: 2
                    },
                    {
                        label: 'Predicted',
                        data: [...new Array(histLen - 1).fill(null), historicalData[histLen - 1], ...predictions],
                        borderColor: this.colors.red,
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderDash: [6, 4],
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        borderWidth: 2,
                        pointBackgroundColor: this.colors.red
                    }
                ]
            },
            options: {
                ...this.defaults,
                scales: {
                    x: { ...this.defaults.scales.x },
                    y: { ...this.defaults.scales.y, title: { display: true, text: label, font: { size: 11 } } }
                }
            }
        });
    },

    // ============ FEATURE IMPORTANCE CHART ============
    renderFeatureImportance(canvasId, features) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const sorted = [...features].sort((a, b) => b.importance - a.importance).slice(0, 10);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sorted.map(f => f.feature.length > 18 ? f.feature.substring(0, 18) + '..' : f.feature),
                datasets: [{
                    label: 'Importance',
                    data: sorted.map(f => f.importance),
                    backgroundColor: this.colors.primaryLighter,
                    borderColor: this.colors.primary,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                ...this.defaults,
                indexAxis: 'y',
                plugins: {
                    ...this.defaults.plugins,
                    legend: { display: false }
                }
            }
        });
    },

    // ============ CLUSTER SCATTER CHART ============
    renderClusterScatter(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const x = data.x || [];
        const y = data.y || [];
        const labels = data.labels || [];

        if (x.length === 0 || y.length === 0) return;

        const uniqueLabels = [...new Set(labels)];
        const clusterColors = this.palette;

        const datasets = uniqueLabels.map(label => {
            const points = [];
            for (let i = 0; i < x.length; i++) {
                if (labels[i] === label) {
                    points.push({ x: x[i], y: y[i] });
                }
            }
            return {
                label: `Cluster ${label}`,
                data: points,
                backgroundColor: clusterColors[label % clusterColors.length] + '80',
                borderColor: clusterColors[label % clusterColors.length],
                borderWidth: 1,
                pointRadius: 4,
                pointHoverRadius: 7,
            };
        });

        this.instances[canvasId] = new Chart(ctx, {
            type: 'scatter',
            data: { datasets },
            options: {
                ...this.defaults,
                scales: {
                    x: { ...this.defaults.scales.x, title: { display: true, text: 'PCA Component 1', font: { size: 11 } } },
                    y: { ...this.defaults.scales.y, title: { display: true, text: 'PCA Component 2', font: { size: 11 } } }
                },
                plugins: {
                    ...this.defaults.plugins,
                    legend: { position: 'top' }
                }
            }
        });
    },

    // ============ PROBLEM SEVERITY PIE ============
    renderProblemSeverity(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    data: [data.critical || 0, data.high || 0, data.medium || 0, data.low || 0],
                    backgroundColor: [this.colors.red, this.colors.orange, this.colors.amber, this.colors.green],
                    borderWidth: 0,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 12, usePointStyle: true } }
                }
            }
        });
    },

    // ============ CLUSTER SIZE BAR ============
    renderClusterSizes(canvasId, sizes) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const labels = Object.keys(sizes);
        const values = Object.values(sizes);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Records',
                    data: values,
                    backgroundColor: labels.map((_, i) => this.palette[i % this.palette.length] + '80'),
                    borderColor: labels.map((_, i) => this.palette[i % this.palette.length]),
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                ...this.defaults,
                plugins: { ...this.defaults.plugins, legend: { display: false } }
            }
        });
    }
};

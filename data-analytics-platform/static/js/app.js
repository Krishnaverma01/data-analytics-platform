/**
 * DataLens - Main Application
 * Connects HTML frontend with Python Flask backend
 */

// Helper: JavaScript equivalent of Python's str.title()
function titleCase(str) {
    if (typeof str !== 'string') str = String(str);
    return str.replace(/\b\w/g, c => c.toUpperCase());
}

const App = {
    sessionId: null,
    analysisData: {},
    columnInfo: {},

    // API base URL
    // For split hosting: API_URL is set in index.html (from the deployment/frontend version)
    // For same-origin hosting: falls back to empty string (relative URLs)
    API: typeof API_URL !== 'undefined' ? API_URL : '',

    // ============ INITIALIZATION ============
    init() {
        this.bindEvents();
        this.setupNavigation();
        this.setupDragDrop();
        // Show info popup
        const modal = document.getElementById('infoModal');
        const okBtn = document.getElementById('modalOk');
        if (modal && okBtn) {
            okBtn.addEventListener('click', () => { modal.style.display = 'none'; });
        }
    },

    // ============ EVENT BINDING ============
    bindEvents() {
        // Upload
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');

        uploadZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e.target.files[0]));

        // Start analysis
        document.getElementById('startAnalysis').addEventListener('click', () => this.runFullAnalysis());
        document.getElementById('runFullAnalysis').addEventListener('click', () => this.runFullAnalysis());

        // Predictions
        document.getElementById('runPrediction').addEventListener('click', () => this.runPredictions());

        // Clustering
        document.getElementById('runClustering').addEventListener('click', () => this.runClustering());

        // Report
        document.getElementById('generateReport').addEventListener('click', () => this.generateReport());

        // Distribution column select
        document.getElementById('distributionColumnSelect').addEventListener('change', (e) => {
            this.renderDistribution(e.target.value);
        });

        // Column search
        document.getElementById('columnSearch').addEventListener('input', (e) => {
            this.filterColumns(e.target.value);
        });

        // Mobile menu
        document.getElementById('mobileMenuBtn').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
            document.querySelector('.sidebar-overlay')?.classList.toggle('active');
        });

        // Theme toggle (placeholder)
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.showToast('Theme switching coming soon!', 'info');
        });
    },

    // ============ NAVIGATION ============
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;

                // Check if data is loaded for analysis sections
                if (section !== 'upload' && !this.sessionId) {
                    this.showToast('Please upload data first', 'warning');
                    return;
                }

                navItems.forEach(n => n.classList.remove('active'));
                item.classList.add('active');

                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                const targetSection = document.getElementById(`section-${section}`);
                if (targetSection) targetSection.classList.add('active');

                document.getElementById('topbarTitle').textContent = item.querySelector('span').textContent;

                // Close mobile sidebar
                document.getElementById('sidebar').classList.remove('open');
            });
        });
    },

    // ============ DRAG & DROP ============
    setupDragDrop() {
        const zone = document.getElementById('uploadZone');

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) this.handleFileUpload(file);
        });
    },

    // ============ FILE UPLOAD ============
    async handleFileUpload(file) {
        if (!file) return;

        const validExts = ['.csv', '.xlsx', '.xls', '.json', '.tsv'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExts.includes(ext)) {
            this.showToast('Unsupported file format. Use CSV, XLSX, JSON, or TSV.', 'error');
            return;
        }

        const progress = document.getElementById('uploadProgress');
        const fill = document.getElementById('progressFill');
        const status = document.getElementById('uploadStatus');

        progress.style.display = 'block';
        fill.style.width = '20%';
        status.textContent = 'Uploading file...';

        const formData = new FormData();
        formData.append('file', file);

        try {
            fill.style.width = '50%';
            status.textContent = 'Processing data...';

            const response = await fetch(`${this.API}/api/upload`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            fill.style.width = '100%';
            status.textContent = 'Upload complete!';

            this.sessionId = data.session_id;
            this.columnInfo = data.column_info || [];

            // Update session info
            document.getElementById('sessionInfo').innerHTML =
                `<i class="fas fa-database"></i><span>${data.filename} (${data.rows} rows)</span>`;

            // Show preview
            this.renderPreview(data);

            // Show run analysis button
            document.getElementById('runFullAnalysis').style.display = 'inline-flex';

            // Enable nav items
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('disabled'));

            // Populate column selects
            this.populateColumnSelects(data.column_info || []);

            this.showToast(`File uploaded: ${data.filename} (${data.rows} rows, ${data.columns} columns)`, 'success');

            setTimeout(() => { progress.style.display = 'none'; }, 1500);

        } catch (error) {
            fill.style.width = '0%';
            status.textContent = 'Upload failed';
            this.showToast(error.message, 'error');
            setTimeout(() => { progress.style.display = 'none'; }, 2000);
        }
    },

    // ============ DATA PREVIEW ============
    renderPreview(data) {
        const preview = document.getElementById('dataPreview');
        preview.style.display = 'block';

        // Info chips
        const infoDiv = document.getElementById('previewInfo');
        infoDiv.innerHTML = `
            <div class="info-chip"><i class="fas fa-table"></i> ${data.rows} rows</div>
            <div class="info-chip"><i class="fas fa-columns"></i> ${data.columns} columns</div>
            <div class="info-chip"><i class="fas fa-file"></i> ${data.filename}</div>
        `;

        // Table
        const thead = document.getElementById('previewThead');
        const tbody = document.getElementById('previewTbody');

        if (data.preview && data.preview.length > 0) {
            thead.innerHTML = '<tr>' + Object.keys(data.preview[0]).map(k => `<th>${k}</th>`).join('') + '</tr>';
            tbody.innerHTML = data.preview.map(row =>
                '<tr>' + Object.values(row).map(v => `<td>${v !== null && v !== undefined ? v : 'N/A'}</td>`).join('') + '</tr>'
            ).join('');
        }
    },

    // ============ POPULATE COLUMN SELECTS ============
    populateColumnSelects(columns) {
        // Prediction target
        const predSelect = document.getElementById('predictionTarget');
        predSelect.innerHTML = '';
        columns.filter(c => c.dtype.includes('float') || c.dtype.includes('int') || c.dtype.includes('number'))
            .forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.name;
                opt.textContent = c.name;
                predSelect.appendChild(opt);
            });

        // Distribution column select (populated after analysis)
    },

    // ============ FULL ANALYSIS ============
    async runFullAnalysis() {
        if (!this.sessionId) {
            this.showToast('Please upload data first', 'warning');
            return;
        }

        this.showLoading('Running comprehensive analysis...');

        try {
            const response = await fetch(`${this.API}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });

            const data = await response.json();

            if (data.error) throw new Error(data.error);

            this.analysisData = data;
            this.renderAllSections(data);
            this.hideLoading();
            this.showToast('Analysis complete!', 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast(`Analysis failed: ${error.message}`, 'error');
        }
    },

    // ============ RENDER ALL SECTIONS ============
    renderAllSections(data) {
        this.renderDashboard(data.business_insights);
        this.renderOverview(data.overview);
        this.renderCorrelations(data.correlations);
        this.renderDistributions(data.distributions);
        this.renderAnomalies(data.anomalies);
        this.renderProblems(data.problems, data.solutions);
        this.renderFeatures(data.feature_suggestions);
        this.renderClustering(data.clustering);
    },

    // ============ BUSINESS DASHBOARD ============
    renderDashboard(bi) {
        if (!bi) return;

        const chartColors = [
            '#4F46E5', '#7C3AED', '#EC4899', '#F59E0B', '#10B981',
            '#3B82F6', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16'
        ];

        // Summary cards
        const summaryDiv = document.getElementById('dashSummary');
        const summaryItems = bi.summary || [];
        const metrics = bi.key_metrics || {};
        const detected = bi.detected_columns || {};

        let summaryHtml = '';
        summaryItems.forEach(s => {
            summaryHtml += `<div class="metric-card info"><div class="metric-label" style="font-size:0.85rem;line-height:1.5;">${s}</div></div>`;
        });
        if (metrics.total_revenue) {
            summaryHtml += `<div class="metric-card success"><div class="metric-value">${metrics.total_revenue.toLocaleString()}</div><div class="metric-label">Total ${detected.money || 'Revenue'}</div></div>`;
        }
        if (metrics.average_revenue) {
            summaryHtml += `<div class="metric-card"><div class="metric-value">${metrics.average_revenue.toLocaleString()}</div><div class="metric-label">Average ${detected.money || 'Revenue'}</div></div>`;
        }
        summaryDiv.innerHTML = summaryHtml;

        // Trend banner
        const trends = bi.trends || {};
        if (trends.direction) {
            const banner = document.getElementById('dashTrendBanner');
            banner.style.display = 'block';
            const isUp = trends.direction === 'increasing';
            const isDown = trends.direction === 'decreasing';
            const icon = isUp ? 'fa-arrow-trend-up' : isDown ? 'fa-arrow-trend-down' : 'fa-minus';
            const color = isUp ? 'var(--accent-green)' : isDown ? 'var(--accent-red)' : 'var(--accent-amber)';
            const label = isUp ? 'Going Up' : isDown ? 'Going Down' : 'Stable';
            document.getElementById('dashTrendBannerContent').innerHTML = `
                <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <i class="fas ${icon}" style="font-size:1.5rem;color:${color};"></i>
                        <span style="font-size:1.2rem;font-weight:700;color:${color};">${label}</span>
                    </div>
                    <span style="font-size:1rem;color:var(--text-secondary);">
                        ${titleCase(detected.money || 'Revenue')} is <strong>${trends.direction}</strong>
                        (${trends.change_percent > 0 ? '+' : ''}${trends.change_percent}% change)
                    </span>
                    ${trends.best_period ? `<span style="font-size:0.85rem;color:var(--text-tertiary);margin-left:auto;">Best: ${trends.best_period.period} | Worst: ${trends.worst_period.period}</span>` : ''}
                </div>
            `;
        }

        // Trend line chart
        if (trends.data) {
            document.getElementById('dashTrendCard').style.display = 'block';
            document.getElementById('dashTrendTitle').textContent =
                `${titleCase(detected.money || 'Value')} Over Time (${trends.data.period_label})`;

            const ctx = document.getElementById('dashTrendChart').getContext('2d');
            if (this._dashTrendChart) this._dashTrendChart.destroy();
            this._dashTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trends.data.labels,
                    datasets: [{
                        label: detected.money || 'Total',
                        data: trends.data.values,
                        borderColor: '#4F46E5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointBackgroundColor: '#4F46E5'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: false, grid: { color: 'rgba(0,0,0,0.05)' } },
                        x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }
                    }
                }
            });
        }

        // Top products bar chart + table
        const topItems = bi.top_items || {};
        if (topItems.by_revenue) {
            const products = topItems.by_revenue;
            document.getElementById('dashTopProductsCard').style.display = 'block';
            document.getElementById('dashTopProductsTitle').textContent = `Top ${detected.product || 'Products'} by ${titleCase(detected.money || 'Revenue')}`;

            const ctx = document.getElementById('dashTopProductsChart').getContext('2d');
            if (this._dashProdChart) this._dashProdChart.destroy();
            this._dashProdChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: products.map(p => p.name.length > 15 ? p.name.substring(0,15)+'...' : p.name),
                    datasets: [{
                        label: detected.money || 'Revenue',
                        data: products.map(p => p.total),
                        backgroundColor: chartColors.slice(0, products.length),
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(0,0,0,0.05)' } },
                        y: { grid: { display: false } }
                    }
                }
            });

            // Products table
            document.getElementById('dashProductsTable').style.display = 'block';
            document.getElementById('dashProductsTableTitle').textContent = `${titleCase(detected.product || 'Product')} Details`;
            document.getElementById('dashProductsThead').innerHTML = `
                <tr><th>${titleCase(detected.product || 'Product')}</th><th>Total ${titleCase(detected.money || 'Revenue')}</th><th>Average</th><th>Orders</th><th>Share</th></tr>`;
            document.getElementById('dashProductsTbody').innerHTML = products.map(p => `
                <tr>
                    <td><strong>${p.name}</strong></td>
                    <td>${p.total.toLocaleString()}</td>
                    <td>${p.average.toLocaleString()}</td>
                    <td>${p.count}</td>
                    <td><span style="color:${p.percentage > 20 ? 'var(--accent-green)' : 'var(--text-secondary)'};font-weight:600;">${p.percentage}%</span></td>
                </tr>
            `).join('');

        } else if (topItems.by_quantity) {
            const products = topItems.by_quantity;
            document.getElementById('dashTopProductsCard').style.display = 'block';
            document.getElementById('dashTopProductsTitle').textContent = `Top ${detected.product || 'Products'} by Quantity`;

            const ctx = document.getElementById('dashTopProductsChart').getContext('2d');
            if (this._dashProdChart) this._dashProdChart.destroy();
            this._dashProdChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: products.map(p => p.name.length > 15 ? p.name.substring(0,15)+'...' : p.name),
                    datasets: [{
                        label: 'Quantity',
                        data: products.map(p => p.quantity),
                        backgroundColor: chartColors.slice(0, products.length),
                        borderRadius: 6
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } } }
            });

            document.getElementById('dashProductsTable').style.display = 'block';
            document.getElementById('dashProductsTableTitle').textContent = `${titleCase(detected.product || 'Product')} Details`;
            document.getElementById('dashProductsThead').innerHTML = `<tr><th>${titleCase(detected.product || 'Product')}</th><th>Quantity</th><th>Transactions</th></tr>`;
            document.getElementById('dashProductsTbody').innerHTML = products.map(p => `<tr><td><strong>${p.name}</strong></td><td>${p.quantity.toLocaleString()}</td><td>${p.transactions}</td></tr>`).join('');

        } else if (topItems.by_frequency) {
            const items = topItems.by_frequency;
            document.getElementById('dashTopProductsCard').style.display = 'block';
            document.getElementById('dashTopProductsTitle').textContent = `Top ${titleCase(detected.product || 'Items')} by Count`;

            const ctx = document.getElementById('dashTopProductsChart').getContext('2d');
            if (this._dashProdChart) this._dashProdChart.destroy();
            this._dashProdChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: items.map(p => p.name.length > 15 ? p.name.substring(0,15)+'...' : p.name),
                    datasets: [{ label: 'Count', data: items.map(p => p.count), backgroundColor: chartColors.slice(0, items.length), borderRadius: 6 }]
                },
                options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } } }
            });
        }

        // Revenue share pie chart
        const comparisons = bi.comparisons || {};
        if (comparisons.revenue_share) {
            document.getElementById('dashPieCard').style.display = 'block';
            const ctx = document.getElementById('dashPieChart').getContext('2d');
            if (this._dashPieChart) this._dashPieChart.destroy();
            this._dashPieChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: comparisons.revenue_share.map(c => c.name),
                    datasets: [{
                        data: comparisons.revenue_share.map(c => c.value),
                        backgroundColor: chartColors.slice(0, comparisons.revenue_share.length),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { boxWidth: 12, padding: 10 } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${comparisons.revenue_share[ctx.dataIndex].percentage}%)`
                            }
                        }
                    }
                }
            });
        } else if (comparisons.category_share) {
            document.getElementById('dashPieCard').style.display = 'block';
            const ctx = document.getElementById('dashPieChart').getContext('2d');
            if (this._dashPieChart) this._dashPieChart.destroy();
            this._dashPieChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: comparisons.category_share.map(c => c.name),
                    datasets: [{ data: comparisons.category_share.map(c => c.value), backgroundColor: chartColors.slice(0, comparisons.category_share.length), borderWidth: 2, borderColor: '#fff' }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 12, padding: 10 } } } }
            });
        }

        // Top customers
        if (topItems.by_customer) {
            const customers = topItems.by_customer;
            document.getElementById('dashTopCustomersCard').style.display = 'block';

            const ctx = document.getElementById('dashTopCustomersChart').getContext('2d');
            if (this._dashCustChart) this._dashCustChart.destroy();
            this._dashCustChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: customers.map(c => c.name.length > 15 ? c.name.substring(0,15)+'...' : c.name),
                    datasets: [{
                        label: detected.money || 'Revenue',
                        data: customers.map(c => c.total),
                        backgroundColor: '#7C3AED',
                        borderRadius: 6
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } } }
            });

            // Customers table
            document.getElementById('dashCustomersTable').style.display = 'block';
            document.getElementById('dashCustomersThead').innerHTML = `
                <tr><th>${titleCase(detected.customer || 'Customer')}</th><th>Total Spent</th><th>Avg Order</th><th>Orders</th><th>Share</th></tr>`;
            document.getElementById('dashCustomersTbody').innerHTML = customers.map(c => `
                <tr>
                    <td><strong>${c.name}</strong></td>
                    <td>${c.total.toLocaleString()}</td>
                    <td>${c.average.toLocaleString()}</td>
                    <td>${c.count}</td>
                    <td><span style="color:${c.percentage > 15 ? 'var(--accent-green)' : 'var(--text-secondary)'};font-weight:600;">${c.percentage}%</span></td>
                </tr>
            `).join('');
        } else if (topItems.by_customer_freq) {
            const customers = topItems.by_customer_freq;
            document.getElementById('dashTopCustomersCard').style.display = 'block';
            const ctx = document.getElementById('dashTopCustomersChart').getContext('2d');
            if (this._dashCustChart) this._dashCustChart.destroy();
            this._dashCustChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: customers.map(c => c.name.length > 15 ? c.name.substring(0,15)+'...' : c.name),
                    datasets: [{ label: 'Orders', data: customers.map(c => c.count), backgroundColor: '#7C3AED', borderRadius: 6 }]
                },
                options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } } }
            });
        }

        // Recommendations
        const recs = bi.recommendations || [];
        if (recs.length > 0) {
            document.getElementById('dashRecommendations').style.display = 'block';
            document.getElementById('dashRecommendationsBody').innerHTML = recs.map(r =>
                `<div class="insight-item"><i class="fas fa-chart-line"></i><p>${r}</p></div>`
            ).join('');
        }
    },

    // ============ OVERVIEW SECTION ============
    renderOverview(overview) {
        if (!overview) return;

        const shape = overview.shape || {};
        const metricsGrid = document.getElementById('overviewMetrics');

        metricsGrid.innerHTML = `
            <div class="metric-card">
                <div class="metric-value">${shape.rows || 'N/A'}</div>
                <div class="metric-label">Total Rows</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${shape.columns || 'N/A'}</div>
                <div class="metric-label">Total Columns</div>
            </div>
            <div class="metric-card ${overview.missing_percentage > 10 ? 'warning' : 'success'}">
                <div class="metric-value">${overview.missing_percentage || 0}%</div>
                <div class="metric-label">Missing Data</div>
            </div>
            <div class="metric-card ${overview.duplicate_percentage > 5 ? 'warning' : 'success'}">
                <div class="metric-value">${overview.duplicate_percentage || 0}%</div>
                <div class="metric-label">Duplicates</div>
            </div>
            <div class="metric-card info">
                <div class="metric-value">${overview.numeric_columns || 0}</div>
                <div class="metric-label">Numeric Cols</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${overview.memory_usage_mb || 0} MB</div>
                <div class="metric-label">Memory Usage</div>
            </div>
        `;

        // Charts
        ChartModule.renderColumnTypes('columnTypesChart', overview);
        const qualityScore = this.analysisData.problems?.overall_score || 85;
        ChartModule.renderQualityScore('qualityScoreChart', qualityScore);

        // Column details table
        const tbody = document.getElementById('columnDetailsBody');
        const colDetails = overview.column_details || [];
        tbody.innerHTML = colDetails.map(col => {
            const stats = col.stats || {};
            return `<tr>
                <td><strong>${col.name}</strong></td>
                <td><span class="format-tag">${col.dtype}</span></td>
                <td>${col.non_null}</td>
                <td class="${col.null_percentage > 10 ? 'text-danger' : ''}">${col.null_percentage}%</td>
                <td>${col.unique_count}</td>
                <td>${stats.mean || '-'}</td>
                <td>${stats.std || '-'}</td>
                <td>${stats.min || '-'}</td>
                <td>${stats.max || '-'}</td>
            </tr>`;
        }).join('');
    },

    // ============ CORRELATIONS SECTION ============
    renderCorrelations(correlations) {
        if (!correlations || correlations.error) {
            document.getElementById('correlationBody').innerHTML =
                `<tr><td colspan="5">${correlations?.error || 'Not available'}</td></tr>`;
            return;
        }

        // Heatmap
        const corrMatrix = correlations.correlation_matrix || {};
        ChartModule.renderCorrelationHeatmap('correlationHeatmap', corrMatrix);

        // Table
        const tbody = document.getElementById('correlationBody');
        const strongest = correlations.strongest_correlations || [];
        tbody.innerHTML = strongest.map(c => `<tr>
            <td>${c.var1}</td>
            <td>${c.var2}</td>
            <td><strong>${c.correlation}</strong></td>
            <td>${c.strength}</td>
            <td><span class="severity-badge ${c.direction === 'positive' ? 'severity-low' : 'severity-critical'}">${c.direction}</span></td>
        </tr>`).join('');

        // Insights
        const insightsDiv = document.getElementById('correlationInsights');
        const insights = correlations.insights || [];
        insightsDiv.innerHTML = insights.map(ins =>
            `<div class="insight-item"><i class="fas fa-lightbulb"></i><p>${ins}</p></div>`
        ).join('');
    },

    // ============ DISTRIBUTIONS SECTION ============
    renderDistributions(distributions) {
        if (!distributions) return;

        this.distributionData = distributions;
        const select = document.getElementById('distributionColumnSelect');

        select.innerHTML = '';
        Object.keys(distributions).forEach(col => {
            const opt = document.createElement('option');
            opt.value = col;
            opt.textContent = col;
            select.appendChild(opt);
        });

        if (Object.keys(distributions).length > 0) {
            this.renderDistribution(Object.keys(distributions)[0]);
        }
    },

    renderDistribution(colName) {
        const data = this.distributionData?.[colName];
        if (!data) return;

        // Histogram
        ChartModule.renderDistribution('distributionChart', colName, data);

        // Box plot
        const stats = data.statistics || {};
        if (stats.q25 !== undefined) {
            ChartModule.renderBoxPlot('boxPlotChart', colName, {
                min: stats.min, q25: stats.q25, q50: stats.q50, q75: stats.q75, max: stats.max
            });
        }

        // Stats display
        const statsDiv = document.getElementById('distributionStats');
        const outlierInfo = data.outliers_iqr || {};
        const normality = data.normality_test || {};

        statsDiv.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card"><div class="metric-value">${stats.mean || '-'}</div><div class="metric-label">Mean</div></div>
                <div class="metric-card"><div class="metric-value">${stats.median || '-'}</div><div class="metric-label">Median</div></div>
                <div class="metric-card"><div class="metric-value">${stats.std || '-'}</div><div class="metric-label">Std Dev</div></div>
                <div class="metric-card ${Math.abs(stats.skewness || 0) > 2 ? 'warning' : ''}"><div class="metric-value">${stats.skewness || '-'}</div><div class="metric-label">Skewness</div></div>
                <div class="metric-card"><div class="metric-value">${stats.kurtosis || '-'}</div><div class="metric-label">Kurtosis</div></div>
                <div class="metric-card ${outlierInfo.percentage > 5 ? 'warning' : 'success'}"><div class="metric-value">${outlierInfo.count || 0}</div><div class="metric-label">Outliers</div></div>
            </div>
            <div style="margin-top: 16px;">
                <p style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 8px;">
                    <strong>Distribution Shape:</strong> ${data.distribution_shape || 'N/A'}
                </p>
                <p style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 8px;">
                    <strong>IQR:</strong> ${stats.iqr || '-'} |
                    <strong>Range:</strong> ${stats.range || '-'}
                </p>
                ${normality.test === 'Shapiro-Wilk' ? `
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 8px;">
                        <strong>Normality (Shapiro-Wilk):</strong> p-value = ${normality.p_value}
                        ${normality.is_normal ? '<span style="color: var(--accent-green);"> (Normal distribution)</span>' : '<span style="color: var(--accent-red);"> (Non-normal distribution)</span>'}
                    </p>
                ` : ''}
                ${outlierInfo.count > 0 ? `
                    <p style="font-size: 0.88rem; color: var(--text-secondary);">
                        <strong>Outlier Bounds:</strong> [${outlierInfo.lower_bound}, ${outlierInfo.upper_bound}]
                        (${outlierInfo.percentage}% of data)
                    </p>
                ` : ''}
            </div>
        `;
    },

    // ============ ANOMALIES SECTION ============
    renderAnomalies(anomalies) {
        if (!anomalies || anomalies.error) {
            document.getElementById('anomalyMetrics').innerHTML =
                `<div class="metric-card"><div class="metric-value">N/A</div><div class="metric-label">${anomalies?.error || 'Not available'}</div></div>`;
            return;
        }

        const metricsGrid = document.getElementById('anomalyMetrics');
        metricsGrid.innerHTML = `
            <div class="metric-card ${anomalies.anomaly_percentage > 10 ? 'danger' : anomalies.anomaly_percentage > 5 ? 'warning' : 'success'}">
                <div class="metric-value">${anomalies.total_anomalies}</div>
                <div class="metric-label">Anomalies Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${anomalies.anomaly_percentage}%</div>
                <div class="metric-label">Anomaly Rate</div>
            </div>
        `;

        // Anomaly score chart
        ChartModule.renderAnomalyScores('anomalyScoreChart', anomalies);

        // Anomaly profile chart
        ChartModule.renderAnomalyProfile('anomalyProfileChart', anomalies.anomaly_profile);

        // Insights
        const insightsDiv = document.getElementById('anomalyInsights');
        const insights = anomalies.insights || [];
        insightsDiv.innerHTML = insights.map(ins =>
            `<div class="insight-item"><i class="fas fa-exclamation-circle"></i><p>${ins}</p></div>`
        ).join('');
    },

    // ============ PREDICTIONS SECTION ============
    async runPredictions() {
        if (!this.sessionId) return;

        const targetCol = document.getElementById('predictionTarget').value;
        const periods = parseInt(document.getElementById('forecastPeriods').value) || 5;

        this.showLoading('Running ML predictions...');

        try {
            const response = await fetch(`${this.API}/api/analyze/predictions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    target_column: targetCol,
                    periods: periods
                })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            this.renderPredictions(data);
            this.hideLoading();
            this.showToast('Predictions complete!', 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast(`Prediction failed: ${error.message}`, 'error');
        }
    },

    renderPredictions(data) {
        const container = document.getElementById('predictionResults');
        if (!data || data.error) {
            container.innerHTML = `<div class="empty-state"><i class="fas fa-brain"></i><h3>${data?.error || 'No predictions available'}</h3></div>`;
            return;
        }

        const predictions = data.predictions || {};
        const target = data.target || 'Unknown';
        let html = '';

        // Linear trend
        if (predictions.linear_trend) {
            const lt = predictions.linear_trend;
            html += `
                <div class="prediction-model-card">
                    <div class="model-header">
                        <span class="model-name">Linear Trend</span>
                        <span class="model-r2 ${lt.r2_score > 0.7 ? 'r2-good' : lt.r2_score > 0.4 ? 'r2-moderate' : 'r2-poor'}">R² = ${lt.r2_score}</span>
                    </div>
                    <p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:10px;">
                        Trend: <strong>${lt.trend}</strong> (slope: ${lt.slope}, intercept: ${lt.intercept})
                    </p>
                    <div class="prediction-values">
                        ${lt.future_values.map((v, i) => `<span class="pred-value">T+${i + 1}: ${v}</span>`).join('')}
                    </div>
                    <div style="margin-top:16px;"><canvas id="predLinearChart" height="200"></canvas></div>
                </div>
            `;
        }

        // Polynomial trend
        if (predictions.polynomial_trend) {
            const pt = predictions.polynomial_trend;
            html += `
                <div class="prediction-model-card">
                    <div class="model-header">
                        <span class="model-name">Polynomial Trend (Degree 2)</span>
                        <span class="model-r2 ${pt.r2_score > 0.7 ? 'r2-good' : pt.r2_score > 0.4 ? 'r2-moderate' : 'r2-poor'}">R² = ${pt.r2_score}</span>
                    </div>
                    <div class="prediction-values">
                        ${pt.future_values.map((v, i) => `<span class="pred-value">T+${i + 1}: ${v}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        // Random Forest
        if (predictions.random_forest) {
            const rf = predictions.random_forest;
            html += `
                <div class="prediction-model-card">
                    <div class="model-header">
                        <span class="model-name">Random Forest Regressor</span>
                        <span class="model-r2 ${rf.r2_score > 0.7 ? 'r2-good' : rf.r2_score > 0.4 ? 'r2-moderate' : 'r2-poor'}">R² = ${rf.r2_score}</span>
                    </div>
                    <div class="metrics-grid" style="margin-bottom:12px;">
                        <div class="metric-card"><div class="metric-value">${rf.mae}</div><div class="metric-label">MAE</div></div>
                        <div class="metric-card"><div class="metric-value">${rf.rmse}</div><div class="metric-label">RMSE</div></div>
                    </div>
                    <h4 style="font-size:0.9rem;margin-bottom:8px;">Feature Importance</h4>
                    <div class="feature-importance-list">
                        ${(rf.feature_importance || []).map(fi => `
                            <div class="fi-item">
                                <span class="fi-label">${fi.feature}</span>
                                <div class="fi-bar-bg"><div class="fi-bar" style="width:${fi.importance * 100}%"></div></div>
                                <span class="fi-value">${fi.importance}</span>
                            </div>
                        `).join('')}
                    </div>
                    <div style="margin-top:16px;"><canvas id="predRFChart" height="200"></canvas></div>
                </div>
            `;
        }

        // Gradient Boosting
        if (predictions.gradient_boosting) {
            const gb = predictions.gradient_boosting;
            html += `
                <div class="prediction-model-card">
                    <div class="model-header">
                        <span class="model-name">Gradient Boosting Regressor</span>
                        <span class="model-r2 ${gb.r2_score > 0.7 ? 'r2-good' : gb.r2_score > 0.4 ? 'r2-moderate' : 'r2-poor'}">R² = ${gb.r2_score}</span>
                    </div>
                    <div class="metrics-grid" style="margin-bottom:12px;">
                        <div class="metric-card"><div class="metric-value">${gb.mae}</div><div class="metric-label">MAE</div></div>
                        <div class="metric-card"><div class="metric-value">${gb.rmse}</div><div class="metric-label">RMSE</div></div>
                    </div>
                </div>
            `;
        }

        // Best model forecast
        if (predictions.best_model_forecast) {
            const bf = predictions.best_model_forecast;
            html += `
                <div class="prediction-model-card" style="border:2px solid var(--accent-green);">
                    <div class="model-header">
                        <span class="model-name">Best Model: ${bf.model}</span>
                        <span class="model-r2 r2-good">R² = ${bf.r2_score}</span>
                    </div>
                    <p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:10px;">
                        Recommended forecast for '${target}':
                    </p>
                    <div class="prediction-values">
                        ${bf.future_values.map((v, i) => `<span class="pred-value" style="background:var(--accent-green-light);">T+${i + 1}: ${v}</span>`).join('')}
                    </div>
                    <div style="margin-top:16px;"><canvas id="predBestChart" height="200"></canvas></div>
                </div>
            `;
        }

        // Prediction insights
        if (data.insights && data.insights.length > 0) {
            html += `<div class="card"><div class="card-header"><h3>Prediction Insights</h3></div><div class="card-body">`;
            data.insights.forEach(ins => {
                html += `<div class="insight-item"><i class="fas fa-chart-line"></i><p>${ins}</p></div>`;
            });
            html += `</div></div>`;
        }

        container.innerHTML = html;

        // Render prediction charts after DOM update
        setTimeout(() => {
            // Get historical data for the target column
            const overview = this.analysisData.overview;
            const colDetails = overview?.column_details || [];
            const targetCol = colDetails.find(c => c.name === target);
            const histLen = 50;

            if (predictions.linear_trend) {
                // Generate approximate historical data from stats
                const stats = targetCol?.stats || {};
                if (stats.mean !== undefined) {
                    const histData = this._generateSyntheticHistData(stats, histLen);
                    ChartModule.renderPredictions('predLinearChart', histData, predictions.linear_trend.future_values, target);
                }
            }
            if (predictions.best_model_forecast) {
                const stats = targetCol?.stats || {};
                if (stats.mean !== undefined) {
                    const histData = this._generateSyntheticHistData(stats, histLen);
                    ChartModule.renderPredictions('predBestChart', histData, predictions.best_model_forecast.future_values, target);
                }
            }
            if (predictions.random_forest && (predictions.random_forest.feature_importance || []).length > 0) {
                ChartModule.renderFeatureImportance('predRFChart', predictions.random_forest.feature_importance);
            }
        }, 100);
    },

    _generateSyntheticHistData(stats, len) {
        // Generate approximate historical data from summary stats
        const data = [];
        const mean = stats.mean || 0;
        const std = stats.std || 1;
        const min = stats.min || mean - 3 * std;
        const max = stats.max || mean + 3 * std;
        for (let i = 0; i < len; i++) {
            const t = i / len;
            data.push(min + t * (max - min) + (Math.random() - 0.5) * std);
        }
        return data;
    },

    // ============ PROBLEMS SECTION ============
    renderProblems(problemsData, solutionsData) {
        if (!problemsData) return;

        // Metrics
        const metricsGrid = document.getElementById('problemMetrics');
        metricsGrid.innerHTML = `
            <div class="metric-card ${problemsData.critical > 0 ? 'danger' : 'success'}">
                <div class="metric-value">${problemsData.critical || 0}</div>
                <div class="metric-label">Critical</div>
            </div>
            <div class="metric-card ${problemsData.high > 0 ? 'warning' : 'success'}">
                <div class="metric-value">${problemsData.high || 0}</div>
                <div class="metric-label">High</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${problemsData.medium || 0}</div>
                <div class="metric-label">Medium</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${problemsData.low || 0}</div>
                <div class="metric-label">Low</div>
            </div>
            <div class="metric-card ${problemsData.overall_score < 60 ? 'danger' : problemsData.overall_score < 80 ? 'warning' : 'success'}">
                <div class="metric-value">${problemsData.overall_score || 0}</div>
                <div class="metric-label">Quality Score</div>
            </div>
        `;

        // Problems list
        const problemsList = document.getElementById('problemsList');
        const problems = problemsData.problems || [];
        problemsList.innerHTML = `<h3 style="margin-bottom:12px;font-size:1.05rem;color:var(--text-primary);">Detected Problems</h3>` +
            problems.map(p => `
                <div class="problem-item">
                    <div class="problem-header">
                        <span class="severity-badge severity-${p.severity.toLowerCase()}">${p.severity}</span>
                        <span class="problem-type">${p.type}</span>
                        <span class="problem-column">in "${p.column}"</span>
                    </div>
                    <div class="problem-details">${p.details}</div>
                    <div class="problem-impact"><strong>Impact:</strong> ${p.impact}</div>
                    <div class="problem-solution"><strong>Solution:</strong> ${p.solution}</div>
                </div>
            `).join('');

        // Solutions list
        const solutionsList = document.getElementById('solutionsList');
        const solutions = solutionsData || [];
        if (solutions.length > 0) {
            solutionsList.innerHTML = `<h3 style="margin-bottom:12px;font-size:1.05rem;color:var(--text-primary);">Recommended Solutions</h3>` +
                solutions.map(s => {
                    const priorityLevel = (s.priority?.level || 'important').toLowerCase();
                    return `
                        <div class="solution-item">
                            <div class="solution-header">
                                <span class="priority-badge priority-${priorityLevel === 'immediate' ? 'immediate' : priorityLevel === 'urgent' ? 'urgent' : priorityLevel === 'important' ? 'important' : 'nice'}">
                                    ${s.priority?.level || 'N/A'}
                                </span>
                                <span class="problem-type">${s.problem_type}</span>
                                <span class="problem-column">- ${s.column}</span>
                                <span style="margin-left:auto;font-size:0.78rem;color:var(--text-tertiary);">${s.priority?.timeline || ''}</span>
                            </div>
                            <div class="problem-details">${s.solution}</div>
                            <ul class="action-steps">
                                ${(s.action_steps || []).map(step => `<li>${step}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }).join('');
        }
    },

    // ============ FEATURES SECTION ============
    renderFeatures(featureData) {
        if (!featureData) return;

        const metricsGrid = document.getElementById('featureMetrics');
        metricsGrid.innerHTML = `
            <div class="metric-card info">
                <div class="metric-value">${featureData.total_suggestions || 0}</div>
                <div class="metric-label">Suggestions</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${(featureData.categories || []).length}</div>
                <div class="metric-label">Categories</div>
            </div>
        `;

        const grid = document.getElementById('featuresGrid');
        const suggestions = featureData.suggestions || [];
        grid.innerHTML = suggestions.map(s => `
            <div class="feature-card">
                <span class="feature-category">${s.category}</span>
                <div class="feature-source">Source: ${s.source_column}</div>
                ${(s.suggested_features || []).map(f => `
                    <div class="feature-item">
                        <span class="feat-name">${f.name}</span>
                        <span style="font-size:0.8rem;color:var(--text-tertiary);">${f.description}</span>
                        <span class="feat-type">${f.type}</span>
                    </div>
                `).join('')}
            </div>
        `).join('');
    },

    // ============ CLUSTERING SECTION ============
    async runClustering() {
        if (!this.sessionId) return;

        const nClusters = document.getElementById('clusterCount').value;
        this.showLoading('Running clustering analysis...');

        try {
            const response = await fetch(`${this.API}/api/analyze/clustering`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    n_clusters: nClusters ? parseInt(nClusters) : null
                })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            this.renderClustering(data);
            this.hideLoading();
            this.showToast(`Found ${data.n_clusters} clusters!`, 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast(`Clustering failed: ${error.message}`, 'error');
        }
    },

    renderClustering(clusterData) {
        if (!clusterData || clusterData.error) {
            document.getElementById('clusterProfiles').innerHTML =
                `<div class="empty-state"><i class="fas fa-object-group"></i><h3>${clusterData?.error || 'Not available'}</h3></div>`;
            return;
        }

        // Scatter chart
        const pcaData = clusterData.pca_coordinates || {};
        ChartModule.renderClusterScatter('clusterChart', pcaData);

        // Cluster profiles
        const profilesDiv = document.getElementById('clusterProfiles');
        const profiles = clusterData.cluster_profiles || {};
        const sizes = clusterData.cluster_sizes || {};
        const insights = clusterData.insights || [];

        let html = '';

        // Cluster size metrics
        html += `<div class="metrics-grid" style="margin-bottom:16px;">`;
        Object.entries(sizes).forEach(([name, count]) => {
            html += `<div class="metric-card info"><div class="metric-value">${count}</div><div class="metric-label">${name}</div></div>`;
        });
        html += `</div>`;

        // Profile cards
        Object.entries(profiles).forEach(([clusterName, profile]) => {
            html += `
                <div class="cluster-profile-card">
                    <div class="cluster-name">${clusterName}</div>
                    <div class="cluster-size">${sizes[clusterName] || 0} records</div>
                    <div class="cluster-features">
                        ${Object.entries(profile).slice(0, 8).map(([feat, info]) => `
                            <div class="cluster-feat">
                                <div class="cluster-feat-name">${feat}</div>
                                <div class="cluster-feat-val">Mean: ${info.mean} (Std: ${info.std})</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        });

        // Insights
        if (insights.length > 0) {
            html += `<div style="margin-top:12px;">`;
            insights.forEach(ins => {
                html += `<div class="insight-item"><i class="fas fa-layer-group"></i><p>${ins}</p></div>`;
            });
            html += `</div>`;
        }

        profilesDiv.innerHTML = html;
    },

    // ============ REPORT GENERATION ============
    async generateReport() {
        if (!this.sessionId) {
            this.showToast('Please upload data and run analysis first', 'warning');
            return;
        }

        this.showLoading('Generating PDF report...');

        try {
            const response = await fetch(`${this.API}/api/report/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            this.hideLoading();

            // Trigger download
            if (data.download_url) {
                const a = document.createElement('a');
                a.href = `${this.API}${data.download_url}`;
                a.download = data.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                this.showToast('Report downloaded successfully!', 'success');
            }

        } catch (error) {
            this.hideLoading();
            this.showToast(`Report generation failed: ${error.message}`, 'error');
        }
    },

    // ============ UTILITY FUNCTIONS ============
    filterColumns(query) {
        const rows = document.querySelectorAll('#columnDetailsBody tr');
        const q = query.toLowerCase();
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(q) ? '' : 'none';
        });
    },

    showLoading(text) {
        document.getElementById('loadingText').textContent = text || 'Loading...';
        document.getElementById('loadingOverlay').classList.add('active');
    },

    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('active');
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-times-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="${icons[type]}"></i><span>${message}</span>`;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());

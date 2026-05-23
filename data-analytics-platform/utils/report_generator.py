"""
PDF Report Generator - Generates comprehensive analysis reports
"""
import os
import io
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np


# Font setup for matplotlib - cross-platform compatible
import platform

_system = platform.system()
_fonts_added = False

# Try common font paths based on OS
_font_paths = []
if _system == 'Windows':
    _windir = os.environ.get('WINDIR', r'C:\Windows')
    _font_paths = [
        os.path.join(_windir, 'Fonts', 'arial.ttf'),
        os.path.join(_windir, 'Fonts', 'segoeui.ttf'),
        os.path.join(_windir, 'Fonts', 'msyh.ttc'),  # Microsoft YaHei (Chinese)
    ]
elif _system == 'Darwin':  # macOS
    _font_paths = [
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
else:  # Linux
    _font_paths = [
        '/usr/share/fonts/truetype/chinese/SarasaMonoSC-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]

for _fp in _font_paths:
    try:
        fm.fontManager.addfont(_fp)
        _fonts_added = True
    except Exception:
        pass

# Set font fallback - use system defaults if no custom fonts found
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'Segoe UI', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


class ReportGenerator:
    """Generate professional PDF analysis reports."""

    # Color palette - soft white theme
    PRIMARY = colors.HexColor('#4F46E5')
    SECONDARY = colors.HexColor('#7C3AED')
    ACCENT = colors.HexColor('#10B981')
    WARNING = colors.HexColor('#F59E0B')
    DANGER = colors.HexColor('#EF4444')
    LIGHT_BG = colors.HexColor('#F9FAFB')
    DARK_TEXT = colors.HexColor('#1F2937')
    MEDIUM_TEXT = colors.HexColor('#4B5563')
    LIGHT_TEXT = colors.HexColor('#9CA3AF')
    TABLE_HEADER = colors.HexColor('#EEF2FF')
    TABLE_ALT = colors.HexColor('#F9FAFB')

    def __init__(self, analysis_data, filename="analysis_report.pdf"):
        self.data = analysis_data
        self.filename = filename
        # Save reports in the project's 'reports' directory (cross-platform)
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.charts_dir = os.path.join(self.output_dir, "temp_charts")
        os.makedirs(self.charts_dir, exist_ok=True)

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=self.PRIMARY,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=self.PRIMARY,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=0,
        ))
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=self.SECONDARY,
            spaceBefore=14,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='BodyText2',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=self.DARK_TEXT,
            spaceAfter=8,
            leading=14,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='InsightText',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=self.MEDIUM_TEXT,
            spaceAfter=6,
            leading=14,
            leftIndent=15,
            fontName='Helvetica-Oblique'
        ))
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            fontSize=20,
            textColor=self.PRIMARY,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            fontSize=9,
            textColor=self.LIGHT_TEXT,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

    def generate(self):
        """Generate the complete PDF report."""
        filepath = os.path.join(self.output_dir, self.filename)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        story = []

        # Cover page
        story.extend(self._build_cover_page())

        # Table of contents
        story.extend(self._build_toc())

        # Sections
        if 'overview' in self.data:
            story.extend(self._build_overview_section())

        if 'correlations' in self.data:
            story.extend(self._build_correlation_section())

        if 'distributions' in self.data:
            story.extend(self._build_distribution_section())

        if 'anomalies' in self.data:
            story.extend(self._build_anomaly_section())

        if 'problems' in self.data:
            story.extend(self._build_problems_section())

        if 'predictions' in self.data:
            story.extend(self._build_prediction_section())

        if 'feature_suggestions' in self.data:
            story.extend(self._build_features_section())

        if 'clustering' in self.data:
            story.extend(self._build_clustering_section())

        # Build
        doc.build(story)

        # Cleanup temp charts
        self._cleanup_charts()

        return filepath

    def _build_cover_page(self):
        elements = []
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("Data Analysis Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3 * inch))

        # Subtitle
        elements.append(Paragraph(
            "Comprehensive Data Analytics & Insights",
            ParagraphStyle('subtitle', parent=self.styles['Normal'],
                          fontSize=14, textColor=self.SECONDARY, alignment=TA_CENTER,
                          fontName='Helvetica')
        ))
        elements.append(Spacer(1, 0.5 * inch))

        # Horizontal line
        elements.append(HRFlowable(
            width="60%", thickness=2, color=self.PRIMARY,
            spaceAfter=20, spaceBefore=10, hAlign='CENTER'
        ))

        # Date and info
        info_style = ParagraphStyle(
            'info', parent=self.styles['Normal'],
            fontSize=11, textColor=self.MEDIUM_TEXT, alignment=TA_CENTER,
            fontName='Helvetica'
        )
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", info_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Key metrics summary
        overview = self.data.get('overview', {})
        if overview:
            metrics_data = [
                ['Total Rows', 'Total Columns', 'Missing %', 'Quality Score'],
                [
                    str(overview.get('shape', {}).get('rows', 'N/A')),
                    str(overview.get('shape', {}).get('columns', 'N/A')),
                    f"{overview.get('missing_percentage', 0)}%",
                    f"{self.data.get('problems', {}).get('overall_score', 'N/A')}"
                ]
            ]
            t = Table(metrics_data, colWidths=[1.2*inch]*4)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 12),
                ('TEXTCOLOR', (0, 1), (-1, 1), self.DARK_TEXT),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(t)

        elements.append(Spacer(1, 1.5 * inch))

        # Footer
        footer_style = ParagraphStyle(
            'footer', parent=self.styles['Normal'],
            fontSize=9, textColor=self.LIGHT_TEXT, alignment=TA_CENTER,
            fontName='Helvetica'
        )
        elements.append(Paragraph("Powered by Advanced Data Analytics Platform", footer_style))

        elements.append(PageBreak())
        return elements

    def _build_toc(self):
        elements = []
        elements.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        sections = [
            ("1. Data Overview", "Dataset shape, types, and basic statistics"),
            ("2. Correlation Analysis", "Inter-variable relationships and dependencies"),
            ("3. Distribution Analysis", "Statistical distributions and normality"),
            ("4. Anomaly Detection", "Outlier identification using Isolation Forest"),
            ("5. Problem Detection", "Data quality issues and their severity"),
            ("6. Predictions & Forecasting", "ML-powered future value predictions"),
            ("7. Feature Engineering", "Suggested new features for improved modeling"),
            ("8. Clustering Analysis", "Natural groupings in the data"),
        ]

        for title, desc in sections:
            elements.append(Paragraph(
                f'<b>{title}</b>', 
                ParagraphStyle('toc_item', parent=self.styles['Normal'],
                              fontSize=11, textColor=self.PRIMARY, fontName='Helvetica-Bold',
                              spaceBefore=8, spaceAfter=2)
            ))
            elements.append(Paragraph(
                desc,
                ParagraphStyle('toc_desc', parent=self.styles['Normal'],
                              fontSize=9, textColor=self.MEDIUM_TEXT, fontName='Helvetica',
                              leftIndent=15, spaceAfter=4)
            ))

        elements.append(PageBreak())
        return elements

    def _build_overview_section(self):
        elements = []
        elements.append(Paragraph("1. Data Overview", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        overview = self.data['overview']

        # Key metrics table
        shape = overview.get('shape', {})
        elements.append(Paragraph(
            f"The dataset contains <b>{shape.get('rows', 'N/A')}</b> rows and "
            f"<b>{shape.get('columns', 'N/A')}</b> columns. "
            f"There are <b>{overview.get('numeric_columns', 0)}</b> numeric columns, "
            f"<b>{overview.get('categorical_columns', 0)}</b> categorical columns, and "
            f"<b>{overview.get('datetime_columns', 0)}</b> datetime columns. "
            f"The dataset uses approximately <b>{overview.get('memory_usage_mb', 0)} MB</b> of memory.",
            self.styles['BodyText2']
        ))
        elements.append(Spacer(1, 0.15 * inch))

        # Data quality summary
        quality_data = [
            ['Metric', 'Value', 'Status'],
            ['Missing Cells', f"{overview.get('missing_cells', 0)} ({overview.get('missing_percentage', 0)}%)", 
             'Good' if overview.get('missing_percentage', 0) < 5 else 'Warning' if overview.get('missing_percentage', 0) < 20 else 'Critical'],
            ['Duplicate Rows', f"{overview.get('duplicate_rows', 0)} ({overview.get('duplicate_percentage', 0)}%)",
             'Good' if overview.get('duplicate_percentage', 0) < 1 else 'Warning'],
            ['Memory Usage', f"{overview.get('memory_usage_mb', 0)} MB",
             'Good' if overview.get('memory_usage_mb', 0) < 100 else 'Warning'],
        ]
        t = Table(quality_data, colWidths=[2*inch, 2.2*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2 * inch))

        # Column details
        elements.append(Paragraph("Column Details", self.styles['SubSection']))
        col_details = overview.get('column_details', [])
        if col_details:
            col_data = [['Column', 'Type', 'Non-Null', 'Null %', 'Unique']]
            for cd in col_details[:30]:  # Limit to 30 columns
                col_data.append([
                    cd['name'][:25],
                    cd['dtype'],
                    str(cd['non_null']),
                    f"{cd['null_percentage']}%",
                    str(cd['unique_count'])
                ])
            t = Table(col_data, colWidths=[1.5*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.8*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t)

        return elements

    def _build_correlation_section(self):
        elements = []
        elements.append(Paragraph("2. Correlation Analysis", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        corr_data = self.data.get('correlations', {})
        if 'error' in corr_data:
            elements.append(Paragraph(corr_data['error'], self.styles['BodyText2']))
            return elements

        # Correlation heatmap
        corr_matrix = corr_data.get('correlation_matrix', {})
        cols = corr_matrix.get('columns', [])
        values = corr_matrix.get('values', [])

        if cols and values:
            try:
                fig, ax = plt.subplots(figsize=(8, 6))
                cmap = plt.cm.RdYlBu_r
                im = ax.imshow(values, cmap=cmap, vmin=-1, vmax=1, aspect='auto')
                ax.set_xticks(range(len(cols)))
                ax.set_yticks(range(len(cols)))
                ax.set_xticklabels([c[:12] for c in cols], rotation=45, ha='right', fontsize=8)
                ax.set_yticklabels([c[:12] for c in cols], fontsize=8)
                plt.colorbar(im, ax=ax, label='Correlation')
                ax.set_title('Correlation Heatmap', fontsize=12, pad=10)

                # Add text annotations for small matrices
                if len(cols) <= 10:
                    for i in range(len(cols)):
                        for j in range(len(cols)):
                            ax.text(j, i, f'{values[i][j]:.2f}', ha='center', va='center',
                                   fontsize=7, color='black' if abs(values[i][j]) < 0.5 else 'white')

                chart_path = os.path.join(self.charts_dir, 'correlation_heatmap.png')
                plt.tight_layout()
                plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
                plt.close()
                elements.append(Image(chart_path, width=5.5*inch, height=4.2*inch))
                elements.append(Spacer(1, 0.15 * inch))
            except Exception:
                pass

        # Strongest correlations
        strongest = corr_data.get('strongest_correlations', [])
        if strongest:
            elements.append(Paragraph("Strongest Correlations", self.styles['SubSection']))
            corr_table = [['Variable 1', 'Variable 2', 'Correlation', 'Strength', 'Direction']]
            for c in strongest[:10]:
                corr_table.append([c['var1'], c['var2'], str(c['correlation']), c['strength'], c['direction']])
            t = Table(corr_table, colWidths=[1.2*inch, 1.2*inch, 1*inch, 1*inch, 0.9*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t)

        # Insights
        insights = corr_data.get('insights', [])
        if insights:
            elements.append(Paragraph("Key Insights", self.styles['SubSection']))
            for ins in insights:
                elements.append(Paragraph(f"* {ins}", self.styles['InsightText']))

        return elements

    def _build_distribution_section(self):
        elements = []
        elements.append(Paragraph("3. Distribution Analysis", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        dist_data = self.data.get('distributions', {})
        if not dist_data:
            elements.append(Paragraph("No numeric columns available for distribution analysis.", self.styles['BodyText2']))
            return elements

        # Create distribution charts
        cols_to_chart = list(dist_data.keys())[:8]
        if cols_to_chart:
            try:
                n_cols = min(3, len(cols_to_chart))
                n_rows = (len(cols_to_chart) + n_cols - 1) // n_cols
                fig, axes = plt.subplots(n_rows, n_cols, figsize=(4*n_cols, 3*n_rows))
                if n_rows == 1 and n_cols == 1:
                    axes = np.array([axes])
                axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]

                for idx, col in enumerate(cols_to_chart):
                    ax = axes[idx]
                    hist = dist_data[col]['histogram']
                    counts = hist['counts']
                    bins = hist['bins']
                    bin_centers = [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
                    ax.bar(range(len(counts)), counts, color='#4F46E5', alpha=0.7, edgecolor='white')
                    ax.set_title(col[:20], fontsize=9, pad=5)
                    ax.set_ylabel('Count', fontsize=7)
                    ax.tick_params(labelsize=7)

                # Hide empty axes
                for idx in range(len(cols_to_chart), len(axes)):
                    axes[idx].set_visible(False)

                chart_path = os.path.join(self.charts_dir, 'distributions.png')
                plt.tight_layout()
                plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
                plt.close()
                elements.append(Image(chart_path, width=6*inch, height=4*inch))
                elements.append(Spacer(1, 0.15 * inch))
            except Exception:
                pass

        # Distribution statistics table
        elements.append(Paragraph("Distribution Statistics", self.styles['SubSection']))
        dist_table = [['Column', 'Mean', 'Median', 'Std', 'Skewness', 'Kurtosis', 'Shape']]
        for col, info in list(dist_data.items())[:15]:
            stats = info.get('statistics', {})
            dist_table.append([
                col[:20],
                str(stats.get('mean', 'N/A')),
                str(stats.get('median', 'N/A')),
                str(stats.get('std', 'N/A')),
                str(stats.get('skewness', 'N/A')),
                str(stats.get('kurtosis', 'N/A')),
                info.get('distribution_shape', 'N/A')[:25]
            ])
        t = Table(dist_table, colWidths=[1*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.8*inch, 1.1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)

        return elements

    def _build_anomaly_section(self):
        elements = []
        elements.append(Paragraph("4. Anomaly Detection", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        anomaly_data = self.data.get('anomalies', {})
        if 'error' in anomaly_data:
            elements.append(Paragraph(anomaly_data['error'], self.styles['BodyText2']))
            return elements

        elements.append(Paragraph(
            f"Using Isolation Forest algorithm, <b>{anomaly_data.get('total_anomalies', 0)}</b> anomalies "
            f"were detected out of total data points, representing "
            f"<b>{anomaly_data.get('anomaly_percentage', 0)}%</b> of the dataset. "
            f"Anomalies are data points that significantly deviate from the normal pattern and may "
            f"indicate data quality issues, fraud, system failures, or genuinely rare events.",
            self.styles['BodyText2']
        ))
        elements.append(Spacer(1, 0.1 * inch))

        # Anomaly profile
        profile = anomaly_data.get('anomaly_profile', {})
        if profile:
            elements.append(Paragraph("Anomaly Profile - Key Deviations", self.styles['SubSection']))
            profile_table = [['Column', 'Normal Mean', 'Anomaly Mean', 'Deviation %']]
            for col, info in profile.items():
                profile_table.append([
                    col[:25],
                    str(info['normal_mean']),
                    str(info['anomaly_mean']),
                    f"{info['deviation_pct']}%"
                ])
            t = Table(profile_table, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t)

        # Insights
        insights = anomaly_data.get('insights', [])
        if insights:
            elements.append(Paragraph("Anomaly Insights", self.styles['SubSection']))
            for ins in insights:
                elements.append(Paragraph(f"* {ins}", self.styles['InsightText']))

        return elements

    def _build_problems_section(self):
        elements = []
        elements.append(Paragraph("5. Problem Detection & Solutions", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        problems_data = self.data.get('problems', {})
        problems = problems_data.get('problems', [])

        # Summary metrics
        elements.append(Paragraph(
            f"A total of <b>{problems_data.get('total_problems', 0)}</b> issues were identified: "
            f"<b>{problems_data.get('critical', 0)}</b> Critical, "
            f"<b>{problems_data.get('high', 0)}</b> High, "
            f"<b>{problems_data.get('medium', 0)}</b> Medium, "
            f"<b>{problems_data.get('low', 0)}</b> Low severity. "
            f"The overall data quality score is <b>{problems_data.get('overall_score', 'N/A')}/100</b>.",
            self.styles['BodyText2']
        ))
        elements.append(Spacer(1, 0.1 * inch))

        # Problems table
        if problems:
            prob_table = [['Type', 'Column', 'Severity', 'Details', 'Solution']]
            for p in problems[:20]:
                prob_table.append([
                    p['type'],
                    p['column'][:15],
                    p['severity'],
                    p['details'][:50],
                    p['solution'][:60]
                ])
            t = Table(prob_table, colWidths=[0.9*inch, 0.8*inch, 0.7*inch, 1.8*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t)

        # Solutions section
        solutions = self.data.get('solutions', [])
        if solutions:
            elements.append(Spacer(1, 0.15 * inch))
            elements.append(Paragraph("Recommended Solutions", self.styles['SubSection']))
            for sol in solutions[:10]:
                elements.append(Paragraph(
                    f'<b>[{sol.get("priority", {}).get("level", "N/A")}]</b> '
                    f'{sol.get("problem_type", "")} - {sol.get("column", "")}: {sol.get("solution", "")}',
                    self.styles['BodyText2']
                ))
                for step in sol.get('action_steps', [])[:3]:
                    elements.append(Paragraph(f"  {step}", self.styles['InsightText']))

        return elements

    def _build_prediction_section(self):
        elements = []
        elements.append(Paragraph("6. Predictions & Forecasting", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        pred_data = self.data.get('predictions', {})
        if 'error' in pred_data:
            elements.append(Paragraph(pred_data['error'], self.styles['BodyText2']))
            return elements

        target = pred_data.get('target', 'N/A')
        elements.append(Paragraph(
            f"Predictions are generated for the target variable '<b>{target}</b>' using multiple "
            f"machine learning models. Each model provides different perspectives on future trends, "
            f"and the best-performing model is selected for final forecasting.",
            self.styles['BodyText2']
        ))
        elements.append(Spacer(1, 0.1 * inch))

        predictions = pred_data.get('predictions', {})

        # Linear trend
        if 'linear_trend' in predictions:
            lt = predictions['linear_trend']
            elements.append(Paragraph("Linear Trend Analysis", self.styles['SubSection']))
            elements.append(Paragraph(
                f"The linear trend shows a <b>{lt['trend']}</b> pattern with a slope of "
                f"<b>{lt['slope']}</b> and R-squared of <b>{lt['r2_score']}</b>. "
                f"Predicted future values: {', '.join([str(v) for v in lt['future_values']])}.",
                self.styles['BodyText2']
            ))

        # Random Forest
        if 'random_forest' in predictions:
            rf = predictions['random_forest']
            elements.append(Paragraph("Random Forest Model", self.styles['SubSection']))
            elements.append(Paragraph(
                f"Random Forest Regressor achieves an R-squared of <b>{rf['r2_score']}</b>, "
                f"MAE of <b>{rf['mae']}</b>, and RMSE of <b>{rf['rmse']}</b>. "
                f"This indicates {'strong' if rf['r2_score'] > 0.7 else 'moderate' if rf['r2_score'] > 0.4 else 'limited'} "
                f"predictive power.",
                self.styles['BodyText2']
            ))
            # Feature importance
            if rf.get('feature_importance'):
                fi_table = [['Feature', 'Importance']]
                for fi in rf['feature_importance'][:8]:
                    fi_table.append([fi['feature'][:25], str(fi['importance'])])
                t = Table(fi_table, colWidths=[3*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                    ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(t)

        # Best model forecast
        if 'best_model_forecast' in predictions:
            bf = predictions['best_model_forecast']
            elements.append(Paragraph("Best Model Forecast", self.styles['SubSection']))
            elements.append(Paragraph(
                f"The best performing model (<b>{bf['model']}</b> with R-squared of <b>{bf['r2_score']}</b>) "
                f"predicts the following future values for '{target}': "
                f"{', '.join([str(v) for v in bf['future_values']])}.",
                self.styles['BodyText2']
            ))

        # Prediction insights
        insights = pred_data.get('insights', [])
        if insights:
            elements.append(Paragraph("Prediction Insights", self.styles['SubSection']))
            for ins in insights:
                elements.append(Paragraph(f"* {ins}", self.styles['InsightText']))

        return elements

    def _build_features_section(self):
        elements = []
        elements.append(Paragraph("7. Feature Engineering Suggestions", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        feat_data = self.data.get('feature_suggestions', {})
        suggestions = feat_data.get('suggestions', [])

        elements.append(Paragraph(
            f"A total of <b>{feat_data.get('total_suggestions', 0)}</b> feature engineering suggestions "
            f"are provided across <b>{len(feat_data.get('categories', []))}</b> categories: "
            f"{', '.join(feat_data.get('categories', []))}. Feature engineering can significantly "
            f"improve model performance by creating more informative representations of the data.",
            self.styles['BodyText2']
        ))
        elements.append(Spacer(1, 0.1 * inch))

        for suggestion in suggestions[:15]:
            elements.append(Paragraph(
                f'<b>{suggestion["category"]}</b> - {suggestion["source_column"][:30]}',
                ParagraphStyle('feat_header', parent=self.styles['Normal'],
                              fontSize=10, textColor=self.SECONDARY, fontName='Helvetica-Bold',
                              spaceBefore=8, spaceAfter=3)
            ))
            for feat in suggestion['suggested_features'][:4]:
                elements.append(Paragraph(
                    f"  - <b>{feat['name'][:35]}</b>: {feat['description']} ({feat['type']})",
                    ParagraphStyle('feat_item', parent=self.styles['Normal'],
                                  fontSize=9, textColor=self.MEDIUM_TEXT, fontName='Helvetica',
                                  leftIndent=20, spaceAfter=2)
                ))

        return elements

    def _build_clustering_section(self):
        elements = []
        elements.append(Paragraph("8. Clustering Analysis", self.styles['SectionHeader']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY, spaceAfter=15))

        cluster_data = self.data.get('clustering', {})
        if 'error' in cluster_data:
            elements.append(Paragraph(cluster_data['error'], self.styles['BodyText2']))
            return elements

        n_clusters = cluster_data.get('n_clusters', 0)
        elements.append(Paragraph(
            f"K-Means clustering identified <b>{n_clusters}</b> natural groupings in the data. "
            f"This unsupervised analysis reveals hidden patterns and segments that may not be apparent "
            f"from individual variable analysis alone.",
            self.styles['BodyText2']
        ))
        elements.append(Spacer(1, 0.1 * inch))

        # Cluster sizes
        sizes = cluster_data.get('cluster_sizes', {})
        if sizes:
            elements.append(Paragraph("Cluster Sizes", self.styles['SubSection']))
            size_data = [['Cluster', 'Count']]
            for name, count in sizes.items():
                size_data.append([name, str(count)])
            t = Table(size_data, colWidths=[2*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.TABLE_ALT]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t)

        # PCA scatter plot
        pca_data = cluster_data.get('pca_coordinates', {})
        if pca_data and pca_data.get('x'):
            try:
                fig, ax = plt.subplots(figsize=(7, 5))
                x = pca_data['x']
                y = pca_data['y']
                labels = pca_data['labels']
                cluster_colors = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#7C3AED', '#EC4899', '#14B8A6', '#F97316']
                for label in set(labels):
                    mask = [l == label for l in labels]
                    cx = [x[i] for i in range(len(x)) if mask[i]]
                    cy = [y[i] for i in range(len(y)) if mask[i]]
                    ax.scatter(cx, cy, c=cluster_colors[label % len(cluster_colors)],
                             label=f'Cluster {label}', alpha=0.6, s=30)
                ax.set_xlabel('PCA Component 1', fontsize=9)
                ax.set_ylabel('PCA Component 2', fontsize=9)
                ax.set_title('PCA Cluster Visualization', fontsize=11)
                ax.legend(fontsize=8, loc='best')
                ax.tick_params(labelsize=8)

                chart_path = os.path.join(self.charts_dir, 'clustering.png')
                plt.tight_layout()
                plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
                plt.close()
                elements.append(Image(chart_path, width=5*inch, height=3.6*inch))
                elements.append(Spacer(1, 0.1 * inch))
            except Exception:
                pass

        # Cluster insights
        insights = cluster_data.get('insights', [])
        if insights:
            elements.append(Paragraph("Cluster Profiles", self.styles['SubSection']))
            for ins in insights:
                elements.append(Paragraph(f"* {ins}", self.styles['InsightText']))

        return elements

    def _cleanup_charts(self):
        """Remove temporary chart images."""
        try:
            for f in os.listdir(self.charts_dir):
                os.remove(os.path.join(self.charts_dir, f))
            os.rmdir(self.charts_dir)
        except Exception:
            pass

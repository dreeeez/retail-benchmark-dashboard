"""
Benchmark Dashboard - Gruppe 18
CSS Styles
"""

DASHBOARD_CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .main-header {
        text-align: center;
        padding: 25px 40px;
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(123, 44, 191, 0.1) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 16px;
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4ff, #7b2cbf, #00d4ff);
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2em;
        margin: 0;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .header-subtitle {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.85em;
        margin-top: 5px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .kpi-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: 150px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
    .kpi-title {
        font-size: 0.7em;
        color: #aaa;
        text-transform: uppercase;
        height: 35px;
        line-height: 1.2;
    }
    .kpi-value-rosenheim {
        font-size: 1.5em;
        font-weight: bold;
        color: #00d4ff;
        height: 50px;
        line-height: 50px;
    }
    .kpi-value-freiburg {
        font-size: 1.5em;
        font-weight: bold;
        color: #7b2cbf;
        height: 50px;
        line-height: 50px;
    }
    .kpi-comparison-positive {
        background: rgba(0, 255, 136, 0.2);
        color: #00ff88;
        padding: 4px 8px;
        border-radius: 15px;
        font-size: 0.75em;
        display: inline-block;
    }
    .kpi-comparison-negative {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        padding: 4px 8px;
        border-radius: 15px;
        font-size: 0.75em;
        display: inline-block;
    }
    .kpi-comparison-neutral {
        background: rgba(255, 255, 255, 0.1);
        color: #aaa;
        padding: 4px 8px;
        border-radius: 15px;
        font-size: 0.75em;
        display: inline-block;
    }
    .month-indicator {
        padding: 12px 24px 10px 24px;
        border-radius: 12px;
        display: block;
        width: 100%;
        max-width: 300px;
    }
    .month-text {
        font-weight: 700;
        font-size: 1.1em;
        letter-spacing: 0.5px;
        text-align: center;
        margin-bottom: 8px;
    }
    .month-progress-bar {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        height: 6px;
        width: 100%;
        overflow: hidden;
    }
    .month-progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease, background-color 0.3s ease;
    }
    .hover-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .hover-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }

    /* Chart Animationen */
    @keyframes chartSlideUp {
        0% {
            opacity: 0;
            transform: translateY(30px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes chartScaleIn {
        0% {
            opacity: 0;
            transform: scale(0.95);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    /* Plotly Chart Container Animation */
    div[data-testid="stPlotlyChart"] {
        animation: chartSlideUp 0.5s ease-out forwards;
        opacity: 0;
    }

    /* Gestaffelte Animation für Charts in Spalten */
    div[data-testid="stColumn"]:nth-child(1) div[data-testid="stPlotlyChart"] {
        animation-delay: 0s;
    }
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stPlotlyChart"] {
        animation-delay: 0.15s;
    }
    div[data-testid="stColumn"]:nth-child(3) div[data-testid="stPlotlyChart"] {
        animation-delay: 0.3s;
    }
    div[data-testid="stColumn"]:nth-child(4) div[data-testid="stPlotlyChart"] {
        animation-delay: 0.45s;
    }

    /* DataFrames Animation */
    div[data-testid="stDataFrame"] {
        animation: chartScaleIn 0.4s ease-out forwards;
        opacity: 0;
    }

    /* KPI Karten gestaffelte Animation */
    div[data-testid="stColumn"]:nth-child(1) .kpi-card {
        animation: chartSlideUp 0.4s ease-out 0.0s forwards;
    }
    div[data-testid="stColumn"]:nth-child(2) .kpi-card {
        animation: chartSlideUp 0.4s ease-out 0.05s forwards;
    }
    div[data-testid="stColumn"]:nth-child(3) .kpi-card {
        animation: chartSlideUp 0.4s ease-out 0.1s forwards;
    }
    div[data-testid="stColumn"]:nth-child(4) .kpi-card {
        animation: chartSlideUp 0.4s ease-out 0.15s forwards;
    }
    div[data-testid="stColumn"]:nth-child(5) .kpi-card {
        animation: chartSlideUp 0.4s ease-out 0.2s forwards;
    }
    div[data-testid="stColumn"]:nth-child(6) .kpi-card {
        animation: chartSlideUp 0.4s ease-out 0.25s forwards;
    }

    /* Subheader Animation */
    div[data-testid="stSubheader"] {
        animation: chartSlideUp 0.3s ease-out forwards;
    }

    /* Chart Info Tooltip */
    .chart-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }
    .chart-title {
        font-size: 1.1em;
        font-weight: 600;
        color: white;
        margin: 0;
    }
    .info-tooltip {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 50%;
        cursor: help;
        font-size: 11px;
        color: #aaa;
        transition: all 0.2s ease;
    }
    .info-tooltip:hover {
        background: rgba(0, 212, 255, 0.3);
        color: #00d4ff;
    }
    .info-tooltip .tooltip-text {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(30, 30, 50, 0.98);
        color: #ddd;
        padding: 12px 14px;
        border-radius: 8px;
        font-size: 12px;
        line-height: 1.5;
        width: 280px;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        z-index: 1000;
        transition: opacity 0.2s ease, visibility 0.2s ease;
    }
    .info-tooltip .tooltip-text::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border-width: 6px;
        border-style: solid;
        border-color: rgba(30, 30, 50, 0.98) transparent transparent transparent;
    }
    .info-tooltip:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    .tooltip-text strong {
        color: #00d4ff;
    }

    /* Make main block full width */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Tabs content full width */
    [data-testid="stTabs"] {
        width: 100% !important;
    }

    [data-testid="stTabContent"] {
        width: 100% !important;
    }

    /* ===== SIDEBAR STYLING ===== */
    /* Sidebar Background & Border */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 100%);
        border-right: 1px solid rgba(0, 212, 255, 0.2);
    }

    /* Sidebar Text Color */
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }

    /* Sidebar Divider */
    [data-testid="stSidebar"] hr {
        border-color: rgba(0, 212, 255, 0.2);
        margin: 1rem 0;
    }

    /* Sidebar Logout Button */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: rgba(255, 68, 68, 0.2);
        border: 1px solid rgba(255, 68, 68, 0.4);
        color: white;
    }

    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(255, 68, 68, 0.3);
        border-color: rgba(255, 68, 68, 0.6);
    }

    /* Sidebar Multiselect & Selectbox */
    [data-testid="stSidebar"] .stMultiSelect,
    [data-testid="stSidebar"] .stSelectbox {
        color: white;
    }
</style>
"""

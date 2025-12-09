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
        padding: 20px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        margin-bottom: 5px;
    }
    .main-header p {
        color: #aaa;
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
        background: linear-gradient(90deg, #00d4ff, #7b2cbf);
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        color: white;
        display: inline-block;
    }
    .hover-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .hover-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
</style>
"""

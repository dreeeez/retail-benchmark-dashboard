import json
import pyodbc
from pathlib import Path

def get_connection():
    # Config-Datei im Hauptverzeichnis (eine Ebene über src/)
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        cfg = json.load(f)

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['user']};"
        f"PWD={cfg['password']};"
        "Encrypt=no;"
    )

    return pyodbc.connect(conn_str)


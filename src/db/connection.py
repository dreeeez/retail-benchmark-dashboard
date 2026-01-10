"""
Benchmark Dashboard - Gruppe 18
Datenbankverbindung
"""

import json
import pyodbc
from pathlib import Path
from contextlib import contextmanager


def get_connection():
    """Erstellt Verbindung zur SQL Server Datenbank"""
    # Config-Datei im Hauptverzeichnis (eine Ebene über src/)
    config_path = Path(__file__).parent.parent.parent / "config.json"
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


@contextmanager
def db_connection():
    """Context Manager für sichere DB-Verbindungen.

    Garantiert automatisches Schließen auch bei Exceptions.

    Verwendung:
        with db_connection() as conn:
            df = pd.read_sql(query, conn)
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

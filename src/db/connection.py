"""
Benchmark Dashboard - Gruppe 18
Datenbankverbindung

Unterstützt:
- Lokale Entwicklung via config.json + pyodbc
- Streamlit Cloud via Session-Credentials + pymssql
"""

import json
from pathlib import Path
from contextlib import contextmanager

# Fixe DB-Konfiguration (Server + Database sind immer gleich)
DB_SERVER = "edu.hdm-server.eu"
DB_DATABASE = "ERPDEV"


def get_db_config():
    """Lädt DB-Konfiguration aus config.json oder Session-Credentials

    Returns:
        dict mit server, database, user, password
    """
    # 1. Versuche config.json (lokale Entwicklung)
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # 2. Fallback: Session-Credentials aus Login (Cloud Deployment)
    try:
        import streamlit as st
        if st.session_state.get('db_user') and st.session_state.get('db_password'):
            return {
                'server': DB_SERVER,
                'database': DB_DATABASE,
                'user': st.session_state.db_user,
                'password': st.session_state.db_password
            }
    except Exception:
        pass

    raise FileNotFoundError(
        "Keine DB-Konfiguration gefunden. "
        "Bitte einloggen oder config.json erstellen."
    )


def get_connection():
    """Erstellt Verbindung zur SQL Server Datenbank

    Verwendet pyodbc lokal (mit ODBC Driver) oder pymssql in der Cloud.
    """
    cfg = get_db_config()

    # Prüfe ob ODBC Driver verfügbar ist
    use_pyodbc = False
    try:
        import pyodbc
        # Prüfe ob der Driver tatsächlich existiert
        drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
        if drivers:
            use_pyodbc = True
    except Exception:
        pass

    if use_pyodbc:
        import pyodbc
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={cfg['server']};"
            f"DATABASE={cfg['database']};"
            f"UID={cfg['user']};"
            f"PWD={cfg['password']};"
            "Encrypt=no;"
        )
        return pyodbc.connect(conn_str)

    # Fallback: pymssql (Cloud ohne ODBC Driver)
    import pymssql
    return pymssql.connect(
        server=cfg['server'],
        user=cfg['user'],
        password=cfg['password'],
        database=cfg['database']
    )


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

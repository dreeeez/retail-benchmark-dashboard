import json
import pyodbc

def get_connection():
    with open("config.json") as f:
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

#   Test branch 
# if __name__ == "__main__":
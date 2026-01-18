"""
Benchmark Dashboard - Gruppe 18
User Authentication Module

Authentifizierung gegen T_USER Tabelle mit Security Level Check
"""

from src.db.connection import DB_SERVER, DB_DATABASE


def _get_auth_connection(username: str, password: str):
    """Erstellt DB-Verbindung für Authentifizierung

    Versucht pymssql zuerst (Cloud-kompatibel), dann pyodbc als Fallback.

    Returns:
        tuple: (connection, use_pyodbc_flag)

    Raises:
        Exception: Mit benutzerfreundlicher Fehlermeldung bei Login-Fehlern
    """
    pymssql_error = None

    # Versuche zuerst pymssql (funktioniert überall ohne ODBC Driver)
    try:
        import pymssql
        conn = pymssql.connect(
            server=DB_SERVER,
            user=username,
            password=password,
            database=DB_DATABASE
        )
        return conn, False
    except Exception as e:
        pymssql_error = e

    # Fallback: pyodbc (nur lokal mit ODBC Driver)
    try:
        import pyodbc
        # Prüfe ob ODBC Driver verfügbar ist
        if 'ODBC Driver 18 for SQL Server' in pyodbc.drivers():
            conn_str = (
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={DB_SERVER};"
                f"DATABASE={DB_DATABASE};"
                f"UID={username};"
                f"PWD={password};"
                "Encrypt=no;"
            )
            return pyodbc.connect(conn_str), True
    except Exception:
        pass

    # Beide Methoden fehlgeschlagen - benutzerfreundliche Fehlermeldung
    error_msg = str(pymssql_error).lower() if pymssql_error else ""

    # Netzwerk-Fehler erkennen (Server nicht erreichbar)
    network_keywords = ["timeout", "unreachable", "refused", "reset", "timed out"]
    if any(kw in error_msg for kw in network_keywords):
        raise Exception("Verbindung zum Server fehlgeschlagen. Bitte später erneut versuchen.")

    # Alle anderen Fehler = Anmeldedaten falsch oder keine DB-Berechtigung
    raise Exception("Ungültige Anmeldedaten oder keine Zugriffsberechtigung")


def authenticate_user(username: str, password: str) -> dict:
    """Authentifiziert einen User gegen T_USER und prüft Security Level

    Args:
        username: Benutzername (= DB User)
        password: Passwort (= DB Password)

    Returns:
        dict mit:
        - authenticated: bool (True wenn erfolgreich)
        - security_level: int (Security Level des Users, None wenn nicht auth)
        - message: str (Fehlermeldung oder Erfolg)
    """
    try:
        conn, is_pyodbc = _get_auth_connection(username, password)
        try:
            cursor = conn.cursor()

            # Prüfe ob User mit Credentials existiert
            # pyodbc verwendet ?, pymssql verwendet %s
            if is_pyodbc:
                cursor.execute("""
                    SELECT USERNAME, USERPASS, SECURITYLEVEL
                    FROM dbo.T_USER
                    WHERE USERNAME = ? AND USERPASS = ?
                """, (username, password))
            else:
                cursor.execute("""
                    SELECT USERNAME, USERPASS, SECURITYLEVEL
                    FROM dbo.T_USER
                    WHERE USERNAME = %s AND USERPASS = %s
                """, (username, password))

            user = cursor.fetchone()

            if not user:
                return {
                    'authenticated': False,
                    'security_level': None,
                    'message': 'Ungültige Anmeldedaten'
                }

            # Security Level aus der Abfrage holen
            security_level = user[2]

            # Prüfe ob Level 3 oder 4
            if security_level not in [3, 4]:
                return {
                    'authenticated': False,
                    'security_level': security_level,
                    'message': f'Keine Berechtigung (Security Level {security_level}). Level 3 oder 4 erforderlich.'
                }

            cursor.close()

            return {
                'authenticated': True,
                'security_level': security_level,
                'message': 'Anmeldung erfolgreich',
                'username': username
            }
        finally:
            conn.close()

    except Exception as e:
        # Debug: Zeige den vollen Fehler
        return {
            'authenticated': False,
            'security_level': None,
            'message': f'DB-Fehler: {str(e)}'
        }


def dev_bypass_login() -> dict:
    """Dev-Bypass für schnelles Testen (SPÄTER ENTFERNEN!)

    Returns:
        dict mit authenticated=True und Security Level 4
    """
    return {
        'authenticated': True,
        'security_level': 4,
        'message': 'DEV MODE - Bypass aktiv',
        'username': 'dev_user'
    }

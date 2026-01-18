"""
Benchmark Dashboard - Gruppe 18
User Authentication Module

Authentifizierung gegen T_USER Tabelle mit Security Level Check
"""

import pyodbc
from src.db.connection import DB_SERVER, DB_DATABASE


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
        # Direkte Verbindung mit Login-Credentials
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={username};"
            f"PWD={password};"
            "Encrypt=no;"
        )
        conn = pyodbc.connect(conn_str)
        try:
            cursor = conn.cursor()

            # Prüfe ob User mit Credentials existiert
            cursor.execute("""
                SELECT USERNAME, USERPASS, SECURITYLEVEL
                FROM dbo.T_USER
                WHERE USERNAME = ? AND USERPASS = ?
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

    except pyodbc.InterfaceError:
        return {
            'authenticated': False,
            'security_level': None,
            'message': 'Datenbankverbindung fehlgeschlagen. Bitte Credentials prüfen.'
        }
    except Exception as e:
        return {
            'authenticated': False,
            'security_level': None,
            'message': f'Fehler bei der Anmeldung: {str(e)}'
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

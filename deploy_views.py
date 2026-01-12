"""
Deployed die Views aus CREATE_VIEWS.sql in die Datenbank
"""
import sys
import os
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

from src.db.connection import get_connection

print("=" * 70)
print("DEPLOY SQL VIEWS")
print("=" * 70)

try:
    # SQL-Datei einlesen
    with open('sql/CREATE_VIEWS.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Views einzeln deployen (aufgeteilt bei GO)
    statements = [s.strip() for s in sql_script.split('GO') if s.strip() and not s.strip().startswith('--')]

    print(f"\nGefunden: {len(statements)} SQL-Statements\n")

    conn = get_connection()
    cursor = conn.cursor()

    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        try:
            # Finde View-Namen für Ausgabe
            view_name = "Unknown"
            if 'CREATE OR ALTER VIEW' in statement:
                view_name = statement.split('CREATE OR ALTER VIEW')[1].split('(')[0].strip()

            print(f"[{i}/{len(statements)}] Deploying: {view_name}")

            cursor.execute(statement)
            conn.commit()
            success_count += 1
            print(f"   ✅ Success!")

        except Exception as e:
            error_count += 1
            print(f"   ❌ Error: {str(e)[:200]}")
            # Continue with next statement

    conn.close()

    print("\n" + "=" * 70)
    print(f"DEPLOYMENT ABGESCHLOSSEN")
    print(f"✅ Erfolgreich: {success_count}")
    print(f"❌ Fehler: {error_count}")
    print("=" * 70)

    if error_count == 0:
        print("\n🎉 ALLE VIEWS ERFOLGREICH DEPLOYED!")
        print("\nJetzt das Dashboard neu starten:")
        print("   → Im Browser F5 drücken oder 'Rerun' klicken")
    else:
        print("\n⚠️ Einige Views konnten nicht deployed werden.")
        print("   Prüfe die Fehlermeldungen oben.")

except Exception as e:
    print(f"❌ FEHLER: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

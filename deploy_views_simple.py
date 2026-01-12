"""
Deployed die Views - Einfache Version
"""
import sys
import os
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

import pyodbc
import json

print("=" * 70)
print("DEPLOY SQL VIEWS (SIMPLE)")
print("=" * 70)

try:
    # Config laden
    with open('config.json', 'r') as f:
        config = json.load(f)

    # SQL-Datei einlesen
    with open('sql/CREATE_VIEWS.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Connection string bauen
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};"
        f"PWD={config['password']};"
        f"Encrypt=no"
    )

    print("\nVerbinde mit Datenbank...")
    conn = pyodbc.connect(conn_str)

    # Batches ausführen (getrennt bei GO)
    batches = [b.strip() for b in sql_script.split('\nGO') if b.strip() and 'CREATE' in b]

    print(f"Gefunden: {len(batches)} View-Definitionen\n")

    cursor = conn.cursor()
    success = 0
    errors = 0

    for i, batch in enumerate(batches, 1):
        try:
            # View-Namen extrahieren
            if 'CREATE OR ALTER VIEW' in batch:
                view_name = batch.split('CREATE OR ALTER VIEW')[1].split()[0].strip()
                print(f"[{i}/{len(batches)}] {view_name}... ", end='')

                cursor.execute(batch)
                conn.commit()
                print("✅")
                success += 1
            else:
                print(f"[{i}/{len(batches)}] Überspringe (kein VIEW)")

        except Exception as e:
            errors += 1
            print(f"❌")
            print(f"   Fehler: {str(e)[:150]}")

    conn.close()

    print("\n" + "=" * 70)
    print(f"✅ Erfolgreich: {success}")
    print(f"❌ Fehler: {errors}")
    print("=" * 70)

    if errors == 0:
        print("\n🎉 ALLE VIEWS ERFOLGREICH DEPLOYED!")
        print("\nNächster Schritt:")
        print("   1. Im Browser zu http://localhost:8502")
        print("   2. F5 drücken oder 'Rerun' klicken")
        print("   3. Dashboard sollte jetzt Daten anzeigen!")

except Exception as e:
    print(f"\n❌ FEHLER: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

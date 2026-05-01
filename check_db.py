import sqlite3
import os

# Check the database
db_path = os.path.join("src", "Database", "crm.db")
print(f"Checking database at: {db_path}")
print(f"Absolute path: {os.path.abspath(db_path)}")
print(f"Exists: {os.path.exists(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"✓ Connected successfully")
    print(f"✓ Tables found: {[t[0] for t in tables]}")
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")

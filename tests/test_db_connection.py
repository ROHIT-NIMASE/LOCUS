
from database.database import get_connection

try:
    conn = get_connection()
    print("SUCCESS: Connected to MySQL!")
    print("Database:", conn.database)

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")

    print("\nTables in library_hotdesking:")
    for table in cursor.fetchall():
        print("-", table[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("CONNECTION FAILED:", e)

import sqlite3
db = sqlite3.connect('gpms.db')
result = db.execute("SELECT id, name, description FROM document_types WHERE name LIKE '%Viva%'").fetchone()
if result:
    print(f"ID: {result[0]}")
    print(f"Name: {result[1]}")
    print(f"Description: {result[2]}")
else:
    print("Not found")
db.close()

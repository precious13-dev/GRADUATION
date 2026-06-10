import sqlite3

db = sqlite3.connect('gpms.db')

# Check if there's a matching clearance item
result = db.execute("SELECT id, title, description FROM clearance_items WHERE title LIKE '%Viva%' OR title LIKE '%Dissertation%'").fetchall()

print(f"Found {len(result)} matching clearance items:")
for row in result:
    print(f"  ID: {row[0]}, Title: {row[1]}")
    print(f"    Description: {row[2]}")

db.close()

import sqlite3

conn = sqlite3.connect('gpms.db')
c = conn.cursor()

# Update clearance_items
c.execute("UPDATE clearance_items SET title = 'Academics Clearance', office_role = 'academics' WHERE office_role = 'registry'")

# Update document_types
c.execute("UPDATE document_types SET reviewing_role = 'academics' WHERE reviewing_role = 'registry'")

conn.commit()

# Verify the changes
c.row_factory = sqlite3.Row
items = c.execute('SELECT * FROM clearance_items').fetchall()
print("Clearance Items:")
for item in items:
    print(f"  {dict(item)}")

docs = c.execute('SELECT * FROM document_types').fetchall()
print("\nDocument Types:")
for doc in docs:
    print(f"  {dict(doc)}")

conn.close()
print("\nDatabase updated successfully!")

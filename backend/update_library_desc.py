import sqlite3

db = sqlite3.connect('gpms.db')

# Find the Library Clearance Certificate
result = db.execute("SELECT id, name, description FROM document_types WHERE name LIKE '%Library%'").fetchone()

if result:
    print("Current record:")
    print(f"ID: {result[0]}")
    print(f"Name: {result[1]}")
    print(f"Description: {result[2]}")
    
    # Update the description
    new_description = "Return all borrowed books and pay any outstanding library fines. Return your student ID card to the library."
    
    db.execute(
        "UPDATE document_types SET description=? WHERE id=?",
        (new_description, result[0])
    )
    db.commit()
    
    # Verify
    updated = db.execute("SELECT id, name, description FROM document_types WHERE id=?", (result[0],)).fetchone()
    print("\nUpdated record:")
    print(f"ID: {updated[0]}")
    print(f"Name: {updated[1]}")
    print(f"Description: {updated[2]}")
else:
    print("Library document type not found")

db.close()

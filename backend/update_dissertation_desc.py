import sqlite3

db = sqlite3.connect('gpms.db')

# Find the Dissertation Defence Record
result = db.execute("SELECT id, name, description FROM document_types WHERE name LIKE '%Dissertation%'").fetchone()

if result:
    print("Current record:")
    print(f"ID: {result[0]}")
    print(f"Name: {result[1]}")
    print(f"Description: {result[2]}")
    
    # Update the description
    new_description = "Official record of your dissertation defence examination outcome. By this stage, you should have already submitted your dissertation on Turnitin through the library and received your similarity report via email — attach this report together with your dissertation defence record."
    
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
    print("Dissertation Defence Record not found")

db.close()

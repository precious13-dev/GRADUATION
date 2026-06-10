import sqlite3

db = sqlite3.connect('gpms.db')

new_name = "Dissertation Defence Record"
new_description = "Official record of your dissertation defence examination outcome. A Turnitin similarity report must be attached within the dissertation."

db.execute(
    "UPDATE document_types SET name=?, description=? WHERE id=6",
    (new_name, new_description)
)
db.commit()

# Verify
result = db.execute("SELECT id, name, description FROM document_types WHERE id=6").fetchone()
print("Updated record:")
print(f"ID: {result[0]}")
print(f"Name: {result[1]}")
print(f"Description: {result[2]}")

db.close()

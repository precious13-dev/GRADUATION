import sqlite3

conn = sqlite3.connect('gpms.db')
c = conn.cursor()
c.row_factory = sqlite3.Row

# Check current assignments
docs = c.execute('SELECT id, name, reviewing_role FROM document_types').fetchall()
print('Current Document Type Assignments:')
print('=' * 70)
for doc in docs:
    print(f'{doc["id"]}. {doc["name"]} -> {doc["reviewing_role"]}')

# Consolidate: Move NRC to department since it's an identity document, not academics
# Keep Grade 12 and Academic Transcript as academics
print('\n\nUpdating...')
print('Moving NRC (National Registration Card) from academics to department')
c.execute("UPDATE document_types SET reviewing_role = 'department' WHERE name LIKE '%NRC%'")
conn.commit()

# Verify changes
docs = c.execute('SELECT id, name, reviewing_role FROM document_types ORDER BY reviewing_role').fetchall()
print('\n\nUpdated Document Type Assignments:')
print('=' * 70)

current_role = None
for doc in docs:
    if doc["reviewing_role"] != current_role:
        current_role = doc["reviewing_role"]
        print(f'\n{current_role.upper()}:')
    print(f'  • {doc["name"]}')

conn.close()
print('\nDatabase updated successfully!')

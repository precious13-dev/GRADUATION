import sqlite3

conn = sqlite3.connect('gpms.db')
c = conn.cursor()
c.row_factory = sqlite3.Row

items = c.execute('SELECT * FROM clearance_items').fetchall()
print('Clearance Items in Database:')
print('=' * 60)
for item in items:
    print(f'{item["id"]}. {item["title"]} ({item["office_role"]})')

conn.close()

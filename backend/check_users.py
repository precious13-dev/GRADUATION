import sqlite3

db = sqlite3.connect('gpms.db')
users = db.execute("SELECT id, name, role FROM users ORDER BY id").fetchall()
print(f"Total users: {len(users)}")
for user in users:
    print(f"  ID: {user[0]}, Name: {user[1]}, Role: {user[2]}")
db.close()

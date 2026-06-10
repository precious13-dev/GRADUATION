import sqlite3

conn = sqlite3.connect('gpms.db')
c = conn.cursor()

# Search for the user
c.row_factory = sqlite3.Row
user = c.execute('SELECT id, name, email, role FROM users WHERE LOWER(name) = LOWER(?)', ('sepo mwila',)).fetchone()

if user:
    user_id = user['id']
    print(f"User found: {user['name']} ({user['email']}) - Role: {user['role']}")
    
    # Delete the user
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    
    print(f"✓ User '{user['name']}' has been successfully removed from the database!")
    
    # Show remaining users
    c.row_factory = sqlite3.Row
    remaining = c.execute('SELECT id, name, email, role FROM users ORDER BY id').fetchall()
    print(f"\nRemaining users ({len(remaining)}):")
    for u in remaining:
        print(f"  - {u['name']} ({u['email']}) - Role: {u['role']}")
else:
    print("User 'sepo mwila' not found in the database!")

conn.close()

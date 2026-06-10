import sqlite3

conn = sqlite3.connect('gpms.db')
c = conn.cursor()

# Get admin user info before deletion
c.row_factory = sqlite3.Row
admin = c.execute('SELECT id, name, email, role FROM users WHERE role = "admin"').fetchone()

if admin:
    print(f"Admin user found: {dict(admin)}")
    admin_id = admin['id']
    
    # Get count of non-admin users
    c.row_factory = None
    non_admin_count = c.execute('SELECT COUNT(*) FROM users WHERE role != "admin"').fetchone()[0]
    print(f"\nRemoving {non_admin_count} non-admin users...")
    
    # Delete all non-admin users
    c.execute('DELETE FROM users WHERE role != "admin"')
    conn.commit()
    
    # Verify
    remaining = c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    c.row_factory = sqlite3.Row
    remaining_users = c.execute('SELECT id, name, email, role FROM users').fetchall()
    
    print(f"✓ Deletion complete!")
    print(f"Remaining users: {remaining}")
    print(f"Users in database:")
    for user in remaining_users:
        print(f"  - {user['name']} ({user['email']}) - Role: {user['role']}")
else:
    print("No admin user found in the database!")

conn.close()

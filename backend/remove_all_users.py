#!/usr/bin/env python3
"""
Delete all users except admin
"""
import sqlite3

DB_PATH = 'gpms.db'

conn = sqlite3.connect(DB_PATH)

# Get admin user
admin = conn.execute("SELECT id FROM users WHERE role='admin'").fetchone()

if admin:
    admin_id = admin[0]
    # Delete all non-admin users
    conn.execute("DELETE FROM users WHERE id != ?", (admin_id,))
    conn.commit()
    
    # Show what's left
    remaining = conn.execute("SELECT id, name, role FROM users").fetchall()
    print("Remaining users:")
    for user in remaining:
        print(f"  ID: {user[0]}, Name: {user[1]}, Role: {user[2]}")
    
    print("\nAll other users have been deleted.")
else:
    print("No admin user found!")

conn.close()

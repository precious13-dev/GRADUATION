import sqlite3

conn = sqlite3.connect('gpms.db')
c = conn.cursor()
c.row_factory = sqlite3.Row

# Find a student user
students = c.execute('SELECT id, name, email, role FROM users WHERE role = "student" LIMIT 1').fetchall()
if students:
    s = students[0]
    print(f'Found student: {s["name"]} ({s["email"]})')
    print(f'Note: You will need the password for this account')
else:
    print('No students found in database')

conn.close()

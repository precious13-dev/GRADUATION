import sqlite3
import bcrypt

conn = sqlite3.connect('gpms.db')
c = conn.cursor()

# Create a test student if it doesn't exist
existing = c.execute("SELECT id FROM users WHERE email = 'test@student.com'").fetchone()
if not existing:
    hashed = bcrypt.hashpw(b'Test@1234', bcrypt.gensalt()).decode()
    c.execute(
        "INSERT INTO users (student_number, name, email, password, role) VALUES (?,?,?,?,?)",
        ('999999', 'Test Student', 'test@student.com', hashed, 'student')
    )
    user_id = c.lastrowid
    
    # Add student profile
    c.execute(
        "INSERT INTO student_profiles (user_id, program, year_of_study) VALUES (?,?,?)",
        (user_id, 'Test Program', 'Final Year')
    )
    conn.commit()
    print(f'Created test student:')
    print(f'  Email: test@student.com')
    print(f'  Password: Test@1234')
else:
    print('Test student already exists')
    print(f'  Email: test@student.com')
    print(f'  Password: Test@1234')

conn.close()

from database import get_db, init_db

# Initialize DB
init_db()

# Get a student
db = get_db()
student = db.execute('SELECT * FROM users WHERE role="student" LIMIT 1').fetchone()
if student:
    print('Student found:', dict(student))
    # Check student's documents
    docs = db.execute('SELECT COUNT(*) as cnt FROM student_documents WHERE student_id=?', (student['id'],)).fetchone()
    print('Documents count:', docs['cnt'])
    # Get document types
    types = db.execute('SELECT COUNT(*) as cnt FROM document_types').fetchone()
    print('Document types:', types['cnt'])
else:
    print('No student found')
db.close()

import sqlite3

conn = sqlite3.connect('gpms.db')
conn.row_factory = sqlite3.Row

# Get all documents
print("ALL STUDENT DOCUMENTS:")
print("-" * 80)
docs = conn.execute('''
    SELECT sd.id, sd.student_id, sd.status, sd.rejection_reason, sd.reviewed_by, sd.reviewed_at,
           dt.reviewing_role, dt.name, u.name as student_name, r.name as reviewer_name
    FROM student_documents sd
    JOIN document_types dt ON dt.id=sd.document_type_id
    JOIN users u ON u.id=sd.student_id
    LEFT JOIN users r ON r.id=sd.reviewed_by
    ORDER BY sd.id
''').fetchall()

for doc in docs:
    print(f"ID {doc['id']:2} | {doc['student_name']:<20} | {doc['name']:<25} | Office: {doc['reviewing_role']:<12} | Status: {doc['status']:<10}", end="")
    if doc['reviewer_name']:
        print(f" | Reviewer: {doc['reviewer_name']}", end="")
    if doc['rejection_reason']:
        print(f" | Rejected: {doc['rejection_reason']}", end="")
    print()

print("\n" + "="*80)
print("CLEARANCE REQUESTS (for comparison):")
print("-" * 80)

creq = conn.execute('''
    SELECT cr.id, cr.status, cr.reviewed_at, u.name as student_name, ci.title, r.name as reviewer_name
    FROM clearance_requests cr
    JOIN users u ON u.id=cr.student_id
    JOIN clearance_items ci ON ci.id=cr.clearance_item_id
    LEFT JOIN users r ON r.id=cr.reviewed_by
    ORDER BY cr.id
''').fetchall()

if creq:
    for req in creq:
        print(f"ID {req['id']:2} | {req['student_name']:<20} | {req['title']:<30} | Status: {req['status']:<10} | Reviewed by: {req['reviewer_name']}")
else:
    print("(No clearance requests)")

conn.close()

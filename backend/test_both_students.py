#!/usr/bin/env python3
"""
Test /api/documents/my with both uploaded and non-uploaded students
"""
import sqlite3

DB_PATH = 'gpms.db'

def test_both_students():
    print("=" * 80)
    print("TESTING: /api/documents/my with multiple students")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get all students
    students = conn.execute(
        "SELECT id, name, student_number FROM users WHERE role='student' ORDER BY name LIMIT 2"
    ).fetchall()
    
    for student in students:
        student_id = student['id']
        student_name = student['name']
        
        print(f"\n{'='*80}")
        print(f"STUDENT: {student_name} ({student['student_number']})")
        print(f"{'='*80}")
        
        # Get document types
        doc_types = conn.execute(
            "SELECT id, name, reviewing_role FROM document_types ORDER BY sort_order"
        ).fetchall()
        
        total_uploaded = 0
        total_approved = 0
        
        print(f"\n{'-'*80}")
        print("DOCUMENTS")
        print(f"{'-'*80}")
        
        for doc_type in doc_types:
            # Check if uploaded
            student_doc = conn.execute(
                "SELECT id, status FROM student_documents WHERE student_id=? AND document_type_id=?",
                (student_id, doc_type['id'])
            ).fetchone()
            
            # Determine status
            if not student_doc:
                status = 'not_uploaded'
                uploaded_text = "❌ Not Uploaded"
            else:
                total_uploaded += 1
                # Check clearance approval
                clearance = conn.execute("""
                    SELECT cr.status FROM clearance_requests cr
                    JOIN clearance_items ci ON ci.id=cr.clearance_item_id
                    WHERE cr.student_id=? AND ci.office_role=?
                """, (student_id, doc_type['reviewing_role'])).fetchone()
                
                if student_doc['status']:
                    status = student_doc['status']
                elif clearance and clearance['status'] == 'approved':
                    status = 'approved'
                else:
                    status = 'pending'
                
                if status == 'approved':
                    total_approved += 1
                    uploaded_text = "✅ Approved"
                elif status == 'rejected':
                    uploaded_text = "❌ Rejected"
                else:
                    uploaded_text = "⏳ Pending Review"
            
            print(f"  {doc_type['name']:<35} | {doc_type['reviewing_role']:<12} | {uploaded_text}")
        
        total_required = len(doc_types)
        progress = round((total_approved / total_required) * 100) if total_required > 0 else 0
        
        print(f"\n  Summary:")
        print(f"    Total Required: {total_required}")
        print(f"    Total Uploaded: {total_uploaded}")
        print(f"    Total Approved: {total_approved}")
        print(f"    Progress: {progress}%")
    
    conn.close()
    print(f"\n{'='*80}")

if __name__ == '__main__':
    test_both_students()

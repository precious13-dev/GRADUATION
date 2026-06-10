#!/usr/bin/env python3
"""
Test that /api/documents/my now returns clearance-based status
"""
import sqlite3

DB_PATH = 'gpms.db'

def test_documents_my():
    print("=" * 80)
    print("TESTING: /api/documents/my endpoint (Clearance-based status)")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get a student
    student = conn.execute(
        "SELECT id, name, student_number FROM users WHERE role='student' LIMIT 1"
    ).fetchone()
    
    if not student:
        print("✗ No student found")
        conn.close()
        return
    
    student_id = student['id']
    print(f"\n✓ Testing with student: {student['name']} ({student['student_number']})")
    
    # Simulate what /api/documents/my returns
    print(f"\n{'-'*80}")
    print("DOCUMENTS LIST (from /api/documents/my)")
    print(f"{'-'*80}")
    
    clearance_items = conn.execute(
        "SELECT * FROM clearance_items WHERE is_active=1 ORDER BY sort_order"
    ).fetchall()
    
    documents = []
    total_approved = 0
    
    for item in clearance_items:
        clearance = conn.execute("""
            SELECT cr.status, cr.remarks, u.name AS reviewed_by_name
            FROM clearance_requests cr
            LEFT JOIN users u ON u.id=cr.reviewed_by
            WHERE cr.clearance_item_id=? AND cr.student_id=?
        """, (item['id'], student_id)).fetchone()
        
        status = clearance['status'] if clearance else None
        
        doc_entry = {
            'type_name': item['title'],
            'reviewing_role': item['office_role'],
            'status': status,
        }
        documents.append(doc_entry)
        
        if status == 'approved':
            total_approved += 1
        
        status_label = status if status else 'not_approved'
        print(f"  {item['title']:<35} | {item['office_role']:<12} | {status_label:<10}")
    
    total_required = len(clearance_items)
    progress_percent = round((total_approved / total_required) * 100) if total_required > 0 else 0
    
    print(f"\n  Summary:")
    print(f"    Total Required: {total_required}")
    print(f"    Total Approved: {total_approved}")
    print(f"    Progress: {progress_percent}%")
    
    print(f"\n{'-'*80}")
    print("EXPECTED STUDENT VIEW")
    print(f"{'-'*80}")
    
    for doc in documents:
        if doc['status'] == 'approved':
            print(f"  ✅ {doc['type_name']:<35} | {doc['reviewing_role']:<12} | APPROVED")
        elif doc['status'] == 'rejected':
            print(f"  ❌ {doc['type_name']:<35} | {doc['reviewing_role']:<12} | REJECTED")
        else:
            print(f"  ⏳ {doc['type_name']:<35} | {doc['reviewing_role']:<12} | PENDING REVIEW")
    
    conn.close()
    print("=" * 80)

if __name__ == '__main__':
    test_documents_my()

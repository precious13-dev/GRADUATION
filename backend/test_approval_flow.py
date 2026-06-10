#!/usr/bin/env python3
"""
Test the document approval flow to confirm status updates work
"""
import sqlite3
import datetime

DB_PATH = 'gpms.db'

def test_document_approval():
    print("=" * 80)
    print("TESTING DOCUMENT APPROVAL FLOW")
    print("=" * 80)
    
    # Get a pending document
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    pending_doc = conn.execute("""
        SELECT sd.id, sd.student_id, sd.status, dt.name, dt.reviewing_role
        FROM student_documents sd
        JOIN document_types dt ON dt.id=sd.document_type_id
        WHERE sd.status='pending'
        LIMIT 1
    """).fetchone()
    
    if not pending_doc:
        print("✗ No pending documents found")
        conn.close()
        return
    
    doc_id = pending_doc['id']
    student_id = pending_doc['student_id']
    
    print(f"\n✓ Found pending document:")
    print(f"  ID: {doc_id}")
    print(f"  Type: {pending_doc['name']}")
    print(f"  Role: {pending_doc['reviewing_role']}")
    print(f"  Student ID: {student_id}")
    
    # Simulate approval (what the backend does)
    print(f"\n→ Simulating approval...")
    reviewer_id = 2  # KENNY MWANZA
    
    conn.execute("""
        UPDATE student_documents 
        SET status=?, reviewed_by=?, reviewed_at=?, updated_at=?
        WHERE id=?
    """, ('approved', reviewer_id, datetime.datetime.now(), datetime.datetime.now(), doc_id))
    
    conn.commit()
    print("  ✓ Commit successful")
    
    # Verify with separate connection (what the debug code does)
    conn_verify = sqlite3.connect(DB_PATH)
    conn_verify.row_factory = sqlite3.Row
    
    verify_doc = conn_verify.execute("""
        SELECT id, status, reviewed_by, reviewed_at FROM student_documents WHERE id=?
    """, (doc_id,)).fetchone()
    
    print(f"\n✓ Verification query (separate connection):")
    if verify_doc:
        print(f"  Status: {verify_doc['status']}")
        print(f"  Reviewed by: {verify_doc['reviewed_by']}")
        print(f"  Reviewed at: {verify_doc['reviewed_at']}")
        
        if verify_doc['status'] == 'approved':
            print("\n✅ SUCCESS: Document approval persisted correctly!")
        else:
            print(f"\n❌ FAIL: Expected 'approved' but got '{verify_doc['status']}'")
    else:
        print(f"  ❌ Document {doc_id} not found!")
    
    conn_verify.close()
    conn.close()
    print("=" * 80)

if __name__ == '__main__':
    test_document_approval()

#!/usr/bin/env python3
"""
Test script to verify document approval status persistence
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'gpms.db')

def check_document_status(doc_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get document status
    doc = conn.execute("""
        SELECT sd.id, sd.student_id, sd.status, sd.reviewed_by, sd.reviewed_at,
               dt.name AS type_name, dt.reviewing_role, u.name AS student_name
        FROM student_documents sd
        JOIN document_types dt ON dt.id=sd.document_type_id
        JOIN users u ON u.id=sd.student_id
        WHERE sd.id=?
    """, (doc_id,)).fetchone()
    
    if doc:
        print(f"\n✓ Document {doc_id} found:")
        print(f"  Student: {doc['student_name']} (ID: {doc['student_id']})")
        print(f"  Type: {doc['type_name']}")
        print(f"  Reviewing Role: {doc['reviewing_role']}")
        print(f"  Status: {doc['status']}")
        print(f"  Reviewed By: {doc['reviewed_by']}")
        print(f"  Reviewed At: {doc['reviewed_at']}")
    else:
        print(f"✗ Document {doc_id} not found")
    
    conn.close()

def list_all_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    docs = conn.execute("""
        SELECT sd.id, sd.student_id, sd.status,
               dt.name AS type_name, dt.reviewing_role, u.name AS student_name
        FROM student_documents sd
        JOIN document_types dt ON dt.id=sd.document_type_id
        JOIN users u ON u.id=sd.student_id
        ORDER BY sd.id
    """).fetchall()
    
    if not docs:
        print("\n✗ No documents found")
        return
    
    print(f"\n✓ Found {len(docs)} documents:")
    print(f"{'ID':<4} {'Student':<20} {'Type':<20} {'Office':<12} {'Status':<10}")
    print("-" * 70)
    
    for doc in docs:
        print(f"{doc['id']:<4} {doc['student_name']:<20} {doc['type_name']:<20} {doc['reviewing_role']:<12} {doc['status']:<10}")
    
    # Count by status
    print("\nStatus Summary:")
    by_status = {}
    for doc in docs:
        status = doc['status']
        by_status[status] = by_status.get(status, 0) + 1
    
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")
    
    conn.close()

if __name__ == '__main__':
    print("=" * 70)
    print("Document Status Check")
    print("=" * 70)
    
    list_all_documents()
    
    # Check specific document if provided
    import sys
    if len(sys.argv) > 1:
        try:
            doc_id = int(sys.argv[1])
            check_document_status(doc_id)
        except ValueError:
            print(f"\nInvalid document ID: {sys.argv[1]}")
    
    print("\n" + "=" * 70)

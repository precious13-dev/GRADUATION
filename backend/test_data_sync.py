#!/usr/bin/env python3
"""
Verify that both clearance checklist and department approval status read from same source
"""
import sqlite3

DB_PATH = 'gpms.db'

def test_data_sync():
    print("=" * 80)
    print("TESTING: Clearance Checklist vs Department Approval Status Sync")
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
    
    # ─── Source 1: Clearance Checklist (from dashboard endpoint) ───────────────
    print(f"\n{'-'*80}")
    print("SOURCE 1: CLEARANCE CHECKLIST (clearance_requests table)")
    print(f"{'-'*80}")
    
    checklist = conn.execute("""
        SELECT ci.title, ci.office_role,
               cr.status, u.name AS reviewed_by_name
        FROM clearance_items ci
        LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
        LEFT JOIN users u ON u.id=cr.reviewed_by
        WHERE ci.is_active=1
        ORDER BY ci.sort_order
    """, (student_id,)).fetchall()
    
    checklist_summary = {'approved': 0, 'rejected': 0, 'pending': 0}
    for item in checklist:
        status = item['status'] or 'pending'
        checklist_summary[status] += 1
        print(f"  {item['title']:<35} | {item['office_role']:<12} | {status:<10}", end="")
        if item['reviewed_by_name']:
            print(f" | {item['reviewed_by_name']}")
        else:
            print()
    
    print(f"\n  Summary: Approved={checklist_summary['approved']}, Rejected={checklist_summary['rejected']}, Pending={checklist_summary['pending']}")
    
    # ─── Source 2: Department Approval Status (from documents/progress endpoint) ───────
    print(f"\n{'-'*80}")
    print("SOURCE 2: DEPARTMENT APPROVAL STATUS (department_statuses)")
    print(f"{'-'*80}")
    
    dept_stats = conn.execute("""
        SELECT ci.office_role AS role, ci.title AS label,
               COUNT(ci.id) AS total,
               SUM(CASE WHEN cr.status='approved' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN cr.status='rejected' THEN 1 ELSE 0 END) AS rejected
        FROM clearance_items ci
        LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
        WHERE ci.is_active=1
        GROUP BY ci.office_role, ci.title
    """, (student_id,)).fetchall()
    
    dept_summary = {'approved': 0, 'rejected': 0, 'pending': 0}
    for ds in dept_stats:
        total = ds['total'] or 1
        approved = ds['approved'] or 0
        rejected = ds['rejected'] or 0
        pending = total - approved - rejected
        
        dept_summary['approved'] += approved
        dept_summary['rejected'] += rejected
        dept_summary['pending'] += pending
        
        print(f"  {ds['label']:<35} | {approved}/{total} approved | {rejected} rejected | {pending} pending")
    
    print(f"\n  Summary: Approved={dept_summary['approved']}, Rejected={dept_summary['rejected']}, Pending={dept_summary['pending']}")
    
    # ─── Verification ───────────────────────────────────────────────────────────
    print(f"\n{'-'*80}")
    print("VERIFICATION")
    print(f"{'-'*80}")
    
    if checklist_summary == dept_summary:
        print("✅ SUCCESS: Both sources report IDENTICAL stats!")
        print(f"   Approved: {checklist_summary['approved']}")
        print(f"   Rejected: {checklist_summary['rejected']}")
        print(f"   Pending:  {checklist_summary['pending']}")
    else:
        print("❌ MISMATCH:")
        print(f"   Checklist: {checklist_summary}")
        print(f"   Dept:      {dept_summary}")
    
    conn.close()
    print("=" * 80)

if __name__ == '__main__':
    test_data_sync()

# backend/app.py
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import bcrypt, datetime
import os, uuid
from werkzeug.utils import secure_filename
from database import get_db, init_db
from auth import create_token, require_auth, create_signed_url, verify_signed_url, get_token_from_request, decode_token

# Set up paths for serving frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=os.path.join(FRONTEND_DIR, 'assets'), static_url_path='/assets')
CORS(app)

# Document upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

OFFICE_ROLES = ['finance', 'library', 'department', 'academics']
ROLE_LABELS = {
    'finance':    'Finance Office',
    'library':    'Library',
    'department': 'Department',
    'academics':  'Academics',
    'supervisor': 'Supervisor',
    'admin':      'Administration',
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

def ok(data=None, message='OK', code=200):
    return jsonify({'success': True, 'message': message, 'data': data or {}}), code

def err(message='Error', code=400):
    return jsonify({'success': False, 'message': message}), code

def create_notification(user_id, title, message):
    db = get_db()
    db.execute(
        "INSERT INTO notifications (user_id, title, message) VALUES (?,?,?)",
        (user_id, title, message)
    )
    db.commit()
    db.close()

def init_clearance_for_student(student_id):
    db = get_db()
    items = db.execute("SELECT id FROM clearance_items WHERE is_active=1").fetchall()
    for item in items:
        db.execute(
            "INSERT OR IGNORE INTO clearance_requests (student_id, clearance_item_id) VALUES (?,?)",
            (student_id, item['id'])
        )
    db.commit()
    db.close()

# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    b = request.get_json() or {}
    for f in ['name', 'email', 'password', 'role']:
        if not b.get(f):
            return err(f"Field '{f}' is required", 422)

    allowed_roles = ['student','finance','library','department','academics','supervisor']
    if b['role'] not in allowed_roles:
        return err('Invalid role', 422)
    if len(b['password']) < 6:
        return err('Password must be at least 6 characters', 422)

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email=?", (b['email'].lower(),)).fetchone()
    if existing:
        db.close(); return err('Email already registered', 409)

    hashed = bcrypt.hashpw(b['password'].encode(), bcrypt.gensalt()).decode()
    cur = db.execute(
        "INSERT INTO users (student_number, name, email, password, role) VALUES (?,?,?,?,?)",
        (b.get('student_number'), b['name'].strip(), b['email'].lower().strip(), hashed, b['role'])
    )
    user_id = cur.lastrowid

    if b['role'] == 'student':
        db.execute(
            "INSERT INTO student_profiles (user_id, program, year_of_study) VALUES (?,?,?)",
            (user_id, b.get('program'), b.get('year_of_study'))
        )
    db.commit()
    db.close()

    if b['role'] == 'student':
        init_clearance_for_student(user_id)

    db2  = get_db()
    user = row_to_dict(db2.execute("SELECT id,name,email,role FROM users WHERE id=?", (user_id,)).fetchone())
    db2.close()

    return ok({'token': create_token(user), 'user': user}, 'Registration successful', 201)


@app.route('/api/auth/login', methods=['POST'])
def login():
    b = request.get_json() or {}
    if not b.get('email') or not b.get('password'):
        return err('Email and password are required', 422)

    db   = get_db()
    user = row_to_dict(db.execute("SELECT * FROM users WHERE email=? AND is_active=1", (b['email'].lower().strip(),)).fetchone())
    db.close()

    if not user or not bcrypt.checkpw(b['password'].encode(), user['password'].encode()):
        return err('Invalid email or password', 401)

    safe = {k: user[k] for k in ['id','name','email','role']}

    # Attach student profile if applicable
    if user['role'] == 'student':
        db2 = get_db()
        sp  = row_to_dict(db2.execute("SELECT * FROM student_profiles WHERE user_id=?", (user['id'],)).fetchone())
        db2.close()
        if sp: safe.update({'program': sp['program'], 'defense_status': sp['defense_status']})

    return ok({'token': create_token(safe), 'user': safe}, 'Login successful')


@app.route('/api/auth/me', methods=['GET'])
@require_auth()
def me():
    db   = get_db()
    user = row_to_dict(db.execute(
        """SELECT u.id, u.student_number, u.name, u.email, u.role,
                  sp.program, sp.year_of_study, sp.defense_status
           FROM users u LEFT JOIN student_profiles sp ON sp.user_id=u.id
           WHERE u.id=? AND u.is_active=1""", (request.user['id'],)).fetchone())
    db.close()
    if not user: return err('User not found', 404)
    return ok({'user': user})

# ── STUDENT ───────────────────────────────────────────────────────────────────

@app.route('/api/student/dashboard', methods=['GET'])
@require_auth(['student'])
def student_dashboard():
    sid = request.user['id']
    db  = get_db()

    student = row_to_dict(db.execute(
        """SELECT u.id, u.student_number, u.name, u.email, u.role,
                  sp.program, sp.year_of_study, sp.defense_status
           FROM users u LEFT JOIN student_profiles sp ON sp.user_id=u.id
           WHERE u.id=?""", (sid,)).fetchone())

    checklist = rows_to_list(db.execute(
        """SELECT ci.id AS item_id, ci.title, ci.description, ci.office_role,
                  cr.id AS request_id, cr.status, cr.remarks,
                  cr.reviewed_at, u.name AS reviewed_by_name
           FROM clearance_items ci
           LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
           LEFT JOIN users u ON u.id=cr.reviewed_by
           WHERE ci.is_active=1 ORDER BY ci.sort_order""", (sid,)).fetchall())

    approved = sum(1 for i in checklist if i['status'] == 'approved')
    rejected = sum(1 for i in checklist if i['status'] == 'rejected')
    pending  = sum(1 for i in checklist if i['status'] not in ('approved','rejected'))
    total    = len(checklist)
    fully_cleared = total > 0 and approved == total

    grad = row_to_dict(db.execute("SELECT * FROM graduation_settings ORDER BY id DESC LIMIT 1").fetchone())
    db.close()

    days_left = None
    if grad:
        target = datetime.date.fromisoformat(grad['graduation_date'])
        days_left = max(0, (target - datetime.date.today()).days)

    return ok({
        'student': student,
        'defense_status': student.get('defense_status', 'not_submitted'),
        'clearance_summary': {'total': total, 'approved': approved, 'rejected': rejected, 'pending': pending},
        'fully_cleared': fully_cleared,
        'graduation': {'date': grad['graduation_date'], 'academic_year': grad.get('academic_year'), 'days_left': days_left} if grad else None,
        'checklist': checklist,
    })


@app.route('/api/student/checklist', methods=['GET'])
@require_auth(['student'])
def student_checklist():
    sid  = request.user['id']
    db   = get_db()
    rows = rows_to_list(db.execute(
        """SELECT ci.id AS item_id, ci.title, ci.description, ci.office_role,
                  cr.status, cr.remarks, cr.reviewed_at, u.name AS reviewed_by_name
           FROM clearance_items ci
           LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
           LEFT JOIN users u ON u.id=cr.reviewed_by
           WHERE ci.is_active=1 ORDER BY ci.sort_order""", (sid,)).fetchall())
    db.close()
    return ok({'checklist': rows})

# ── CLEARANCE (Office Staff) ──────────────────────────────────────────────────

@app.route('/api/clearance/items', methods=['GET'])
@require_auth()
def clearance_items():
    db    = get_db()
    items = rows_to_list(db.execute("SELECT * FROM clearance_items WHERE is_active=1 ORDER BY sort_order").fetchall())
    db.close()
    return ok({'items': items})


@app.route('/api/clearance/pending', methods=['GET'])
@require_auth(OFFICE_ROLES)
def clearance_pending():
    role = request.user['role']
    db   = get_db()
    rows = rows_to_list(db.execute(
        """SELECT cr.id, cr.status, cr.created_at,
                  u.id AS student_id, u.name AS student_name, u.student_number,
                  ci.title AS clearance_title, ci.description
           FROM clearance_requests cr
           JOIN users u ON u.id=cr.student_id
           JOIN clearance_items ci ON ci.id=cr.clearance_item_id
           WHERE ci.office_role=? AND cr.status='pending'
           ORDER BY cr.created_at""", (role,)).fetchall())
    db.close()
    return ok({'requests': rows})


@app.route('/api/clearance/all', methods=['GET'])
@require_auth(OFFICE_ROLES)
def clearance_all():
    role = request.user['role']
    db   = get_db()
    rows = rows_to_list(db.execute(
        """SELECT cr.id, cr.status, cr.remarks, cr.reviewed_at, cr.created_at,
                  u.id AS student_id, u.name AS student_name, u.student_number,
                  ci.title AS clearance_title, rev.name AS reviewed_by_name
           FROM clearance_requests cr
           JOIN users u ON u.id=cr.student_id
           JOIN clearance_items ci ON ci.id=cr.clearance_item_id
           LEFT JOIN users rev ON rev.id=cr.reviewed_by
           WHERE ci.office_role=? ORDER BY cr.updated_at DESC""", (role,)).fetchall())
    db.close()
    return ok({'requests': rows})


@app.route('/api/clearance/final-graduating-students', methods=['GET'])
@require_auth(['admin'] + OFFICE_ROLES)
def final_graduating_students():
    """Returns students fully cleared across ALL offices (library, finance, department, academics)."""
    required_roles = ['library', 'finance', 'department', 'academics']
    db = get_db()

    # Total required clearance items for the required roles
    total_required = db.execute(
        "SELECT COUNT(*) FROM clearance_items WHERE is_active=1 AND office_role IN (?,?,?,?)",
        tuple(required_roles)
    ).fetchone()[0]

    if total_required == 0:
        db.close()
        return ok({'students': []})

    # For each student, compute approval count + max reviewed_at among approvals
    rows = rows_to_list(db.execute(
        f"""
        SELECT
            u.id AS student_id,
            u.name AS student_name,
            u.student_number,
            sp.program,
            sp.dissertation_grade,
            MAX(CASE WHEN ci.office_role IN (?,?,?,?) AND cr.status='approved' THEN cr.reviewed_at ELSE NULL END) AS fully_cleared_at
        FROM users u
        JOIN student_profiles sp ON sp.user_id=u.id
        JOIN clearance_items ci ON ci.is_active=1
        LEFT JOIN clearance_requests cr
            ON cr.student_id=u.id AND cr.clearance_item_id=ci.id
        WHERE u.role='student' AND u.is_active=1 AND ci.office_role IN (?,?,?,?)
        GROUP BY u.id, u.name, u.student_number, sp.program, sp.dissertation_grade
        HAVING
            SUM(CASE WHEN ci.is_active=1 AND ci.office_role IN (?,?,?,?) AND cr.status='approved' THEN 1 ELSE 0 END) = ?
        """,
        tuple(required_roles + required_roles + required_roles + [total_required])
    ).fetchall())

    # Ensure only those with ALL required approvals and no rejected/pending
    # (HAVING already ensures count of approvals equals total required items.)

    # Normalize fully_cleared_at to None if NULL
    for r in rows:
        if not r.get('fully_cleared_at'):
            r['fully_cleared_at'] = None

    db.close()
    return ok({'students': rows})


@app.route('/api/clearance/history', methods=['GET'])
@require_auth(OFFICE_ROLES)
def clearance_history():

    role = request.user['role']
    status_filter = request.args.get('status', 'all')  # 'pending', 'approved', 'rejected', 'all'
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    search = request.args.get('search', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    db = get_db()
    
    # Build query
    query = """SELECT cr.id, cr.status, cr.remarks, cr.reviewed_at, cr.created_at,
                      u.id AS student_id, u.name AS student_name, u.student_number,
                      ci.title AS clearance_title, rev.name AS reviewed_by_name
               FROM clearance_requests cr
               JOIN users u ON u.id=cr.student_id
               JOIN clearance_items ci ON ci.id=cr.clearance_item_id
               LEFT JOIN users rev ON rev.id=cr.reviewed_by
               WHERE ci.office_role=?"""
    params = [role]
    
    # Only show processed (non-pending) requests
    query += " AND cr.status IN ('approved', 'rejected')"
    
    # Filter by status
    if status_filter in ('approved', 'rejected'):
        query += " AND cr.status=?"
        params.append(status_filter)
    
    # Filter by date range
    if date_from:
        query += " AND DATE(cr.reviewed_at) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND DATE(cr.reviewed_at) <= ?"
        params.append(date_to)
    
    # Search by student name or number
    if search:
        query += " AND (LOWER(u.name) LIKE ? OR LOWER(u.student_number) LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query})"
    total_count = db.execute(count_query, params).fetchone()[0]
    
    # Add ordering and pagination
    query += " ORDER BY cr.reviewed_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    rows = rows_to_list(db.execute(query, params).fetchall())
    db.close()
    
    return ok({
        'records': rows,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page
        }
    })


@app.route('/api/clearance/<int:req_id>/review', methods=['PUT'])
@require_auth(OFFICE_ROLES)
def clearance_review(req_id):
    b      = request.get_json() or {}
    status = b.get('status', '')
    if status not in ('approved', 'rejected'):
        return err('Status must be approved or rejected', 422)

    db  = get_db()
    req = row_to_dict(db.execute(
        """SELECT cr.*, ci.office_role, ci.title AS clearance_title,
                  u.name AS student_name, u.student_number,
                  sp.defense_status
           FROM clearance_requests cr
           JOIN clearance_items ci ON ci.id=cr.clearance_item_id
           JOIN users u ON u.id=cr.student_id
           LEFT JOIN student_profiles sp ON sp.user_id=cr.student_id
           WHERE cr.id=?""", (req_id,)).fetchone())

    if not req:
        db.close(); return err('Request not found', 404)
    if req['office_role'] != request.user['role']:
        db.close(); return err('This item does not belong to your office', 403)
    if req['status'] != 'pending':
        db.close(); return err('Already reviewed', 409)
    if status == 'approved' and req.get('defense_status') != 'passed':
        db.close(); return err('Student has not passed their project defence yet', 403)

    db.execute(
        "UPDATE clearance_requests SET status=?, reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP, remarks=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, request.user['id'], b.get('remarks', ''), req_id)
    )
    db.commit()
    db.close()

    create_notification(
        req['student_id'],
        f"{'Approved' if status=='approved' else 'Rejected'}: {req['clearance_title']}",
        f"Your clearance for \"{req['clearance_title']}\" was {status}." +
        (f" Remarks: {b['remarks']}" if b.get('remarks') else '')
    )
    return ok({}, f'Request {status} successfully')

# ── SUPERVISOR ────────────────────────────────────────────────────────────────

@app.route('/api/supervisor/students', methods=['GET'])
@require_auth(['supervisor'])
def supervisor_students():
    db   = get_db()
    rows = rows_to_list(db.execute(
        """SELECT u.id, u.student_number, u.name, u.email, u.created_at,
                  sp.program, sp.year_of_study, sp.defense_status
           FROM users u JOIN student_profiles sp ON sp.user_id=u.id
           WHERE u.role='student' AND u.is_active=1 ORDER BY u.name""").fetchall())
    db.close()
    return ok({'students': rows})


@app.route('/api/supervisor/students/<int:student_id>', methods=['GET'])
@require_auth(['supervisor'])
def supervisor_student_detail(student_id):
    db      = get_db()
    student = row_to_dict(db.execute(
        """SELECT u.*, sp.program, sp.year_of_study, sp.defense_status
           FROM users u LEFT JOIN student_profiles sp ON sp.user_id=u.id
           WHERE u.id=? AND u.role='student'""", (student_id,)).fetchone())
    if not student:
        db.close(); return err('Student not found', 404)

    clearance = rows_to_list(db.execute(
        """SELECT cr.id, ci.title, ci.office_role, cr.status, cr.reviewed_at, cr.remarks
           FROM clearance_requests cr JOIN clearance_items ci ON ci.id=cr.clearance_item_id
           WHERE cr.student_id=? ORDER BY ci.sort_order""", (student_id,)).fetchall())
    db.close()
    return ok({'student': student, 'clearance': clearance})


@app.route('/api/supervisor/defense/<int:student_id>', methods=['PUT'])
@require_auth(['supervisor'])
def update_defense(student_id):

    b      = request.get_json() or {}
    status = b.get('status', '')
    grade  = b.get('grade')

    if status not in ('pending', 'passed', 'failed'):
        return err('Status must be: pending, passed, or failed', 422)

    if status == 'passed':
        # Grade selection is mandatory for approval
        if not grade:
            return err('Please select a dissertation grade before approving.', 422)
        if grade not in ('Distinction', 'Merit', 'Credit', 'Pass'):
            return err("Invalid grade. Must be one of: Distinction, Merit, Credit, Pass", 422)

    db      = get_db()
    student = row_to_dict(db.execute("SELECT * FROM users WHERE id=? AND role='student'", (student_id,)).fetchone())
    if not student:
        db.close(); return err('Student not found', 404)

    db.execute(
        """UPDATE student_profiles SET defense_status=?,
           defense_passed_at=CASE WHEN ? = 'passed' THEN CURRENT_TIMESTAMP ELSE NULL END,
           defense_passed_by=CASE WHEN ? = 'passed' THEN ? ELSE NULL END,
           dissertation_grade=CASE WHEN ? = 'passed' THEN ? ELSE NULL END
           WHERE user_id=?""",
        (status, status, status, request.user['id'], status, grade, student_id)
    )


    db.commit()
    db.close()

    msgs = {
        'passed':  'Congratulations! Your project defence has been marked as PASSED. You may now proceed with clearance.',
        'failed':  'Your project defence has been marked as FAILED. Please contact your supervisor.',
        'pending': 'Your defence status has been updated to Pending.',
    }
    titles = {'passed': 'Defence Passed', 'failed': 'Defence Not Passed', 'pending': 'Defence Status Updated'}
    create_notification(student_id, titles[status], msgs[status])
    return ok({}, f"Defence status updated to '{status}'")

# ── ADMIN ─────────────────────────────────────────────────────────────────────

@app.route('/api/admin/users', methods=['GET'])
@require_auth(['admin'])
def admin_get_users():
    role   = request.args.get('role')
    db     = get_db()
    query  = """SELECT u.id, u.student_number, u.name, u.email, u.role, u.is_active, u.created_at,
                       sp.program, sp.year_of_study, sp.defense_status
                FROM users u LEFT JOIN student_profiles sp ON sp.user_id=u.id"""
    params = ()
    if role:
        query += " WHERE u.role=?"; params = (role,)
    query += " ORDER BY u.created_at DESC"
    users = rows_to_list(db.execute(query, params).fetchall())
    db.close()
    return ok({'users': users})


@app.route('/api/admin/users', methods=['POST'])
@require_auth(['admin'])
def admin_create_user():
    b = request.get_json() or {}
    for f in ['name', 'email', 'password', 'role']:
        if not b.get(f): return err(f"Field '{f}' is required", 422)

    db = get_db()
    if db.execute("SELECT id FROM users WHERE email=?", (b['email'].lower(),)).fetchone():
        db.close(); return err('Email already exists', 409)

    hashed = bcrypt.hashpw(b['password'].encode(), bcrypt.gensalt()).decode()
    cur    = db.execute(
        "INSERT INTO users (student_number, name, email, password, role) VALUES (?,?,?,?,?)",
        (b.get('student_number'), b['name'].strip(), b['email'].lower().strip(), hashed, b['role'])
    )
    uid = cur.lastrowid
    if b['role'] == 'student':
        db.execute("INSERT INTO student_profiles (user_id, program, year_of_study) VALUES (?,?,?)",
                   (uid, b.get('program'), b.get('year_of_study')))
    db.commit()
    db.close()
    if b['role'] == 'student':
        init_clearance_for_student(uid)
    return ok({'id': uid}, 'User created', 201)


@app.route('/api/admin/users/<int:uid>/toggle', methods=['PUT'])
@require_auth(['admin'])
def admin_toggle_user(uid):
    db  = get_db()
    row = db.execute("SELECT is_active FROM users WHERE id=?", (uid,)).fetchone()
    if not row: db.close(); return err('User not found', 404)
    new = 0 if row['is_active'] else 1
    db.execute("UPDATE users SET is_active=? WHERE id=?", (new, uid))
    db.commit(); db.close()
    return ok({'is_active': new}, 'User activated' if new else 'User deactivated')


@app.route('/api/admin/reports/clearance', methods=['GET'])
@require_auth(['admin'])
def admin_clearance_report():
    db         = get_db()
    total_items = db.execute("SELECT COUNT(*) FROM clearance_items WHERE is_active=1").fetchone()[0]
    rows       = rows_to_list(db.execute(
        """SELECT u.id, u.name, u.student_number, sp.defense_status,
                  COUNT(cr.id) AS total_requests,
                  SUM(CASE WHEN cr.status='approved' THEN 1 ELSE 0 END) AS approved,
                  SUM(CASE WHEN cr.status='rejected' THEN 1 ELSE 0 END) AS rejected,
                  SUM(CASE WHEN cr.status='pending'  THEN 1 ELSE 0 END) AS pending
           FROM users u
           JOIN student_profiles sp ON sp.user_id=u.id
           LEFT JOIN clearance_requests cr ON cr.student_id=u.id
           WHERE u.role='student' AND u.is_active=1
           GROUP BY u.id, u.name, u.student_number, sp.defense_status
           ORDER BY approved DESC""").fetchall())
    db.close()
    for r in rows:
        r['fully_cleared'] = (r['approved'] or 0) == total_items and total_items > 0
    return ok({
        'total_students': len(rows),
        'defense_passed': sum(1 for r in rows if r['defense_status'] == 'passed'),
        'fully_cleared':  sum(1 for r in rows if r['fully_cleared']),
        'students':       rows,
    })


@app.route('/api/admin/graduation-date', methods=['GET'])
@require_auth(['admin'])
def get_grad_date():
    db  = get_db()
    row = row_to_dict(db.execute("SELECT * FROM graduation_settings ORDER BY id DESC LIMIT 1").fetchone())
    db.close()
    return ok({'graduation': row})


@app.route('/api/admin/graduation-date', methods=['PUT'])
@require_auth(['admin'])
def set_grad_date():
    b = request.get_json() or {}
    if not b.get('graduation_date'): return err('graduation_date is required', 422)
    db  = get_db()
    row = db.execute("SELECT id FROM graduation_settings ORDER BY id DESC LIMIT 1").fetchone()
    if row:
        db.execute("UPDATE graduation_settings SET graduation_date=?, academic_year=?, updated_by=? WHERE id=?",
                   (b['graduation_date'], b.get('academic_year'), request.user['id'], row['id']))
    else:
        db.execute("INSERT INTO graduation_settings (graduation_date, academic_year, updated_by) VALUES (?,?,?)",
                   (b['graduation_date'], b.get('academic_year'), request.user['id']))
    db.commit(); db.close()
    return ok({}, 'Graduation date updated')


@app.route('/api/admin/clearance-items', methods=['POST'])
@require_auth(['admin'])
def admin_add_clearance_item():
    b = request.get_json() or {}
    if not b.get('title') or not b.get('office_role'): return err('title and office_role required', 422)
    if b['office_role'] not in OFFICE_ROLES: return err('Invalid office_role', 422)
    db  = get_db()
    cur = db.execute("INSERT INTO clearance_items (title, description, office_role, sort_order) VALUES (?,?,?,?)",
                     (b['title'], b.get('description'), b['office_role'], b.get('sort_order', 0)))
    db.commit(); db.close()
    return ok({'id': cur.lastrowid}, 'Clearance item added', 201)

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────

@app.route('/api/notifications', methods=['GET'])
@require_auth()
def get_notifications():
    uid  = request.user['id']
    db   = get_db()
    rows = rows_to_list(db.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 30", (uid,)).fetchall())
    unread = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (uid,)).fetchone()[0]
    db.close()
    return ok({'notifications': rows, 'unread_count': unread})


@app.route('/api/notifications/<int:nid>/read', methods=['PUT'])
@require_auth()
def mark_read(nid):
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (nid, request.user['id']))
    db.commit(); db.close()
    return ok({}, 'Marked as read')


@app.route('/api/notifications/read-all', methods=['PUT'])
@require_auth()
def mark_all_read():
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (request.user['id'],))
    db.commit(); db.close()
    return ok({}, 'All marked as read')

# ── DOCUMENTS ─────────────────────────────────────────────────────────────────

# Route 1: GET /api/documents/types
@app.route('/api/documents/types', methods=['GET'])
@require_auth()
def get_document_types():
    db = get_db()
    types = rows_to_list(db.execute("SELECT * FROM document_types ORDER BY sort_order").fetchall())
    db.close()
    return ok({'types': types})


# Route 2: GET /api/documents/my
@app.route('/api/documents/my', methods=['GET'])
@require_auth(['student'])
def get_my_documents():
    student_id = request.user['id']
    db = get_db()
    
    # Get all document types (primary source for what student needs)
    doc_types = rows_to_list(db.execute(
        "SELECT * FROM document_types ORDER BY sort_order").fetchall())
    
    # Get student's submission status
    submission = row_to_dict(db.execute(
        "SELECT * FROM document_submissions WHERE student_id=?", (student_id,)).fetchone())
    
    # Build document list with correct status logic
    documents = []
    total_uploaded = 0
    total_approved = 0
    
    for doc_type in doc_types:
        # Check if student uploaded this document
        student_doc = row_to_dict(db.execute(
            "SELECT * FROM student_documents WHERE student_id=? AND document_type_id=?",
            (student_id, doc_type['id'])).fetchone())
        
        # Check if corresponding clearance exists and its status
        clearance = row_to_dict(db.execute(
            """SELECT cr.status FROM clearance_requests cr
               JOIN clearance_items ci ON ci.id=cr.clearance_item_id
               WHERE cr.student_id=? AND ci.office_role=?""",
            (student_id, doc_type['reviewing_role'])).fetchone())
        
        # Determine status with correct priority:
        # 1. If clearance is approved → Approved (highest priority)
        # 2. If document explicitly rejected → Rejected
        # 3. If document not uploaded → Not Uploaded
        # 4. Otherwise → Pending Review
        if clearance and clearance['status'] == 'approved':
            # Clearance approval overrides everything - document is approved
            status = 'approved'
        elif student_doc and student_doc['status'] == 'rejected':
            # Explicit rejection takes priority
            status = 'rejected'
        elif not student_doc:
            # Not uploaded - show "Not Uploaded"
            status = None
        else:
            # Document uploaded but clearance not yet approved
            status = 'pending'
        
        doc_entry = {
            'type_id': doc_type['id'],
            'type_name': doc_type['name'],
            'description': doc_type['description'],
            'reviewing_role': doc_type['reviewing_role'],
            'is_required': doc_type['is_required'],
            'doc_id': student_doc['id'] if student_doc else None,
            'filename': student_doc['filename'] if student_doc else None,
            'original_name': student_doc['original_name'] if student_doc else None,
            'status': status,
            'rejection_reason': student_doc['rejection_reason'] if student_doc else None,
            'uploaded_at': student_doc['uploaded_at'] if student_doc else None,
        }
        documents.append(doc_entry)
        
        if student_doc:
            total_uploaded += 1
        if status == 'approved':
            total_approved += 1
    
    total_required = len(doc_types)
    progress_percent = round((total_approved / total_required) * 100) if total_required > 0 else 0
    
    db.close()
    
    return ok({
        'submitted': submission is not None,
        'submitted_at': submission['submitted_at'] if submission else None,
        'documents': documents,
        'total_required': total_required,
        'total_uploaded': total_uploaded,
        'total_approved': total_approved,
        'progress_percent': progress_percent,
    })


# Route 3: POST /api/documents/upload
@app.route('/api/documents/upload', methods=['POST'])
@require_auth(['student'])
def upload_document():
    student_id = request.user['id']
    
    if 'file' not in request.files or 'document_type_id' not in request.form:
        return err('Missing file or document_type_id', 400)
    
    file = request.files['file']
    doc_type_id = request.form.get('document_type_id', type=int)
    
    if file.filename == '':
        return err('No file selected', 400)
    
    if not allowed_file(file.filename):
        return err('File type not allowed. Allowed: PDF, JPG, JPEG, PNG', 400)
    
    if file.content_length and file.content_length > MAX_FILE_BYTES:
        return err('File too large. Maximum size: 5MB', 400)
    
    # Check if document type exists
    db = get_db()
    doc_type = row_to_dict(db.execute(
        "SELECT * FROM document_types WHERE id=?", (doc_type_id,)).fetchone())
    
    if not doc_type:
        db.close()
        return err('Document type not found', 404)
    
    # Check if already uploaded with pending or approved status
    existing = row_to_dict(db.execute(
        "SELECT * FROM student_documents WHERE student_id=? AND document_type_id=? AND status IN ('pending', 'approved')",
        (student_id, doc_type_id)).fetchone())
    
    if existing:
        db.close()
        return err('You have already submitted this document.', 409)
    
    # If previous was rejected, delete old file
    old_doc = row_to_dict(db.execute(
        "SELECT * FROM student_documents WHERE student_id=? AND document_type_id=? AND status='rejected'",
        (student_id, doc_type_id)).fetchone())
    
    if old_doc:
        old_path = os.path.join(UPLOAD_FOLDER, old_doc['filename'])
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Save file with UUID filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    
    # Insert or update document record
    if old_doc:
        db.execute(
            "UPDATE student_documents SET filename=?, original_name=?, file_size=?, mime_type=?, status='pending', reviewed_by=NULL, reviewed_at=NULL, rejection_reason=NULL, uploaded_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (filename, secure_filename(file.filename), file_size, file.content_type, old_doc['id'])
        )
        doc_id = old_doc['id']
    else:
        cur = db.execute(
            "INSERT INTO student_documents (student_id, document_type_id, filename, original_name, file_size, mime_type, status) VALUES (?,?,?,?,?,?,?)",
            (student_id, doc_type_id, filename, secure_filename(file.filename), file_size, file.content_type, 'pending')
        )
        doc_id = cur.lastrowid
    
    db.commit()
    db.close()
    
    return ok({'document': {
        'doc_id': doc_id,
        'status': 'pending',
        'uploaded_at': datetime.datetime.now().isoformat(),
    }}, 'Document uploaded successfully')


# Route 4: POST /api/documents/submit
@app.route('/api/documents/submit', methods=['POST'])
@require_auth(['student'])
def submit_documents():
    student_id = request.user['id']
    db = get_db()
    
    # Get all required document types
    required_types = rows_to_list(db.execute(
        "SELECT id FROM document_types WHERE is_required=1").fetchall())
    
    required_ids = [t['id'] for t in required_types]
    
    # Check that all required documents are uploaded (not rejected)
    for req_id in required_ids:
        doc = row_to_dict(db.execute(
            "SELECT * FROM student_documents WHERE student_id=? AND document_type_id=? AND status IN ('pending', 'approved')",
            (student_id, req_id)).fetchone())
        
        if not doc:
            db.close()
            return err('Please upload all required documents before submitting.', 400)
    
    # Insert or update submission record
    existing = row_to_dict(db.execute(
        "SELECT * FROM document_submissions WHERE student_id=?", (student_id,)).fetchone())
    
    if not existing:
        db.execute(
            "INSERT INTO document_submissions (student_id, status) VALUES (?,?)",
            (student_id, 'submitted')
        )
    
    db.commit()
    db.close()
    
    # Create notification
    create_notification(
        student_id,
        "Documents Submitted",
        "Your graduation documents have been submitted for review. Complete approval typically takes 48 hours. Track each department's progress on your dashboard."
    )
    
    return ok({}, 'Documents submitted successfully')


# Route 5: GET /api/documents/student/<int:student_id>
@app.route('/api/documents/student/<int:student_id>', methods=['GET'])
@require_auth(['finance', 'library', 'academics', 'supervisor', 'admin', 'department'])
def get_student_documents(student_id):
    db = get_db()
    
    # Get student
    student = row_to_dict(db.execute(
        "SELECT id, name, student_number FROM users WHERE id=? AND role='student'",
        (student_id,)).fetchone())
    
    if not student:
        db.close()
        return err('Student not found', 404)
    
    # Get submission status
    submission = row_to_dict(db.execute(
        "SELECT * FROM document_submissions WHERE student_id=?", (student_id,)).fetchone())
    
    # Get all documents with type info
    docs = rows_to_list(db.execute(
        """SELECT sd.*, dt.name AS type_name, dt.reviewing_role, u.name AS reviewed_by_name
           FROM student_documents sd
           JOIN document_types dt ON dt.id=sd.document_type_id
           LEFT JOIN users u ON u.id=sd.reviewed_by
           WHERE sd.student_id=?
           ORDER BY dt.sort_order""", (student_id,)).fetchall())
    
    db.close()
    
    return ok({
        'student': student,
        'submitted': submission is not None,
        'submitted_at': submission['submitted_at'] if submission else None,
        'documents': docs,
    })


# Route 6: GET /api/documents/pending
@app.route('/api/documents/pending', methods=['GET'])
@require_auth(['finance', 'library', 'academics', 'supervisor'])
def get_pending_documents():
    user_role = request.user['role']
    db = get_db()
    
    # Get all students who have submitted + have pending docs for this role
    students = rows_to_list(db.execute(
        """SELECT DISTINCT u.id AS student_id, u.name AS student_name, u.student_number, ds.submitted_at
           FROM document_submissions ds
           JOIN users u ON u.id=ds.student_id
           WHERE u.is_active=1 AND EXISTS (
               SELECT 1 FROM student_documents sd
               JOIN document_types dt ON dt.id=sd.document_type_id
               WHERE sd.student_id=u.id AND sd.status='pending' AND dt.reviewing_role=?
           )
           ORDER BY ds.submitted_at""", (user_role,)).fetchall())
    
    # For each student, get their pending documents for this role
    result = []
    for student in students:
        docs = rows_to_list(db.execute(
            """SELECT sd.*, dt.name AS type_name
               FROM student_documents sd
               JOIN document_types dt ON dt.id=sd.document_type_id
               WHERE sd.student_id=? AND sd.status='pending' AND dt.reviewing_role=?
               ORDER BY dt.sort_order""", (student['student_id'], user_role)).fetchall())
        
        student['pending_count'] = len(docs)
        student['documents'] = docs
        result.append(student)
    
    db.close()
    
    return ok({'students': result})


# Route 7: GET /api/documents/all-submissions
@app.route('/api/documents/all-submissions', methods=['GET'])
@require_auth(['finance', 'library', 'academics', 'supervisor', 'admin', 'department'])
def get_all_submissions():
    user_role = request.user['role']
    db = get_db()
    
    # Get all students who have submitted
    students = rows_to_list(db.execute(
        """SELECT u.id AS student_id, u.name AS student_name, u.student_number, ds.submitted_at
           FROM document_submissions ds
           JOIN users u ON u.id=ds.student_id
           WHERE u.is_active=1
           ORDER BY ds.submitted_at DESC""").fetchall())
    
    # For each student, get ALL documents
    result = []
    for student in students:
        docs = rows_to_list(db.execute(
            """SELECT sd.*, dt.name AS type_name, dt.reviewing_role
               FROM student_documents sd
               JOIN document_types dt ON dt.id=sd.document_type_id
               WHERE sd.student_id=?
               ORDER BY dt.sort_order""", (student['student_id'],)).fetchall())
        
        student['documents'] = docs
        result.append(student)
    
    db.close()
    
    return ok({'students': result})


# Route 8: PUT /api/documents/<int:doc_id>/review
@app.route('/api/documents/<int:doc_id>/review', methods=['PUT'])
@require_auth(['finance', 'library', 'academics', 'supervisor', 'admin', 'department'])
def review_document(doc_id):
    user_role = request.user['role']
    b = request.get_json() or {}
    status = b.get('status', '')
    
    if status not in ('approved', 'rejected'):
        return err('Status must be approved or rejected', 422)
    
    if status == 'rejected' and not b.get('rejection_reason'):
        return err('Rejection reason is required', 422)
    
    db = get_db()
    
    # Get document with type and student info
    doc = row_to_dict(db.execute(
        """SELECT sd.*, dt.name AS type_name, dt.reviewing_role, u.name AS student_name
           FROM student_documents sd
           JOIN document_types dt ON dt.id=sd.document_type_id
           JOIN users u ON u.id=sd.student_id
           WHERE sd.id=?""", (doc_id,)).fetchone())
    
    if not doc:
        db.close()
        return err('Document not found', 404)
    
    # Check authorization
    can_review = (user_role == doc['reviewing_role'] or 
                  user_role in ('admin', 'supervisor'))
    
    if not can_review:
        db.close()
        return err('You cannot review this document type', 403)
    
    # Update document
    db.execute(
        """UPDATE student_documents 
           SET status=?, reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP, 
               rejection_reason=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (status, request.user['id'], b.get('rejection_reason'), doc_id)
    )
    db.commit()
    
    # DEBUG: Verify the update persisted using a NEW connection
    db_verify = get_db()
    verify = row_to_dict(db_verify.execute(
        "SELECT id, status, reviewed_by, reviewed_at FROM student_documents WHERE id=?",
        (doc_id,)).fetchone())
    db_verify.close()
    
    print(f"[DEBUG] Document {doc_id} reviewed by {request.user['id']} ({user_role}): requested_status={status}, db_status={verify['status'] if verify else 'NOT FOUND'}")
    
    db.close()
    
    # Create notification
    role_label = ROLE_LABELS.get(doc['reviewing_role'], doc['reviewing_role'])
    if status == 'approved':
        create_notification(
            doc['student_id'],
            f"Document Approved: {doc['type_name']}",
            f"Your {doc['type_name']} has been approved by the {role_label} office."
        )
    else:
        create_notification(
            doc['student_id'],
            f"Document Rejected: {doc['type_name']}",
            f"Your {doc['type_name']} was rejected by the {role_label} office. Reason: {b['rejection_reason']}. Please upload a corrected document."
        )
    
    # Check if all documents are now approved
    db2 = get_db()
    total_required = db2.execute("SELECT COUNT(*) FROM document_types WHERE is_required=1").fetchone()[0]
    total_approved = db2.execute(
        """SELECT COUNT(*) FROM student_documents sd
           WHERE sd.student_id=? AND sd.status='approved' AND EXISTS (
               SELECT 1 FROM document_types dt WHERE dt.id=sd.document_type_id AND dt.is_required=1
           )""", (doc['student_id'],)).fetchone()[0]
    db2.close()
    
    if total_approved == total_required and total_required > 0:
        create_notification(
            doc['student_id'],
            "All Documents Approved!",
            "Congratulations! All your graduation documents have been approved. You may now proceed with the final graduation steps."
        )
    
    return ok({}, 'Document reviewed successfully')


# Route 8b: GET /api/documents/<int:doc_id>/signed-url
@app.route('/api/documents/<int:doc_id>/signed-url', methods=['GET'])
@require_auth()
def get_signed_document_url(doc_id):
    """Generate a signed URL for temporary file access (no auth header needed)"""
    db = get_db()
    doc = row_to_dict(db.execute(
        """SELECT sd.*, u.id AS student_id FROM student_documents sd
           JOIN users u ON u.id=sd.student_id
           WHERE sd.id=?""", (doc_id,)).fetchone())
    db.close()
    
    if not doc:
        return err('Document not found', 404)
    
    # Authorization: student can access own, office/supervisor/admin can access any
    can_access = (request.user['id'] == doc['student_id'] or 
                  request.user['role'] in ['finance', 'library', 'academics', 'supervisor', 'admin', 'department'])
    
    if not can_access:
        return err('You cannot access this document', 403)
    
    # Generate signed URL token (valid for 5 minutes)
    signed_token, expiry = create_signed_url(doc_id, request.user['id'], expires_in_seconds=300)
    
    return ok({
        'signed_token': signed_token,
        'url': f"http://localhost:5000/api/documents/download/{doc_id}?signed={signed_token}",
        'expires_at': expiry
    }, 'Signed URL generated')


# Route 9: GET /api/documents/download/<int:doc_id>
@app.route('/api/documents/download/<int:doc_id>', methods=['GET'])
def download_document(doc_id):
    """
    Download/stream a document. Supports:
    1. Authenticated request with Bearer token (Authorization header)
    2. Signed URL token via ?signed=... parameter
    """
    db = get_db()
    doc = row_to_dict(db.execute(
        """SELECT sd.*, u.id AS student_id FROM student_documents sd
           JOIN users u ON u.id=sd.student_id
           WHERE sd.id=?""", (doc_id,)).fetchone())
    db.close()
    
    if not doc:
        return err('Document not found', 404)
    
    # Check authorization: Bearer token OR signed URL
    user_id = None
    is_authorized = False
    
    # Try signed URL first
    signed_token = request.args.get('signed')
    if signed_token:
        verified = verify_signed_url(signed_token)
        if verified and verified['doc_id'] == doc_id:
            user_id = verified['user_id']
            is_authorized = True
    
    # Fall back to Bearer token if no signed URL
    if not is_authorized:
        token = get_token_from_request()
        if token:
            payload = decode_token(token)
            if payload:
                user_id = payload['id']
                # Authorization: student can download own, office/supervisor/admin can download any
                is_authorized = (user_id == doc['student_id'] or 
                                payload['role'] in ['finance', 'library', 'academics', 'supervisor', 'admin', 'department'])
    
    if not is_authorized:
        return err('Unauthorized', 401)
    
    filepath = os.path.join(UPLOAD_FOLDER, doc['filename'])
    if not os.path.exists(filepath):
        return err('File not found', 404)
    
    # Check if inline view is requested (for iframe previews)
    inline = request.args.get('inline', 'true').lower() == 'true'
    
    if inline:
        # Display inline for PDF and image types
        return send_file(filepath, as_attachment=False)
    else:
        # Force download
        return send_file(filepath, as_attachment=True, download_name=doc['original_name'])


# Route 10: GET /api/documents/progress/<int:student_id>
@app.route('/api/documents/progress/<int:student_id>', methods=['GET'])
@require_auth()
def get_documents_progress(student_id):
    db = get_db()
    
    # Get student
    student = row_to_dict(db.execute(
        "SELECT id FROM users WHERE id=? AND role='student'", (student_id,)).fetchone())
    
    if not student:
        db.close()
        return err('Student not found', 404)
    
    # Count totals from CLEARANCE REQUESTS (same source as dashboard)
    # This ensures department approval status matches the clearance checklist
    total_required = db.execute(
        "SELECT COUNT(*) FROM clearance_items WHERE is_active=1").fetchone()[0]
    
    total_approved = db.execute(
        """SELECT COUNT(*) FROM clearance_items ci
           LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
           WHERE ci.is_active=1 AND cr.status='approved'""", (student_id,)).fetchone()[0]
    
    total_rejected = db.execute(
        """SELECT COUNT(*) FROM clearance_items ci
           LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
           WHERE ci.is_active=1 AND cr.status='rejected'""", (student_id,)).fetchone()[0]
    
    total_pending = total_required - total_approved - total_rejected
    
    # Check if any documents have been uploaded (for showing the tracker)
    total_uploaded = db.execute(
        "SELECT COUNT(*) FROM student_documents WHERE student_id=?", (student_id,)).fetchone()[0]
    
    # Get department approval statuses from CLEARANCE REQUESTS (unified source)
    dept_stats = rows_to_list(db.execute(
        """SELECT ci.office_role AS role, ci.title AS label,
                  COUNT(ci.id) AS total,
                  SUM(CASE WHEN cr.status='approved' THEN 1 ELSE 0 END) AS approved,
                  SUM(CASE WHEN cr.status='rejected' THEN 1 ELSE 0 END) AS rejected
           FROM clearance_items ci
           LEFT JOIN clearance_requests cr ON cr.clearance_item_id=ci.id AND cr.student_id=?
           WHERE ci.is_active=1
           GROUP BY ci.office_role, ci.title""", (student_id,)).fetchall())
    
    # Build department status objects using CLEARANCE data
    dept_statuses = []
    for ds in dept_stats:
        role = ds['role']
        total = ds['total'] or 1
        approved = ds['approved'] or 0
        rejected = ds['rejected'] or 0
        
        if approved == total:
            status_val = 'complete'
        elif rejected > 0:
            status_val = 'rejected'
        elif approved > 0:
            status_val = 'partial'
        else:
            status_val = 'pending'
        
        dept_statuses.append({
            'role': role,
            'label': ROLE_LABELS.get(role, role),
            'approved': approved,
            'total': total,
            'status': status_val,
        })
    
    progress_percent = round((total_approved / total_required) * 100) if total_required > 0 else 0
    fully_approved = total_approved == total_required and total_required > 0
    
    db.close()
    
    return ok({
        'total_required': total_required,
        'total_uploaded': total_uploaded,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'total_pending': total_pending,
        'progress_percent': progress_percent,
        'fully_approved': fully_approved,
        'department_statuses': dept_statuses,
    })

# ── Frontend Serving ─────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def root():
    return send_file(os.path.join(FRONTEND_DIR, 'pages', 'login.html'))

@app.route('/pages/<path:filename>', methods=['GET'])
def serve_page(filename):
    return send_file(os.path.join(FRONTEND_DIR, 'pages', filename))

@app.route('/logo.jpg', methods=['GET'])
def serve_logo():
    logo_path = os.path.join(BASE_DIR, 'logo.jpg')
    if os.path.exists(logo_path):
        return send_file(logo_path, mimetype='image/jpeg')
    return jsonify({'error': 'Logo not found'}), 404

@app.route('/css/<path:filename>', methods=['GET'])
def serve_css(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets', 'css'), filename)

@app.route('/js/<path:filename>', methods=['GET'])
def serve_js(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets', 'js'), filename)

@app.route('/<path:filename>', methods=['GET'])
def serve_page_root(filename):
    if filename.endswith('.html'):
        filepath = os.path.join(FRONTEND_DIR, 'pages', filename)
        if os.path.exists(filepath):
            return send_file(filepath)
    return err('Not Found', 404)

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("\n GPMS Backend running at http://localhost:5000\n")
    app.run(debug=True, port=5000)

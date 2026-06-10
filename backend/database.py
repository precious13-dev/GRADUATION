# backend/database.py
import sqlite3, os, bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), 'gpms.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        student_number TEXT UNIQUE,
        name           TEXT NOT NULL,
        email          TEXT NOT NULL UNIQUE,
        password       TEXT NOT NULL,
        role           TEXT NOT NULL DEFAULT 'student',
        is_active      INTEGER NOT NULL DEFAULT 1,
        created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS student_profiles (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id                 INTEGER NOT NULL UNIQUE,
        program                 TEXT,
        year_of_study           INTEGER,
        defense_status          TEXT NOT NULL DEFAULT 'not_submitted',
        defense_passed_at       DATETIME,
        defense_passed_by       INTEGER,
        dissertation_grade      TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS clearance_items (

        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        description TEXT,
        office_role TEXT NOT NULL,
        sort_order  INTEGER DEFAULT 0,
        is_active   INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS clearance_requests (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id        INTEGER NOT NULL,
        clearance_item_id INTEGER NOT NULL,
        status            TEXT NOT NULL DEFAULT 'pending',
        reviewed_by       INTEGER,
        reviewed_at       DATETIME,
        remarks           TEXT,
        created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (student_id, clearance_item_id),
        FOREIGN KEY (student_id)        REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (clearance_item_id) REFERENCES clearance_items(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        title      TEXT NOT NULL,
        message    TEXT NOT NULL,
        is_read    INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS graduation_settings (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        graduation_date TEXT NOT NULL,
        academic_year   TEXT,
        updated_by      INTEGER,
        updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS document_types (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        description  TEXT,
        reviewing_role TEXT NOT NULL,
        is_required  INTEGER NOT NULL DEFAULT 1,
        sort_order   INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS student_documents (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id       INTEGER NOT NULL,
        document_type_id INTEGER NOT NULL,
        filename         TEXT NOT NULL,
        original_name    TEXT NOT NULL,
        file_size        INTEGER,
        mime_type        TEXT,
        status           TEXT NOT NULL DEFAULT 'pending',
        reviewed_by      INTEGER,
        reviewed_at      DATETIME,
        rejection_reason TEXT,
        uploaded_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id)       REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (document_type_id) REFERENCES document_types(id),
        FOREIGN KEY (reviewed_by)      REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS document_submissions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id   INTEGER NOT NULL UNIQUE,
        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status       TEXT NOT NULL DEFAULT 'submitted',
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Seed clearance items if empty
    existing = c.execute("SELECT COUNT(*) FROM clearance_items").fetchone()[0]
    if existing == 0:
        c.executemany(
            "INSERT INTO clearance_items (title, description, office_role, sort_order) VALUES (?,?,?,?)",
            [
                ('Library Clearance',    'Return all borrowed books and clear any library fines.',           'library',    1),
                ('Finance Clearance',    'Clear all outstanding tuition fees and financial obligations.',    'finance',    2),
                ('Department Clearance', 'Submit all required academic work and departmental requirements.', 'department', 3),
                ('Academics Clearance',   'Confirm all academic records are complete and up to date.',        'academics',   4),
            ]
        )

    # Seed document types if empty
    existing_docs = c.execute("SELECT COUNT(*) FROM document_types").fetchone()[0]
    if existing_docs == 0:
        c.executemany(
            "INSERT INTO document_types (name, description, reviewing_role, is_required, sort_order) VALUES (?,?,?,?,?)",
            [
                ('Grade 12 Certificate',              'Original Grade 12 certificate showing at least 5 O-Level credits or better.',         'academics',   1, 1),
                ('Academic Transcript',               'Official university academic transcript showing all completed courses and grades.',     'academics',   1, 2),
                ('Proof of Graduation Fee Payment',   'Bank receipt or payment confirmation for the graduation fee.',                         'finance',    1, 3),
                ('Financial Clearance Statement',     'Official statement confirming all tuition fees and financial obligations are settled.', 'finance',    1, 4),
                ('Library Clearance Certificate',     'Certificate from the library confirming all books are returned and fines are cleared.', 'library',    1, 5),
                ('Viva Voce / Dissertation Defence Record', 'Official record of your dissertation defence examination outcome.',              'supervisor', 1, 6),
                ('NRC (National Registration Card)',  'A clear copy of your valid National Registration Card.',                               'academics',   1, 7),
            ]
        )

    # Seed admin if not present
    admin = c.execute("SELECT id FROM users WHERE email = 'admin@cavendish.co.zm'").fetchone()
    if not admin:
        hashed = bcrypt.hashpw(b'Admin@1234', bcrypt.gensalt()).decode()
        c.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
            ('System Admin', 'admin@cavendish.co.zm', hashed, 'admin')
        )

    # Seed graduation date if not present
    grad = c.execute("SELECT id FROM graduation_settings").fetchone()
    if not grad:
        c.execute(
            "INSERT INTO graduation_settings (graduation_date, academic_year) VALUES (?,?)",
            ('2026-09-30', '2025/2026')
        )

    conn.commit()
    conn.close()
    print("Database ready.")

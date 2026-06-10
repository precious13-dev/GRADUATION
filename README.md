# Graduation Process Management System
**Cavendish University Zambia | Student: Precious Inonge Mate (106322)**

## Stack
- **Backend:** Python 3 + Flask + SQLite (no database server needed)
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Auth:** JWT (PyJWT)

---

## Setup (5 minutes)

### 1. Install Python 3
Download from https://python.org if not already installed.
Make sure to tick "Add Python to PATH" during installation.

### 2. Install dependencies
Open a terminal / command prompt in the `backend/` folder and run:
```
pip install -r requirements.txt
```

### 3. Start the backend
Still in the `backend/` folder, run:
```
python app.py
```
You should see:
```
Database ready.
GPMS Backend running at http://localhost:5000
```

### 4. Open the frontend
Open your browser and go to:
```
http://localhost/graduation-system/frontend/pages/login.html
```
Or simply open the file directly:
```
graduation-system/frontend/pages/login.html
```

---

## Default Admin Login
| Field    | Value                        |
|----------|------------------------------|
| Email    | admin@cavendish.co.zm        |
| Password | Admin@1234                   |

---

## Project Structure
```
graduation-system/
├── backend/
│   ├── app.py           ← All API routes (Flask)
│   ├── database.py      ← SQLite setup + seed data
│   ├── auth.py          ← JWT create/decode + route decorator
│   ├── requirements.txt
│   └── gpms.db          ← Created automatically on first run
├── frontend/
│   ├── assets/
│   │   ├── css/main.css
│   │   └── js/app.js
│   └── pages/
│       ├── login.html
│       ├── student-dashboard.html
│       ├── office-dashboard.html
│       ├── supervisor-dashboard.html
│       └── admin-dashboard.html
└── README.md
```

## User Roles
| Role         | Access                                      |
|--------------|---------------------------------------------|
| `student`    | Dashboard, countdown, clearance checklist   |
| `finance`    | Approve/reject finance clearance requests   |
| `library`    | Approve/reject library clearance requests   |
| `department` | Approve/reject department clearance         |
| `academics`  | Approve/reject academics clearance          |
| `supervisor` | Mark student defence as passed/failed       |
| `admin`      | Full system: users, reports, settings       |

## Business Rule
Students **must have defence marked as Passed** by a supervisor before any office can approve their clearances.

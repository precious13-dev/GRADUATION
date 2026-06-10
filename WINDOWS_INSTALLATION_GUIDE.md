# Windows Installation Guide - Graduation System

**Complete Step-by-Step Instructions for Installing & Running the Graduation Management System on Windows**

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Step 1: Install Python](#step-1-install-python)
4. [Step 2: Get the System Files](#step-2-get-the-system-files)
5. [Step 3: Open Command Prompt](#step-3-open-command-prompt)
6. [Step 4: Create Virtual Environment](#step-4-create-virtual-environment)
7. [Step 5: Install Dependencies](#step-5-install-dependencies)
8. [Step 6: Run the Backend](#step-6-run-the-backend)
9. [Step 7: Open in Browser](#step-7-open-in-browser)
10. [Step 8: Test the System](#step-8-test-the-system)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [How to Stop & Restart](#how-to-stop--restart)
13. [Moving to Another Computer](#moving-to-another-computer)

---

## System Requirements

### Minimum Requirements
- **Windows**: Windows 7 or newer (Windows 10/11 recommended)
- **RAM**: 2GB minimum (4GB recommended)
- **Hard Drive**: 500MB free space
- **Browser**: Chrome, Firefox, Edge, or Safari
- **Internet**: Required for downloading Python and dependencies

### What You'll Need
- Administrator access (to install Python)
- A text editor or VS Code (optional, for viewing code)
- Approximately 30 minutes for initial setup

---

## Pre-Installation Checklist

Before starting, verify you have the following:

- [ ] Windows computer with administrator rights
- [ ] Internet connection
- [ ] Project folder (or will download it)
- [ ] Google Chrome or another web browser
- [ ] Free space on hard drive (~500MB minimum)

---

## Step 1: Install Python

### What is Python?
Python is the programming language this system runs on. Flask (the web server) is built with Python.

### Download Python

1. Open your web browser
2. Go to: **https://www.python.org/downloads/**
3. Click the large yellow button that says **"Download Python 3.12"** (or latest version)
   - The website will auto-detect your Windows version
   - You'll see either "Windows installer (64-bit)" or "Windows installer (32-bit)"

### Install Python

1. Find the downloaded file (usually in **Downloads** folder)
2. **Right-click** → Select **"Run as Administrator"**
3. A window will appear. **IMPORTANT STEP:**
   - ✅ **Check the box: "Add Python to PATH"** (bottom left)
   - This is CRITICAL - don't skip this!

4. Click **"Install Now"** (recommended option)
5. Wait for installation to complete (2-3 minutes)
6. When done, you'll see **"Setup was successful"**
7. Click **"Close"**

### Verify Python Installation

1. Open **Command Prompt**:
   - Press **Windows Key + R**
   - Type **`cmd`**
   - Press **Enter**

2. Type this command:
   ```cmd
   python --version
   ```

3. Press **Enter**

4. You should see something like:
   ```
   Python 3.12.0
   ```

   ✅ **If you see a version number, Python is installed correctly!**

   ❌ **If you see "python is not recognized", then:**
   - Python wasn't added to PATH
   - Go back to Python installation and check the "Add Python to PATH" box
   - Restart installation if needed

---

## Step 2: Get the System Files

### Option A: You Already Have the Folder
If you already have the `graduation-system` folder, skip to **Step 3**.

### Option B: Download from GitHub/Share
If someone sent you the files:
1. Extract the ZIP file to your desired location
2. Remember the location (e.g., `C:\Users\YourName\Desktop\graduation-system`)

### Recommended Location
```
C:\Users\YourName\Desktop\graduation-system
```

Or anywhere you like - just remember the path!

---

## Step 3: Open Command Prompt

### Method 1: Quick Method (Recommended)

1. Open the **graduation-system** folder in Windows Explorer
2. **Hold Shift** and **Right-click** inside the empty space of the folder
3. Select **"Open PowerShell window here"** or **"Open Command Prompt here"**
4. A black window will open in that folder
5. You're done! Skip to Step 4.

### Method 2: Manual Method

1. Press **Windows Key + R**
2. Type: `cmd`
3. Press **Enter**
4. A black window (Command Prompt) opens
5. Type:
   ```cmd
   cd C:\Users\YourName\Desktop\graduation-system
   ```
   Replace `YourName` with your actual Windows username
6. Press **Enter**

### You Should See:
```
C:\Users\YourName\Desktop\graduation-system>
```

---

## Step 4: Create Virtual Environment

### What's Happening?
You're creating an isolated Python environment just for this project.

### Command:
Copy and paste this exactly:
```cmd
python -m venv .venv
```

Press **Enter**

### Expected Result:
```
C:\Users\YourName\Desktop\graduation-system>
```

(It will return to the prompt, and a `.venv` folder will be created)

### Verify:
1. Open Windows Explorer
2. Navigate to your `graduation-system` folder
3. You should see a new folder called `.venv`
   - It might be hidden (that's normal)
   - If you don't see it, go to View → Check "Hidden items"

---

## Step 5: Activate Virtual Environment

This step "activates" your isolated Python environment.

### Command (Windows):
```cmd
.venv\Scripts\activate
```

Press **Enter**

### Expected Result:
Your command prompt should now display:
```
(.venv) C:\Users\YourName\Desktop\graduation-system>
```

Notice the **(.venv)** at the beginning - that means it's activated! ✅

### If This Didn't Work:

**Error: "cannot be loaded because running scripts is disabled"**

Run this command instead:
```cmd
powershell -ExecutionPolicy Bypass -Command ".venv\Scripts\Activate.ps1"
```

Or try:
```cmd
.venv\Scripts\activate.bat
```

---

## Step 6: Install Dependencies

### What's Happening?
You're installing the required Python packages:
- Flask (web framework)
- Flask-CORS (allows browser requests)
- PyJWT (authentication tokens)
- bcrypt (password hashing)

### Commands:

First, navigate to the backend folder:
```cmd
cd backend
```

You should see:
```
(.venv) C:\Users\YourName\Desktop\graduation-system\backend>
```

Now install the dependencies:
```cmd
pip install -r requirements.txt
```

Press **Enter**

### Expected Output:
```
Collecting flask==3.0.3
Downloading flask-3.0.3-py3-none-any.whl (101 kB)
...
Successfully installed bcrypt-4.1.3 flask==3.0.3 flask-cors==4.0.1 PyJWT==2.8.0
```

This takes 30 seconds to 2 minutes depending on internet speed.

✅ **When you see "Successfully installed...", dependencies are done!**

---

## Step 7: Run the Backend

### Command:
```cmd
python app.py
```

Press **Enter**

### Expected Output (Wait 5-10 seconds):
```
Database ready.

 GPMS Backend running at http://localhost:5000

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

✅ **The system is now running!**

### Important Notes:
- **Keep this window open** - The backend must stay running
- Don't close this command prompt
- If you close it, the system stops

### If You Closed It Accidentally:
1. The system stops working
2. Just run `python app.py` again
3. It restarts immediately

---

## Step 8: Open in Browser

### Step 1: Open Your Browser
- Click on Chrome, Firefox, Edge, or Safari
- Or open a new browser window

### Step 2: Type the URL
In the address bar, type:
```
http://localhost:5000
```

### Step 3: Press Enter

You should see the **login page** with:
- Cavendish University logo
- "Welcome back" heading
- Email and password fields

✅ **If you see the login page, the system is working!**

---

## Step 9: Test the System

### Login with Default Credentials

| Field | Value |
|-------|-------|
| Email | admin@cavendish.co.zm |
| Password | Admin@1234 |

### Steps:
1. Type the email in the email field
2. Type the password in the password field
3. Click **"Sign In"**
4. Wait 2-3 seconds

### Expected Result:
You should see the **Admin Dashboard** with:
- Navigation menu on the left
- Statistics cards at the top
- Various management sections

✅ **If you see the dashboard, the system is fully installed!**

---

## Creating Test Accounts

Once logged in as Admin:

1. Click **"User Management"** in the sidebar
2. Click **"Create New User"** button
3. Fill in:
   - Name: `Test Student`
   - Email: `student@cavendish.co.zm`
   - Password: `Test@1234`
   - Role: `Student`
4. Click **"Create"**

✅ New user is created and stored in the database!

---

## Troubleshooting Guide

### Problem 1: "Python is not recognized"

**Cause:** Python not added to PATH during installation

**Solution:**
1. Uninstall Python:
   - Go to Settings → Apps & Features
   - Find "Python"
   - Click "Uninstall"
2. Reinstall Python (see Step 1)
3. **IMPORTANT:** Check "Add Python to PATH" checkbox
4. Restart computer
5. Try again

---

### Problem 2: "Permission denied" when running python

**Cause:** Admin rights or execution policy issue

**Solution Option 1:**
```cmd
python --version
```

**Solution Option 2 (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -Command "python --version"
```

**Solution Option 3:**
1. Right-click Command Prompt
2. Select "Run as Administrator"
3. Try again

---

### Problem 3: "ModuleNotFoundError: No module named 'flask'"

**Cause:** Dependencies not installed or wrong folder

**Solution:**
```cmd
# Make sure you're in the right folder
cd C:\Users\YourName\Desktop\graduation-system\backend

# Make sure virtual environment is activated
.venv\Scripts\activate

# You should see (.venv) at the start

# Now install dependencies
pip install -r requirements.txt

# Then run
python app.py
```

---

### Problem 4: "Port 5000 already in use"

**Cause:** Another program is using port 5000 (maybe Flask running twice)

**Solution 1:**
Close your Flask window (Command Prompt running `app.py`) and open a new one.

**Solution 2:**
Find and stop the process:
```cmd
netstat -ano | findstr :5000
```

This shows the process ID. Then:
```cmd
taskkill /PID XXXX /F
```
Replace `XXXX` with the number shown

**Solution 3:**
Change Flask port in `app.py`:
1. Open `backend/app.py` in a text editor
2. Find the line: `app.run(debug=True, port=5000)`
3. Change to: `app.run(debug=True, port=5001)`
4. Save the file
5. Run `python app.py` again
6. Visit `http://localhost:5001` instead

---

### Problem 5: "Connection refused" when opening localhost:5000

**Cause:** Backend server not running

**Solution:**
1. Make sure your Command Prompt window shows:
   ```
   GPMS Backend running at http://localhost:5000
   ```
2. If not, run: `python app.py`
3. Wait 5 seconds
4. Refresh browser (F5)

---

### Problem 6: Login Page Shows But Login Doesn't Work

**Cause:** Multiple issues possible

**Solutions:**

**Check 1: Backend is running**
- Is the Flask window showing activity?
- Try refreshing browser

**Check 2: Verify credentials**
- Email: `admin@cavendish.co.zm` (exact spelling)
- Password: `Admin@1234` (case-sensitive)

**Check 3: Database issue**
1. Close Flask (Ctrl+C in Command Prompt)
2. Delete `backend/gpms.db` file
3. Run `python app.py` again
4. Database recreates with fresh data
5. Try logging in again

**Check 4: Browser cache**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Close and reopen browser
3. Try again

---

### Problem 7: "The requested URL was not found"

**Cause:** Trying to access wrong URL

**Correct URLs:**
- ✅ `http://localhost:5000` - Login page
- ✅ `http://localhost:5000/admin-dashboard.html` - After login
- ❌ `http://localhost:5000/frontend/pages/login.html` - Wrong!
- ❌ `http://localhost/graduation-system` - Wrong!

---

### Problem 8: Virtual Environment Won't Activate

**Error:**
```
cannot be loaded because running scripts is disabled on this system
```

**Solution 1:**
```cmd
.venv\Scripts\activate.bat
```

**Solution 2 (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Solution 3 (Bypass):**
```cmd
powershell -ExecutionPolicy Bypass -Command ".venv\Scripts\Activate.ps1"
```

---

### Problem 9: "pip is not recognized"

**Cause:** Virtual environment not activated

**Solution:**
```cmd
# Activate virtual environment FIRST
.venv\Scripts\activate

# You should see (.venv) appear

# Now try pip
pip install -r requirements.txt
```

---

### Problem 10: Files Downloaded But Can't Find Them

**How to find files:**

1. Open Windows Explorer (Windows Key + E)
2. Look in common locations:
   - Desktop
   - Downloads
   - Documents
   - C:\Users\YourName\

3. If you can't find it:
   - Click in address bar
   - Type the path exactly
   - Press Enter

---

## How to Stop & Restart

### Stopping the Backend

**In the Command Prompt window running `python app.py`:**
- Press **Ctrl + C**

You'll see:
```
KeyboardInterrupt
```

The system stops. ✅

### Restarting the Backend

In the same Command Prompt:

```cmd
python app.py
```

Press **Enter**

It starts again immediately!

### Complete Restart

If something isn't working:

1. **Stop the backend** (Ctrl+C)
2. **Close the Command Prompt window**
3. **Delete** `backend/gpms.db` (optional - clears all data)
4. **Edit `backend/app.py` if needed**
5. **Open new Command Prompt** in graduation-system folder
6. **Activate venv:** `.venv\Scripts\activate`
7. **Go to backend:** `cd backend`
8. **Run:** `python app.py`

---

## Quick Reference Commands

### All Commands You'll Use

```cmd
# Navigate to project
cd C:\Users\YourName\Desktop\graduation-system

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Go to backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the system
python app.py

# Deactivate virtual environment (when done)
deactivate

# Check Python version
python --version

# Check pip version
pip --version

# List installed packages
pip list

# Uninstall all packages (if needed)
pip uninstall -r requirements.txt -y
```

---

## Folder Structure After Installation

After successful installation, your folder should look like:

```
graduation-system/
├── .venv/                          ← Virtual environment (created)
│   ├── Scripts/
│   ├── Lib/
│   └── pyvenv.cfg
│
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── database.py
│   ├── requirements.txt
│   └── gpms.db                    ← Database (created on first run)
│
├── frontend/
│   ├── pages/
│   ├── assets/
│   └── ...
│
├── logo.jpg
├── README.md
├── SYSTEM_EXPLANATION.md
└── WINDOWS_INSTALLATION_GUIDE.md
```

---

## Security First Time Setup

### After First Login (Important!)

1. **Change Admin Password**
   - Click on Settings
   - Change default password from "Admin@1234" to something secure
   - This is crucial before production use!

2. **Create Restricted Accounts**
   - Create individual accounts for staff/students
   - Don't share the admin account

3. **Backup Database**
   - Copy `backend/gpms.db` to a safe location
   - Do this regularly (weekly recommended)

---

## Performance Tips

### Running Smoothly

**What's Normal:**
- First load: 2-3 seconds
- Login: 1-2 seconds
- Dashboard load: 1-2 seconds

**If It's Slow:**
1. Close other programs (browsers, apps)
2. Free up RAM
3. Restart the backend
4. Check internet connection

**If You Have Many Users:**
- SQLite works for ~50 users
- For more, consider upgrading to PostgreSQL (advanced)

---

## Next Steps After Installation

### What to Do Now

1. **Explore the System**
   - Log in and navigate all pages
   - Test creating users
   - See how everything works

2. **Read the Documentation**
   - Open `SYSTEM_EXPLANATION.md`
   - Understanding how it works helps with troubleshooting

3. **Customize (Optional)**
   - Change colors in `frontend/assets/css/main.css`
   - Update text in HTML files
   - Modify settings

4. **Deploy to Production (Advanced)**
   - Follow deployment guide (separate document)
   - Use proper server (Heroku, AWS, etc.)
   - Set up HTTPS

---

## Getting Help

### If Something Goes Wrong

1. **Check the terminal output** - Error messages are helpful
2. **Verify all commands** - Copy/paste exactly
3. **Restart everything** - Turn it off and back on
4. **Check file paths** - Make sure they're correct
5. **Search the troubleshooting section** above

### Common Error Messages & Solutions

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `python is not recognized` | Python not in PATH | Reinstall Python with PATH checkbox |
| `No module named 'flask'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `Port 5000 already in use` | Flask already running | Kill process or use different port |
| `FileNotFoundError: gpms.db` | Database path wrong | Make sure running from `backend/` folder |
| `Connection refused` | Backend not running | Run `python app.py` |
| `Cannot connect to localhost:5000` | Wrong URL or firewall | Check URL and firewall settings |

---

## Important Notes to Remember

### Do's ✅
- ✅ Keep the backend Command Prompt window open
- ✅ Use `localhost:5000` in browser
- ✅ Activate virtual environment before installing packages
- ✅ Keep the database file (`gpms.db`) safe
- ✅ Follow exact paths and file names

### Don'ts ❌
- ❌ Don't close the Flask Command Prompt (backend stops)
- ❌ Don't delete the `.venv` folder (unless you know what you're doing)
- ❌ Don't manually edit `.db` file (corrupt it)
- ❌ Don't install Python in Program Files folder (permission issues)
- ❌ Don't skip "Add Python to PATH" during installation

---

## Windows Versions

This guide works for:
- ✅ Windows 10
- ✅ Windows 11
- ✅ Windows 7/8 (mostly - some features may vary)
- ✅ Windows Server 2016+

---

## Summary Checklist

- [ ] Downloaded and installed Python 3.12+
- [ ] Added Python to PATH
- [ ] Have the `graduation-system` folder
- [ ] Created virtual environment (`.venv`)
- [ ] Activated virtual environment
- [ ] Installed dependencies from `requirements.txt`
- [ ] Database file (`gpms.db`) created
- [ ] Backend running on `http://localhost:5000`
- [ ] Can see login page in browser
- [ ] Can log in with `admin@cavendish.co.zm` / `Admin@1234`
- [ ] Can see admin dashboard

**If all boxes are checked: System is installed! 🎉**

---

## Final Troubleshooting

### "I did everything but it still doesn't work"

**Try this complete reset:**

1. Close all Command Prompt windows

2. Delete the `.venv` folder:
   - Navigate to `graduation-system`
   - Right-click `.venv` → Delete

3. Delete the database:
   - Go to `graduation-system/backend`
   - Delete `gpms.db` file (if it exists)

4. Open Command Prompt in `graduation-system` folder

5. Run each command (slowly, one at a time):
   ```cmd
   python -m venv .venv
   ```
   Wait 5 seconds.

   ```cmd
   .venv\Scripts\activate
   ```
   Should see `(.venv)` appear.

   ```cmd
   cd backend
   ```

   ```cmd
   pip install -r requirements.txt
   ```
   Wait for "Successfully installed..." message.

   ```cmd
   python app.py
   ```
   Wait for "GPMS Backend running at http://localhost:5000" message.

6. Open browser: `http://localhost:5000`

7. Log in with `admin@cavendish.co.zm` / `Admin@1234`

This complete reset usually fixes any issues!

---

**Congratulations! You now have a fully functional Graduation Management System on Windows! 🎓**

For more information, see `SYSTEM_EXPLANATION.md`

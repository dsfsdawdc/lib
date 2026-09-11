# Civic Shelf: Local Public Library Management System

A Flask and MySQL system for public library administration, staff workflows, member registration, catalogue management, borrowing requests, circulation transactions, and audit history.

## Setup

The project includes a `.venv` with the required packages. To activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Create the database schema first:

```powershell
Get-Content .\schema.sql | .\mysql.exe -u root -p
```

If you already created the database using an older version that has `book_authors`, run the one-time migration before starting the app:

```powershell
Get-Content .\migration_author_id.sql | .\mysql.exe -u root -p
```

For an existing database, add physical copy counts with:

```powershell
Get-Content .\migration_copy_counts.sql | .\mysql.exe -u root -p
```

Load the demo catalogue and accounts (optional):

```powershell
Get-Content .\seed.sql | .\mysql.exe -u root -p
```

The seeded accounts use the password `Library123!` and include `admin.demo`, `staff.demo`, `maya.chen`, `noah.williams`, `sofia.reyes`, and `liam.patel`. Change or remove demo credentials before production use.

Set the connection values for the current PowerShell session, or copy `.env.example` as a reference:

```powershell
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "your-password"
$env:MYSQL_DATABASE = "dblib"
$env:SECRET_KEY = "replace-with-a-long-random-secret"
```

For production, set `SESSION_COOKIE_SECURE=1` when serving over HTTPS. Never commit `.env` or real passwords.

Start the app:

```powershell
python app.py
```

Start the app:

```powershell
flask --app app run --debug
```

Create the first administrator interactively:

```powershell
flask --app app create-admin
```

Main pages:

- `/login` authenticates admins, staff, and members.
- `/dashboard` shows role-aware operational metrics.
- `/books` is the searchable catalogue. Admins and staff can add new book records; only admins can edit or delete them; members can request available books from this page.
- `/catalogue/manage` lets admins and staff add authors, publishers, and shelves. Only admins can edit or delete those records.
- `/members` lets admins and staff register members.
- `/requests` lets members submit requests and staff approve or decline them.
- `/staff` lets admins approve, decline, or suspend staff accounts.
- `/db-test` opens a MySQL connection and confirms the selected database.

Security features include Werkzeug password hashing, role-based access control, CSRF tokens on every POST, parameterized SQL, secure session cookie settings, and audit logging for important operations. The MySQL server must be running and the `dblib` schema must exist before using authenticated pages.

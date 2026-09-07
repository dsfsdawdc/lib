import json
import re
import secrets
from functools import wraps

import mysql.connector
from flask import current_app, flash, g, redirect, request, session, url_for


def get_db_connection():
    return mysql.connector.connect(
        host=current_app.config["MYSQL_HOST"],
        port=current_app.config["MYSQL_PORT"],
        user=current_app.config["MYSQL_USER"],
        password=current_app.config["MYSQL_PASSWORD"],
        database=current_app.config["MYSQL_DATABASE"],
    )


def query_db(query, params=(), *, fetch_one=False, commit=False):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchone() if fetch_one else cursor.fetchall()
        if commit:
            connection.commit()
        return result
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def paginate_rows(rows, page):
    page = max(1, int(page or 1))
    total_pages = max(1, (len(rows) + 9) // 10)
    page = min(page, total_pages)
    start = (page - 1) * 10
    return rows[start:start + 10], page, total_pages


def next_membership_number():
    existing_numbers = query_db("SELECT membership_no FROM members WHERE membership_no LIKE 'LIB-%'")
    highest_number = 999
    for row in existing_numbers:
        match = re.fullmatch(r"LIB-(\d+)", row["membership_no"])
        if match:
            highest_number = max(highest_number, int(match.group(1)))
    return f"LIB-{highest_number + 1}"


def log_audit(action, entity_type, entity_id=None, details=None):
    query_db(
        "INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, details, ip_address) VALUES (%s, %s, %s, %s, %s, %s)",
        (g.user["id"] if g.user else None, action, entity_type, entity_id, json.dumps(details) if details is not None else None, request.remote_addr),
        commit=True,
    )


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        if g.user["status"] != "active":
            session.clear()
            flash("Your account is not active.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(*args, **kwargs):
            if g.user["role"] not in roles:
                flash("You do not have permission to perform that action.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator

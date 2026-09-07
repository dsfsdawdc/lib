import secrets

from flask import flash, g, jsonify, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash

from .shared import csrf_token, login_required, query_db


def register(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def load_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id:
            try:
                g.user = query_db(
                    "SELECT id, username, full_name, email, role, status FROM users WHERE id = %s",
                    (user_id,),
                    fetch_one=True,
                )
            except Error:
                session.clear()

        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            if not submitted_token or not secrets.compare_digest(submitted_token, session.get("csrf_token", "")):
                return jsonify({"error": "Invalid CSRF token"}), 400

    @app.context_processor
    def inject_user():
        return {"current_user": g.user}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = query_db(
                "SELECT id, username, password_hash, full_name, role, status FROM users WHERE username = %s",
                (username,),
                fetch_one=True,
            )
            if user and user["status"] == "active" and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                csrf_token()
                return redirect(url_for("dashboard"))
            flash("Invalid credentials or inactive account.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/api/username-availability")
    @login_required
    def username_availability():
        username = request.args.get("username", "").strip()
        existing = query_db(
            "SELECT id FROM users WHERE username = %s AND id <> %s",
            (username, g.user["id"]),
            fetch_one=True,
        ) if username else None
        return jsonify({"available": not existing})

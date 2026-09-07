from flask import g, jsonify, redirect, render_template, url_for
from mysql.connector import Error

from .shared import login_required, query_db


def register(app):
    @app.get("/")
    def index():
        if g.user:
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/dashboard")
    @login_required
    def dashboard():
        if g.user["role"] == "member":
            return redirect(url_for("books"))
        metrics = query_db(
            """
            SELECT
                (SELECT COUNT(*) FROM books WHERE status = 'available') AS available_books,
                (SELECT COUNT(*) FROM members WHERE status = 'active') AS active_members,
                (SELECT COUNT(*) FROM borrow_requests WHERE status = 'pending') AS pending_requests,
                (SELECT COUNT(*) FROM book_transactions WHERE status = 'borrowed' AND due_date < CURDATE()) AS overdue_books
            """,
            fetch_one=True,
        )
        recent_books = query_db(
            """
            SELECT b.id, b.title, b.isbn, b.status, p.name AS publisher
            FROM books b LEFT JOIN publishers p ON p.id = b.publisher_id
            ORDER BY b.created_at DESC LIMIT 8
            """
        )
        return render_template("dashboard.html", metrics=metrics, recent_books=recent_books)

    @app.get("/db-test")
    def db_test():
        connection = None
        cursor = None
        try:
            connection = query_db("SELECT DATABASE()", fetch_one=True)
            return jsonify({"status": "connected", "database": connection["DATABASE()"]})
        except Error as error:
            return jsonify({"status": "error", "message": str(error)}), 503

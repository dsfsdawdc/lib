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
                (SELECT COUNT(*) FROM book_transactions WHERE status IN ('borrowed', 'renewed', 'overdue') AND due_date < CURDATE()) AS overdue_books
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
        charts = {}
        if g.user["role"] == "admin":
            charts = {
                "borrowing_trends": query_db(
                    """
                    SELECT DATE_FORMAT(issue_date, '%b %Y') AS label, COUNT(*) AS total
                    FROM book_transactions
                    WHERE issue_date >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH)
                    GROUP BY YEAR(issue_date), MONTH(issue_date), DATE_FORMAT(issue_date, '%b %Y')
                    ORDER BY YEAR(issue_date), MONTH(issue_date)
                    """
                ),
                "most_borrowed": query_db(
                    """
                    SELECT b.title AS label, COUNT(*) AS total
                    FROM book_transactions t JOIN books b ON b.id = t.book_id
                    GROUP BY t.book_id, b.title
                    ORDER BY total DESC, b.title
                    LIMIT 5
                    """
                ),
                "request_status": query_db(
                    "SELECT status AS label, COUNT(*) AS total FROM borrow_requests GROUP BY status ORDER BY status"
                ),
                "overdue_books": query_db(
                    """
                    SELECT b.title AS label, COUNT(*) AS total
                    FROM book_transactions t JOIN books b ON b.id = t.book_id
                    WHERE t.status IN ('borrowed', 'renewed', 'overdue') AND t.due_date < CURDATE()
                    GROUP BY t.book_id, b.title
                    ORDER BY total DESC, b.title
                    LIMIT 5
                    """
                ),
                "inventory_status": query_db(
                    "SELECT status AS label, COUNT(*) AS total FROM books GROUP BY status ORDER BY status"
                ),
                "active_members": query_db(
                    """
                    SELECT DATE_FORMAT(joined_at, '%b %Y') AS label, COUNT(*) AS total
                    FROM members
                    WHERE status = 'active' AND joined_at >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH)
                    GROUP BY YEAR(joined_at), MONTH(joined_at), DATE_FORMAT(joined_at, '%b %Y')
                    ORDER BY YEAR(joined_at), MONTH(joined_at)
                    """
                ),
            }
        return render_template("dashboard.html", metrics=metrics, recent_books=recent_books, charts=charts)

    @app.get("/db-test")
    def db_test():
        connection = None
        cursor = None
        try:
            connection = query_db("SELECT DATABASE()", fetch_one=True)
            return jsonify({"status": "connected", "database": connection["DATABASE()"]})
        except Error as error:
            return jsonify({"status": "error", "message": str(error)}), 503

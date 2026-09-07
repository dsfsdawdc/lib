from flask import flash, g, jsonify, redirect, render_template, request, url_for

from .shared import log_audit, paginate_rows, query_db, roles_required, login_required


def register(app):
    @app.get("/requests")
    @login_required
    def requests():
        if g.user["role"] == "member":
            member = query_db("SELECT id FROM members WHERE user_id = %s", (g.user["id"],), fetch_one=True)
            rows = query_db("SELECT r.id, b.title, r.request_type, r.status, r.requested_at FROM borrow_requests r JOIN books b ON b.id = r.book_id WHERE r.member_id = %s ORDER BY r.requested_at DESC", (member["id"],))
            rows, page, pages = paginate_rows(rows, request.args.get("page", 1, type=int))
            return render_template("requests.html", requests=rows, pending_requests=[], processed_requests=[], page=page, pages=pages)
        rows = query_db(
            """
            SELECT r.id, b.title, r.request_type, r.status, r.requested_at,
                   member_user.full_name AS member_name, reviewer.id AS reviewer_id,
                   reviewer.full_name AS reviewer_name, reviewer.role AS reviewer_role
            FROM borrow_requests r JOIN books b ON b.id = r.book_id JOIN members m ON m.id = r.member_id
            JOIN users member_user ON member_user.id = m.user_id LEFT JOIN users reviewer ON reviewer.id = r.reviewed_by
            ORDER BY r.requested_at DESC
            """
        )
        pending_requests, pending_page, pending_pages = paginate_rows([row for row in rows if row["status"] == "pending"], request.args.get("pending_page", 1, type=int))
        processed_requests, processed_page, processed_pages = paginate_rows([row for row in rows if row["status"] != "pending"], request.args.get("processed_page", 1, type=int))
        return render_template("requests.html", requests=rows, pending_requests=pending_requests, processed_requests=processed_requests, pending_page=pending_page, pending_pages=pending_pages, processed_page=processed_page, processed_pages=processed_pages)

    @app.post("/requests/<int:request_id>/<action>")
    @roles_required("admin", "staff")
    def update_request(request_id, action):
        if action not in {"approve", "decline"}:
            return jsonify({"error": "Invalid action"}), 400
        status = "approved" if action == "approve" else "declined"
        query_db("UPDATE borrow_requests SET status = %s, reviewed_by = %s, reviewed_at = NOW() WHERE id = %s AND status = 'pending'", (status, g.user["id"], request_id), commit=True)
        query_db("INSERT INTO borrow_transaction_events (request_id, action, actor_id) VALUES (%s, %s, %s)", (request_id, status, g.user["id"]), commit=True)
        if action == "approve":
            query_db("INSERT INTO book_transactions (request_id, book_id, member_id, issued_by, issue_date, due_date, status) SELECT r.id, r.book_id, r.member_id, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'borrowed' FROM borrow_requests r JOIN books b ON b.id = r.book_id WHERE r.id = %s AND r.status = 'approved' AND b.available_copies > 0", (g.user["id"], request_id), commit=True)
            transaction = query_db("SELECT id FROM book_transactions WHERE request_id = %s ORDER BY id DESC LIMIT 1", (request_id,), fetch_one=True)
            if transaction:
                query_db("UPDATE borrow_transaction_events SET transaction_id = %s WHERE request_id = %s AND action = 'approved' AND transaction_id IS NULL ORDER BY id DESC LIMIT 1", (transaction["id"], request_id), commit=True)
            query_db("UPDATE books b JOIN borrow_requests r ON r.book_id = b.id SET b.available_copies = b.available_copies - 1, b.status = CASE WHEN b.available_copies - 1 = 0 THEN 'borrowed' ELSE 'available' END WHERE r.id = %s AND b.available_copies > 0", (request_id,), commit=True)
        log_audit(action, "borrow_request", request_id)
        flash(f"Request {action}d.", "success")
        return redirect(url_for("requests"))

    @app.post("/requests")
    @roles_required("member")
    def create_request():
        book_id = request.form.get("book_id", "")
        request_type = request.form.get("request_type", "borrow")
        if request_type not in {"borrow", "reserve"}:
            request_type = "borrow"
        member = query_db("SELECT id FROM members WHERE user_id = %s", (g.user["id"],), fetch_one=True)
        duplicate = query_db("SELECT b.title, b.isbn FROM books b WHERE b.id = %s AND (EXISTS (SELECT 1 FROM borrow_requests r WHERE r.member_id = %s AND r.book_id = b.id AND r.status IN ('pending', 'approved')) OR EXISTS (SELECT 1 FROM book_transactions t WHERE t.member_id = %s AND t.book_id = b.id))", (book_id, member["id"], member["id"]), fetch_one=True)
        if duplicate:
            flash(f"You already borrowed or requested '{duplicate['title']}' (ISBN: {duplicate['isbn']}).", "error")
            return redirect(url_for("books"))
        query_db("INSERT INTO borrow_requests (member_id, book_id, request_type, status) VALUES (%s, %s, %s, 'pending')", (member["id"], book_id, request_type), commit=True)
        log_audit("create", "borrow_request", details=f"book:{book_id}")
        flash("Request submitted for staff review.", "success")
        return redirect(url_for("requests"))

    @app.get("/transactions")
    @roles_required("admin", "staff")
    def transactions():
        rows = query_db(
            """
            SELECT t.id, t.issue_date, t.due_date, t.return_date, t.renewal_count,
                   CASE WHEN t.status = 'borrowed' AND t.due_date < CURDATE() THEN 'overdue' ELSE t.status END AS display_status,
                   b.title, m.membership_no, member_user.full_name AS member_name,
                   issuer.full_name AS issuer_name, returner.full_name AS returner_name,
                   accepted.full_name AS accepted_by_name, renewed.full_name AS renewed_by_name,
                   returned.full_name AS returned_by_name
            FROM book_transactions t JOIN books b ON b.id = t.book_id JOIN members m ON m.id = t.member_id
            JOIN users member_user ON member_user.id = m.user_id JOIN users issuer ON issuer.id = t.issued_by
            LEFT JOIN users returner ON returner.id = t.returned_to
            LEFT JOIN borrow_transaction_events accepted_event ON accepted_event.transaction_id = t.id AND accepted_event.action = 'approved'
            LEFT JOIN users accepted ON accepted.id = accepted_event.actor_id
            LEFT JOIN borrow_transaction_events renewed_event ON renewed_event.transaction_id = t.id AND renewed_event.action = 'renewed'
            LEFT JOIN users renewed ON renewed.id = renewed_event.actor_id
            LEFT JOIN borrow_transaction_events returned_event ON returned_event.transaction_id = t.id AND returned_event.action = 'returned'
            LEFT JOIN users returned ON returned.id = returned_event.actor_id
            ORDER BY t.issue_date DESC, t.id DESC
            """
        )
        active_rows, active_page, active_pages = paginate_rows([row for row in rows if row["display_status"] != "returned"], request.args.get("active_page", 1, type=int))
        returned_rows, returned_page, returned_pages = paginate_rows([row for row in rows if row["display_status"] == "returned"], request.args.get("returned_page", 1, type=int))
        return render_template("transactions.html", transactions=rows, active_transactions=active_rows, returned_transactions=returned_rows, active_page=active_page, active_pages=active_pages, returned_page=returned_page, returned_pages=returned_pages)

    @app.post("/transactions/<int:transaction_id>/<action>")
    @roles_required("admin", "staff")
    def update_transaction(transaction_id, action):
        transaction = query_db("SELECT request_id, status, renewal_count, return_date FROM book_transactions WHERE id = %s", (transaction_id,), fetch_one=True)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404
        if action == "return":
            if transaction["return_date"] is not None or transaction["status"] not in {"borrowed", "renewed", "overdue"}:
                flash("This transaction has already been returned or is not active.", "error")
                return redirect(url_for("transactions"))
            query_db("UPDATE book_transactions t JOIN books b ON b.id = t.book_id SET t.status = 'returned', t.return_date = CURDATE(), t.returned_to = %s, b.available_copies = LEAST(b.total_copies, b.available_copies + 1), b.status = 'available' WHERE t.id = %s AND t.status IN ('borrowed', 'renewed', 'overdue') AND t.return_date IS NULL", (g.user["id"], transaction_id), commit=True)
            if transaction["request_id"]:
                query_db("INSERT INTO borrow_transaction_events (transaction_id, request_id, action, actor_id) VALUES (%s, %s, 'returned', %s)", (transaction_id, transaction["request_id"], g.user["id"]), commit=True)
            log_audit("return", "book_transaction", transaction_id)
            flash("Book marked as returned.", "success")
        elif action == "renew":
            if transaction["return_date"] is not None or transaction["status"] not in {"borrowed", "overdue"} or transaction["renewal_count"] != 0:
                flash("This transaction can only be renewed once while it is active.", "error")
                return redirect(url_for("transactions"))
            query_db("UPDATE book_transactions SET due_date = DATE_ADD(due_date, INTERVAL 14 DAY), renewal_count = 1, status = 'renewed' WHERE id = %s AND status IN ('borrowed', 'overdue') AND renewal_count = 0 AND return_date IS NULL", (transaction_id,), commit=True)
            if transaction["request_id"]:
                query_db("INSERT INTO borrow_transaction_events (transaction_id, request_id, action, actor_id) VALUES (%s, %s, 'renewed', %s)", (transaction_id, transaction["request_id"], g.user["id"]), commit=True)
            log_audit("renew", "book_transaction", transaction_id)
            flash("Book renewed where eligible. It can be returned but not renewed again.", "success")
        else:
            return jsonify({"error": "Invalid action"}), 400
        return redirect(url_for("transactions"))

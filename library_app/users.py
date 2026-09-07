from datetime import date

from flask import flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .shared import get_db_connection, log_audit, next_membership_number, paginate_rows, query_db, roles_required


def register(app):
    @app.route("/staff", methods=["GET", "POST"])
    @roles_required("admin")
    def staff():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip() or None
            existing_username = query_db("SELECT id FROM users WHERE username = %s", (username,), fetch_one=True)
            if not username or not password or not full_name:
                flash("Username, password, and full name are required.", "error")
            elif existing_username:
                flash("That username already exists. Choose another username.", "error")
            else:
                query_db("INSERT INTO users (username, password_hash, full_name, email, role, status, approved_by, approved_at) VALUES (%s, %s, %s, %s, 'staff', 'active', %s, NOW())", (username, generate_password_hash(password), full_name, email, g.user["id"]), commit=True)
                log_audit("create", "staff_user", details=username)
                flash("Staff account created and activated.", "success")
                return redirect(url_for("staff"))
        rows = query_db("SELECT id, username, full_name, email, role, status, created_at FROM users WHERE role = 'staff' ORDER BY created_at DESC")
        rows, page, pages = paginate_rows(rows, request.args.get("page", 1, type=int))
        return render_template("staff.html", staff=rows, page=page, pages=pages)

    @app.route("/account", methods=["GET", "POST"])
    @roles_required("staff", "member")
    def account():
        if request.method == "POST":
            current_password = request.form.get("current_password", "")
            new_username = request.form.get("new_username", "").strip()
            new_password = request.form.get("new_password", "")
            new_email = request.form.get("email", "").strip() or None
            user = query_db("SELECT password_hash, email, username_changed_at, password_changed_at FROM users WHERE id = %s", (g.user["id"],), fetch_one=True)
            if not user or not check_password_hash(user["password_hash"], current_password):
                flash("Current password is incorrect.", "error")
            else:
                updates = []
                values = []
                if new_email != user["email"]:
                    updates.append("email = %s")
                    values.append(new_email)
                if new_username:
                    if user["username_changed_at"]:
                        flash("Your username has already been changed once.", "error")
                        return render_template("account.html")
                    duplicate = query_db("SELECT id FROM users WHERE username = %s AND id <> %s", (new_username, g.user["id"]), fetch_one=True)
                    if duplicate:
                        flash("That username is already in use.", "error")
                        return render_template("account.html")
                    updates.extend(["username = %s", "username_changed_at = NOW()"])
                    values.append(new_username)
                if new_password:
                    if user["password_changed_at"]:
                        flash("Your password has already been changed once.", "error")
                        return render_template("account.html")
                    updates.extend(["password_hash = %s", "password_changed_at = NOW()"])
                    values.append(generate_password_hash(new_password))
                if not updates:
                    flash("Enter a new username, a new password, or both.", "error")
                else:
                    values.append(g.user["id"])
                    query_db(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", tuple(values), commit=True)
                    log_audit("update_account", "user", g.user["id"])
                    if new_username or new_password:
                        session.clear()
                        flash("Account updated. Please sign in again.", "success")
                        return redirect(url_for("login"))
                    flash("Email updated.", "success")
                    return redirect(url_for("account"))
        return render_template("account.html")

    @app.post("/staff/<int:user_id>/<action>")
    @roles_required("admin")
    def update_staff(user_id, action):
        if action not in {"approve", "decline", "suspend"}:
            return {"error": "Invalid action"}, 400
        status = {"approve": "active", "decline": "declined", "suspend": "suspended"}[action]
        query_db("UPDATE users SET status = %s, approved_by = %s, approved_at = NOW() WHERE id = %s AND role = 'staff'", (status, g.user["id"], user_id), commit=True)
        log_audit(action, "user", user_id)
        flash(f"Staff account {action}d.", "success")
        return redirect(url_for("staff"))

    @app.route("/members", methods=["GET", "POST"])
    @roles_required("admin", "staff")
    def members():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip() or None
            phone = request.form.get("phone", "").strip() or None
            address = request.form.get("address", "").strip() or None
            existing_username = query_db("SELECT id FROM users WHERE username = %s", (username,), fetch_one=True)
            if not all((username, password, full_name)):
                flash("Username, password, and full name are required.", "error")
            elif existing_username:
                flash("That username already exists. Choose another username.", "error")
            else:
                connection = get_db_connection()
                cursor = connection.cursor()
                try:
                    membership_no = next_membership_number()
                    cursor.execute("INSERT INTO users (username, password_hash, full_name, email, role, status, approved_by, approved_at) VALUES (%s, %s, %s, %s, 'member', 'active', %s, NOW())", (username, generate_password_hash(password), full_name, email, g.user["id"]))
                    cursor.execute("INSERT INTO members (user_id, membership_no, phone, address, joined_at) VALUES (%s, %s, %s, %s, %s)", (cursor.lastrowid, membership_no, phone, address, date.today()))
                    connection.commit()
                    log_audit("create", "member", details=membership_no)
                    flash("Member registered.", "success")
                    return redirect(url_for("members"))
                finally:
                    cursor.close()
                    connection.close()
        rows = query_db("SELECT m.membership_no, u.full_name, u.username, m.phone, m.status, m.joined_at FROM members m JOIN users u ON u.id = m.user_id ORDER BY m.joined_at DESC")
        rows, page, pages = paginate_rows(rows, request.args.get("page", 1, type=int))
        return render_template("members.html", members=rows, page=page, pages=pages, next_membership_no=next_membership_number())

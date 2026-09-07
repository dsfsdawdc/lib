from flask import flash, g, jsonify, redirect, render_template, request, url_for

from .shared import log_audit, paginate_rows, query_db, roles_required


def register(app):
    @app.route("/books", methods=["GET", "POST"])
    @roles_required("admin", "staff", "member")
    def books():
        if request.method == "POST":
            if g.user["role"] not in {"admin", "staff"}:
                return jsonify({"error": "Only staff and admins can add books"}), 403
            title = request.form.get("title", "").strip()
            isbn = request.form.get("isbn", "").strip()
            author_id = request.form.get("author_id", "").strip()
            if not title or not isbn:
                flash("Title and ISBN are required.", "error")
            else:
                total_copies = max(1, int(request.form.get("total_copies", "1") or 1))
                query_db(
                    "INSERT INTO books (title, isbn, author_id, publisher_id, shelf_id, publication_year, total_copies, available_copies, status) VALUES (%s, %s, NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''), NULLIF(%s, ''), %s, %s, 'available')",
                    (title, isbn, author_id, request.form.get("publisher_id", ""), request.form.get("shelf_id", ""), request.form.get("publication_year", ""), total_copies, total_copies),
                    commit=True,
                )
                log_audit("create", "book", details=title)
                flash("Book added.", "success")
                return redirect(url_for("books"))
        search = request.args.get("q", "").strip()
        search_value = f"%{search}%"
        rows = query_db(
            """
            SELECT b.id, b.title, b.isbn, b.publication_year, b.total_copies, b.available_copies, b.status,
                   a.name AS author, p.name AS publisher, s.code AS shelf
            FROM books b
            LEFT JOIN authors a ON a.id = b.author_id
            LEFT JOIN publishers p ON p.id = b.publisher_id
            LEFT JOIN bookshelves s ON s.id = b.shelf_id
            WHERE %s = '' OR b.title LIKE %s OR a.name LIKE %s OR b.isbn LIKE %s
                OR CAST(b.publication_year AS CHAR) LIKE %s OR p.name LIKE %s
            ORDER BY b.title
            """,
            (search, search_value, search_value, search_value, search_value, search_value),
        )
        if g.user["role"] in {"admin", "staff"}:
            authors = query_db("SELECT id, name FROM authors ORDER BY name")
            publishers = query_db("SELECT id, name FROM publishers ORDER BY name")
            shelves = query_db("SELECT id, code, section FROM bookshelves ORDER BY code")
        else:
            authors = publishers = shelves = []
        books_page, page, pages = paginate_rows(rows, request.args.get("page", 1, type=int))
        return render_template("books.html", books=books_page, authors=authors, publishers=publishers, shelves=shelves, search=search, page=page, pages=pages)

    @app.post("/books/<int:book_id>/copies")
    @roles_required("admin", "staff")
    def add_book_copy(book_id):
        query_db("UPDATE books SET total_copies = total_copies + 1, available_copies = available_copies + 1, status = 'available' WHERE id = %s", (book_id,), commit=True)
        log_audit("add_copy", "book", book_id)
        flash("One physical copy added.", "success")
        return redirect(url_for("books", q=request.form.get("q", "")))

    @app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
    @roles_required("admin")
    def edit_book(book_id):
        if request.method == "POST":
            total_copies = max(1, int(request.form.get("total_copies", "1") or 1))
            available_copies = max(0, min(total_copies, int(request.form.get("available_copies", "0") or 0)))
            query_db(
                "UPDATE books SET title = %s, isbn = %s, author_id = NULLIF(%s, ''), publisher_id = NULLIF(%s, ''), shelf_id = NULLIF(%s, ''), publication_year = NULLIF(%s, ''), total_copies = %s, available_copies = %s, status = CASE WHEN %s = 0 THEN 'borrowed' ELSE 'available' END WHERE id = %s",
                (request.form.get("title", "").strip(), request.form.get("isbn", "").strip(), request.form.get("author_id", ""), request.form.get("publisher_id", ""), request.form.get("shelf_id", ""), request.form.get("publication_year", ""), total_copies, available_copies, available_copies, book_id),
                commit=True,
            )
            log_audit("edit", "book", book_id)
            flash("Book updated.", "success")
            return redirect(url_for("books"))
        book = query_db("SELECT * FROM books WHERE id = %s", (book_id,), fetch_one=True)
        if not book:
            return jsonify({"error": "Book not found"}), 404
        return render_template("edit_book.html", book=book, authors=query_db("SELECT id, name FROM authors ORDER BY name"), publishers=query_db("SELECT id, name FROM publishers ORDER BY name"), shelves=query_db("SELECT id, code, section FROM bookshelves ORDER BY code"))

    @app.post("/catalogue/<entity>/<int:entity_id>/delete")
    @roles_required("admin")
    def delete_catalogue_item(entity, entity_id):
        tables = {"book": "books", "author": "authors", "publisher": "publishers", "shelf": "bookshelves"}
        if entity not in tables:
            return jsonify({"error": "Invalid catalogue entity"}), 400
        query_db(f"DELETE FROM {tables[entity]} WHERE id = %s", (entity_id,), commit=True)
        log_audit("delete", entity, entity_id)
        flash(f"{entity.capitalize()} deleted.", "success")
        return redirect(url_for("manage_catalogue"))

    @app.route("/catalogue/<entity>/<int:entity_id>/edit", methods=["GET", "POST"])
    @roles_required("admin")
    def edit_catalogue_item(entity, entity_id):
        if entity not in {"author", "publisher", "shelf"}:
            return jsonify({"error": "Invalid catalogue entity"}), 400
        table = {"author": "authors", "publisher": "publishers", "shelf": "bookshelves"}[entity]
        if request.method == "POST":
            if entity == "author":
                query_db("UPDATE authors SET name = %s, biography = %s WHERE id = %s", (request.form.get("name", "").strip(), request.form.get("biography", ""), entity_id), commit=True)
            elif entity == "publisher":
                query_db("UPDATE publishers SET name = %s, email = %s, phone = %s WHERE id = %s", (request.form.get("name", "").strip(), request.form.get("email", ""), request.form.get("phone", ""), entity_id), commit=True)
            else:
                query_db("UPDATE bookshelves SET code = %s, section = %s, description = %s WHERE id = %s", (request.form.get("code", "").strip(), request.form.get("section", "").strip(), request.form.get("description", ""), entity_id), commit=True)
            log_audit("edit", entity, entity_id)
            flash(f"{entity.capitalize()} updated.", "success")
            return redirect(url_for("manage_catalogue"))
        item = query_db(f"SELECT * FROM {table} WHERE id = %s", (entity_id,), fetch_one=True)
        if not item:
            return jsonify({"error": "Record not found"}), 404
        return render_template("edit_catalogue.html", entity=entity, item=item)

    @app.route("/catalogue/manage", methods=["GET", "POST"])
    @roles_required("admin", "staff")
    def manage_catalogue():
        if request.method == "POST":
            entity = request.form.get("entity")
            values = {
                "author": ("INSERT INTO authors (name, biography) VALUES (%s, %s)", (request.form.get("name", "").strip(), request.form.get("biography", ""))),
                "publisher": ("INSERT INTO publishers (name, email, phone) VALUES (%s, %s, %s)", (request.form.get("name", "").strip(), request.form.get("email", ""), request.form.get("phone", ""))),
                "shelf": ("INSERT INTO bookshelves (code, section, description) VALUES (%s, %s, %s)", (request.form.get("code", "").strip(), request.form.get("section", "").strip(), request.form.get("description", ""))),
            }
            if entity not in values:
                return jsonify({"error": "Invalid catalogue entity"}), 400
            query_db(values[entity][0], values[entity][1], commit=True)
            log_audit("create", entity)
            flash(f"{entity.capitalize()} added.", "success")
            return redirect(url_for("manage_catalogue"))
        authors, authors_page, authors_pages = paginate_rows(query_db("SELECT * FROM authors ORDER BY name"), request.args.get("authors_page", 1, type=int))
        publishers, publishers_page, publishers_pages = paginate_rows(query_db("SELECT * FROM publishers ORDER BY name"), request.args.get("publishers_page", 1, type=int))
        shelves, shelves_page, shelves_pages = paginate_rows(query_db("SELECT * FROM bookshelves ORDER BY code"), request.args.get("shelves_page", 1, type=int))
        return render_template("manage_catalogue.html", authors=authors, publishers=publishers, shelves=shelves, authors_page=authors_page, authors_pages=authors_pages, publishers_page=publishers_page, publishers_pages=publishers_pages, shelves_page=shelves_page, shelves_pages=shelves_pages)

    @app.post("/correction-reports")
    @roles_required("admin", "staff")
    def create_correction_report():
        entity_type = request.form.get("entity_type", "")
        requested_action = request.form.get("requested_action", "")
        entity_id = request.form.get("entity_id", "").strip()
        reason = request.form.get("reason", "").strip()
        if entity_type not in {"book", "author", "publisher", "bookshelf"} or requested_action not in {"correction", "deletion"} or not entity_id or not reason:
            flash("Record, reason, and requested action are required.", "error")
        else:
            query_db("INSERT INTO catalogue_correction_reports (submitted_by, entity_type, entity_id, reason, requested_action) VALUES (%s, %s, %s, %s, %s)", (g.user["id"], entity_type, entity_id, reason, requested_action), commit=True)
            log_audit("create", "catalogue_correction_report", details={"entity_type": entity_type, "entity_id": entity_id})
            flash("Correction report submitted to the admin.", "success")
        return redirect(url_for("manage_catalogue"))

    @app.get("/correction-reports")
    @roles_required("admin")
    def correction_reports():
        reports = query_db(
            """
            SELECT r.*, submitter.full_name AS submitter_name, handler.full_name AS handler_name,
                   CASE r.entity_type WHEN 'book' THEN (SELECT title FROM books WHERE id = r.entity_id) WHEN 'author' THEN (SELECT name FROM authors WHERE id = r.entity_id) WHEN 'publisher' THEN (SELECT name FROM publishers WHERE id = r.entity_id) WHEN 'bookshelf' THEN (SELECT code FROM bookshelves WHERE id = r.entity_id) END AS entity_name
            FROM catalogue_correction_reports r JOIN users submitter ON submitter.id = r.submitted_by LEFT JOIN users handler ON handler.id = r.handled_by ORDER BY r.submitted_at DESC
            """
        )
        reports, page, pages = paginate_rows(reports, request.args.get("page", 1, type=int))
        return render_template("correction_reports.html", reports=reports, page=page, pages=pages)

    @app.post("/correction-reports/<int:report_id>/<action>")
    @roles_required("admin")
    def update_correction_report(report_id, action):
        if action not in {"resolve", "decline"}:
            return jsonify({"error": "Invalid action"}), 400
        status = "resolved" if action == "resolve" else "declined"
        query_db("UPDATE catalogue_correction_reports SET status = %s, handled_by = %s, handled_at = NOW() WHERE id = %s AND status = 'pending'", (status, g.user["id"], report_id), commit=True)
        log_audit(action, "catalogue_correction_report", report_id)
        flash(f"Correction report {status}.", "success")
        return redirect(url_for("correction_reports"))

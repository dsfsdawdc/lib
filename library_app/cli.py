from flask import current_app
from werkzeug.security import generate_password_hash

from .shared import query_db


def register(app):
    @app.cli.command("create-admin")
    def create_admin():
        username = input("Admin username: ").strip()
        password = input("Admin password: ")
        full_name = input("Full name: ").strip()
        query_db(
            "INSERT INTO users (username, password_hash, full_name, role, status) VALUES (%s, %s, %s, 'admin', 'active')",
            (username, generate_password_hash(password), full_name),
            commit=True,
        )
        print("Admin account created.")

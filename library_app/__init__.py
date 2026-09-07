import os

from flask import Flask

from . import auth, catalogue, circulation, cli, system, users


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret"),
        MYSQL_HOST=os.getenv("MYSQL_HOST", "127.0.0.1"),
        MYSQL_PORT=int(os.getenv("MYSQL_PORT", "3306")),
        MYSQL_USER=os.getenv("MYSQL_USER", "root"),
        MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD", "mjlabao789"),
        MYSQL_DATABASE=os.getenv("MYSQL_DATABASE", "dblib"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
    )

    auth.register(app)
    system.register(app)
    catalogue.register(app)
    circulation.register(app)
    users.register(app)
    cli.register(app)
    return app

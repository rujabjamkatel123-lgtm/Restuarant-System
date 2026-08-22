from flask import Flask, render_template, redirect, url_for
import os

from app.routes.auth import AuthRoutes
from app.routes.customer import CustomerRoutes
from app.routes.receptionist import ReceptionistRoutes
from app.routes.manager import ManagerRoutes

import config


def create_app():

    # =========================================================
    # CREATE FLASK APP
    # =========================================================

    app = Flask(__name__)

    # =========================================================
    # SECRET KEY
    # =========================================================

    app.secret_key = config.SECRET_KEY

    # =========================================================
    # SESSION SETTINGS
    # =========================================================

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Vercel uses HTTPS.
    # Local development normally uses HTTP.
    #
    # IMPORTANT:
    # Do NOT use request.is_secure here because create_app()
    # runs before an HTTP request exists.

    app.config["SESSION_COOKIE_SECURE"] = (
        os.environ.get("VERCEL") == "1"
    )

    # =========================================================
    # AUTH ROUTES
    # =========================================================

    auth_routes = AuthRoutes()

    app.register_blueprint(
        auth_routes.register()
    )

    # =========================================================
    # ROOT ROUTE
    # =========================================================

    @app.route("/")
    def index():

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # CUSTOMER ROUTES
    # =========================================================

    customer_routes = CustomerRoutes()

    app.register_blueprint(
        customer_routes.register(),
        url_prefix="/customer"
    )

    # =========================================================
    # RECEPTIONIST ROUTES
    # =========================================================

    receptionist_routes = ReceptionistRoutes()

    app.register_blueprint(
        receptionist_routes.register(),
        url_prefix="/receptionist"
    )

    # =========================================================
    # MANAGER ROUTES
    # =========================================================

    manager_routes = ManagerRoutes()

    app.register_blueprint(
        manager_routes.register(),
        url_prefix="/manager"
    )

    # =========================================================
    # 404 ERROR
    # =========================================================

    @app.errorhandler(404)
    def page_not_found(error):

        return render_template(
            "notfound.html"
        ), 404

    # =========================================================
    # 500 ERROR
    # =========================================================

    @app.errorhandler(500)
    def internal_server_error(error):

        print(
            "FLASK INTERNAL SERVER ERROR:",
            repr(error)
        )

        return (
            "Internal Server Error. "
            "Please check the Vercel logs."
        ), 500

    # =========================================================
    # RETURN APP
    # =========================================================

    return app
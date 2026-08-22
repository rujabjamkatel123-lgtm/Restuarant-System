from flask import Flask, render_template, redirect, url_for, request

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
    app.config["SESSION_COOKIE_SECURE"] = False

    # IMPORTANT:
    #
    # Local development:
    #     http://127.0.0.1:5000
    #     http://localhost:5000
    #
    # Vercel:
    #     https://restuarantsystem.vercel.app
    #
    # Secure cookies are required on HTTPS but should not
    # be forced during local HTTP development.

    app.config["SESSION_COOKIE_SECURE"] = (
        request.is_secure
    )

    # =========================================================
    # AUTH ROUTES
    # =========================================================

    auth_routes = AuthRoutes()

    app.register_blueprint(
        auth_routes.register()
    )

    # =========================================================
    # ROOT
    # =========================================================

    @app.route("/")
    def index():

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # CUSTOMER ROUTES
    #
    # IMPORTANT:
    #
    # Customer QR ordering does NOT require login.
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
            "Please check the Vercel logs.",
            500
        )

    # =========================================================
    # RETURN APP
    # =========================================================

    return app
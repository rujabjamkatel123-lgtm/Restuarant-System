from flask import (
    Flask,
    render_template,
    redirect,
    url_for
)

from app.routes.auth import AuthRoutes
from app.routes.customer import CustomerRoutes
from app.routes.receptionist import ReceptionistRoutes
from app.routes.manager import ManagerRoutes

import config


def create_app():

    # =========================================================
    # CREATE FLASK APPLICATION
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

    # IMPORTANT:
    # Do NOT use request.is_secure here.
    #
    # Vercel calls create_app() before an HTTP request exists.
    #
    # Vercel uses HTTPS, so this can safely be True.
    app.config["SESSION_COOKIE_SECURE"] = True

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
    # NO LOGIN REQUIRED
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

        return render_template(
            "notfound.html"
        ), 500

    # =========================================================
    # RETURN APPLICATION
    # =========================================================

    return app
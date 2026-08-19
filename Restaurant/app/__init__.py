from flask import Flask, render_template, redirect, url_for  # <--- Make sure redirect and url_for are imported

from app.routes.auth import AuthRoutes
from app.modules.database import Database
from app.routes.customer import CustomerRoutes
from app.routes.receptionist import ReceptionistRoutes
from app.routes.manager import ManagerRoutes    
import config


def create_app():

    # ── Create Flask application ─────────────────────
    app = Flask(__name__)

    # ── Secret key for sessions and flash messages ───
    app.secret_key = config.SECRET_KEY

    # ── Create database tables ───────────────────────
    with app.app_context():
        Database.create_tables()

    # ── Register authentication and dashboard routes ─
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())

    # ── Root URL redirect to Login ───────────────────
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # ── 404 Error Page ───────────────────────────────
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("notfound.html"), 404

    customer_routes = CustomerRoutes()
    app.register_blueprint(
        customer_routes.register(),
        url_prefix="/customer"
    )

    receptionist_routes = ReceptionistRoutes()
    app.register_blueprint(
        receptionist_routes.register(),
        url_prefix="/receptionist"
    )

    manager_routes = ManagerRoutes()
    app.register_blueprint(
        manager_routes.register(),
        url_prefix="/manager"
    )

    return app
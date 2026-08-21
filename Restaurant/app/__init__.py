from flask import Flask, render_template, redirect, url_for

from app.routes.auth import AuthRoutes
from app.routes.customer import CustomerRoutes
from app.routes.receptionist import ReceptionistRoutes
from app.routes.manager import ManagerRoutes

from app.modules.database import Database

import config


def create_app():

    app = Flask(__name__)

    # =====================================================
    # SECRET KEY
    # =====================================================

    app.secret_key = config.SECRET_KEY

    # =====================================================
    # DATABASE
    # =====================================================

    with app.app_context():
        Database.create_tables()

    # =====================================================
    # AUTH ROUTES
    # =====================================================

    auth_routes = AuthRoutes()

    app.register_blueprint(
        auth_routes.register()
    )

    # =====================================================
    # ROOT
    # =====================================================

    @app.route("/")
    def index():

        return redirect(
            url_for("auth.login")
        )

    # =====================================================
    # CUSTOMER
    # =====================================================

    customer_routes = CustomerRoutes()

    app.register_blueprint(
        customer_routes.register(),
        url_prefix="/customer"
    )

    # =====================================================
    # RECEPTIONIST
    # =====================================================

    receptionist_routes = ReceptionistRoutes()

    app.register_blueprint(
        receptionist_routes.register(),
        url_prefix="/receptionist"
    )

    # =====================================================
    # MANAGER
    # =====================================================

    manager_routes = ManagerRoutes()

    app.register_blueprint(
        manager_routes.register(),
        url_prefix="/manager"
    )

    # =====================================================
    # 404
    # =====================================================

    @app.errorhandler(404)
    def page_not_found(error):

        return render_template(
            "notfound.html"
        ), 404

    return app
from flask import Blueprint

from app.controllers.manager import ManagerController
from app.auth import manager_required


class ManagerRoutes:
    def __init__(self):
        self.bp = Blueprint("manager", __name__)
        self.controller = ManagerController()

    def register(self):

        # ── Manager Dashboard ────────────────────────────────
        self.bp.route("/dashboard", methods=["GET"])(
            manager_required(self.controller.dashboard)
        )

        # ── Menu Management ─────────────────────────────────
        self.bp.route("/menu", methods=["GET"])(
            manager_required(self.controller.menu)
        )

        # ── Add Menu Item ───────────────────────────────────
        self.bp.route("/menu/add", methods=["GET", "POST"])(
            manager_required(self.controller.add_menu_item)
        )

        # ── Edit Menu Item ──────────────────────────────────
        self.bp.route(
            "/menu/edit/<int:item_id>",
            methods=["GET", "POST"]
        )(
            manager_required(self.controller.edit_menu_item)
        )

        # ── Delete Menu Item ─────────────────────────────────
        self.bp.route(
            "/menu/delete/<int:item_id>",
            methods=["POST"]
        )(
            manager_required(self.controller.delete_menu_item)
        )

        # ── Order History ───────────────────────────────────
        self.bp.route("/history", methods=["GET"])(
            manager_required(self.controller.history)
        )

        # ── Reports ─────────────────────────────────────────
        self.bp.route("/reports", methods=["GET"])(
            manager_required(self.controller.reports)
        )

        # ── Sales Statistics ─────────────────────────────────
        self.bp.route("/sales", methods=["GET"])(
            manager_required(self.controller.sales)
        )

        # ── Filter Reports By Date ──────────────────────────
        self.bp.route("/reports/filter", methods=["GET"])(
            manager_required(self.controller.filter_reports)
        )

        # ── View Order ──────────────────────────────────────
        self.bp.route(
            "/order/<int:order_id>",
            methods=["GET"]
        )(
            manager_required(self.controller.view_order)
        )

        return self.bp  
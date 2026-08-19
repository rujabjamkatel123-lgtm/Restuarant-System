from flask import Blueprint

from app.controllers.receptionist import ReceptionistController
from app.auth import login_required, receptionist_required


class ReceptionistRoutes:
    def __init__(self):
        self.bp = Blueprint("receptionist", __name__)
        self.controller = ReceptionistController()

    def register(self):

        # ── Receptionist Dashboard ──────────────────────────
        self.bp.route("/dashboard", methods=["GET"])(
            receptionist_required(self.controller.dashboard)
        )

        # ── Order Management ────────────────────────────────
        self.bp.route("/orders", methods=["GET"])(
            receptionist_required(self.controller.orders)
        )

        # ── View Single Order ────────────────────────────────
        self.bp.route("/order/<int:order_id>", methods=["GET"])(
            receptionist_required(self.controller.view_order)
        )

        # ── Mark Order As Preparing ──────────────────────────
        self.bp.route(
            "/order/<int:order_id>/preparing",
            methods=["POST"]
        )(
            receptionist_required(self.controller.mark_preparing)
        )

        # ── Mark Order As Ready ──────────────────────────────
        self.bp.route(
            "/order/<int:order_id>/ready",
            methods=["POST"]
        )(
            receptionist_required(self.controller.mark_ready)
        )

        # ── Mark Order As Served ────────────────────────────
        self.bp.route(
            "/order/<int:order_id>/served",
            methods=["POST"]
        )(
            receptionist_required(self.controller.mark_served)
        )

        # ── Cancel Order ────────────────────────────────────
        self.bp.route(
            "/order/<int:order_id>/cancel",
            methods=["POST"]
        )(
            receptionist_required(self.controller.cancel_order)
        )

        # ── Notifications ───────────────────────────────────
        self.bp.route("/notifications", methods=["GET"])(
            receptionist_required(self.controller.notifications)
        )

        return self.bp
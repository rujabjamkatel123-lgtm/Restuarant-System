from flask import Blueprint

from app.controllers.customer import CustomerController
from app.auth import login_required


class CustomerRoutes:
    def __init__(self):
        self.bp = Blueprint("customer", __name__)
        self.controller = CustomerController()

    def register(self):

        # ── Customer Dashboard ───────────────────────────────
        self.bp.route("/dashboard", methods=["GET"])(
            login_required(self.controller.dashboard)
        )

        # ── Customer Menu ───────────────────────────────────
        self.bp.route("/menu", methods=["GET"])(
            login_required(self.controller.menu)
        )

        # ── Add Item To Cart ────────────────────────────────
        self.bp.route("/cart/add/<int:item_id>", methods=["POST"])(
            login_required(self.controller.add_to_cart)
        )

        # ── View Cart ───────────────────────────────────────
        self.bp.route("/cart", methods=["GET"])(
            login_required(self.controller.cart)
        )

        # ── Update Cart Item Quantity ───────────────────────
        self.bp.route("/cart/update/<int:item_id>", methods=["POST"])(
            login_required(self.controller.update_cart)
        )

        # ── Remove Item From Cart ───────────────────────────
        self.bp.route("/cart/remove/<int:item_id>", methods=["POST"])(
            login_required(self.controller.remove_from_cart)
        )

        # ── Clear Cart ──────────────────────────────────────
        self.bp.route("/cart/clear", methods=["POST"])(
            login_required(self.controller.clear_cart)
        )

        # ── Select Table ───────────────────────────────────
        self.bp.route("/table/<int:table_id>", methods=["POST"])(
            login_required(self.controller.select_table)
        )

        # ── Place Order ─────────────────────────────────────
        self.bp.route("/order/place", methods=["POST"])(
            login_required(self.controller.place_order)
        )

        # ── Customer Orders ─────────────────────────────────
        self.bp.route("/orders", methods=["GET"])(
            login_required(self.controller.orders)
        )

        # ── View Single Order ───────────────────────────────
        self.bp.route("/order/<int:order_id>", methods=["GET"])(
            login_required(self.controller.view_order)
        )

        # ── Mobile Customer Dashboard ───────────────────────
        self.bp.route("/mobile", methods=["GET"])(
            login_required(self.controller.mobile)
        )

        return self.bp
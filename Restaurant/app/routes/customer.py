from flask import Blueprint

from app.controllers.customer import CustomerController


class CustomerRoutes:

    def __init__(self):
        self.bp = Blueprint("customer", __name__)
        self.controller = CustomerController()

    def register(self):

        # =====================================================
        # CUSTOMER DASHBOARD
        # =====================================================
        # IMPORTANT:
        # NO login_required
        #
        # Customer enters through QR code.
        # =====================================================

        self.bp.route(
            "/dashboard",
            methods=["GET"]
        )(
            self.controller.dashboard
        )

        # =====================================================
        # MENU
        # =====================================================

        self.bp.route(
            "/menu",
            methods=["GET"]
        )(
            self.controller.menu
        )

        # =====================================================
        # ADD TO CART
        # =====================================================

        self.bp.route(
            "/cart/add/<int:item_id>",
            methods=["POST"]
        )(
            self.controller.add_to_cart
        )

        # =====================================================
        # CART
        # =====================================================

        self.bp.route(
            "/cart",
            methods=["GET"]
        )(
            self.controller.cart
        )

        # =====================================================
        # UPDATE CART
        # =====================================================

        self.bp.route(
            "/cart/update/<int:item_id>",
            methods=["POST"]
        )(
            self.controller.update_cart
        )

        # =====================================================
        # REMOVE FROM CART
        # =====================================================

        self.bp.route(
            "/cart/remove/<int:item_id>",
            methods=["POST"]
        )(
            self.controller.remove_from_cart
        )

        # =====================================================
        # CLEAR CART
        # =====================================================

        self.bp.route(
            "/cart/clear",
            methods=["POST"]
        )(
            self.controller.clear_cart
        )

        # =====================================================
        # PLACE ORDER
        # =====================================================

        self.bp.route(
            "/order/place",
            methods=["POST"]
        )(
            self.controller.place_order
        )

        # =====================================================
        # QR TABLE ENTRY
        #
        # NO LOGIN REQUIRED
        #
        # Example:
        #
        # Table 1 -> /customer/qr/1
        # Table 2 -> /customer/qr/2
        # Table 5 -> /customer/qr/5
        # =====================================================

        self.bp.route(
            "/qr/<int:table_id>",
            methods=["GET"]
        )(
            self.controller.scan_qr
        )

        # =====================================================
        # ORDER HISTORY
        # =====================================================

        self.bp.route(
            "/orders",
            methods=["GET"]
        )(
            self.controller.orders
        )

        # =====================================================
        # SINGLE ORDER
        # =====================================================

        self.bp.route(
            "/order/<int:order_id>",
            methods=["GET"]
        )(
            self.controller.view_order
        )

        return self.bp
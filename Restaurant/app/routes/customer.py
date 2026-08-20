from flask import Blueprint

from app.controllers.customer import CustomerController


class CustomerRoutes:

    def __init__(self):

        self.bp = Blueprint(
            "customer",
            __name__
        )

        self.controller = CustomerController()

    def register(self):

        # =====================================================
        # CUSTOMER DASHBOARD
        #
        # NO LOGIN REQUIRED
        #
        # Customer reaches this page through QR code.
        # =====================================================

        self.bp.route(
            "/dashboard",
            methods=["GET"]
        )(
            self.controller.dashboard
        )

        # =====================================================
        # QR CODE ENTRY
        #
        # NO LOGIN REQUIRED
        #
        # Examples:
        #
        # /customer/qr/1
        # /customer/qr/2
        # /customer/qr/5
        #
        # This route identifies the customer's table and
        # stores it in the session.
        # =====================================================

        self.bp.route(
            "/qr/<int:table_id>",
            methods=["GET"]
        )(
            self.controller.scan_qr
        )

        # =====================================================
        # MENU
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/menu",
            methods=["GET"]
        )(
            self.controller.menu
        )

        # =====================================================
        # ADD ITEM TO CART
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/cart/add/<int:item_id>",
            methods=["POST"]
        )(
            self.controller.add_to_cart
        )

        # =====================================================
        # VIEW CART
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/cart",
            methods=["GET"]
        )(
            self.controller.cart
        )

        # =====================================================
        # UPDATE CART ITEM QUANTITY
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/cart/update/<int:item_id>",
            methods=["POST"]
        )(
            self.controller.update_cart
        )

        # =====================================================
        # REMOVE ITEM FROM CART
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/cart/remove/<int:item_id>",
            methods=["POST"]
        )(
            self.controller.remove_from_cart
        )

        # =====================================================
        # CLEAR CART
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/cart/clear",
            methods=["POST"]
        )(
            self.controller.clear_cart
        )

        # =====================================================
        # PLACE ORDER
        #
        # NO LOGIN REQUIRED
        #
        # Table is obtained from the QR/session.
        # =====================================================

        self.bp.route(
            "/order/place",
            methods=["POST"]
        )(
            self.controller.place_order
        )

        # =====================================================
        # CUSTOMER ORDER HISTORY
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/orders",
            methods=["GET"]
        )(
            self.controller.orders
        )

        # =====================================================
        # VIEW SINGLE ORDER
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/order/<int:order_id>",
            methods=["GET"]
        )(
            self.controller.view_order
        )

        # =====================================================
        # MOBILE CUSTOMER DASHBOARD
        #
        # NO LOGIN REQUIRED
        # =====================================================

        self.bp.route(
            "/mobile",
            methods=["GET"]
        )(
            self.controller.mobile
        )

        # =====================================================
        # RETURN BLUEPRINT
        # =====================================================

        return self.bp
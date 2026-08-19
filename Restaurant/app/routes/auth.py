from flask import Blueprint

from app.controllers.auth import AuthController
from app.auth import login_required, role_required


class AuthRoutes:

    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()

    def register(self):

        # =====================================================
        # AUTHENTICATION ROUTES
        # =====================================================

        # ── Login ────────────────────────────────────────────
        self.bp.route(
            "/login",
            methods=["GET", "POST"]
        )(
            self.controller.login
        )

        # ── Mobile Login ─────────────────────────────────────
        self.bp.route(
            "/mobile-login",
            methods=["GET", "POST"]
        )(
            self.controller.mobile_login
        )

        # ── Register Customer ────────────────────────────────
        self.bp.route(
            "/register",
            methods=["GET", "POST"]
        )(
            self.controller.register
        )

        # ── Forgot Password ──────────────────────────────────
        self.bp.route(
            "/forgot-password",
            methods=["GET", "POST"]
        )(
            self.controller.forgot_password
        )

        # ── Verify OTP ───────────────────────────────────────
        self.bp.route(
            "/verify-otp",
            methods=["GET", "POST"]
        )(
            self.controller.verify_otp
        )

        # ── Logout ───────────────────────────────────────────
        self.bp.route(
            "/logout",
            methods=["GET", "POST"]
        )(
            self.controller.logout
        )


        # =====================================================
        # CUSTOMER ROUTES
        # =====================================================

        # ── Customer Dashboard ──────────────────────────────
        self.bp.route(
            "/customer",
            methods=["GET"]
        )(
            role_required("customer")(
                self.controller.customer_dashboard
            )
        )

        # ── Customer Mobile Dashboard ────────────────────────
        self.bp.route(
            "/customer/mobile",
            methods=["GET"]
        )(
            role_required("customer")(
                self.controller.customer_mobile_dashboard
            )
        )

        # ── Customer Menu ────────────────────────────────────
        self.bp.route(
            "/customer/menu",
            methods=["GET"]
        )(
            role_required("customer")(
                self.controller.menu
            )
        )

        # ── Customer Add Item To Cart ────────────────────────
        self.bp.route(
            "/customer/cart/add/<int:item_id>",
            methods=["POST"]
        )(
            role_required("customer")(
                self.controller.add_to_cart
            )
        )

        # ── Customer View Cart ───────────────────────────────
        self.bp.route(
            "/customer/cart",
            methods=["GET"]
        )(
            role_required("customer")(
                self.controller.view_cart
            )
        )

        # ── Customer Remove Item From Cart ───────────────────
        self.bp.route(
            "/customer/cart/remove/<int:item_id>",
            methods=["POST"]
        )(
            role_required("customer")(
                self.controller.remove_from_cart
            )
        )

        # ── Customer Update Cart ─────────────────────────────
        self.bp.route(
            "/customer/cart/update/<int:item_id>",
            methods=["POST"]
        )(
            role_required("customer")(
                self.controller.update_cart
            )
        )

        # ── Customer Place Order ─────────────────────────────
        self.bp.route(
            "/customer/order/place",
            methods=["POST"]
        )(
            role_required("customer")(
                self.controller.place_order
            )
        )

        # ── Customer Order History ───────────────────────────
        self.bp.route(
            "/customer/history",
            methods=["GET"],
            endpoint="customer_order_history"
        )(
            role_required("customer")(
                self.controller.order_history
            )
        )

        # ── Customer Change Password ─────────────────────────
        self.bp.route(
            "/customer/change-password",
            methods=["POST"]
        )(
            role_required("customer")(
                self.controller.change_password
            )
        )


        # =====================================================
        # RECEPTIONIST ROUTES
        # =====================================================

        # ── Receptionist Dashboard ───────────────────────────
        self.bp.route(
            "/receptionist",
            methods=["GET"]
        )(
            role_required("receptionist")(
                self.controller.receptionist_dashboard
            )
        )

        # ── Receptionist Home ────────────────────────────────
        self.bp.route(
            "/receptionist/home",
            methods=["GET"]
        )(
            role_required("receptionist")(
                self.controller.receptionist_home
            )
        )

        # ── Receptionist Order Management ────────────────────
        self.bp.route(
            "/receptionist/orders",
            methods=["GET"]
        )(
            role_required("receptionist")(
                self.controller.order_management
            )
        )

        # ── Mark Order Preparing ─────────────────────────────
        self.bp.route(
            "/receptionist/order/<int:order_id>/preparing",
            methods=["POST"]
        )(
            role_required("receptionist")(
                self.controller.mark_preparing
            )
        )

        # ── Mark Order Ready ─────────────────────────────────
        self.bp.route(
            "/receptionist/order/<int:order_id>/ready",
            methods=["POST"]
        )(
            role_required("receptionist")(
                self.controller.mark_ready
            )
        )

        # ── Mark Order Served ────────────────────────────────
        self.bp.route(
            "/receptionist/order/<int:order_id>/served",
            methods=["POST"]
        )(
            role_required("receptionist")(
                self.controller.mark_served
            )
        )


        # =====================================================
        # MANAGER ROUTES
        # =====================================================

        # ── Manager Dashboard ────────────────────────────────
        self.bp.route(
            "/manager",
            methods=["GET"]
        )(
            role_required("manager")(
                self.controller.manager_dashboard
            )
        )

        # ── Manager Statistics ───────────────────────────────
        self.bp.route(
            "/manager/statistics",
            methods=["GET"]
        )(
            role_required("manager")(
                self.controller.statistics
            )
        )

        # ── Manager Sales Report ─────────────────────────────
        self.bp.route(
            "/manager/sales",
            methods=["GET"]
        )(
            role_required("manager")(
                self.controller.sales_report
            )
        )

        # ── Manager Order History ────────────────────────────
        self.bp.route(
            "/manager/history",
            methods=["GET"],
            endpoint="manager_order_history"
        )(
            role_required("manager")(
                self.controller.order_history
            )
        )

        # ── Manager Menu Management ──────────────────────────
        self.bp.route(
            "/manager/menu/add",
            methods=["POST"]
        )(
            role_required("manager")(
                self.controller.add_menu_item
            )
        )

        self.bp.route(
            "/manager/menu/edit/<int:item_id>",
            methods=["POST"]
        )(
            role_required("manager")(
                self.controller.edit_menu_item
            )
        )

        self.bp.route(
            "/manager/menu/delete/<int:item_id>",
            methods=["POST"]
        )(
            role_required("manager")(
                self.controller.delete_menu_item
            )
        )

        # =====================================================
        # RETURN BLUEPRINT
        # =====================================================

        return self.bp
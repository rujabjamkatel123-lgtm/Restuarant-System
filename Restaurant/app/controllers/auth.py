"""
=============================================================
  Restaurant Management System
  AuthController

  Responsibilities:
      - Login / Register / Logout
      - Forgot Password / OTP
      - Customer Dashboard
      - Customer Menu and Cart
      - Customer Order Placement
      - Customer Order History
      - Receptionist Order Management
      - Manager Dashboard and Reports
      - Manager Menu Management
=============================================================
"""

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.controllers.base_controllers import BaseController
from app.modules.user import User
from app.modules.menu import MenuItem
from app.modules.database import Database
import os

from werkzeug.utils import secure_filename
from flask import current_app
    

class AuthController(BaseController):

    def __init__(self):
        super().__init__()

        self.user_model = User()
        self.menu_model = MenuItem()

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    def login(self):
        """
        Login for customer, receptionist and manager.
        """

        if request.method == "GET":
            return render_template("auth/login.html")

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        mobile = request.form.get("mobile")

        if not email or not password:
            flash(
                "Email and password are required.",
                "danger"
            )
            return render_template("auth/login.html")

        user_data = self.user_model.find_by_email(email)

        if not user_data:
            flash(
                "Invalid email or password.",
                "danger"
            )
            return render_template("auth/login.html")

        user = User.from_db(user_data)

        if not user.check_password(password):
            flash(
                "Invalid email or password.",
                "danger"
            )
            return render_template("auth/login.html")

        # Store login information in session
        session["user_id"] = user_data["id"]
        session["user_name"] = user_data["name"]
        session["user_email"] = user_data["email"]
        session["role"] = user_data["role"]

        # Mobile login
        if mobile and user_data["role"] == "customer":
            return redirect(
                url_for("auth.customer_mobile_dashboard")
            )

        # Normal dashboard based on role
        if user_data["role"] == "customer":

            return redirect(
                url_for("auth.customer_dashboard")
            )

        elif user_data["role"] == "receptionist":

            return redirect(
                url_for("auth.receptionist_dashboard")
            )

        elif user_data["role"] == "manager":

            return redirect(
                url_for("auth.manager_dashboard")
            )

        flash(
            "Invalid user role.",
            "danger"
        )

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # MOBILE LOGIN
    # =========================================================

    def mobile_login(self):
        """
        Mobile-specific login page.
        """

        if request.method == "GET":

            return render_template(
                "auth/mobile_login.html"
            )

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if not email or not password:

            flash(
                "Email and password are required.",
                "danger"
            )

            return render_template(
                "auth/mobile_login.html"
            )

        user_data = self.user_model.find_by_email(
            email
        )

        if not user_data:

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "auth/mobile_login.html"
            )

        user = User.from_db(user_data)

        if not user.check_password(password):

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "auth/mobile_login.html"
            )

        session["user_id"] = user_data["id"]
        session["user_name"] = user_data["name"]
        session["user_email"] = user_data["email"]
        session["role"] = user_data["role"]

        if user_data["role"] == "customer":

            return redirect(
                url_for(
                    "auth.customer_mobile_dashboard"
                )
            )

        flash(
            "Mobile dashboard is currently available for customers.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # REGISTER
    # =========================================================

    def register(self):
        """
        Register a new customer.
        """

        if request.method == "GET":

            return render_template(
                "auth/register.html"
            )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        if not name or not email or not password:

            flash(
                "All required fields must be filled.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        role = request.form.get(
            "role",
            "customer"
        ).strip().lower()

        if role not in [
            "customer",
            "receptionist",
            "manager"
        ]:

            flash(
                "Invalid role selected.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        new_user = User(
            name=name,
            email=email,
            password=password,
            role=role
        )

        if new_user.email_exists():

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        new_user.save()

        flash(
            "Account created successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):

        session.clear()

        flash(
            "You have been logged out successfully.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # FORGOT PASSWORD
    # =========================================================

    def forgot_password(self):
        """
        Start forgot-password process.
        """

        if request.method == "GET":

            return render_template(
                "auth/forgot_password.html"
            )

        email = request.form.get(
            "email",
            ""
        ).strip()

        if not email:

            flash(
                "Please enter your email.",
                "danger"
            )

            return render_template(
                "auth/forgot_password.html"
            )

        user = self.user_model.find_by_email(
            email
        )

        if not user:

            flash(
                "No account was found with this email.",
                "danger"
            )

            return render_template(
                "auth/forgot_password.html"
            )

        import random
        from datetime import datetime, timedelta

        otp = str(
            random.randint(100000, 999999)
        )

        hashed_otp = generate_password_hash(otp)

        expiry_time = (
            datetime.now()
            + timedelta(minutes=5)
        )

        self.user_model.save_reset_otp(
            email,
            hashed_otp,
            expiry_time
        )

        session["reset_email"] = email

        # Development only
        print(
            f"PASSWORD RESET OTP for {email}: {otp}"
        )

        flash(
            "OTP generated. Check the development console.",
            "success"
        )

        return redirect(
            url_for("auth.verify_otp")
        )

    # =========================================================
    # VERIFY OTP
    # =========================================================

    def verify_otp(self):

        if request.method == "GET":

            return render_template(
                "auth/verify_otp.html"
            )

        email = session.get(
            "reset_email"
        )

        if not email:

            flash(
                "Password reset session expired.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        otp = request.form.get(
            "otp",
            ""
        ).strip()

        new_password = request.form.get(
            "password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        if not otp or not new_password:

            flash(
                "OTP and new password are required.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html"
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html"
            )

        user_data = self.user_model.find_by_email(
            email
        )

        if not user_data:

            flash(
                "User not found.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        from datetime import datetime

        stored_otp = user_data.get(
            "reset_otp"
        )

        otp_expiry = user_data.get(
            "reset_otp_expires"
        )

        if not stored_otp:

            flash(
                "Invalid OTP.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html"
            )

        if otp_expiry and datetime.now() > otp_expiry:

            flash(
                "OTP has expired.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html"
            )

        if not check_password_hash(
            stored_otp,
            otp
        ):

            flash(
                "Invalid OTP.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html"
            )

        hashed_password = generate_password_hash(
            new_password,
            method="pbkdf2:sha256"
        )

        self.user_model.update_password_by_email(
            email,
            hashed_password
        )

        session.pop(
            "reset_email",
            None
        )

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    # =========================================================
    # CHANGE PASSWORD
    # =========================================================

    def change_password(self):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        current_password = request.form.get(
            "current_password",
            ""
        ).strip()

        new_password = request.form.get(
            "new_password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        user_data = self.user_model.find_by_id(
            session["user_id"]
        )

        if not user_data:

            flash(
                "User not found.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        user = User.from_db(user_data)

        if not user.check_password(
            current_password
        ):

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.login")
            )

        if new_password != confirm_password:

            flash(
                "New passwords do not match.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.login")
            )

        user.name = user_data["name"]
        user.email = user_data["email"]

        user.set_password(
            new_password
        )

        user.update(
            session["user_id"],
            update_password=True
        )

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            request.referrer or
            url_for("auth.login")
        )

    # =========================================================
    # CUSTOMER DASHBOARD
    # =========================================================

    def customer_dashboard(self):

        menu_items = self.menu_model.get_all()

        tables = self.get_tables()

        cart = session.get(
            "cart",
            {}
        )

        cart_total = self.calculate_cart_total(
            cart
        )

        return render_template(
            "customer/dashboard.html",
            menu_items=menu_items,
            tables=tables,
            cart=cart,
            cart_total=cart_total,
            user_name=session.get("user_name")
        )

    # =========================================================
    # CUSTOMER MOBILE DASHBOARD
    # =========================================================

    def customer_mobile_dashboard(self):

        menu_items = self.menu_model.get_all()

        tables = self.get_tables()

        cart = session.get(
            "cart",
            {}
        )

        cart_total = self.calculate_cart_total(
            cart
        )

        return render_template(
            "customer/mobile_dashboard.html",
            menu_items=menu_items,
            tables=tables,
            cart=cart,
            cart_total=cart_total,
            user_name=session.get("user_name")
        )

    # =========================================================
    # CUSTOMER MENU
    # =========================================================

    def menu(self):

        menu_items = self.menu_model.get_all()

        cart = session.get(
            "cart",
            {}
        )

        cart_total = self.calculate_cart_total(
            cart
        )

        return render_template(
            "customer/dashboard.html",
            menu_items=menu_items,
            cart=cart,
            cart_total=cart_total
        )

    # =========================================================
    # CUSTOMER VIEW CART
    # =========================================================

    def view_cart(self):

        cart = session.get(
            "cart",
            {}
        )

        cart_total = self.calculate_cart_total(
            cart
        )

        tables = self.get_tables()

        return render_template(
            "customer/cart.html",
            cart=cart,
            cart_total=cart_total,
            tables=tables,
            user_name=session.get("user_name")
        )

    # =========================================================
    # ADD ITEM TO CART
    # =========================================================

    def add_to_cart(self, item_id):

        item = self.menu_model.find_by_id(
            item_id
        )

        if not item:

            flash(
                "Menu item not found.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.customer_dashboard")
            )

        quantity = request.form.get(
            "quantity",
            1
        )

        try:

            quantity = int(quantity)

            if quantity < 1:
                quantity = 1

        except (ValueError, TypeError):

            quantity = 1

        cart = session.get(
            "cart",
            {}
        )

        item_key = str(item_id)

        if item_key in cart:

            cart[item_key]["quantity"] += quantity

        else:

            cart[item_key] = {
                "id": item["id"],
                "name": item["name"],
                "price": float(item["price"]),
                "quantity": quantity
            }

        session["cart"] = cart
        session.modified = True

        flash(
            f"{item['name']} added to cart.",
            "success"
        )

        return redirect(
            request.referrer or
            url_for("auth.customer_dashboard")
        )

    # =========================================================
    # REMOVE ITEM FROM CART
    # =========================================================

    def remove_from_cart(self, item_id):

        cart = session.get(
            "cart",
            {}
        )

        item_key = str(item_id)

        if item_key in cart:

            item_name = cart[item_key].get(
                "name",
                "Item"
            )

            del cart[item_key]

            session["cart"] = cart
            session.modified = True

            flash(
                f"{item_name} removed from cart.",
                "success"
            )

        return redirect(
            url_for("auth.view_cart")
        )

    # =========================================================
    # UPDATE CART
    # =========================================================

    def update_cart(self, item_id):

        quantity = request.form.get(
            "quantity",
            1
        )

        try:

            quantity = int(quantity)

        except (ValueError, TypeError):

            quantity = 1

        cart = session.get(
            "cart",
            {}
        )

        item_key = str(item_id)

        if item_key in cart:

            if quantity <= 0:

                del cart[item_key]

            else:

                cart[item_key]["quantity"] = quantity

            session["cart"] = cart
            session.modified = True

        return redirect(
            request.referrer or
            url_for("auth.view_cart")
        )

    # =========================================================
    # PLACE ORDER
    # =========================================================

    def place_order(self):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        cart = session.get(
            "cart",
            {}
        )

        if not cart:

            flash(
                "Your cart is empty.",
                "warning"
            )

            return redirect(
                url_for("auth.view_cart")
            )

        table_id = request.form.get(
            "table_id"
        )

        if not table_id:

            flash(
                "Please select a table.",
                "warning"
            )

            return redirect(
                url_for("auth.view_cart")
            )

        db = Database()

        try:

            db.execute(
                """
                INSERT INTO orders
                (user_id, table_id, status)
                VALUES (%s, %s, %s)
                """,
                (
                    session["user_id"],
                    table_id,
                    "pending"
                )
            )

            order = db.fetch_one(
                """
                SELECT LAST_INSERT_ID() AS id
                """
            )

            if not order:

                raise Exception(
                    "Unable to create order."
                )

            order_id = order["id"]

            for item in cart.values():

                db.execute(
                    """
                    INSERT INTO order_items
                    (
                        order_id,
                        item_id,
                        quantity,
                        price_at_order
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["id"],
                        item["quantity"],
                        item["price"]
                    )
                )

            db.close()

            session["cart"] = {}
            session.modified = True

            flash(
                "Order placed successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "auth.customer_order_history"
                )
            )

        except Exception as e:

            try:
                db.close()
            except Exception:
                pass

            print(
                "Order placement error:",
                e
            )

            flash(
                "Unable to place order.",
                "danger"
            )

            return redirect(
                url_for("auth.view_cart")
            )

    # =========================================================
    # CUSTOMER / MANAGER ORDER HISTORY
    # =========================================================

    def order_history(self):

        if session.get("role") == "manager":

            return self.manager_order_history()

        if "user_id" not in session:

            flash(
                "Please login first.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        db = Database()

        orders = db.fetch_all(
            """
            SELECT
                o.id,
                o.created_at,
                o.status,
                t.name AS table_name,

                COALESCE(
                    SUM(
                        oi.quantity *
                        oi.price_at_order
                    ),
                    0
                ) AS total

            FROM orders o

            LEFT JOIN restaurant_tables t
                ON o.table_id = t.id

            LEFT JOIN order_items oi
                ON o.id = oi.order_id

            WHERE o.user_id = %s

            GROUP BY
                o.id,
                o.created_at,
                o.status,
                t.name

            ORDER BY o.id DESC
            """,
            (
                session["user_id"],
            )
        )

        db.close()

        return render_template(
            "customer/orders.html",
            orders=orders
        )

    # =========================================================
    # RECEPTIONIST DASHBOARD
    # =========================================================

    def receptionist_dashboard(self):

        orders = self.get_incoming_orders()

        return render_template(
            "receptionist/dashboard.html",
            orders=orders
        )

    # =========================================================
    # RECEPTIONIST HOME
    # =========================================================

    def receptionist_home(self):

        orders = self.get_incoming_orders()

        return render_template(
            "receptionist/home.html",
            orders=orders
        )

    # =========================================================
    # ORDER MANAGEMENT
    # =========================================================

    def order_management(self):

        orders = self.get_incoming_orders()

        return render_template(
            "receptionist/orders.html",
            orders=orders
        )

    # =========================================================
    # MARK ORDER AS PREPARING
    # =========================================================

    def mark_preparing(self, order_id):

        self.update_order_status(
            order_id,
            "preparing"
        )

        flash(
            "Order marked as preparing.",
            "success"
        )

        return redirect(
            request.referrer or
            url_for("auth.receptionist_dashboard")
        )

    # =========================================================
    # MARK ORDER AS READY
    # =========================================================

    def mark_ready(self, order_id):

        self.update_order_status(
            order_id,
            "ready"
        )

        flash(
            "Order marked as ready.",
            "success"
        )

        return redirect(
            request.referrer or
            url_for("auth.receptionist_dashboard")
        )

    # =========================================================
    # MARK ORDER AS SERVED
    # =========================================================

    def mark_served(self, order_id):

        self.update_order_status(
            order_id,
            "served"
        )

        flash(
            "Order marked as served.",
            "success"
        )

        return redirect(
            request.referrer or
            url_for("auth.receptionist_dashboard")
        )

    # =========================================================
    # MANAGER DASHBOARD
    # =========================================================

    def manager_dashboard(self):

        statistics = self.get_statistics()

        recent_orders = self.get_recent_orders()

        return render_template(
            "manager/dashboard.html",
            statistics=statistics,
            recent_orders=recent_orders
        )

    # =========================================================
    # MANAGER STATISTICS
    # =========================================================

    def statistics(self):

        start_date = request.args.get(
            "start_date"
        )

        end_date = request.args.get(
            "end_date"
        )

        statistics = self.get_statistics(
            start_date,
            end_date
        )

        return render_template(
            "manager/statistics.html",
            statistics=statistics,
            start_date=start_date,
            end_date=end_date
        )

    # =========================================================
    # SALES REPORT
    # =========================================================

    def sales_report(self):

        start_date = request.args.get(
            "start_date"
        )

        end_date = request.args.get(
            "end_date"
        )

        db = Database()

        if start_date and end_date:

            sales = db.fetch_all(
                """
                SELECT
                    DATE(o.created_at) AS sale_date,

                    SUM(
                        oi.quantity *
                        oi.price_at_order
                    ) AS total_sales

                FROM orders o

                JOIN order_items oi
                    ON o.id = oi.order_id

                WHERE o.status = 'served'

                AND DATE(o.created_at)
                    BETWEEN %s AND %s

                GROUP BY
                    DATE(o.created_at)

                ORDER BY
                    sale_date DESC
                """,
                (
                    start_date,
                    end_date
                )
            )

        else:

            sales = db.fetch_all(
                """
                SELECT
                    DATE(o.created_at) AS sale_date,

                    SUM(
                        oi.quantity *
                        oi.price_at_order
                    ) AS total_sales

                FROM orders o

                JOIN order_items oi
                    ON o.id = oi.order_id

                WHERE o.status = 'served'

                GROUP BY
                    DATE(o.created_at)

                ORDER BY
                    sale_date DESC
                """
            )

        db.close()

        return render_template(
            "manager/sales.html",
            sales=sales,
            start_date=start_date,
            end_date=end_date
        )

    # =========================================================
    # MANAGER ORDER HISTORY
    # =========================================================

    def manager_order_history(self):

        db = Database()

        orders = db.fetch_all(
            """
            SELECT
                o.id,
                o.created_at,
                o.status,

                u.name AS customer_name,

                t.name AS table_name,

                COALESCE(
                    SUM(
                        oi.quantity *
                        oi.price_at_order
                    ),
                    0
                ) AS total

            FROM orders o

            JOIN users u
                ON o.user_id = u.id

            LEFT JOIN restaurant_tables t
                ON o.table_id = t.id

            LEFT JOIN order_items oi
                ON o.id = oi.order_id

            GROUP BY
                o.id,
                o.created_at,
                o.status,
                u.name,
                t.name

            ORDER BY
                o.id DESC
            """
        )

        db.close()

        return render_template(
            "manager/history.html",
            orders=orders
        )

    # =========================================================
    # ADD MENU ITEM
    # =========================================================

    def add_menu_item(self):

        # IMPORTANT:
        # The HTML form sends category_id,
        # not category.

        name = request.form.get(
            "name",
            ""
        ).strip()

        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # Checkbox:
        # checked = 1
        # unchecked = 0
        available = (
            1
            if request.form.get("available")
            else 0
        )

        # -----------------------------------------------------
        # REQUIRED FIELD VALIDATION
        # -----------------------------------------------------

        if not name or not category_id or not price:

            flash(
                "Name, category and price are required.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # PRICE VALIDATION
        # -----------------------------------------------------

        try:

            price = float(price)

            if price < 0:
                raise ValueError

        except (ValueError, TypeError):

            flash(
                "Price must be a valid number.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # CATEGORY VALIDATION
        # -----------------------------------------------------

        try:

            category_id = int(category_id)

        except (ValueError, TypeError):

            flash(
                "Invalid category selected.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # SAVE MENU ITEM
        # -----------------------------------------------------

        try:

            self.menu_model.save(
                name=name,
                price=price,
                category_id=category_id,
                description=description,
                available=available
            )

            flash(
                "Menu item added successfully.",
                "success"
            )

        except Exception as e:

            print(
                "Add menu item error:",
                e
            )

            flash(
                f"Unable to add menu item: {e}",
                "danger"
            )

        return redirect(
            request.referrer or
            url_for("auth.manager_dashboard")
        )

    # =========================================================
    # EDIT MENU ITEM
    # =========================================================

    def edit_menu_item(self, item_id):

        item = self.menu_model.find_by_id(
            item_id
        )

        if not item:

            flash(
                "Menu item not found.",
                "danger"
            )

            return redirect(
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # GET REQUEST
        # -----------------------------------------------------

        if request.method == "GET":

            return render_template(
                "manager/edit_menu_item.html",
                item=item
            )

        # -----------------------------------------------------
        # POST REQUEST
        # -----------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        available = (
            1
            if request.form.get("available")
            else 0
        )

        # -----------------------------------------------------
        # REQUIRED FIELD VALIDATION
        # -----------------------------------------------------

        if not name or not category_id or not price:

            flash(
                "Name, category and price are required.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # PRICE VALIDATION
        # -----------------------------------------------------

        try:

            price = float(price)

            if price < 0:
                raise ValueError

        except (ValueError, TypeError):

            flash(
                "Price must be a valid number.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # CATEGORY VALIDATION
        # -----------------------------------------------------

        try:

            category_id = int(category_id)

        except (ValueError, TypeError):

            flash(
                "Invalid category selected.",
                "danger"
            )

            return redirect(
                request.referrer or
                url_for("auth.manager_dashboard")
            )

        # -----------------------------------------------------
        # UPDATE MENU ITEM
        # -----------------------------------------------------

        try:

            self.menu_model.update(
                item_id=item_id,
                name=name,
                price=price,
                category_id=category_id,
                description=description,
                available=available
            )

            flash(
                "Menu item updated successfully.",
                "success"
            )

        except Exception as e:

            print(
                "Edit menu item error:",
                e
            )

            flash(
                f"Unable to update menu item: {e}",
                "danger"
            )

        return redirect(
            request.referrer or
            url_for("auth.manager_dashboard")
        )

    # =========================================================
    # DELETE MENU ITEM
    # =========================================================

    def delete_menu_item(self, item_id):

        item = self.menu_model.find_by_id(
            item_id
        )

        if not item:

            flash(
                "Menu item not found.",
                "danger"
            )

            return redirect(
                url_for("auth.manager_dashboard")
            )

        try:

            self.menu_model.delete(
                item_id
            )

            flash(
                "Menu item deleted successfully.",
                "success"
            )

        except Exception as e:

            print(
                "Delete menu item error:",
                e
            )

            flash(
                f"Unable to delete menu item: {e}",
                "danger"
            )

        return redirect(
            request.referrer or
            url_for("auth.manager_dashboard")
        )

    # =========================================================
    # HELPER: GET TABLES
    # =========================================================

    def get_tables(self):

        db = Database()

        tables = db.fetch_all(
            """
            SELECT *
            FROM restaurant_tables
            ORDER BY id
            """
        )

        db.close()

        return tables

    # =========================================================
    # HELPER: CALCULATE CART TOTAL
    # =========================================================

    def calculate_cart_total(self, cart):

        total = 0.0

        for item in cart.values():

            try:

                price = float(
                    item.get(
                        "price",
                        0
                    )
                )

            except (ValueError, TypeError):

                price = 0.0

            try:

                quantity = int(
                    item.get(
                        "quantity",
                        0
                    )
                )

            except (ValueError, TypeError):

                quantity = 0

            total += price * quantity

        return total

    # =========================================================
    # HELPER: GET INCOMING ORDERS
    # =========================================================

    def get_incoming_orders(self):

        db = Database()

        orders = db.fetch_all(
            """
            SELECT
                o.id,
                o.created_at,
                o.status,

                u.name AS customer_name,

                t.name AS table_name,

                mi.name AS item_name,

                oi.quantity,

                oi.price_at_order

            FROM orders o

            JOIN users u
                ON o.user_id = u.id

            LEFT JOIN restaurant_tables t
                ON o.table_id = t.id

            JOIN order_items oi
                ON o.id = oi.order_id

            JOIN menu_items mi
                ON oi.item_id = mi.id

            WHERE o.status IN
                ('pending', 'preparing', 'ready')

            ORDER BY
                o.created_at ASC
            """
        )

        db.close()

        return orders

    # =========================================================
    # HELPER: UPDATE ORDER STATUS
    # =========================================================

    def update_order_status(
        self,
        order_id,
        status
    ):

        allowed_statuses = [
            "pending",
            "preparing",
            "ready",
            "served"
        ]

        if status not in allowed_statuses:
            return False

        db = Database()

        db.execute(
            """
            UPDATE orders
            SET status = %s
            WHERE id = %s
            """,
            (
                status,
                order_id
            )
        )

        db.close()

        return True

    # =========================================================
    # HELPER: GET STATISTICS
    # =========================================================

    def get_statistics(
        self,
        start_date=None,
        end_date=None
    ):

        db = Database()

        date_condition = ""
        params = []

        if start_date and end_date:

            date_condition = """
                AND DATE(o.created_at)
                BETWEEN %s AND %s
            """

            params = [
                start_date,
                end_date
            ]

        result = db.fetch_one(
            f"""
            SELECT

                COALESCE(
                    SUM(
                        oi.quantity *
                        oi.price_at_order
                    ),
                    0
                ) AS total_sales,

                COALESCE(
                    SUM(oi.quantity),
                    0
                ) AS total_items,

                COUNT(
                    DISTINCT o.id
                ) AS total_orders

            FROM orders o

            JOIN order_items oi
                ON o.id = oi.order_id

            WHERE o.status = 'served'

            {date_condition}
            """,
            tuple(params)
        )

        db.close()

        return result

    # =========================================================
    # HELPER: GET RECENT ORDERS
    # =========================================================

    def get_recent_orders(self):

        db = Database()

        orders = db.fetch_all(
            """
            SELECT
                o.id,
                o.created_at,
                o.status,

                u.name AS customer_name,

                t.name AS table_name

            FROM orders o

            JOIN users u
                ON o.user_id = u.id

            LEFT JOIN restaurant_tables t
                ON o.table_id = t.id

            ORDER BY
                o.created_at DESC

            LIMIT 10
            """
        )

        db.close()

        return orders
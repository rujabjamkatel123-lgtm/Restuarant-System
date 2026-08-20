"""
=============================================================
    Restaurant Management System
    Customer Controller
=============================================================

Customer flow:

    Customer scans QR code
            ↓
    QR contains table ID
            ↓
    scan_qr(table_id)
            ↓
    table_id + table_name stored in session
            ↓
    Customer Dashboard
            ↓
    Browse Menu
            ↓
    Add items to cart
            ↓
    Place Order
            ↓
    Order saved with correct table
            ↓
    Customer Order History

Only two customer HTML pages are required:

    customer/dashboard.html
    customer/orders.html
=============================================================
"""

from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request
)

from app.controllers.base_controllers import BaseController
from app.modules.database import Database


class CustomerController(BaseController):

    # =========================================================
    # MENU (ALIAS)
    # =========================================================

    def menu(self):
        """
        Alias for dashboard, as the menu is displayed on the customer dashboard.
        """
        return self.dashboard()

    # =========================================================
    # CART (ALIAS)
    # =========================================================

    def cart(self):
        """
        Alias for dashboard, as the cart is managed on the customer dashboard.
        """
        return self.dashboard()

    # =========================================================
    # VIEW ORDER (ALIAS)
    # =========================================================

    def view_order(self, order_id=None):
        """
        Alias for orders, as order history and details are handled there.
        """
        return self.orders()

    # =========================================================
    # MOBILE (ALIAS)
    # =========================================================

    def mobile(self):
        """
        Alias for dashboard, as mobile views are handled there.
        """
        return self.dashboard()

    # =========================================================
    # CUSTOMER DASHBOARD
    # =========================================================

    def dashboard(self):
        """
        Main customer page.

        Everything is handled inside dashboard.html:

            - Restaurant welcome
            - Automatically selected table
            - Menu
            - Cart / current order
            - Total amount
            - Add item
            - Remove item
            - Place order
        """

        # -----------------------------------------------------
        # Table must normally come from QR scan
        # -----------------------------------------------------

        table_id = session.get("table_id")

        if not table_id:
            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        db = Database()

        try:

            # -------------------------------------------------
            # Get the actual table from database
            # -------------------------------------------------

            selected_table = db.fetch_one(
                """
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
                """,
                (table_id,)
            )

            # -------------------------------------------------
            # If table no longer exists
            # -------------------------------------------------

            if not selected_table:

                session.pop("table_id", None)
                session.pop("table_name", None)

                flash(
                    "This table could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )

            # -------------------------------------------------
            # Get available menu items
            # -------------------------------------------------

            menu_items = db.fetch_all(
                """
                SELECT
                    menu_items.id,
                    menu_items.name,
                    menu_items.price,
                    menu_items.category_id,
                    menu_items.description,
                    menu_items.image,
                    menu_categories.name AS category
                FROM menu_items

                LEFT JOIN menu_categories
                    ON menu_items.category_id =
                       menu_categories.id

                WHERE menu_items.available = 1

                ORDER BY
                    menu_categories.name,
                    menu_items.name
                """
            )

        except Exception as e:

            print("Customer dashboard error:", e)

            flash(
                "Unable to load the restaurant menu.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        finally:
            db.close()

        # -----------------------------------------------------
        # Keep table name synchronized with database
        # -----------------------------------------------------

        session["table_id"] = selected_table["id"]
        session["table_name"] = selected_table["name"]

        # -----------------------------------------------------
        # Get current cart
        # -----------------------------------------------------

        cart = self.get_cart()

        # -----------------------------------------------------
        # Calculate total
        # -----------------------------------------------------

        total = self.calculate_cart_total(cart)

        # -----------------------------------------------------
        # Render ONLY dashboard.html
        # -----------------------------------------------------

        return render_template(
            "customer/dashboard.html",

            menu_items=menu_items,

            cart=cart,

            total=total,

            selected_table=selected_table,

            table_id=selected_table["id"],

            table_name=selected_table["name"]
        )

    # =========================================================
    # QR CODE SCANNER
    # =========================================================

    def scan_qr(self, table_id):
        """
        This route is opened by the QR code.

        Example:

            Table 1 QR
            /customer/scan/1

        Table 2 QR
            /customer/scan/2

        Table 5 QR
            /customer/scan/5

        The table number comes directly from the QR URL.

        IMPORTANT:
        This does NOT use table 1 as a default.
        """

        db = Database()

        try:

            table = db.fetch_one(
                """
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
                """,
                (table_id,)
            )

        except Exception as e:

            print("QR table lookup error:", e)

            flash(
                "Unable to read the table QR code.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        finally:
            db.close()

        # -----------------------------------------------------
        # Invalid QR / invalid table
        # -----------------------------------------------------

        if not table:

            session.pop("table_id", None)
            session.pop("table_name", None)

            flash(
                "Invalid table QR code.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        # -----------------------------------------------------
        # IMPORTANT
        #
        # Store the table that was actually scanned.
        # -----------------------------------------------------

        session["table_id"] = int(table["id"])
        session["table_name"] = table["name"]

        # -----------------------------------------------------
        # New table = new cart
        #
        # This prevents an old customer's cart from being
        # carried into another table.
        # -----------------------------------------------------

        session.pop("cart", None)

        session.modified = True

        flash(
            f'Welcome! You are ordering from {table["name"]}.',
            "success"
        )

        # -----------------------------------------------------
        # Always go to dashboard.html
        # -----------------------------------------------------

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # GET CART
    # =========================================================

    def get_cart(self):
        """
        Get current customer's cart from Flask session.

        Example:

        {
            "1": {
                "id": 1,
                "name": "Momo",
                "price": 180,
                "quantity": 2
            }
        }
        """

        cart = session.get("cart", {})

        # Safety check
        if not isinstance(cart, dict):
            cart = {}

        return cart

    # =========================================================
    # CALCULATE CART TOTAL
    # =========================================================

    def calculate_cart_total(self, cart):
        """
        Calculate:

            price × quantity

        for every item.
        """

        total = 0

        for item in cart.values():

            try:

                price = float(
                    item.get("price", 0)
                )

                quantity = int(
                    item.get("quantity", 0)
                )

                total += price * quantity

            except (
                ValueError,
                TypeError
            ):

                continue

        return total

    # =========================================================
    # ADD ITEM TO CART
    # =========================================================

    def add_to_cart(self, item_id):
        """
        Add one menu item.

        If item already exists:

            quantity + 1

        Otherwise:

            quantity = 1
        """

        # -----------------------------------------------------
        # Make sure customer scanned a QR code
        # -----------------------------------------------------

        if not session.get("table_id"):

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        db = Database()

        try:

            item = db.fetch_one(
                """
                SELECT
                    menu_items.id,
                    menu_items.name,
                    menu_items.price,
                    menu_items.category_id,
                    menu_categories.name AS category

                FROM menu_items

                LEFT JOIN menu_categories
                    ON menu_items.category_id =
                       menu_categories.id

                WHERE menu_items.id = %s
                AND menu_items.available = 1
                """,
                (item_id,)
            )

        except Exception as e:

            print("Add to cart error:", e)

            flash(
                "Unable to add item.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        finally:
            db.close()

        # -----------------------------------------------------
        # Item does not exist
        # -----------------------------------------------------

        if not item:

            flash(
                "Menu item not found.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        # -----------------------------------------------------
        # Get cart
        # -----------------------------------------------------

        cart = self.get_cart()

        item_key = str(item["id"])

        # -----------------------------------------------------
        # Item already exists
        # -----------------------------------------------------

        if item_key in cart:

            cart[item_key]["quantity"] = (
                int(cart[item_key].get("quantity", 0))
                + 1
            )

        # -----------------------------------------------------
        # New item
        # -----------------------------------------------------

        else:

            cart[item_key] = {
                "id": item["id"],
                "name": item["name"],
                "price": float(item["price"]),
                "category": item.get("category"),
                "quantity": 1
            }

        # -----------------------------------------------------
        # Save cart
        # -----------------------------------------------------

        session["cart"] = cart
        session.modified = True

        flash(
            f'{item["name"]} added to your order.',
            "success"
        )

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT redirect to customer.menu.
        #
        # We only have dashboard.html.
        # -----------------------------------------------------

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # REMOVE ITEM FROM CART
    # =========================================================

    def remove_from_cart(self, item_id):
        """
        Completely remove an item from cart.

        This fixes the old problem where the route redirected
        to customer.cart, even though cart.html is no longer used.
        """

        cart = self.get_cart()

        item_key = str(item_id)

        # -----------------------------------------------------
        # Item exists
        # -----------------------------------------------------

        if item_key in cart:

            item_name = cart[item_key].get(
                "name",
                "Item"
            )

            del cart[item_key]

            session["cart"] = cart
            session.modified = True

            flash(
                f"{item_name} removed from your order.",
                "success"
            )

        else:

            flash(
                "Item was not found in your order.",
                "warning"
            )

        # -----------------------------------------------------
        # Stay on dashboard
        # -----------------------------------------------------

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # UPDATE CART QUANTITY
    # =========================================================

    def update_cart(self, item_id):
        """
        Update one item's quantity.

        Expected POST:

            quantity=3
        """

        cart = self.get_cart()

        item_key = str(item_id)

        if item_key not in cart:

            flash(
                "Item not found in your order.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        quantity = request.form.get(
            "quantity",
            1
        )

        try:

            quantity = int(quantity)

        except (
            ValueError,
            TypeError
        ):

            quantity = 1

        # -----------------------------------------------------
        # Quantity 0 = remove
        # -----------------------------------------------------

        if quantity <= 0:

            del cart[item_key]

        else:

            cart[item_key]["quantity"] = quantity

        session["cart"] = cart
        session.modified = True

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # CLEAR CART
    # =========================================================

    def clear_cart(self):
        """
        Remove every item from current order.
        """

        session.pop("cart", None)
        session.modified = True

        flash(
            "Your current order has been cleared.",
            "success"
        )

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # PLACE ORDER
    # =========================================================

    def place_order(self):
        """
        Create order using the table stored by QR scan.

        VERY IMPORTANT:

            table_id = session["table_id"]

        We do NOT get the table from the HTML form.

        Therefore:

            QR Table 1 → order.table_id = 1
            QR Table 2 → order.table_id = 2
            QR Table 5 → order.table_id = 5
        """

        # -----------------------------------------------------
        # Get scanned table
        # -----------------------------------------------------

        table_id = session.get("table_id")

        # -----------------------------------------------------
        # Get cart
        # -----------------------------------------------------

        cart = self.get_cart()

        # -----------------------------------------------------
        # Table check
        # -----------------------------------------------------

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        # -----------------------------------------------------
        # Cart check
        # -----------------------------------------------------

        if not cart:

            flash(
                "Your order is empty.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        db = Database()

        try:

            # -------------------------------------------------
            # Verify table still exists
            # -------------------------------------------------

            table = db.fetch_one(
                """
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
                """,
                (table_id,)
            )

            if not table:

                raise Exception(
                    "The scanned table no longer exists."
                )

            # -------------------------------------------------
            # Create order
            # -------------------------------------------------

            db.execute(
                """
                INSERT INTO orders
                (
                    user_id,
                    table_id,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    session.get("user_id"),
                    table["id"],
                    "pending"
                )
            )

            # -------------------------------------------------
            # Get order ID
            # -------------------------------------------------

            order = db.fetch_one(
                """
                SELECT
                    LAST_INSERT_ID()
                    AS order_id
                """
            )

            if not order:

                raise Exception(
                    "Unable to create order."
                )

            order_id = order["order_id"]

            # -------------------------------------------------
            # Insert every cart item
            # -------------------------------------------------

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
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        order_id,
                        item["id"],
                        int(item["quantity"]),
                        float(item["price"])
                    )
                )

            # -------------------------------------------------
            # Close database
            # -------------------------------------------------

            db.close()

            # -------------------------------------------------
            # Clear cart ONLY after successful order
            # -------------------------------------------------

            session.pop("cart", None)
            session.modified = True

            flash(
                f'Order #{order_id} placed successfully for '
                f'{table["name"]}.',
                "success"
            )

            # -------------------------------------------------
            # Go to order history
            # -------------------------------------------------

            return redirect(
                url_for("customer.orders")
            )

        except Exception as e:

            try:
                db.close()
            except Exception:
                pass

            print(
                "ORDER PLACEMENT ERROR:",
                e
            )

            flash(
                "Unable to place your order. "
                "Please try again.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

    # =========================================================
    # CUSTOMER ORDER HISTORY
    # =========================================================

    def orders(self):
        """
        Display all orders made by the current customer.

        This uses:

            customer/orders.html
        """

        user_id = self.get_current_user_id()

        if not user_id:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        db = Database()

        try:

            # -------------------------------------------------
            # Get orders
            # -------------------------------------------------

            orders = db.fetch_all(
                """
                SELECT
                    orders.id,
                    orders.created_at,
                    orders.status,
                    restaurant_tables.name
                    AS table_name

                FROM orders

                LEFT JOIN restaurant_tables
                    ON orders.table_id =
                       restaurant_tables.id

                WHERE orders.user_id = %s

                ORDER BY
                    orders.created_at DESC
                """,
                (user_id,)
            )

            # -------------------------------------------------
            # Get items for every order
            # -------------------------------------------------

            for order in orders:

                order["items"] = db.fetch_all(
                    """
                    SELECT
                        order_items.quantity,
                        order_items.price_at_order,
                        menu_items.name

                    FROM order_items

                    INNER JOIN menu_items
                        ON order_items.item_id =
                           menu_items.id

                    WHERE order_items.order_id = %s

                    ORDER BY menu_items.name
                    """,
                    (order["id"],)
                )

                # ---------------------------------------------
                # Calculate total
                # ---------------------------------------------

                order["total"] = 0

                for item in order["items"]:

                    order["total"] += (
                        float(
                            item["price_at_order"]
                        )
                        *
                        int(
                            item["quantity"]
                        )
                    )

        except Exception as e:

            print(
                "Order history error:",
                e
            )

            flash(
                "Unable to load your order history.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        finally:
            db.close()

        return render_template(
            "customer/orders.html",
            orders=orders
        )
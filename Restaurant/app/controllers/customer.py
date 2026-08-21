"""
=============================================================
    Restaurant Management System
    Customer Controller
=============================================================

CUSTOMER FLOW

    Customer scans QR
            ↓
    /customer/qr/<table_id>
            ↓
    Table is stored in session
            ↓
    Customer Dashboard
            ↓
    Add food
            ↓
    Item added to session cart
            ↓
    Place Order
            ↓
    Order stored in database
            ↓
    Table becomes occupied
            ↓
    Receptionist clears table
            ↓
    QR works again

IMPORTANT:

    Customer QR ordering does NOT require login.

    The customer is identified by:
        - table_id
        - table_name
        - session cart

=============================================================
"""

from flask import (
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from app.modules.database import Database


class CustomerController:

    # =========================================================
    # HELPER
    # =========================================================

    def get_table_id(self):
        """
        Get the table ID.

        Normally it comes from the session.

        As a backup, it can also come from the POST form.
        This prevents the customer from being unnecessarily
        sent to the login page if the session table value
        is temporarily unavailable.
        """

        table_id = session.get("table_id")

        if table_id:
            try:
                return int(table_id)
            except (ValueError, TypeError):
                pass

        # -----------------------------------------------------
        # Backup: hidden form field
        # -----------------------------------------------------

        form_table_id = request.form.get("table_id")

        if form_table_id:
            try:
                table_id = int(form_table_id)

                # Restore it into session
                session["table_id"] = table_id
                session.modified = True

                return table_id

            except (ValueError, TypeError):
                pass

        return None

    # =========================================================
    # CUSTOMER DASHBOARD
    # =========================================================

    def dashboard(self):
        """
        Main customer dashboard.

        Customer reaches this page through the QR code.

        NO LOGIN REQUIRED.
        """

        table_id = self.get_table_id()

        # -----------------------------------------------------
        # Customer has not scanned QR
        # -----------------------------------------------------

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            # IMPORTANT:
            # Do NOT redirect to auth.login.
            #
            # There is no customer login requirement.
            #
            # We simply return to the customer landing/QR flow.
            return redirect(
                url_for("customer.menu")
            )

        db = Database()

        selected_table = None
        menu_items = []

        try:

            # -------------------------------------------------
            # Get selected table
            # -------------------------------------------------

            selected_table = db.fetch_one("""
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))

            # -------------------------------------------------
            # Invalid table
            # -------------------------------------------------

            if not selected_table:

                session.pop("table_id", None)
                session.pop("table_name", None)
                session.pop("cart", None)

                flash(
                    "This table does not exist.",
                    "danger"
                )

                return redirect(
                    url_for("customer.menu")
                )

            # -------------------------------------------------
            # Keep table information synchronized
            # -------------------------------------------------

            session["table_id"] = int(
                selected_table["id"]
            )

            session["table_name"] = (
                selected_table["name"]
            )

            session.modified = True

            # -------------------------------------------------
            # Get available menu
            # -------------------------------------------------

            menu_items = db.fetch_all("""
                SELECT
                    mi.id,
                    mi.name,
                    mi.price,
                    mi.half_plate_price,
                    mi.description,
                    mi.image,
                    mi.category_id,
                    mc.name AS category

                FROM menu_items mi

                LEFT JOIN menu_categories mc
                    ON mi.category_id = mc.id

                WHERE mi.available = 1

                ORDER BY
                    mc.name ASC,
                    mi.name ASC
            """)

        except Exception as e:

            print(
                "CUSTOMER DASHBOARD ERROR:",
                e
            )

            flash(
                "Unable to load the restaurant menu.",
                "danger"
            )

        finally:

            db.close()

        # -----------------------------------------------------
        # Cart
        # -----------------------------------------------------

        cart = self.get_cart()

        total = self.calculate_cart_total(
            cart
        )

        # -----------------------------------------------------
        # Get order history
        # -----------------------------------------------------

        orders = []

        try:

            db = Database()

            orders = db.fetch_all("""
                SELECT
                    o.id,
                    o.table_id,
                    t.name AS table_name,
                    o.status,
                    o.created_at,

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

                WHERE o.table_id = %s

                GROUP BY
                    o.id,
                    o.table_id,
                    t.name,
                    o.status,
                    o.created_at

                ORDER BY
                    o.id DESC

                LIMIT 20
            """, (table_id,))

        except Exception as e:

            print(
                "CUSTOMER HISTORY ERROR:",
                e
            )

        finally:

            try:
                db.close()
            except Exception:
                pass

        # -----------------------------------------------------
        # Render dashboard
        # -----------------------------------------------------

        return render_template(
            "customer/dashboard.html",

            selected_table=selected_table,

            table_id=selected_table["id"],

            table_name=selected_table["name"],

            menu_items=menu_items,

            cart=cart,

            total=total,

            orders=orders
        )

    # =========================================================
    # QR CODE ENTRY
    # =========================================================

    def scan_qr(self, table_id):
        """
        Customer enters through the QR code.

        Example:

            /customer/qr/1
            /customer/qr/2
            /customer/qr/5

        NO LOGIN REQUIRED.
        """

        db = Database()

        try:

            # -------------------------------------------------
            # Find table
            # -------------------------------------------------

            table = db.fetch_one("""
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))

            # -------------------------------------------------
            # Invalid table
            # -------------------------------------------------

            if not table:

                session.pop("table_id", None)
                session.pop("table_name", None)
                session.pop("cart", None)

                flash(
                    "Invalid table QR code.",
                    "danger"
                )

                return redirect(
                    url_for("customer.menu")
                )

            # -------------------------------------------------
            # Check active order
            # -------------------------------------------------

            active_order = db.fetch_one("""
                SELECT
                    id,
                    status

                FROM orders

                WHERE table_id = %s

                AND status IN (
                    'pending',
                    'preparing',
                    'ready'
                )

                ORDER BY id DESC

                LIMIT 1
            """, (table_id,))

        except Exception as e:

            print(
                "QR SCAN ERROR:",
                e
            )

            flash(
                "Unable to read the table QR code.",
                "danger"
            )

            return redirect(
                url_for("customer.menu")
            )

        finally:

            db.close()

        # =====================================================
        # TABLE OCCUPIED
        # =====================================================

        if active_order:

            session["table_id"] = int(
                table["id"]
            )

            session["table_name"] = (
                table["name"]
            )

            session["cart"] = {}

            session.modified = True

            flash(
                f'{table["name"]} is currently occupied. '
                'Please wait until the receptionist clears this table.',
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        # =====================================================
        # TABLE AVAILABLE
        # =====================================================

        session["table_id"] = int(
            table["id"]
        )

        session["table_name"] = (
            table["name"]
        )

        # New QR session = new cart
        session["cart"] = {}

        session.modified = True

        flash(
            f'Welcome! You are ordering from {table["name"]}.',
            "success"
        )

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # MENU
    # =========================================================

    def menu(self):
        """
        Customer menu/dashboard entry.

        NO LOGIN REQUIRED.
        """

        # If the customer already has a QR table,
        # show dashboard.
        if self.get_table_id():

            return self.dashboard()

        # Otherwise show a simple message.
        # This avoids sending the customer to login.
        return render_template(
            "customer/dashboard.html",
            selected_table=None,
            table_id=None,
            table_name=None,
            menu_items=[],
            cart={},
            total=0,
            orders=[]
        )

    # =========================================================
    # CART PAGE
    # =========================================================

    def cart(self):
        """
        Cart is displayed on dashboard.
        """

        return self.dashboard()

    # =========================================================
    # GET CART
    # =========================================================

    def get_cart(self):

        cart = session.get(
            "cart",
            {}
        )

        if not isinstance(cart, dict):

            cart = {}

        return cart

    # =========================================================
    # CALCULATE CART TOTAL
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

            except (
                ValueError,
                TypeError
            ):

                price = 0.0

            try:

                quantity = int(
                    item.get(
                        "quantity",
                        0
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                quantity = 0

            total += (
                price *
                quantity
            )

        return total

    # =========================================================
    # ADD TO CART
    # =========================================================

    def add_to_cart(self, item_id):
        """
        Add a menu item to the customer's cart.

        NO LOGIN REQUIRED.

        The table is identified from:
            1. session
            2. hidden form table_id backup
        """

        table_id = self.get_table_id()

        # -----------------------------------------------------
        # No table
        # -----------------------------------------------------

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            # IMPORTANT:
            # Never redirect to auth.login here.
            return redirect(
                url_for("customer.menu")
            )

        db = Database()

        try:

            # -------------------------------------------------
            # Check table
            # -------------------------------------------------

            table = db.fetch_one("""
                SELECT
                    id,
                    name

                FROM restaurant_tables

                WHERE id = %s
            """, (table_id,))

            if not table:

                session.pop("table_id", None)
                session.pop("table_name", None)
                session.pop("cart", None)

                flash(
                    "This table no longer exists.",
                    "danger"
                )

                return redirect(
                    url_for("customer.menu")
                )

            # -------------------------------------------------
            # Check active order
            # -------------------------------------------------

            active_order = db.fetch_one("""
                SELECT
                    id

                FROM orders

                WHERE table_id = %s

                AND status IN (
                    'pending',
                    'preparing',
                    'ready'
                )

                LIMIT 1
            """, (table_id,))

            if active_order:

                session["cart"] = {}

                session.modified = True

                flash(
                    "This table already has an active order. "
                    "Please wait for the receptionist to clear it.",
                    "warning"
                )

                return redirect(
                    url_for("customer.dashboard")
                )

            # -------------------------------------------------
            # Get menu item
            # -------------------------------------------------

            item = db.fetch_one("""
                SELECT
                    mi.id,
                    mi.name,
                    mi.price,
                    mi.description,
                    mi.image,
                    mi.category_id,
                    mc.name AS category

                FROM menu_items mi

                LEFT JOIN menu_categories mc
                    ON mi.category_id = mc.id

                WHERE mi.id = %s

                AND mi.available = 1

            """, (item_id,))

        except Exception as e:

            print(
                "ADD TO CART ERROR:",
                e
            )

            flash(
                "Unable to add this item.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        finally:

            db.close()

        # -----------------------------------------------------
        # Item unavailable
        # -----------------------------------------------------

        if not item:

            flash(
                "This menu item is not available.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        # -----------------------------------------------------
        # Get cart
        # -----------------------------------------------------

        cart = self.get_cart()

        item_key = str(
            item_id
        )

        # -----------------------------------------------------
        # Existing item
        # -----------------------------------------------------

        if item_key in cart:

            current_quantity = int(
                cart[item_key].get(
                    "quantity",
                    0
                )
            )

            cart[item_key]["quantity"] = (
                current_quantity + 1
            )

        # -----------------------------------------------------
        # New item
        # -----------------------------------------------------

        else:

            cart[item_key] = {

                "id": int(
                    item["id"]
                ),

                "name": item["name"],

                "price": float(
                    item["price"]
                ),

                "quantity": 1
            }

        # -----------------------------------------------------
        # Save session
        # -----------------------------------------------------

        session["cart"] = cart

        session["table_id"] = int(
            table["id"]
        )

        session["table_name"] = (
            table["name"]
        )

        session.modified = True

        flash(
            f'{item["name"]} added to your order.',
            "success"
        )

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # Go back to customer dashboard.
        #
        # NOT auth.login
        # -----------------------------------------------------

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # UPDATE CART
    # =========================================================

    def update_cart(self, item_id):

        table_id = self.get_table_id()

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("customer.menu")
            )

        cart = self.get_cart()

        item_key = str(
            item_id
        )

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

            quantity = int(
                quantity
            )

        except (
            ValueError,
            TypeError
        ):

            quantity = 1

        # -----------------------------------------------------
        # Zero = remove
        # -----------------------------------------------------

        if quantity <= 0:

            del cart[item_key]

        else:

            cart[item_key]["quantity"] = (
                quantity
            )

        session["cart"] = cart
        session.modified = True

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # REMOVE FROM CART
    # =========================================================

    def remove_from_cart(self, item_id):

        cart = self.get_cart()

        item_key = str(
            item_id
        )

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

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # CLEAR CART
    # =========================================================

    def clear_cart(self):

        session["cart"] = {}

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
        Place the customer's order.

        NO LOGIN REQUIRED.

        Table comes from QR/session.
        """

        table_id = self.get_table_id()

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
                url_for("customer.menu")
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
            # Verify table
            # -------------------------------------------------

            table = db.fetch_one("""
                SELECT
                    id,
                    name

                FROM restaurant_tables

                WHERE id = %s
            """, (table_id,))

            if not table:

                raise Exception(
                    "Table does not exist."
                )

            # -------------------------------------------------
            # Prevent duplicate order
            # -------------------------------------------------

            active_order = db.fetch_one("""
                SELECT
                    id,
                    status

                FROM orders

                WHERE table_id = %s

                AND status IN (
                    'pending',
                    'preparing',
                    'ready'
                )

                LIMIT 1
            """, (table_id,))

            if active_order:

                session["cart"] = {}
                session.modified = True

                flash(
                    "This table already has an active order. "
                    "The receptionist must clear the table first.",
                    "warning"
                )

                return redirect(
                    url_for("customer.dashboard")
                )

            # -------------------------------------------------
            # Create order
            # -------------------------------------------------

            db.execute("""
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
            """, (
                None,
                table_id,
                "pending"
            ))

            # -------------------------------------------------
            # Get new order ID
            # -------------------------------------------------

            order_result = db.fetch_one("""
                SELECT
                    LAST_INSERT_ID() AS id
            """)

            if not order_result:

                raise Exception(
                    "Unable to create order."
                )

            order_id = order_result["id"]

            # -------------------------------------------------
            # Insert order items
            # -------------------------------------------------

            inserted_items = 0

            for item in cart.values():

                try:

                    quantity = int(
                        item.get(
                            "quantity",
                            1
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    quantity = 1

                try:

                    price = float(
                        item.get(
                            "price",
                            0
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    price = 0

                if quantity <= 0:

                    continue

                db.execute("""
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
                """, (
                    order_id,
                    item["id"],
                    quantity,
                    price
                ))

                inserted_items += 1

            # -------------------------------------------------
            # Make sure at least one item was inserted
            # -------------------------------------------------

            if inserted_items == 0:

                raise Exception(
                    "No valid items in cart."
                )

            # -------------------------------------------------
            # Clear cart
            # -------------------------------------------------

            session["cart"] = {}

            session["table_id"] = int(
                table["id"]
            )

            session["table_name"] = (
                table["name"]
            )

            session.modified = True

            flash(
                f'Order #{order_id} placed successfully '
                f'for {table["name"]}.',
                "success"
            )

            return redirect(
                url_for("customer.orders")
            )

        except Exception as e:

            print(
                "ORDER PLACEMENT ERROR:",
                e
            )

            flash(
                "Unable to place your order. Please try again.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        finally:

            db.close()

    # =========================================================
    # CUSTOMER ORDERS
    # =========================================================

    def orders(self):
        """
        Show orders for the current QR table.

        NO LOGIN REQUIRED.
        """

        table_id = self.get_table_id()

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("customer.menu")
            )

        db = Database()

        try:

            orders = db.fetch_all("""
                SELECT
                    o.id,
                    o.table_id,
                    t.name AS table_name,
                    o.status,
                    o.created_at,

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

                WHERE o.table_id = %s

                GROUP BY
                    o.id,
                    o.table_id,
                    t.name,
                    o.status,
                    o.created_at

                ORDER BY
                    o.id DESC
            """, (table_id,))

        except Exception as e:

            print(
                "CUSTOMER ORDERS ERROR:",
                e
            )

            orders = []

            flash(
                "Unable to load order history.",
                "danger"
            )

        finally:

            db.close()

        return render_template(
            "customer/orders.html",
            orders=orders
        )

    # =========================================================
    # VIEW SINGLE ORDER
    # =========================================================

    def view_order(self, order_id):

        table_id = self.get_table_id()

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("customer.menu")
            )

        db = Database()

        try:

            order = db.fetch_one("""
                SELECT
                    o.id,
                    o.table_id,
                    t.name AS table_name,
                    o.status,
                    o.created_at

                FROM orders o

                LEFT JOIN restaurant_tables t
                    ON o.table_id = t.id

                WHERE o.id = %s

                AND o.table_id = %s
            """, (
                order_id,
                table_id
            ))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("customer.orders")
                )

            order["items"] = db.fetch_all("""
                SELECT
                    oi.item_id,
                    mi.name,
                    oi.quantity,
                    oi.price_at_order,

                    (
                        oi.quantity *
                        oi.price_at_order
                    ) AS subtotal

                FROM order_items oi

                LEFT JOIN menu_items mi
                    ON oi.item_id = mi.id

                WHERE oi.order_id = %s

                ORDER BY oi.id ASC
            """, (order_id,))

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
                "VIEW ORDER ERROR:",
                e
            )

            flash(
                "Unable to load this order.",
                "danger"
            )

            return redirect(
                url_for("customer.orders")
            )

        finally:

            db.close()

        return render_template(
            "customer/orders.html",
            orders=[order],
            selected_order=order
        )

    # =========================================================
    # MOBILE
    # =========================================================

    def mobile(self):

        return self.dashboard()
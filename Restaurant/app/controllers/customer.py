"""
=============================================================
    Restaurant Management System
    Customer Controller
=============================================================

Customer flow:

    Customer scans QR
            ↓
    /customer/qr/<table_id>
            ↓
    Check table
            ↓
    Check if table already has active order
            ↓
       ┌───────────────┐
       │               │
     FREE           OCCUPIED
       │               │
       ↓               ↓
    Dashboard      Block access
       │
       ↓
    Add food
       │
       ↓
    Place order
       │
       ↓
    Table becomes occupied
       │
       ↓
    Receptionist clears table
       │
       ↓
    QR works again

Only customer dashboard and orders pages are required.
"""

from flask import (
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
    jsonify
)

from app.modules.database import Database


class CustomerController:

    # =========================================================
    # CUSTOMER DASHBOARD
    # =========================================================

    def dashboard(self):
        """
        Main customer dashboard.

        The table MUST come from the QR code.
        There is no manual table selection.
        """

        table_id = session.get("table_id")

        # -----------------------------------------------------
        # Customer must enter through QR
        # -----------------------------------------------------

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
            # Get selected table
            # -------------------------------------------------

            selected_table = db.fetch_one("""
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))

            if not selected_table:

                session.pop("table_id", None)
                session.pop("table_name", None)
                session.pop("cart", None)

                flash(
                    "This table does not exist.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )

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

            print("CUSTOMER DASHBOARD ERROR:", e)

            selected_table = None
            menu_items = []

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

        total = self.calculate_cart_total(cart)

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

            total=total
        )

    # =========================================================
    # QR CODE ENTRY
    # =========================================================

    def scan_qr(self, table_id):
        """
        Customer enters through the table QR code.

        Example:

            Table 1:
                /customer/qr/1

            Table 5:
                /customer/qr/5

        The table ID comes directly from the QR URL.

        No login is required.
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
                    url_for("auth.login")
                )

            # -------------------------------------------------
            # IMPORTANT:
            #
            # Check whether this table already has an
            # active order.
            #
            # Active:
            #   pending
            #   preparing
            #   ready
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

            print("QR SCAN ERROR:", e)

            flash(
                "Unable to read the table QR code.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        finally:

            db.close()

        # =====================================================
        # TABLE OCCUPIED
        # =====================================================

        if active_order:

            # Do not allow this QR to start another order.

            session.pop("cart", None)

            session["table_id"] = int(table["id"])
            session["table_name"] = table["name"]

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

        # Store the EXACT table scanned.

        session["table_id"] = int(table["id"])
        session["table_name"] = table["name"]

        # New table session = new cart.

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
        Menu is already part of dashboard.html.
        """

        return self.dashboard()

    # =========================================================
    # CART
    # =========================================================

    def cart(self):
        """
        Cart is already displayed on dashboard.html.
        """

        return self.dashboard()

    # =========================================================
    # GET CART
    # =========================================================

    def get_cart(self):

        cart = session.get("cart", {})

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
                    item.get("price", 0)
                )

            except (
                ValueError,
                TypeError
            ):

                price = 0.0

            try:

                quantity = int(
                    item.get("quantity", 0)
                )

            except (
                ValueError,
                TypeError
            ):

                quantity = 0

            total += price * quantity

        return total

    # =========================================================
    # ADD TO CART
    # =========================================================

    def add_to_cart(self, item_id):

        table_id = session.get("table_id")

        # -----------------------------------------------------
        # QR check
        # -----------------------------------------------------

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        db = Database()

        try:

            # -------------------------------------------------
            # Check table still exists
            # -------------------------------------------------

            table = db.fetch_one("""
                SELECT id, name
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
                    url_for("auth.login")
                )

            # -------------------------------------------------
            # IMPORTANT:
            #
            # Check if another order has already occupied
            # this table.
            # -------------------------------------------------

            active_order = db.fetch_one("""
                SELECT id
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
            # Get food item
            # -------------------------------------------------

            item = db.fetch_one("""
                SELECT
                    mi.id,
                    mi.name,
                    mi.price,
                    mi.description,
                    mi.image,
                    mc.name AS category

                FROM menu_items mi

                LEFT JOIN menu_categories mc
                    ON mi.category_id = mc.id

                WHERE mi.id = %s
                AND mi.available = 1
            """, (item_id,))

        except Exception as e:

            print("ADD TO CART ERROR:", e)

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
        # Item does not exist
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

        item_key = str(item_id)

        # -----------------------------------------------------
        # Existing item
        # -----------------------------------------------------

        if item_key in cart:

            cart[item_key]["quantity"] = (
                int(
                    cart[item_key].get(
                        "quantity",
                        0
                    )
                ) + 1
            )

        # -----------------------------------------------------
        # New item
        # -----------------------------------------------------

        else:

            cart[item_key] = {

                "id": item["id"],

                "name": item["name"],

                "price": float(
                    item["price"]
                ),

                "quantity": 1

            }

        session["cart"] = cart
        session.modified = True

        flash(
            f'{item["name"]} added to your order.',
            "success"
        )

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # UPDATE CART
    # =========================================================

    def update_cart(self, item_id):

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
        # Quantity zero = remove
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
    # REMOVE FROM CART
    # =========================================================

    def remove_from_cart(self, item_id):

        cart = self.get_cart()

        item_key = str(item_id)

        # -----------------------------------------------------
        # FIX:
        #
        # Always convert item ID to string because session
        # dictionary keys are stored as strings.
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
        Create an order using ONLY the table stored in
        the QR session.

        The HTML cannot choose the table.
        """

        table_id = session.get("table_id")

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
            # VERY IMPORTANT:
            #
            # Prevent duplicate order from same table.
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
            #
            # user_id is NULL because QR customers do not
            # need to log in.
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
                SELECT LAST_INSERT_ID() AS id
            """)

            if not order_result:

                raise Exception(
                    "Unable to create order."
                )

            order_id = order_result["id"]

            # -------------------------------------------------
            # Insert order items
            # -------------------------------------------------

            for item in cart.values():

                quantity = int(
                    item.get(
                        "quantity",
                        1
                    )
                )

                price = float(
                    item.get(
                        "price",
                        0
                    )
                )

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

            # -------------------------------------------------
            # Clear cart
            # -------------------------------------------------

            session["cart"] = {}

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
        Show order history using the current QR table.

        Since QR customers don't log in, orders are identified
        by the table session.
        """

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

        # The dashboard itself is responsive.
        return self.dashboard()
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
    # GET TABLE ID
    # =========================================================

    def get_table_id(self):

        table_id = session.get("table_id")

        if table_id:
            try:
                return int(table_id)
            except (ValueError, TypeError):
                pass

        form_table_id = request.form.get("table_id")

        if form_table_id:
            try:
                table_id = int(form_table_id)

                session["table_id"] = table_id
                session.modified = True

                return table_id

            except (ValueError, TypeError):
                pass

        return None

    # =========================================================
    # GET CART
    # =========================================================

    def get_cart(self):

        cart = session.get("cart", {})

        if not isinstance(cart, dict):
            cart = {}

        return cart

    # =========================================================
    # CALCULATE TOTAL
    # =========================================================

    def calculate_cart_total(self, cart):

        total = 0.0

        for item in cart.values():

            try:
                price = float(item.get("price", 0))
            except (ValueError, TypeError):
                price = 0.0

            try:
                quantity = int(item.get("quantity", 0))
            except (ValueError, TypeError):
                quantity = 0

            total += price * quantity

        return total

    # =========================================================
    # CUSTOMER DASHBOARD
    # =========================================================

    def dashboard(self):

        db = Database()

        try:

            # -------------------------------------------------
            # GET ALL TABLES
            # -------------------------------------------------

            tables = db.fetch_all("""
                SELECT
                    *
                FROM restaurant_tables
                ORDER BY id
            """)

            # -------------------------------------------------
            # SELECTED TABLE
            # -------------------------------------------------

            table_id = session.get("table_id")

            selected_table = None

            if table_id:

                try:
                    table_id = int(table_id)
                except (ValueError, TypeError):
                    table_id = None

                if table_id:

                    selected_table = db.fetch_one("""
                        SELECT
                            *
                        FROM restaurant_tables
                        WHERE id = %s
                    """, (table_id,))

            # -------------------------------------------------
            # MENU ITEMS
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

            # -------------------------------------------------
            # CUSTOMER ORDERS
            # -------------------------------------------------

            orders = []

            if table_id:

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

                    ORDER BY o.id DESC

                    LIMIT 20
                """, (table_id,))

        except Exception as e:

            print("CUSTOMER DASHBOARD ERROR:", e)

            tables = []
            selected_table = None
            menu_items = []
            orders = []

            flash(
                "Unable to load the customer dashboard.",
                "danger"
            )

        finally:

            db.close()

        # -----------------------------------------------------
        # CART
        # -----------------------------------------------------

        cart = self.get_cart()

        total = self.calculate_cart_total(cart)

        # -----------------------------------------------------
        # RENDER ONLY ONE CUSTOMER PAGE
        # -----------------------------------------------------

        return render_template(
            "customer/dashboard.html",

            tables=tables,

            selected_table=selected_table,

            table_id=(
                selected_table["id"]
                if selected_table
                else None
            ),

            table_name=(
                selected_table["name"]
                if selected_table
                else None
            ),

            menu_items=menu_items,

            cart=cart,

            total=total,

            orders=orders
        )

    # =========================================================
    # QR SCAN
    # =========================================================

    def scan_qr(self, table_id):

        db = Database()

        try:

            table = db.fetch_one("""
                SELECT
                    id,
                    name
                FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))

            if not table:

                flash(
                    "Invalid table QR code.",
                    "danger"
                )

                return redirect(
                    url_for("customer.menu")
                )

            # -------------------------------------------------
            # CHECK ACTIVE ORDER
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
                "Unable to read this QR code.",
                "danger"
            )

            return redirect(
                url_for("customer.menu")
            )

        finally:

            db.close()

        # -----------------------------------------------------
        # SAVE TABLE IN SESSION
        # -----------------------------------------------------

        session["table_id"] = int(table["id"])
        session["table_name"] = table["name"]

        # -----------------------------------------------------
        # IF TABLE ALREADY HAS ACTIVE ORDER
        # -----------------------------------------------------

        if active_order:

            flash(
                f'{table["name"]} already has an active order.',
                "warning"
            )

        else:

            # New customer session/order
            session["cart"] = {}

            flash(
                f'Welcome! You are ordering from {table["name"]}.',
                "success"
            )

        session.modified = True

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # MENU
    # =========================================================

    def menu(self):

        return self.dashboard()

    # =========================================================
    # CART
    # =========================================================

    def cart(self):

        return self.dashboard()

    # =========================================================
    # ADD TO CART
    # =========================================================

    def add_to_cart(self, item_id):

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

        if not item:

            flash(
                "This menu item is not available.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        cart = self.get_cart()

        key = str(item_id)

        if key in cart:

            cart[key]["quantity"] += 1

        else:

            cart[key] = {
                "id": int(item["id"]),
                "name": item["name"],
                "price": float(item["price"]),
                "quantity": 1
            }

        session["cart"] = cart
        session.modified = True

        flash(
            f'{item["name"]} added to your order.',
            "success"
        )

        # IMPORTANT
        # Always return to dashboard.
        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # UPDATE CART
    # =========================================================

    def update_cart(self, item_id):

        cart = self.get_cart()

        key = str(item_id)

        if key not in cart:

            return redirect(
                url_for("customer.dashboard")
            )

        try:

            quantity = int(
                request.form.get("quantity", 1)
            )

        except (ValueError, TypeError):

            quantity = 1

        if quantity <= 0:

            del cart[key]

        else:

            cart[key]["quantity"] = quantity

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

        key = str(item_id)

        if key in cart:

            item_name = cart[key].get(
                "name",
                "Item"
            )

            del cart[key]

            session["cart"] = cart
            session.modified = True

            flash(
                f"{item_name} removed from your order.",
                "success"
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
            "Your order has been cleared.",
            "success"
        )

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # PLACE ORDER
    # =========================================================

    def place_order(self):

        table_id = self.get_table_id()

        cart = self.get_cart()

        if not table_id:

            flash(
                "Please scan the QR code on your table first.",
                "warning"
            )

            return redirect(
                url_for("customer.menu")
            )

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
            # CHECK TABLE
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
            # CHECK EXISTING ACTIVE ORDER
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

                flash(
                    "This table already has an active order.",
                    "warning"
                )

                return redirect(
                    url_for("customer.dashboard")
                )

            # -------------------------------------------------
            # CREATE ORDER
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

            order = db.fetch_one("""
                SELECT LAST_INSERT_ID() AS id
            """)

            if not order:

                raise Exception(
                    "Order could not be created."
                )

            order_id = order["id"]

            # -------------------------------------------------
            # ADD ORDER ITEMS
            # -------------------------------------------------

            for item in cart.values():

                quantity = int(
                    item.get("quantity", 1)
                )

                price = float(
                    item.get("price", 0)
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
            # CLEAR CART
            # -------------------------------------------------

            session["cart"] = {}

            session.modified = True

            flash(
                f"Order #{order_id} placed successfully!",
                "success"
            )

            # IMPORTANT:
            # Stay on dashboard.
            return redirect(
                url_for("customer.dashboard")
            )

        except Exception as e:

            print(
                "PLACE ORDER ERROR:",
                e
            )

            flash(
                "Unable to place your order.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        finally:

            db.close()

    # =========================================================
    # ORDERS
    # =========================================================

    def orders(self):

        return self.dashboard()

    # =========================================================
    # VIEW ORDER
    # =========================================================

    def view_order(self, order_id):

        return self.dashboard()

    # =========================================================
    # MOBILE
    # =========================================================

    def mobile(self):

        return self.dashboard()
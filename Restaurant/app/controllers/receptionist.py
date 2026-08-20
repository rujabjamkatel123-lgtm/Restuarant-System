"""
=============================================================
  Restaurant Receptionist Controller
=============================================================

  Main responsibilities:

    - Display receptionist dashboard
    - Display incoming orders
    - View order details
    - Change order status
    - Mark orders as preparing
    - Mark orders as ready
    - Mark orders as served
    - Cancel orders
    - Clear restaurant tables
    - Provide order notifications

=============================================================
"""

from flask import render_template, redirect, url_for, flash

from app.controllers.base_controllers import BaseController
from app.modules.database import Database


class ReceptionistController(BaseController):
    """
    Controller for Receptionist operations.
    """

    # =========================================================
    # RECEPTIONIST DASHBOARD
    # =========================================================

    def dashboard(self):
        """
        Display receptionist dashboard.

        Shows:
            - Pending orders
            - Preparing orders
            - Ready orders
            - Served orders
            - Recent orders
            - Table information
        """

        db = Database()

        try:

            # -------------------------------------------------
            # Get all orders
            # -------------------------------------------------

            orders = db.fetch_all("""
                SELECT
                    o.id,
                    o.table_id,
                    t.name AS table_name,
                    o.status,
                    o.created_at
                FROM orders o

                LEFT JOIN restaurant_tables t
                    ON o.table_id = t.id

                ORDER BY o.id DESC
            """)

            # -------------------------------------------------
            # Pending orders
            # -------------------------------------------------

            incoming_count = db.fetch_one("""
                SELECT COUNT(*) AS total
                FROM orders
                WHERE status = 'pending'
            """)

            # -------------------------------------------------
            # Preparing orders
            # -------------------------------------------------

            preparing_count = db.fetch_one("""
                SELECT COUNT(*) AS total
                FROM orders
                WHERE status = 'preparing'
            """)

            # -------------------------------------------------
            # Ready orders
            # -------------------------------------------------

            ready_count = db.fetch_one("""
                SELECT COUNT(*) AS total
                FROM orders
                WHERE status = 'ready'
            """)

            # -------------------------------------------------
            # Served orders
            # -------------------------------------------------

            served_count = db.fetch_one("""
                SELECT COUNT(*) AS total
                FROM orders
                WHERE status = 'served'
            """)

            # -------------------------------------------------
            # Tables with current status
            # -------------------------------------------------

            tables = db.fetch_all("""
                SELECT
                    t.id,
                    t.name,

                    (
                        SELECT o.id
                        FROM orders o
                        WHERE o.table_id = t.id
                        AND o.status IN (
                            'pending',
                            'preparing',
                            'ready',
                            'served'
                        )
                        ORDER BY o.id DESC
                        LIMIT 1
                    ) AS current_order_id,

                    (
                        SELECT o.status
                        FROM orders o
                        WHERE o.table_id = t.id
                        AND o.status IN (
                            'pending',
                            'preparing',
                            'ready',
                            'served'
                        )
                        ORDER BY o.id DESC
                        LIMIT 1
                    ) AS current_order_status

                FROM restaurant_tables t
                ORDER BY t.id ASC
            """)

            return render_template(
                "receptionist/dashboard.html",

                orders=orders,

                incoming_count=incoming_count["total"],
                preparing_count=preparing_count["total"],
                ready_count=ready_count["total"],
                served_count=served_count["total"],

                tables=tables
            )

        finally:
            db.close()

    # =========================================================
    # ALL ORDERS
    # =========================================================

    def orders(self):
        """
        Display all restaurant orders.
        """

        db = Database()

        try:

            orders = db.fetch_all("""
                SELECT
                    o.id,
                    o.table_id,
                    t.name AS table_name,
                    o.status,
                    o.created_at

                FROM orders o

                LEFT JOIN restaurant_tables t
                    ON o.table_id = t.id

                ORDER BY o.id DESC
            """)

            return render_template(
                "receptionist/orders.html",
                orders=orders
            )

        finally:
            db.close()

    # =========================================================
    # ORDER DETAILS
    # =========================================================

    def order_details(self, order_id):
        """
        Display items belonging to an order.
        """

        db = Database()

        try:

            # -------------------------------------------------
            # Get order
            # -------------------------------------------------

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
            """, (order_id,))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            # -------------------------------------------------
            # Get order items
            # -------------------------------------------------

            items = db.fetch_all("""
                SELECT
                    oi.id,
                    oi.item_id,
                    m.name AS item_name,
                    oi.quantity,
                    oi.price_at_order,

                    (
                        oi.quantity * oi.price_at_order
                    ) AS subtotal

                FROM order_items oi

                JOIN menu_items m
                    ON oi.item_id = m.id

                WHERE oi.order_id = %s

                ORDER BY oi.id ASC
            """, (order_id,))

            # -------------------------------------------------
            # Calculate total
            # -------------------------------------------------

            total = sum(
                float(item["subtotal"])
                for item in items
            )

            return render_template(
                "receptionist/orders.html",
                order=order,
                items=items,
                total=total
            )

        finally:
            db.close()

    # =========================================================
    # MARK ORDER AS PREPARING
    # =========================================================

    def mark_preparing(self, order_id):
        """
        Change pending order to preparing.
        """

        db = Database()

        try:

            order = db.fetch_one("""
                SELECT
                    id,
                    status
                FROM orders
                WHERE id = %s
            """, (order_id,))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            if order["status"] != "pending":

                flash(
                    "Only pending orders can be marked as preparing.",
                    "warning"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            db.execute("""
                UPDATE orders

                SET status = 'preparing'

                WHERE id = %s
            """, (order_id,))

            flash(
                f"Order #{order_id} is now being prepared.",
                "info"
            )

            return redirect(
                url_for("receptionist.orders")
            )

        finally:
            db.close()

    # =========================================================
    # MARK ORDER AS READY
    # =========================================================

    def mark_ready(self, order_id):
        """
        Change preparing order to ready.
        """

        db = Database()

        try:

            order = db.fetch_one("""
                SELECT
                    id,
                    status
                FROM orders
                WHERE id = %s
            """, (order_id,))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            if order["status"] != "preparing":

                flash(
                    "Only preparing orders can be marked as ready.",
                    "warning"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            db.execute("""
                UPDATE orders

                SET status = 'ready'

                WHERE id = %s
            """, (order_id,))

            flash(
                f"Order #{order_id} is ready.",
                "success"
            )

            return redirect(
                url_for("receptionist.orders")
            )

        finally:
            db.close()

    # =========================================================
    # MARK ORDER AS SERVED
    # =========================================================

    def mark_served(self, order_id):
        """
        Mark ready order as served.

        IMPORTANT:

        The table is NOT cleared here.

        After the order is served, the table remains occupied
        until receptionist explicitly clicks "Clear Table".
        """

        db = Database()

        try:

            order = db.fetch_one("""
                SELECT
                    id,
                    table_id,
                    status
                FROM orders
                WHERE id = %s
            """, (order_id,))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            if order["status"] != "ready":

                flash(
                    "Only ready orders can be marked as served.",
                    "warning"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            db.execute("""
                UPDATE orders

                SET status = 'served'

                WHERE id = %s
            """, (order_id,))

            flash(
                f"Order #{order_id} has been served. "
                f"The table must now be cleared before another customer can use its QR code.",
                "success"
            )

            return redirect(
                url_for("receptionist.orders")
            )

        finally:
            db.close()

    # =========================================================
    # CLEAR TABLE
    # =========================================================

    def clear_table(self, table_id):
        """
        Clear a restaurant table.

        A table can only be cleared after its current order
        has been served.

        When cleared:

            served -> cleared

        The customer QR code will then become available again.
        """

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

                flash(
                    "Table not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Find latest order for this table
            # -------------------------------------------------

            latest_order = db.fetch_one("""
                SELECT
                    id,
                    status
                FROM orders

                WHERE table_id = %s

                ORDER BY id DESC

                LIMIT 1
            """, (table_id,))

            # -------------------------------------------------
            # No previous order
            # -------------------------------------------------

            if not latest_order:

                flash(
                    f"{table['name']} is already clear.",
                    "info"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Check order status
            # -------------------------------------------------

            status = latest_order["status"]

            # -------------------------------------------------
            # Cannot clear active order
            # -------------------------------------------------

            if status in (
                "pending",
                "preparing",
                "ready"
            ):

                flash(
                    f"{table['name']} cannot be cleared yet. "
                    f"The current order is still {status}.",
                    "warning"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Already cleared
            # -------------------------------------------------

            if status == "cleared":

                flash(
                    f"{table['name']} is already clear.",
                    "info"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Cancelled order
            # -------------------------------------------------

            if status == "cancelled":

                db.execute("""
                    UPDATE orders

                    SET status = 'cleared'

                    WHERE id = %s
                """, (latest_order["id"],))

                flash(
                    f"{table['name']} has been cleared.",
                    "success"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Served order
            # -------------------------------------------------

            if status == "served":

                db.execute("""
                    UPDATE orders

                    SET status = 'cleared'

                    WHERE id = %s
                """, (latest_order["id"],))

                flash(
                    f"{table['name']} is now clear. "
                    f"The table QR code can be used again.",
                    "success"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Unknown status
            # -------------------------------------------------

            flash(
                f"Table cannot be cleared because its latest "
                f"order has an unknown status: {status}.",
                "warning"
            )

            return redirect(
                url_for("receptionist.dashboard")
            )

        finally:
            db.close()

    # =========================================================
    # CANCEL ORDER
    # =========================================================

    def cancel_order(self, order_id):
        """
        Cancel an order.

        The order is not deleted.

        It remains in the database so the manager can see
        the order history.
        """

        db = Database()

        try:

            order = db.fetch_one("""
                SELECT
                    id,
                    status
                FROM orders
                WHERE id = %s
            """, (order_id,))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            if order["status"] in (
                "served",
                "cleared",
                "cancelled"
            ):

                flash(
                    "This order can no longer be cancelled.",
                    "warning"
                )

                return redirect(
                    url_for("receptionist.orders")
                )

            db.execute("""
                UPDATE orders

                SET status = 'cancelled'

                WHERE id = %s
            """, (order_id,))

            flash(
                f"Order #{order_id} has been cancelled.",
                "warning"
            )

            return redirect(
                url_for("receptionist.orders")
            )

        finally:
            db.close()

    # =========================================================
    # NOTIFICATIONS
    # =========================================================

    def notifications(self):
        """
        Return pending orders for receptionist notifications.
        """

        db = Database()

        try:

            notifications = db.fetch_all("""
                SELECT
                    o.id,
                    o.table_id,
                    t.name AS table_name,
                    o.status,
                    o.created_at

                FROM orders o

                LEFT JOIN restaurant_tables t
                    ON o.table_id = t.id

                WHERE o.status = 'pending'

                ORDER BY o.id DESC
            """)

            return {
                "count": len(notifications),
                "orders": notifications
            }

        finally:
            db.close()

    # =========================================================
    # VIEW SINGLE ORDER
    # =========================================================

    def view_order(self, order_id):
        """
        Display complete information about a specific order.
        """

        db = Database()

        try:

            # -------------------------------------------------
            # Get order
            # -------------------------------------------------

            order = db.fetch_one("""
                SELECT
                    orders.id,
                    orders.table_id,
                    orders.created_at,
                    orders.status,

                    restaurant_tables.name AS table_name

                FROM orders

                LEFT JOIN restaurant_tables
                    ON orders.table_id = restaurant_tables.id

                WHERE orders.id = %s
            """, (order_id,))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("receptionist.dashboard")
                )

            # -------------------------------------------------
            # Get order items
            # -------------------------------------------------

            order["items"] = db.fetch_all("""
                SELECT
                    order_items.quantity,
                    order_items.price_at_order,

                    menu_items.name

                FROM order_items

                INNER JOIN menu_items
                    ON order_items.item_id = menu_items.id

                WHERE order_items.order_id = %s

                ORDER BY order_items.id ASC
            """, (order_id,))

            # -------------------------------------------------
            # Calculate total
            # -------------------------------------------------

            order["total"] = 0

            for item in order["items"]:

                order["total"] += (
                    float(item["price_at_order"])
                    * int(item["quantity"])
                )

            return render_template(
                "receptionist/view_order.html",
                order=order
            )

        finally:
            db.close()
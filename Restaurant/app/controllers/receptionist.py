"""
=============================================================
  Receptionist Controller
=============================================================
  This controller handles all receptionist-related operations.

  Main responsibilities:
    - Display receptionist dashboard
    - Display incoming orders
    - View order details
    - Change order status
    - Mark orders as preparing
    - Mark orders as ready
    - Mark orders as served
    - Provide simple order notifications

  OOP Concepts:
    - Inheritance: ReceptionistController inherits BaseController
    - Encapsulation: Database operations are handled through
      the Database class.
    - Separation of Responsibility: Controller handles the
      application logic while models handle database operations.
=============================================================
"""

from flask import render_template, redirect, url_for, flash

from app.controllers.base_controllers import BaseController
from app.modules.database import Database


class ReceptionistController(BaseController):
    """
    Controller for the Receptionist Dashboard.
    """

    # =========================================================
    # Receptionist Dashboard
    # =========================================================

    def dashboard(self):
        """
        Display the receptionist dashboard.

        The dashboard shows:
            - Total incoming orders
            - Preparing orders
            - Ready orders
            - Served orders
            - Recent orders
        """

        db = Database()

        # Get all orders with table information
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

        # Count orders by status
        incoming_count = db.fetch_one("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE status = 'pending'
        """)

        preparing_count = db.fetch_one("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE status = 'preparing'
        """)

        ready_count = db.fetch_one("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE status = 'ready'
        """)

        served_count = db.fetch_one("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE status = 'served'
        """)

        db.close()

        return render_template(
            "receptionist/dashboard.html",
            orders=orders,
            incoming_count=incoming_count["total"],
            preparing_count=preparing_count["total"],
            ready_count=ready_count["total"],
            served_count=served_count["total"]
        )

    # =========================================================
    # Order Management
    # =========================================================

    def orders(self):
        """
        Display all restaurant orders for the receptionist.
        """

        db = Database()

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

        db.close()

        return render_template(
            "receptionist/orders.html",
            orders=orders
        )

    # =========================================================
    # Order Details
    # =========================================================

    def order_details(self, order_id):
        """
        Display the items belonging to a particular order.
        """

        db = Database()

        # Get order information
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
            db.close()

            flash("Order not found.", "danger")
            return redirect(url_for("receptionist.orders"))

        # Get items in the order
        items = db.fetch_all("""
            SELECT
                oi.id,
                oi.item_id,
                m.name AS item_name,
                oi.quantity,
                oi.price_at_order,
                (oi.quantity * oi.price_at_order) AS subtotal
            FROM order_items oi
            JOIN menu_items m
                ON oi.item_id = m.id
            WHERE oi.order_id = %s
            ORDER BY oi.id ASC
        """, (order_id,))

        db.close()

        # Calculate total
        total = sum(
            item["subtotal"]
            for item in items
        )

        return render_template(
            "receptionist/orders.html",
            order=order,
            items=items,
            total=total
        )

    # =========================================================
    # Mark Order as Preparing
    # =========================================================

    def mark_preparing(self, order_id):
        """
        Change an order status from pending to preparing.
        """

        db = Database()

        order = db.fetch_one("""
            SELECT id
            FROM orders
            WHERE id = %s
        """, (order_id,))

        if not order:
            db.close()

            flash("Order not found.", "danger")
            return redirect(url_for("receptionist.orders"))

        db.execute("""
            UPDATE orders
            SET status = 'preparing'
            WHERE id = %s
        """, (order_id,))

        db.close()

        flash(
            f"Order #{order_id} is now being prepared.",
            "info"
        )

        return redirect(url_for("receptionist.orders"))

    # =========================================================
    # Mark Order as Ready
    # =========================================================

    def mark_ready(self, order_id):
        """
        Change an order status to ready.
        """

        db = Database()

        order = db.fetch_one("""
            SELECT id
            FROM orders
            WHERE id = %s
        """, (order_id,))

        if not order:
            db.close()

            flash("Order not found.", "danger")
            return redirect(url_for("receptionist.orders"))

        db.execute("""
            UPDATE orders
            SET status = 'ready'
            WHERE id = %s
        """, (order_id,))

        db.close()

        flash(
            f"Order #{order_id} is ready.",
            "success"
        )

        return redirect(url_for("receptionist.orders"))

    # =========================================================
    # Mark Order as Served
    # =========================================================

    def mark_served(self, order_id):
        """
        Mark an order as served.
        """

        db = Database()

        order = db.fetch_one("""
            SELECT id
            FROM orders
            WHERE id = %s
        """, (order_id,))

        if not order:
            db.close()

            flash("Order not found.", "danger")
            return redirect(url_for("receptionist.orders"))

        db.execute("""
            UPDATE orders
            SET status = 'served'
            WHERE id = %s
        """, (order_id,))

        db.close()

        flash(
            f"Order #{order_id} has been served.",
            "success"
        )

        return redirect(url_for("receptionist.orders"))

    # =========================================================
    # Cancel Order
    # =========================================================

    def cancel_order(self, order_id):
        """
        Cancel an order.

        The order is not deleted from the database.
        Its status is changed to 'cancelled' so that the
        manager can still see it in the order history.
        """

        db = Database()

        order = db.fetch_one("""
            SELECT id
            FROM orders
            WHERE id = %s
        """, (order_id,))

        if not order:
            db.close()

            flash("Order not found.", "danger")
            return redirect(url_for("receptionist.orders"))

        db.execute("""
            UPDATE orders
            SET status = 'cancelled'
            WHERE id = %s
        """, (order_id,))

        db.close()

        flash(
            f"Order #{order_id} has been cancelled.",
            "warning"
        )

        return redirect(url_for("receptionist.orders"))

    # =========================================================
    # Order Notification
    # =========================================================

    def notifications(self):
        """
        Get pending orders that can be displayed as
        receptionist notifications.

        This is a simple database-based notification system
        for the MVP.

        Later it can be replaced with:
            - AJAX polling
            - Fetch API
            - WebSocket
            - Flask-SocketIO
        """

        db = Database()

        notifications = db.fetch_all("""
            SELECT
                o.id,
                t.name AS table_name,
                o.status,
                o.created_at
            FROM orders o
            LEFT JOIN restaurant_tables t
                ON o.table_id = t.id
            WHERE o.status = 'pending'
            ORDER BY o.id DESC
        """)

        db.close()

        return {
            "count": len(notifications),
            "orders": notifications
        }
    def view_order(self, order_id):
        """
        Display details for a specific order for the receptionist.
        """
        db = Database()

        # Fetch the order details along with table and customer info
        order = db.fetch_one("""
            SELECT
                orders.id,
                orders.created_at,
                orders.status,
                restaurant_tables.name AS table_name
            FROM orders
            LEFT JOIN restaurant_tables
                ON orders.table_id = restaurant_tables.id
            WHERE orders.id = %s
        """, (order_id,))

        if not order:
            db.close()
            flash("Order not found.", "danger")
            return redirect(url_for("receptionist.dashboard"))

        # Fetch all items belonging to this order
        order["items"] = db.fetch_all("""
            SELECT
                order_items.quantity,
                order_items.price_at_order,
                menu_items.name
            FROM order_items
            INNER JOIN menu_items
                ON order_items.item_id = menu_items.id
            WHERE order_items.order_id = %s
        """, (order_id,))

        # Calculate total price
        order["total"] = 0
        for item in order["items"]:
            order["total"] += (
                float(item["price_at_order"])
                * int(item["quantity"])
            )

        db.close()

        return render_template(
            "receptionist/view_order.html",
            order=order
        )
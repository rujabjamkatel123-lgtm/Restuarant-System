"""
=============================================================
  Restaurant Order Module
=============================================================
  This module manages restaurant orders.

  Main responsibilities:
    - Get all orders
    - Find an order by ID
    - Create a new order
    - Update order status
    - Delete an order
    - Get orders for a specific table
    - Calculate order total
    - Get recent orders
    - Get order history

  OOP Concepts:
    - Encapsulation: SQL/database operations are kept inside
      the Order class.
    - Abstraction: Controllers use simple methods instead of
      writing SQL queries directly.
=============================================================
"""

from app.modules.database import Database


class Order:
    """
    Order Model — represents a restaurant customer order.
    """

    def __init__(
        self,
        table_id=None,
        status="pending"
    ):
        self.table_id = table_id
        self.status = status

    # =========================================================
    # Get All Orders
    # =========================================================

    def get_all(self):
        """
        Get all restaurant orders.

        Table information is included so the receptionist
        can see which table placed the order.
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

        return orders

    # =========================================================
    # Find Order By ID
    # =========================================================

    def find_by_id(self, order_id):
        """
        Find one order using its ID.
        """

        db = Database()

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

        db.close()

        return order

    # =========================================================
    # Create Order
    # =========================================================

    def save(self, table_id=None, status="pending"):
        """
        Create a new restaurant order.

        Returns the newly created order ID.
        """

        table_id = (
            table_id
            if table_id is not None
            else self.table_id
        )

        status = (
            status
            if status is not None
            else self.status
        )

        db = Database()

        db.execute("""
            INSERT INTO orders
            (
                table_id,
                status
            )
            VALUES (%s, %s)
        """, (
            table_id,
            status
        ))

        # Get the newly created order
        order = db.fetch_one("""
            SELECT id
            FROM orders
            WHERE table_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (table_id,))

        db.close()

        if order:
            return order["id"]

        return None

    # =========================================================
    # Update Order Status
    # =========================================================

    def update_status(self, order_id, status):
        """
        Change the status of an order.

        Possible statuses:
            pending
            preparing
            ready
            served
            cancelled
        """

        db = Database()

        db.execute("""
            UPDATE orders
            SET status = %s
            WHERE id = %s
        """, (
            status,
            order_id
        ))

        db.close()

    # =========================================================
    # Delete Order
    # =========================================================

    def delete(self, order_id):
        """
        Delete an order.

        Normally, cancelled orders should not be deleted because
        the manager needs them for history. This method is kept
        for administrative use.
        """

        db = Database()

        db.execute("""
            DELETE FROM orders
            WHERE id = %s
        """, (order_id,))

        db.close()

    # =========================================================
    # Get Orders By Table
    # =========================================================

    def get_by_table(self, table_id):
        """
        Get all orders belonging to a particular table.
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
            WHERE o.table_id = %s
            ORDER BY o.id DESC
        """, (table_id,))

        db.close()

        return orders

    # =========================================================
    # Get Active Order For Table
    # =========================================================

    def get_active_by_table(self, table_id):
        """
        Get the current active order for a table.

        Active orders:
            pending
            preparing
            ready
        """

        db = Database()

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
            WHERE o.table_id = %s
              AND o.status IN (
                  'pending',
                  'preparing',
                  'ready'
              )
            ORDER BY o.id DESC
            LIMIT 1
        """, (table_id,))

        db.close()

        return order

    # =========================================================
    # Get Pending Orders
    # =========================================================

    def get_pending(self):
        """
        Get orders that have just been placed.

        Used by the receptionist dashboard.
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
            WHERE o.status = 'pending'
            ORDER BY o.created_at ASC
        """)

        db.close()

        return orders

    # =========================================================
    # Get Preparing Orders
    # =========================================================

    def get_preparing(self):
        """
        Get orders currently being prepared.
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
            WHERE o.status = 'preparing'
            ORDER BY o.created_at ASC
        """)

        db.close()

        return orders

    # =========================================================
    # Get Ready Orders
    # =========================================================

    def get_ready(self):
        """
        Get orders that are ready to be served.
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
            WHERE o.status = 'ready'
            ORDER BY o.created_at ASC
        """)

        db.close()

        return orders

    # =========================================================
    # Get Served Orders
    # =========================================================

    def get_served(self):
        """
        Get orders that have already been served.
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
            WHERE o.status = 'served'
            ORDER BY o.created_at DESC
        """)

        db.close()

        return orders

    # =========================================================
    # Get Order Items
    # =========================================================

    def get_items(self, order_id):
        """
        Get all menu items belonging to an order.
        """

        db = Database()

        items = db.fetch_all("""
            SELECT
                oi.id,
                oi.order_id,
                oi.item_id,
                m.name AS item_name,
                oi.quantity,
                oi.price_at_order,
                (
                    oi.quantity *
                    oi.price_at_order
                ) AS subtotal
            FROM order_items oi
            JOIN menu_items m
                ON oi.item_id = m.id
            WHERE oi.order_id = %s
            ORDER BY oi.id ASC
        """, (order_id,))

        db.close()

        return items

    # =========================================================
    # Calculate Order Total
    # =========================================================

    def get_total(self, order_id):
        """
        Calculate the total amount of an order.
        """

        db = Database()

        result = db.fetch_one("""
            SELECT
                COALESCE(
                    SUM(
                        quantity *
                        price_at_order
                    ),
                    0
                ) AS total
            FROM order_items
            WHERE order_id = %s
        """, (order_id,))

        db.close()

        return result["total"]

    # =========================================================
    # Get Complete Order
    # =========================================================

    def get_complete_order(self, order_id):
        """
        Get an order together with:
            - Table information
            - Order items
            - Total amount
        """

        order = self.find_by_id(order_id)

        if not order:
            return None

        items = self.get_items(order_id)

        total = self.get_total(order_id)

        return {
            "order": order,
            "items": items,
            "total": total
        }

    # =========================================================
    # Count Orders By Status
    # =========================================================

    def count_by_status(self, status):
        """
        Count orders having a particular status.

        Example:
            count_by_status("pending")
        """

        db = Database()

        result = db.fetch_one("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE status = %s
        """, (status,))

        db.close()

        return result["total"]

    # =========================================================
    # Get Recent Orders
    # =========================================================

    def get_recent(self, limit=10):
        """
        Get the most recent restaurant orders.

        The limit is controlled internally to avoid placing
        arbitrary SQL into the query.
        """

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10

        if limit <= 0:
            limit = 10

        if limit > 100:
            limit = 100

        db = Database()

        orders = db.fetch_all(f"""
            SELECT
                o.id,
                o.table_id,
                t.name AS table_name,
                o.status,
                o.created_at
            FROM orders o
            LEFT JOIN restaurant_tables t
                ON o.table_id = t.id
            ORDER BY o.created_at DESC
            LIMIT {limit}
        """)

        db.close()

        return orders

    # =========================================================
    # Get Order History
    # =========================================================

    def get_history(self):
        """
        Get completed and cancelled orders.

        Used by the Manager Dashboard history page.
        """

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
            WHERE o.status IN (
                'served',
                'cancelled'
            )
            GROUP BY
                o.id,
                o.table_id,
                t.name,
                o.status,
                o.created_at
            ORDER BY o.created_at DESC
        """)

        db.close()

        return orders
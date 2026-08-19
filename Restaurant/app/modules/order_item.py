"""
=============================================================
  Restaurant Order Item Module
=============================================================
  This module manages individual items inside restaurant
  orders.

  Example:

      Order #10
          ├── Pizza x 2
          ├── Coke x 1
          └── Burger x 1

  The "orders" table stores Order #10.

  The "order_items" table stores:
      Pizza  -> quantity 2
      Coke   -> quantity 1
      Burger -> quantity 1

  Main responsibilities:
    - Get all order items
    - Find an order item by ID
    - Add an item to an order
    - Update item quantity
    - Delete an order item
    - Get all items for an order
    - Calculate item subtotal
    - Calculate order total

  OOP Concepts:
    - Encapsulation: Database operations are kept inside
      the OrderItem class.
    - Abstraction: Controllers can use simple methods without
      writing SQL queries directly.
=============================================================
"""

from app.modules.database import Database


class OrderItem:
    """
    OrderItem Model — represents one menu item inside
    a restaurant order.
    """

    def __init__(
        self,
        order_id=None,
        item_id=None,
        quantity=1,
        price_at_order=None
    ):
        self.order_id = order_id
        self.item_id = item_id
        self.quantity = quantity
        self.price_at_order = price_at_order

    # =========================================================
    # Get All Order Items
    # =========================================================

    def get_all(self):
        """
        Get all order items.

        Menu item information is included so that we can
        display the actual menu item name.
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
            ORDER BY oi.id DESC
        """)

        db.close()

        return items

    # =========================================================
    # Find Order Item By ID
    # =========================================================

    def find_by_id(self, order_item_id):
        """
        Find one order item using its ID.
        """

        db = Database()

        item = db.fetch_one("""
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
            WHERE oi.id = %s
        """, (order_item_id,))

        db.close()

        return item

    # =========================================================
    # Add Item To Order
    # =========================================================

    def save(
        self,
        order_id=None,
        item_id=None,
        quantity=None,
        price_at_order=None
    ):
        """
        Add a menu item to an order.

        The price is stored at the time the order is created.

        This is important because if the restaurant changes
        the menu price later, old orders should still keep
        their original price.
        """

        order_id = (
            order_id
            if order_id is not None
            else self.order_id
        )

        item_id = (
            item_id
            if item_id is not None
            else self.item_id
        )

        quantity = (
            quantity
            if quantity is not None
            else self.quantity
        )

        # -----------------------------------------------------
        # If price was not supplied, get the current menu price
        # -----------------------------------------------------

        if price_at_order is None:
            price_at_order = self.price_at_order

        if price_at_order is None:

            db = Database()

            menu_item = db.fetch_one("""
                SELECT price
                FROM menu_items
                WHERE id = %s
            """, (item_id,))

            if menu_item:
                price_at_order = menu_item["price"]

            db.close()

        # -----------------------------------------------------
        # Insert order item
        # -----------------------------------------------------

        db = Database()

        db.execute("""
            INSERT INTO order_items
            (
                order_id,
                item_id,
                quantity,
                price_at_order
            )
            VALUES (%s, %s, %s, %s)
        """, (
            order_id,
            item_id,
            quantity,
            price_at_order
        ))

        db.close()

    # =========================================================
    # Update Quantity
    # =========================================================

    def update_quantity(self, order_item_id, quantity):
        """
        Update the quantity of an order item.
        """

        db = Database()

        db.execute("""
            UPDATE order_items
            SET quantity = %s
            WHERE id = %s
        """, (
            quantity,
            order_item_id
        ))

        db.close()

    # =========================================================
    # Delete Order Item
    # =========================================================

    def delete(self, order_item_id):
        """
        Delete one item from an order.
        """

        db = Database()

        db.execute("""
            DELETE FROM order_items
            WHERE id = %s
        """, (order_item_id,))

        db.close()

    # =========================================================
    # Get Items By Order
    # =========================================================

    def get_by_order(self, order_id):
        """
        Get every menu item belonging to one order.
        """

        db = Database()

        items = db.fetch_all("""
            SELECT
                oi.id,
                oi.order_id,
                oi.item_id,
                m.name AS item_name,
                m.category,
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
    # Find Item In Specific Order
    # =========================================================

    def find_by_order_and_item(self, order_id, item_id):
        """
        Find a particular menu item inside an order.

        This is useful when the customer adds the same item
        to the cart again.
        """

        db = Database()

        item = db.fetch_one("""
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
              AND oi.item_id = %s
            LIMIT 1
        """, (
            order_id,
            item_id
        ))

        db.close()

        return item

    # =========================================================
    # Increase Quantity
    # =========================================================

    def increase_quantity(self, order_item_id, amount=1):
        """
        Increase the quantity of an order item.
        """

        db = Database()

        db.execute("""
            UPDATE order_items
            SET quantity = quantity + %s
            WHERE id = %s
        """, (
            amount,
            order_item_id
        ))

        db.close()

    # =========================================================
    # Decrease Quantity
    # =========================================================

    def decrease_quantity(self, order_item_id, amount=1):
        """
        Decrease the quantity of an order item.

        Quantity will never be allowed to become zero or
        negative through this method.
        """

        db = Database()

        db.execute("""
            UPDATE order_items
            SET quantity = quantity - %s
            WHERE id = %s
              AND quantity > %s
        """, (
            amount,
            order_item_id,
            amount
        ))

        db.close()

    # =========================================================
    # Calculate Item Subtotal
    # =========================================================

    def get_subtotal(self, order_item_id):
        """
        Calculate the subtotal of one order item.

        Example:

            Pizza price = 500
            Quantity    = 2

            Subtotal = 1000
        """

        db = Database()

        result = db.fetch_one("""
            SELECT
                COALESCE(
                    quantity * price_at_order,
                    0
                ) AS subtotal
            FROM order_items
            WHERE id = %s
        """, (order_item_id,))

        db.close()

        if result:
            return result["subtotal"]

        return 0

    # =========================================================
    # Calculate Complete Order Total
    # =========================================================

    def get_order_total(self, order_id):
        """
        Calculate the total price of all items in an order.
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
    # Count Items In Order
    # =========================================================

    def count_by_order(self, order_id):
        """
        Count the total quantity of menu items in an order.

        Example:

            Pizza x 2
            Coke x 1

            Total = 3 items
        """

        db = Database()

        result = db.fetch_one("""
            SELECT
                COALESCE(
                    SUM(quantity),
                    0
                ) AS total
            FROM order_items
            WHERE order_id = %s
        """, (order_id,))

        db.close()

        return result["total"]
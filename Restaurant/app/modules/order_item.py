"""
=============================================================
Restaurant Order Item Module
=============================================================
Manages individual items inside restaurant orders.
=============================================================
"""

from app.modules.database import Database


class OrderItem:

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
    # GET ALL ORDER ITEMS
    # =========================================================

    def get_all(self):

        db = Database()

        try:

            return db.fetch_all("""
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

        finally:
            db.close()

    # =========================================================
    # FIND BY ID
    # =========================================================

    def find_by_id(self, order_item_id):

        db = Database()

        try:

            return db.fetch_one("""
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
            """, (
                order_item_id,
            ))

        finally:
            db.close()

    # =========================================================
    # ADD ITEM TO ORDER
    # =========================================================

    def save(
        self,
        order_id=None,
        item_id=None,
        quantity=None,
        price_at_order=None
    ):

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

        if price_at_order is None:
            price_at_order = self.price_at_order

        # Get current menu price if no price was supplied
        if price_at_order is None:

            db = Database()

            try:

                menu_item = db.fetch_one("""
                    SELECT price
                    FROM menu_items
                    WHERE id = %s
                """, (
                    item_id,
                ))

                if menu_item:
                    price_at_order = menu_item["price"]

            finally:
                db.close()

        if price_at_order is None:
            raise ValueError(
                "Unable to determine menu item price."
            )

        db = Database()

        try:

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
                item_id,
                quantity,
                price_at_order
            ))

        finally:
            db.close()

    # =========================================================
    # UPDATE QUANTITY
    # =========================================================

    def update_quantity(self, order_item_id, quantity):

        if quantity < 1:
            raise ValueError(
                "Quantity must be at least 1."
            )

        db = Database()

        try:

            db.execute("""
                UPDATE order_items
                SET quantity = %s
                WHERE id = %s
            """, (
                quantity,
                order_item_id
            ))

        finally:
            db.close()

    # =========================================================
    # DELETE ORDER ITEM
    # =========================================================

    def delete(self, order_item_id):

        db = Database()

        try:

            db.execute("""
                DELETE FROM order_items
                WHERE id = %s
            """, (
                order_item_id,
            ))

        finally:
            db.close()

    # =========================================================
    # GET ITEMS BY ORDER
    # =========================================================

    def get_by_order(self, order_id):

        db = Database()

        try:

            return db.fetch_all("""
                SELECT
                    oi.id,
                    oi.order_id,
                    oi.item_id,
                    m.name AS item_name,
                    m.category_id,
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
            """, (
                order_id,
            ))

        finally:
            db.close()

    # =========================================================
    # FIND ITEM IN SPECIFIC ORDER
    # =========================================================

    def find_by_order_and_item(
        self,
        order_id,
        item_id
    ):

        db = Database()

        try:

            return db.fetch_one("""
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

        finally:
            db.close()

    # =========================================================
    # INCREASE QUANTITY
    # =========================================================

    def increase_quantity(
        self,
        order_item_id,
        amount=1
    ):

        if amount < 1:
            raise ValueError(
                "Increase amount must be positive."
            )

        db = Database()

        try:

            db.execute("""
                UPDATE order_items
                SET quantity = quantity + %s
                WHERE id = %s
            """, (
                amount,
                order_item_id
            ))

        finally:
            db.close()

    # =========================================================
    # DECREASE QUANTITY
    # =========================================================

    def decrease_quantity(
        self,
        order_item_id,
        amount=1
    ):

        if amount < 1:
            raise ValueError(
                "Decrease amount must be positive."
            )

        db = Database()

        try:

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

        finally:
            db.close()

    # =========================================================
    # GET ITEM SUBTOTAL
    # =========================================================

    def get_subtotal(self, order_item_id):

        db = Database()

        try:

            result = db.fetch_one("""
                SELECT
                    COALESCE(
                        quantity * price_at_order,
                        0
                    ) AS subtotal

                FROM order_items

                WHERE id = %s
            """, (
                order_item_id,
            ))

            if result:
                return result["subtotal"]

            return 0

        finally:
            db.close()

    # =========================================================
    # GET COMPLETE ORDER TOTAL
    # =========================================================

    def get_order_total(self, order_id):

        db = Database()

        try:

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
            """, (
                order_id,
            ))

            if result:
                return result["total"]

            return 0

        finally:
            db.close()

    # =========================================================
    # COUNT ITEMS IN ORDER
    # =========================================================

    def count_by_order(self, order_id):

        db = Database()

        try:

            result = db.fetch_one("""
                SELECT
                    COALESCE(
                        SUM(quantity),
                        0
                    ) AS total

                FROM order_items

                WHERE order_id = %s
            """, (
                order_id,
            ))

            if result:
                return result["total"]

            return 0

        finally:
            db.close()
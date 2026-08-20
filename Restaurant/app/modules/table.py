"""
=============================================================
Restaurant Table Module
=============================================================
Manages restaurant tables and table availability.
=============================================================
"""

from app.modules.database import Database


class Table:
    """
    Table Model — represents a restaurant table.
    """

    def __init__(self, name=None):
        self.name = name

    # =========================================================
    # GET ALL TABLES
    # =========================================================

    def get_all(self):
        db = Database()

        try:
            return db.fetch_all("""
                SELECT *
                FROM restaurant_tables
                ORDER BY id ASC
            """)
        finally:
            db.close()

    # =========================================================
    # FIND TABLE BY ID
    # =========================================================

    def find_by_id(self, table_id):
        db = Database()

        try:
            return db.fetch_one("""
                SELECT *
                FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))
        finally:
            db.close()

    # =========================================================
    # CREATE TABLE
    # =========================================================

    def save(self, name=None):
        name = name if name is not None else self.name

        db = Database()

        try:
            db.execute("""
                INSERT INTO restaurant_tables (name)
                VALUES (%s)
            """, (name,))
        finally:
            db.close()

    # =========================================================
    # UPDATE TABLE
    # =========================================================

    def update(self, table_id, name):
        db = Database()

        try:
            db.execute("""
                UPDATE restaurant_tables
                SET name = %s
                WHERE id = %s
            """, (
                name,
                table_id
            ))
        finally:
            db.close()

    # =========================================================
    # DELETE TABLE
    # =========================================================

    def delete(self, table_id):
        db = Database()

        try:
            db.execute("""
                DELETE FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))
        finally:
            db.close()

    # =========================================================
    # CHECK TABLE NAME
    # =========================================================

    def name_exists(self, name, exclude_id=None):
        db = Database()

        try:

            if exclude_id is not None:

                result = db.fetch_one("""
                    SELECT id
                    FROM restaurant_tables
                    WHERE name = %s
                    AND id != %s
                """, (
                    name,
                    exclude_id
                ))

            else:

                result = db.fetch_one("""
                    SELECT id
                    FROM restaurant_tables
                    WHERE name = %s
                """, (name,))

            return result is not None

        finally:
            db.close()

    # =========================================================
    # COUNT TABLES
    # =========================================================

    def count_all(self):
        db = Database()

        try:
            result = db.fetch_one("""
                SELECT COUNT(*) AS total
                FROM restaurant_tables
            """)

            return result["total"] if result else 0

        finally:
            db.close()

    # =========================================================
    # GET AVAILABLE TABLES
    # =========================================================

    def get_available(self):
        """
        A table is available when it does not currently have
        an active order.
        """

        db = Database()

        try:

            return db.fetch_all("""
                SELECT
                    t.id,
                    t.name
                FROM restaurant_tables t

                WHERE NOT EXISTS (
                    SELECT 1
                    FROM orders o
                    WHERE o.table_id = t.id
                    AND o.status IN (
                        'pending',
                        'preparing',
                        'ready'
                    )
                )

                ORDER BY t.id ASC
            """)

        finally:
            db.close()

    # =========================================================
    # GET TABLES WITH ORDER STATUS
    # =========================================================

    def get_with_order_status(self):
        db = Database()

        try:

            return db.fetch_all("""
                SELECT
                    t.id,
                    t.name,
                    o.id AS order_id,
                    o.status AS order_status

                FROM restaurant_tables t

                LEFT JOIN orders o
                    ON t.id = o.table_id
                    AND o.status IN (
                        'pending',
                        'preparing',
                        'ready'
                    )

                ORDER BY t.id ASC
            """)

        finally:
            db.close()
"""
=============================================================
  Restaurant Table Module
=============================================================
  This module manages restaurant tables.

  Main responsibilities:
    - Get all restaurant tables
    - Find a table by ID
    - Create a new table
    - Update a table
    - Delete a table
    - Check table information

  OOP Concepts:
    - Encapsulation: Database operations are kept inside
      the Table class.
    - Abstraction: Controllers do not need to know the
      SQL details used to manage tables.
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
    # Get All Tables
    # =========================================================

    def get_all(self):
        """
        Get all restaurant tables.

        Tables are returned in ID order.
        """

        db = Database()

        tables = db.fetch_all("""
            SELECT *
            FROM restaurant_tables
            ORDER BY id ASC
        """)

        db.close()

        return tables

    # =========================================================
    # Find Table By ID
    # =========================================================

    def find_by_id(self, table_id):
        """
        Find one restaurant table using its ID.
        """

        db = Database()

        table = db.fetch_one("""
            SELECT *
            FROM restaurant_tables
            WHERE id = %s
        """, (table_id,))

        db.close()

        return table

    # =========================================================
    # Save / Create Table
    # =========================================================

    def save(self, name=None):
        """
        Create a new restaurant table.

        If name is not supplied, the name stored in the
        object is used.
        """

        name = name if name is not None else self.name

        db = Database()

        db.execute("""
            INSERT INTO restaurant_tables
            (name)
            VALUES (%s)
        """, (name,))

        db.close()

    # =========================================================
    # Update Table
    # =========================================================

    def update(self, table_id, name):
        """
        Update an existing restaurant table.
        """

        db = Database()

        db.execute("""
            UPDATE restaurant_tables
            SET name = %s
            WHERE id = %s
        """, (
            name,
            table_id
        ))

        db.close()

    # =========================================================
    # Delete Table
    # =========================================================

    def delete(self, table_id):
        """
        Delete a restaurant table by ID.
        """

        db = Database()

        db.execute("""
            DELETE FROM restaurant_tables
            WHERE id = %s
        """, (table_id,))

        db.close()

    # =========================================================
    # Check Table Name
    # =========================================================

    def name_exists(self, name, exclude_id=None):
        """
        Check whether a table name already exists.

        exclude_id is useful when editing a table so that
        the table being edited is not considered a duplicate.
        """

        db = Database()

        if exclude_id:

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

        db.close()

        return result is not None

    # =========================================================
    # Count Tables
    # =========================================================

    def count_all(self):
        """
        Return the total number of restaurant tables.
        """

        db = Database()

        result = db.fetch_one("""
            SELECT COUNT(*) AS total
            FROM restaurant_tables
        """)

        db.close()

        return result["total"]

    # =========================================================
    # Get Available Tables
    # =========================================================

    def get_available(self):
        """
        Get tables that are currently available.

        A table is considered available when there is no
        active order for it.

        Active orders are:
            pending
            preparing
            ready
        """

        db = Database()

        tables = db.fetch_all("""
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

        db.close()

        return tables

    # =========================================================
    # Get Table With Current Order
    # =========================================================

    def get_with_order_status(self):
        """
        Get all tables together with their current order status.

        This can be useful for the receptionist dashboard.
        """

        db = Database()

        tables = db.fetch_all("""
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

        db.close()

        return tables
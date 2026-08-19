"""
=============================================================
  OOP Concept: ABSTRACTION & INHERITANCE (Base Model)
=============================================================
  - Abstraction: We define WHAT every restaurant model should
    do (find, create, update, delete) without saying HOW.

  - Inheritance: Child classes such as User, MenuItem, Order,
    RestaurantTable, etc. will inherit these methods and
    reuse them automatically.

  - Encapsulation: The database connection details are hidden
    inside the Database class. Outside code does not directly
    handle the database connection.

=============================================================
"""

from abc import ABC, abstractmethod
from .database import Database


class BaseModel(ABC):
    """
    Abstract Base Class for all restaurant models.

    ABC = Abstract Base Class

    - You CANNOT create an object of BaseModel directly.
    - Child classes MUST define the 'table' property.
    - Child classes INHERIT all the helper methods below.

    Restaurant models that can inherit from this class:

        User
        MenuCategory
        MenuItem
        RestaurantTable
        Order
        OrderItem
        Payment
    """

    # ── Abstract Property (child MUST define this) ──────────

    @property
    @abstractmethod
    def table(self):
        """
        Each child model must specify its database table name.

        Example:

            return "menu_items"

        or:

            return "orders"
        """
        pass

    # ── Shared Methods (inherited by all child models) ──────

    # @abstractmethod
    # def save(self):
    #     pass

    def find_by_id(self, record_id):
        """
        Find a single restaurant record by its ID.

        Example:

            menu_item.find_by_id(1)

        This could find:

            Menu Item 1
            Order 1
            User 1
            Table 1
        """

        db = Database()

        result = db.fetch_one(
            f"SELECT * FROM {self.table} WHERE id = %s",
            (record_id,)
        )

        db.close()

        return result

    def find_by(self, column, value):
        """
        Find a single record by any column.

        Examples:

            user.find_by('username', 'admin')

            menu_item.find_by('name', 'Pizza')

            restaurant_table.find_by('name', 'Table 1')
        """

        db = Database()

        result = db.fetch_one(
            f"SELECT * FROM {self.table} WHERE {column} = %s",
            (value,)
        )

        db.close()

        return result

    def find_all(self, order_by="id"):
        """
        Get all records from the model's table.

        Example:

            menu_item.find_all()

        This can be used by the customer dashboard to
        display all available menu items.
        """

        db = Database()

        results = db.fetch_all(
            f"SELECT * FROM {self.table} ORDER BY {order_by}"
        )

        db.close()

        return results

    def count_all(self):
        """
        Count the total number of records in the table.

        Example:

            menu_item.count_all()

        Can be useful for dashboard statistics.
        """

        db = Database()

        result = db.fetch_one(
            f"SELECT COUNT(*) AS total FROM {self.table}"
        )

        db.close()

        return result["total"]

    def delete_by_id(self, record_id):
        """
        Delete a record by its ID.

        Example:

            menu_item.delete_by_id(5)

        This can be used by the Manager dashboard
        to delete a menu item.
        """

        db = Database()

        db.execute(
            f"DELETE FROM {self.table} WHERE id = %s",
            (record_id,)
        )

        db.close()
"""
=============================================================
  Restaurant Management System
  Customer Controller
=============================================================

  This controller handles all customer-related operations.

  Customer can:
    - View dashboard
    - Select a restaurant table
    - View menu items
    - Add food items to cart
    - Update cart quantities
    - Remove items from cart
    - Clear cart
    - Place an order
    - View previous orders

  OOP Concept:
    INHERITANCE
      CustomerController inherits common methods from
      BaseController.

    ENCAPSULATION
      Customer-related logic is kept inside this controller
      instead of putting it directly inside the routes.
=============================================================
"""

from flask import render_template, session, redirect, url_for, flash

from app.controllers.base_controllers import BaseController
from app.modules.database import Database


class CustomerController(BaseController):
    """
    Customer Controller

    Handles all functionality available to customers.
    """

    # =========================================================
    # CUSTOMER DASHBOARD
    # =========================================================

    def dashboard(self):
        """
        Display the customer dashboard.

        The dashboard shows:
            - Available restaurant tables
            - Customer information
            - Selected table
        """

        db = Database()

        tables = db.fetch_all("""
            SELECT *
            FROM restaurant_tables
            ORDER BY id
        """)

        db.close()

        selected_table = session.get("table_id")

        return render_template(
            "customer/dashboard.html",
            tables=tables,
            selected_table=selected_table
        )


    # =========================================================
    # SELECT TABLE
    # =========================================================

    def select_table(self, table_id):
        """
        Select a restaurant table.

        The selected table is stored in the session so that
        the customer does not need to select it again while
        ordering.
        """

        db = Database()

        table = db.fetch_one("""
            SELECT *
            FROM restaurant_tables
            WHERE id = %s
        """, (table_id,))

        db.close()

        if not table:
            flash(
                "Selected table does not exist.",
                "danger"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        # Store selected table in session
        session["table_id"] = table["id"]
        session["table_name"] = table["name"]

        flash(
            f'{table["name"]} selected successfully.',
            "success"
        )

        return redirect(
            url_for("customer.menu")
        )


    # =========================================================
    # MENU
    # =========================================================

    def menu(self):
        """
        Display the restaurant menu.

        Menu items are loaded from the database.

        The customer must select a table before viewing
        the ordering menu.
        """

        table_id = session.get("table_id")

        if not table_id:
            flash(
                "Please select a table first.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        db = Database()

        menu_items = db.fetch_all("""
            SELECT
                menu_items.id,
                menu_items.name,
                menu_items.price,
                menu_items.category_id,
                menu_categories.name AS category
            FROM menu_items
            LEFT JOIN menu_categories
                ON menu_items.category_id = menu_categories.id
            WHERE menu_items.available = 1
            ORDER BY menu_categories.name, menu_items.name
        """)

        db.close()

        cart = self.get_cart()

        total = self.calculate_cart_total(cart)

        return render_template(
            "customer/menu.html",
            menu_items=menu_items,
            cart=cart,
            total=total,
            table_id=table_id,
            table_name=session.get("table_name")
        )


    # =========================================================
    # CART
    # =========================================================

    def get_cart(self):
        """
        Get the customer's current cart from the session.

        Cart example:

        {
            "1": {
                "id": 1,
                "name": "Chicken Burger",
                "price": 250,
                "quantity": 2
            }
        }
        """

        return session.get("cart", {})


    def calculate_cart_total(self, cart):
        """
        Calculate the total price of all items in the cart.
        """

        total = 0

        for item in cart.values():

            total += (
                float(item["price"])
                * int(item["quantity"])
            )

        return total

    # =========================================================
    # VIEW SINGLE ORDER
    # =========================================================

    def view_order(self, order_id):
        """
        Display details for a single customer order.
        """
        user_id = self.get_current_user_id()

        db = Database()

        # Fetch the specific order belonging to the user
        order = db.fetch_one("""
            SELECT
                orders.id,
                orders.created_at,
                orders.status,
                restaurant_tables.name AS table_name
            FROM orders
            LEFT JOIN restaurant_tables
                ON orders.table_id = restaurant_tables.id
            WHERE orders.id = %s AND orders.user_id = %s
        """, (order_id, user_id))

        if not order:
            db.close()
            flash("Order not found.", "danger")
            return redirect(url_for("customer.orders"))

        # Fetch items for this order
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
            "customer/view_order.html",
            order=order
        )


    # =========================================================
    # MOBILE DASHBOARD
    # =========================================================

    def mobile(self):
        """
        Display the mobile customer dashboard.
        """
        db = Database()

        tables = db.fetch_all("""
            SELECT *
            FROM restaurant_tables
            ORDER BY id
        """)

        db.close()

        selected_table = session.get("table_id")

        return render_template(
            "customer/mobile.html",
            tables=tables,
            selected_table=selected_table
        )


    # =========================================================
    # ADD TO CART
    # =========================================================

    def add_to_cart(self, item_id):
        """
        Add a menu item to the customer's cart.

        If the item already exists:
            increase quantity.

        Otherwise:
            create a new cart item.
        """

        # Customer must select a table first
        if not session.get("table_id"):

            flash(
                "Please select a table first.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        db = Database()

        item = db.fetch_one("""
            SELECT
                menu_items.id,
                menu_items.name,
                menu_items.price,
                menu_items.category_id,
                menu_categories.name AS category
            FROM menu_items
            LEFT JOIN menu_categories
                ON menu_items.category_id = menu_categories.id
            WHERE menu_items.id = %s
            AND menu_items.available = 1
        """, (item_id,))

        db.close()

        if not item:

            flash(
                "Menu item not found.",
                "danger"
            )

            return redirect(
                url_for("customer.menu")
            )

        cart = self.get_cart()

        item_key = str(item["id"])

        # Item already exists
        if item_key in cart:

            cart[item_key]["quantity"] += 1

        # New item
        else:

            cart[item_key] = {
                "id": item["id"],
                "name": item["name"],
                "price": float(item["price"]),
                "category": item["category"],
                "quantity": 1
            }

        session["cart"] = cart

        # Tell Flask that session data changed
        session.modified = True

        flash(
            f'{item["name"]} added to cart.',
            "success"
        )

        return redirect(
            url_for("customer.menu")
        )


    # =========================================================
    # UPDATE CART
    # =========================================================

    def update_cart(self):
        """
        Update quantities of items in the cart.

        The HTML form should send:

            item_id
            quantity
        """

        cart = self.get_cart()

        for item_id in cart:

            quantity = session.get(
                "_dummy",
                None
            )

        # Read submitted form data
        from flask import request

        for item_id in cart:

            quantity = request.form.get(
                f"quantity_{item_id}"
            )

            if quantity is None:
                continue

            try:
                quantity = int(quantity)

            except ValueError:
                continue

            if quantity <= 0:

                del cart[item_id]

            else:

                cart[item_id]["quantity"] = quantity

        session["cart"] = cart
        session.modified = True

        flash(
            "Cart updated successfully.",
            "success"
        )

        return redirect(
            url_for("customer.cart")
        )


    # =========================================================
    # REMOVE FROM CART
    # =========================================================

    def remove_from_cart(self, item_id):
        """
        Remove one item from the cart.
        """

        cart = self.get_cart()

        item_key = str(item_id)

        if item_key in cart:

            item_name = cart[item_key]["name"]

            del cart[item_key]

            session["cart"] = cart
            session.modified = True

            flash(
                f"{item_name} removed from cart.",
                "success"
            )

        return redirect(
            url_for("customer.cart")
        )


    # =========================================================
    # CART PAGE
    # =========================================================

    def cart(self):
        """
        Display the customer's cart.
        """

        if not session.get("table_id"):

            flash(
                "Please select a table first.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        cart = self.get_cart()

        total = self.calculate_cart_total(cart)

        return render_template(
            "customer/cart.html",
            cart=cart,
            total=total,
            table_id=session.get("table_id"),
            table_name=session.get("table_name")
        )


    # =========================================================
    # CLEAR CART
    # =========================================================

    def clear_cart(self):
        """
        Remove all items from the cart.
        """

        session.pop("cart", None)

        flash(
            "Cart cleared successfully.",
            "success"
        )

        return redirect(
            url_for("customer.cart")
        )


    # =========================================================
    # PLACE ORDER
    # =========================================================

    def place_order(self):
        """
        Place the customer's order.

        Flow:

            Customer Cart
                  ↓
            Create Order
                  ↓
            Create Order Items
                  ↓
            Clear Cart
                  ↓
            Customer Orders
        """

        table_id = session.get("table_id")
        cart = self.get_cart()

        # Check table
        if not table_id:

            flash(
                "Please select a table first.",
                "warning"
            )

            return redirect(
                url_for("customer.dashboard")
            )

        # Check cart
        if not cart:

            flash(
                "Your cart is empty.",
                "warning"
            )

            return redirect(
                url_for("customer.cart")
            )

        db = Database()

        try:

            # -------------------------------------------------
            # Create Order
            # -------------------------------------------------

            db.execute("""
                INSERT INTO orders
                (
                    user_id,
                    table_id,
                    status
                )
                VALUES (%s, %s, %s)
            """, (
                session.get("user_id"),
                table_id,
                "pending"
            ))

            # Get newly created order
            order = db.fetch_one("""
                SELECT LAST_INSERT_ID() AS order_id
            """)

            order_id = order["order_id"]


            # -------------------------------------------------
            # Create Order Items
            # -------------------------------------------------

            for item in cart.values():

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
                    item["id"],
                    item["quantity"],
                    item["price"]
                ))


            # -------------------------------------------------
            # Close Database
            # -------------------------------------------------

            db.close()


            # -------------------------------------------------
            # Clear Cart
            # -------------------------------------------------

            session.pop("cart", None)


            flash(
                f"Order #{order_id} placed successfully!",
                "success"
            )

            return redirect(
                url_for("customer.orders")
            )


        except Exception as e:

            db.close()

            print(
                "Order placement error:",
                e
            )

            flash(
                "Unable to place your order. Please try again.",
                "danger"
            )

            return redirect(
                url_for("customer.cart")
            )


    # =========================================================
    # CUSTOMER ORDERS
    # =========================================================

    def orders(self):
        """
        Display orders placed by the current customer.
        """

        user_id = self.get_current_user_id()

        db = Database()

        orders = db.fetch_all("""
            SELECT
                orders.id,
                orders.created_at,
                orders.status,
                restaurant_tables.name AS table_name
            FROM orders
            LEFT JOIN restaurant_tables
                ON orders.table_id = restaurant_tables.id
            WHERE orders.user_id = %s
            ORDER BY orders.created_at DESC
        """, (user_id,))


        # -----------------------------------------------------
        # Get items for each order
        # -----------------------------------------------------

        for order in orders:

            order["items"] = db.fetch_all("""
                SELECT
                    order_items.quantity,
                    order_items.price_at_order,
                    menu_items.name
                FROM order_items
                INNER JOIN menu_items
                    ON order_items.item_id = menu_items.id
                WHERE order_items.order_id = %s
            """, (order["id"],))


            # Calculate order total
            order["total"] = 0

            for item in order["items"]:

                order["total"] += (
                    float(item["price_at_order"])
                    * int(item["quantity"])
                )


        db.close()

        return render_template(
            "customer/orders.html",
            orders=orders
        )
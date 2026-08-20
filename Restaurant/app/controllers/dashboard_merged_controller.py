# Replace your dashboard() method in app/controllers/customer.py with this.
# It now gathers everything the page needs in one place: tables, the
# selected table (as a full row), the menu, and the current cart --
# since dashboard.html is your only customer template.

    def dashboard(self):
        db = Database()

        tables = db.fetch_all("""
            SELECT *
            FROM restaurant_tables
            ORDER BY id
        """)

        table_id = session.get("table_id")

        selected_table = None
        if table_id:
            selected_table = db.fetch_one("""
                SELECT *
                FROM restaurant_tables
                WHERE id = %s
            """, (table_id,))

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
            "customer/dashboard.html",
            tables=tables,
            selected_table=selected_table,
            menu_items=menu_items,
            cart=cart,
            total=total
        )


# You can now delete the old menu() method -- dashboard() replaces it.
# (Leave it if anything else still calls url_for("customer.menu"); just
# make sure nothing does before removing it.)

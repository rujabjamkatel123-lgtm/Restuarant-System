"""
=============================================================
  Restaurant Management System - Manager Controller
=============================================================
"""

import os
import uuid

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
    current_app
)

from werkzeug.utils import secure_filename

from app.controllers.base_controllers import BaseController
from app.modules.database import Database


class ManagerController(BaseController):
    """
    Controller for all manager operations.
    """

    # =========================================================
    # DATABASE COMPATIBILITY
    # =========================================================

    def _ensure_half_plate_column(self):
        """
        Make sure menu_items has half_plate_price column.
        """

        db = Database()

        try:
            column = db.fetch_one("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'menu_items'
                  AND COLUMN_NAME = 'half_plate_price'
            """)

            if not column:
                db.execute("""
                    ALTER TABLE menu_items
                    ADD COLUMN half_plate_price DECIMAL(10,2) NULL
                    AFTER price
                """)

        except Exception as e:
            print(
                "Half plate column check:",
                e
            )

        finally:
            db.close()

    # =========================================================
    # MANAGER DASHBOARD
    # =========================================================

    def dashboard(self):

        db = Database()

        try:

            today_sales = db.fetch_one("""
                SELECT
                    COALESCE(
                        SUM(
                            oi.quantity *
                            oi.price_at_order
                        ),
                        0
                    ) AS total_sales
                FROM orders o

                JOIN order_items oi
                    ON o.id = oi.order_id

                WHERE DATE(o.created_at) = CURDATE()
                  AND o.status != 'cancelled'
            """)

            today_orders = db.fetch_one("""
                SELECT
                    COUNT(*) AS total
                FROM orders

                WHERE DATE(created_at) = CURDATE()
                  AND status != 'cancelled'
            """)

            today_items = db.fetch_one("""
                SELECT
                    COALESCE(
                        SUM(oi.quantity),
                        0
                    ) AS total_items
                FROM orders o

                JOIN order_items oi
                    ON o.id = oi.order_id

                WHERE DATE(o.created_at) = CURDATE()
                  AND o.status != 'cancelled'
            """)

            recent_orders = db.fetch_all("""
                SELECT
                    o.id,
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

                GROUP BY
                    o.id,
                    t.name,
                    o.status,
                    o.created_at

                ORDER BY o.id DESC

                LIMIT 10
            """)

        finally:
            db.close()

        return render_template(
            "manager/dashboard.html",
            today_sales=(
                today_sales["total_sales"]
                if today_sales
                else 0
            ),
            today_orders=(
                today_orders["total"]
                if today_orders
                else 0
            ),
            today_items=(
                today_items["total_items"]
                if today_items
                else 0
            ),
            recent_orders=recent_orders
        )

    # =========================================================
    # REPORTS
    # =========================================================

    def reports(self):

        start_date = request.args.get(
            "start_date"
        )

        end_date = request.args.get(
            "end_date"
        )

        db = Database()

        try:

            if start_date and end_date:

                sales = db.fetch_one("""
                    SELECT
                        COALESCE(
                            SUM(
                                oi.quantity *
                                oi.price_at_order
                            ),
                            0
                        ) AS total_sales

                    FROM orders o

                    JOIN order_items oi
                        ON o.id = oi.order_id

                    WHERE DATE(o.created_at)
                          BETWEEN %s AND %s

                      AND o.status != 'cancelled'
                """, (
                    start_date,
                    end_date
                ))

                order_count = db.fetch_one("""
                    SELECT
                        COUNT(*) AS total

                    FROM orders

                    WHERE DATE(created_at)
                          BETWEEN %s AND %s

                      AND status != 'cancelled'
                """, (
                    start_date,
                    end_date
                ))

                item_count = db.fetch_one("""
                    SELECT
                        COALESCE(
                            SUM(oi.quantity),
                            0
                        ) AS total_items

                    FROM orders o

                    JOIN order_items oi
                        ON o.id = oi.order_id

                    WHERE DATE(o.created_at)
                          BETWEEN %s AND %s

                      AND o.status != 'cancelled'
                """, (
                    start_date,
                    end_date
                ))

                popular_items = db.fetch_all("""
                    SELECT
                        m.name,

                        SUM(
                            oi.quantity
                        ) AS quantity_sold,

                        SUM(
                            oi.quantity *
                            oi.price_at_order
                        ) AS revenue

                    FROM order_items oi

                    JOIN orders o
                        ON oi.order_id = o.id

                    JOIN menu_items m
                        ON oi.item_id = m.id

                    WHERE DATE(o.created_at)
                          BETWEEN %s AND %s

                      AND o.status != 'cancelled'

                    GROUP BY
                        m.id,
                        m.name

                    ORDER BY
                        quantity_sold DESC
                """, (
                    start_date,
                    end_date
                ))

            else:

                sales = db.fetch_one("""
                    SELECT
                        COALESCE(
                            SUM(
                                oi.quantity *
                                oi.price_at_order
                            ),
                            0
                        ) AS total_sales

                    FROM orders o

                    JOIN order_items oi
                        ON o.id = oi.order_id

                    WHERE DATE(o.created_at) = CURDATE()
                      AND o.status != 'cancelled'
                """)

                order_count = db.fetch_one("""
                    SELECT
                        COUNT(*) AS total

                    FROM orders

                    WHERE DATE(created_at) = CURDATE()
                      AND status != 'cancelled'
                """)

                item_count = db.fetch_one("""
                    SELECT
                        COALESCE(
                            SUM(oi.quantity),
                            0
                        ) AS total_items

                    FROM orders o

                    JOIN order_items oi
                        ON o.id = oi.order_id

                    WHERE DATE(o.created_at) = CURDATE()
                      AND o.status != 'cancelled'
                """)

                popular_items = db.fetch_all("""
                    SELECT
                        m.name,

                        SUM(
                            oi.quantity
                        ) AS quantity_sold,

                        SUM(
                            oi.quantity *
                            oi.price_at_order
                        ) AS revenue

                    FROM order_items oi

                    JOIN orders o
                        ON oi.order_id = o.id

                    JOIN menu_items m
                        ON oi.item_id = m.id

                    WHERE DATE(o.created_at) = CURDATE()
                      AND o.status != 'cancelled'

                    GROUP BY
                        m.id,
                        m.name

                    ORDER BY
                        quantity_sold DESC
                """)

        finally:
            db.close()

        return render_template(
            "manager/reports.html",
            total_sales=(
                sales["total_sales"]
                if sales
                else 0
            ),
            total_orders=(
                order_count["total"]
                if order_count
                else 0
            ),
            total_items=(
                item_count["total_items"]
                if item_count
                else 0
            ),
            popular_items=popular_items,
            start_date=start_date,
            end_date=end_date
        )

    # =========================================================
    # ORDER HISTORY
    # =========================================================

    def history(self):

        start_date = request.args.get(
            "start_date"
        )

        end_date = request.args.get(
            "end_date"
        )

        db = Database()

        query = """
            SELECT
                o.id,
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
        """

        params = []

        if start_date and end_date:

            query += """
                WHERE DATE(o.created_at)
                BETWEEN %s AND %s
            """

            params.extend([
                start_date,
                end_date
            ])

        query += """
            GROUP BY
                o.id,
                t.name,
                o.status,
                o.created_at

            ORDER BY
                o.created_at DESC
        """

        try:

            orders = db.fetch_all(
                query,
                tuple(params) if params else None
            )

        finally:
            db.close()

        return render_template(
            "manager/history.html",
            orders=orders,
            start_date=start_date,
            end_date=end_date
        )

    # =========================================================
    # ORDER DETAILS
    # =========================================================

    def order_details(self, order_id):

        db = Database()

        try:

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
            """, (
                order_id,
            ))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("manager.history")
                )

            items = db.fetch_all("""
                SELECT
                    oi.id,
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
            """, (
                order_id,
            ))

        finally:
            db.close()

        total = sum(
            float(item["subtotal"])
            for item in items
        )

        return render_template(
            "manager/order_details.html",
            order=order,
            items=items,
            total=total
        )

    # =========================================================
    # DAILY SALES
    # =========================================================

    def daily_sales(self):

        db = Database()

        try:

            daily_sales = db.fetch_all("""
                SELECT
                    DATE(o.created_at)
                    AS sale_date,

                    COALESCE(
                        SUM(
                            oi.quantity *
                            oi.price_at_order
                        ),
                        0
                    ) AS total_sales

                FROM orders o

                JOIN order_items oi
                    ON o.id = oi.order_id

                WHERE o.status != 'cancelled'

                GROUP BY
                    DATE(o.created_at)

                ORDER BY
                    sale_date DESC

                LIMIT 30
            """)

        finally:
            db.close()

        return daily_sales

    # =========================================================
    # MONTHLY SALES
    # =========================================================

    def monthly_sales(self):

        db = Database()

        try:

            monthly_sales = db.fetch_all("""
                SELECT
                    YEAR(o.created_at)
                    AS sale_year,

                    MONTH(o.created_at)
                    AS sale_month,

                    COALESCE(
                        SUM(
                            oi.quantity *
                            oi.price_at_order
                        ),
                        0
                    ) AS total_sales

                FROM orders o

                JOIN order_items oi
                    ON o.id = oi.order_id

                WHERE o.status != 'cancelled'

                GROUP BY
                    YEAR(o.created_at),
                    MONTH(o.created_at)

                ORDER BY
                    sale_year DESC,
                    sale_month DESC
            """)

        finally:
            db.close()

        return monthly_sales

    # =========================================================
    # MENU PERFORMANCE
    # =========================================================

    def menu_performance(self):

        db = Database()

        try:

            items = db.fetch_all("""
                SELECT
                    m.id,
                    m.name,
                    m.price,

                    COALESCE(
                        SUM(oi.quantity),
                        0
                    ) AS quantity_sold,

                    COALESCE(
                        SUM(
                            oi.quantity *
                            oi.price_at_order
                        ),
                        0
                    ) AS revenue

                FROM menu_items m

                LEFT JOIN order_items oi
                    ON m.id = oi.item_id

                LEFT JOIN orders o
                    ON oi.order_id = o.id
                   AND o.status != 'cancelled'

                GROUP BY
                    m.id,
                    m.name,
                    m.price

                ORDER BY
                    quantity_sold DESC
            """)

        finally:
            db.close()

        return items

    # =========================================================
    # MENU MANAGEMENT
    # =========================================================

    def menu(self):

        self._ensure_half_plate_column()

        db = Database()

        try:

            menu_items = db.fetch_all("""
                SELECT
                    menu_items.id,
                    menu_items.name,
                    menu_items.price,
                    menu_items.half_plate_price,
                    menu_items.category_id,
                    menu_items.description,
                    menu_items.image,
                    menu_items.available,

                    menu_categories.name AS category

                FROM menu_items

                LEFT JOIN menu_categories
                    ON menu_items.category_id =
                    menu_categories.id

                ORDER BY
                    menu_categories.name,
                    menu_items.name
            """)

            categories = db.fetch_all("""
                SELECT *
                FROM menu_categories
                ORDER BY name
            """)

        finally:

            db.close()

        return render_template(
            "manager/menu.html",
            menu_items=menu_items,
            categories=categories
        )

    # =========================================================
    # ADD MENU ITEM
    # =========================================================

    def add_menu_item(self):

        self._ensure_half_plate_column()

        # -----------------------------------------------------
        # GET
        # -----------------------------------------------------

        if request.method == "GET":

            return redirect(
                url_for("manager.menu")
            )

        # -----------------------------------------------------
        # POST
        # -----------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        # Accept category_id from the new form
        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        # Also accept category from your existing form
        category = request.form.get(
            "category",
            ""
        ).strip()

        full_price = request.form.get(
            "price",
            ""
        ).strip()

        half_price = request.form.get(
            "half_plate_price",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        available = (
            1
            if request.form.get("available")
            else 0
        )

        # =====================================================
        # VALIDATION
        # =====================================================

        if not name:

            flash(
                "Food name is required.",
                "danger"
            )

            return redirect(
                url_for("manager.menu")
            )

        if not category_id and not category:

            flash(
                "Category is required.",
                "danger"
            )

            return redirect(
                url_for("manager.menu")
            )

        if not full_price:

            flash(
                "Full plate price is required.",
                "danger"
            )

            return redirect(
                url_for("manager.menu")
            )

        # =====================================================
        # CONVERT CATEGORY NAME TO CATEGORY ID
        # =====================================================

        if not category_id and category:

            category_mapping = {
                "Main-Course": 1,
                "Main Course": 1,
                "Appetizers": 2,
                "Beverages": 3,
                "Desserts": 4
            }

            category_id = category_mapping.get(
                category
            )

        if not category_id:

            flash(
                "Invalid category selected.",
                "danger"
            )

            return redirect(
                url_for("manager.menu")
            )

        # =====================================================
        # CONVERT CATEGORY ID
        # =====================================================

        try:

            category_id = int(
                category_id
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Invalid category.",
                "danger"
            )

            return redirect(
                url_for("manager.menu")
            )

        # =====================================================
        # CONVERT PRICES
        # =====================================================

        try:

            full_price_value = float(
                full_price
            )

            if full_price_value < 0:
                raise ValueError

            if half_price:

                half_price_value = float(
                    half_price
                )

                if half_price_value < 0:
                    raise ValueError

            else:

                half_price_value = None

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter valid prices.",
                "danger"
            )

            return redirect(
                url_for("manager.menu")
            )

        # =====================================================
        # DATABASE INSERT
        # =====================================================

        db = Database()

        try:

            db.execute("""
                INSERT INTO menu_items
                (
                    name,
                    price,
                    half_plate_price,
                    category_id,
                    description,
                    available
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                name,
                full_price_value,
                half_price_value,
                category_id,
                description,
                available
            ))

            flash(
                "Menu item added successfully!",
                "success"
            )

        except Exception as e:

            print(
                "ADD MENU ITEM ERROR:",
                e
            )

            flash(
                f"Error adding menu item: {e}",
                "danger"
            )

        finally:

            db.close()

        return redirect(
            url_for("manager.menu")
        )

    # =========================================================
    # EDIT MENU ITEM
    # =========================================================

    def edit_menu_item(self, item_id):

        self._ensure_half_plate_column()

        db = Database()

        try:

            item = db.fetch_one("""
                SELECT *
                FROM menu_items
                WHERE id = %s
            """, (
                item_id,
            ))

            if not item:

                flash(
                    "Menu item not found.",
                    "danger"
                )

                return redirect(
                    url_for("manager.menu")
                )

            if request.method == "POST":

                name = request.form.get(
                    "name",
                    ""
                ).strip()

                category_id = request.form.get(
                    "category_id",
                    ""
                ).strip()

                category = request.form.get(
                    "category",
                    ""
                ).strip()

                full_price = request.form.get(
                    "price",
                    ""
                ).strip()

                half_price = request.form.get(
                    "half_plate_price",
                    ""
                ).strip()

                description = request.form.get(
                    "description",
                    ""
                ).strip()

                available = (
                    1
                    if request.form.get("available")
                    else 0
                )

                if not category_id and category:

                    category_mapping = {
                        "Main-Course": 1,
                        "Main Course": 1,
                        "Appetizers": 2,
                        "Beverages": 3,
                        "Desserts": 4
                    }

                    category_id = category_mapping.get(
                        category
                    )

                if not name or not category_id or not full_price:

                    flash(
                        "Name, category and price are required.",
                        "danger"
                    )

                    return redirect(
                        request.referrer or
                        url_for("manager.menu")
                    )

                try:

                    category_id = int(
                        category_id
                    )

                    full_price_value = float(
                        full_price
                    )

                    if half_price:

                        half_price_value = float(
                            half_price
                        )

                    else:

                        half_price_value = None

                except (
                    ValueError,
                    TypeError
                ):

                    flash(
                        "Please enter valid values.",
                        "danger"
                    )

                    return redirect(
                        request.referrer or
                        url_for("manager.menu")
                    )

                db.execute("""
                    UPDATE menu_items

                    SET
                        name = %s,
                        price = %s,
                        half_plate_price = %s,
                        category_id = %s,
                        description = %s,
                        available = %s

                    WHERE id = %s
                """, (
                    name,
                    full_price_value,
                    half_price_value,
                    category_id,
                    description,
                    available,
                    item_id
                ))

                flash(
                    "Menu item updated successfully!",
                    "success"
                )

                return redirect(
                    url_for("manager.menu")
                )

            categories = db.fetch_all("""
                SELECT *
                FROM menu_categories
                ORDER BY name
            """)

        finally:
            db.close()

        return render_template(
            "manager/edit_menu_item.html",
            item=item,
            categories=categories
        )

    # =========================================================
    # DELETE MENU ITEM
    # =========================================================

    def delete_menu_item(self, item_id):

        db = Database()

        try:

            item = db.fetch_one("""
                SELECT *
                FROM menu_items
                WHERE id = %s
            """, (
                item_id,
            ))

            if not item:

                flash(
                    "Menu item not found.",
                    "danger"
                )

                return redirect(
                    url_for("manager.menu")
                )

            db.execute("""
                DELETE FROM menu_items
                WHERE id = %s
            """, (
                item_id,
            ))

            flash(
                "Menu item deleted successfully!",
                "success"
            )

        except Exception as e:

            print(
                "DELETE MENU ITEM ERROR:",
                e
            )

            flash(
                f"Error deleting menu item: {e}",
                "danger"
            )

        finally:
            db.close()

        return redirect(
            url_for("manager.menu")
        )

    # =========================================================
    # SALES
    # =========================================================

    def sales(self):

        db = Database()

        try:

            orders = db.fetch_all("""
                SELECT
                    orders.id,
                    orders.created_at,
                    orders.status,

                    restaurant_tables.name
                    AS table_name

                FROM orders

                LEFT JOIN restaurant_tables
                    ON orders.table_id =
                       restaurant_tables.id

                ORDER BY
                    orders.created_at DESC
            """)

            total_sales = 0

            for order in orders:

                order["items"] = db.fetch_all("""
                    SELECT
                        order_items.quantity,
                        order_items.price_at_order,
                        menu_items.name

                    FROM order_items

                    INNER JOIN menu_items
                        ON order_items.item_id =
                           menu_items.id

                    WHERE order_items.order_id = %s
                """, (
                    order["id"],
                ))

                order["total"] = 0

                for item in order["items"]:

                    order["total"] += (
                        float(
                            item["price_at_order"]
                        )
                        *
                        int(
                            item["quantity"]
                        )
                    )

                if order["status"] in [
                    "completed",
                    "delivered",
                    "paid",
                    "served"
                ]:

                    total_sales += order["total"]

        finally:
            db.close()

        return render_template(
            "manager/sales.html",
            orders=orders,
            total_sales=total_sales
        )

    # =========================================================
    # FILTER REPORTS
    # =========================================================

    def filter_reports(self):

        db = Database()

        start_date = (
            request.form.get("start_date")
            or request.args.get("start_date")
        )

        end_date = (
            request.form.get("end_date")
            or request.args.get("end_date")
        )

        status = (
            request.form.get("status")
            or request.args.get("status")
        )

        query = """
            SELECT
                orders.id,
                orders.created_at,
                orders.status,

                restaurant_tables.name
                AS table_name

            FROM orders

            LEFT JOIN restaurant_tables
                ON orders.table_id =
                   restaurant_tables.id

            WHERE 1 = 1
        """

        params = []

        if start_date:

            query += """
                AND DATE(orders.created_at) >= %s
            """

            params.append(
                start_date
            )

        if end_date:

            query += """
                AND DATE(orders.created_at) <= %s
            """

            params.append(
                end_date
            )

        if status and status != "all":

            query += """
                AND orders.status = %s
            """

            params.append(
                status
            )

        query += """
            ORDER BY
                orders.created_at DESC
        """

        try:

            orders = db.fetch_all(
                query,
                tuple(params)
            )

            total_sales = 0

            for order in orders:

                order["items"] = db.fetch_all("""
                    SELECT
                        order_items.quantity,
                        order_items.price_at_order,
                        menu_items.name

                    FROM order_items

                    INNER JOIN menu_items
                        ON order_items.item_id =
                           menu_items.id

                    WHERE order_items.order_id = %s
                """, (
                    order["id"],
                ))

                order["total"] = 0

                for item in order["items"]:

                    order["total"] += (
                        float(
                            item["price_at_order"]
                        )
                        *
                        int(
                            item["quantity"]
                        )
                    )

                if order["status"] in [
                    "completed",
                    "delivered",
                    "paid",
                    "served"
                ]:

                    total_sales += order["total"]

        finally:
            db.close()

        return render_template(
            "manager/sales.html",
            orders=orders,
            total_sales=total_sales,
            start_date=start_date,
            end_date=end_date,
            status=status
        )

    # =========================================================
    # VIEW ORDER
    # =========================================================

    def view_order(self, order_id):

        db = Database()

        try:

            order = db.fetch_one("""
                SELECT
                    orders.id,
                    orders.created_at,
                    orders.status,

                    restaurant_tables.name
                    AS table_name

                FROM orders

                LEFT JOIN restaurant_tables
                    ON orders.table_id =
                       restaurant_tables.id

                WHERE orders.id = %s
            """, (
                order_id,
            ))

            if not order:

                flash(
                    "Order not found.",
                    "danger"
                )

                return redirect(
                    url_for("manager.sales")
                )

            order["items"] = db.fetch_all("""
                SELECT
                    order_items.quantity,
                    order_items.price_at_order,
                    menu_items.name

                FROM order_items

                INNER JOIN menu_items
                    ON order_items.item_id =
                       menu_items.id

                WHERE order_items.order_id = %s
            """, (
                order_id,
            ))

            order["total"] = 0

            for item in order["items"]:

                order["total"] += (
                    float(
                        item["price_at_order"]
                    )
                    *
                    int(
                        item["quantity"]
                    )
                )

        finally:
            db.close()

        return render_template(
            "manager/view_order.html",
            order=order
        )
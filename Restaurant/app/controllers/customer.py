"""
=============================================================
                CUSTOMER CONTROLLER
=============================================================
"""

from flask import (
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
    jsonify
)

from app.modules.database import Database
from app.modules.table import Table


class CustomerController:

    # =========================================================
    # DASHBOARD
    # =========================================================

    def dashboard(self):

        table_id = session.get("customer_table_id")

        selected_table = None

        if table_id:
            table_model = Table()
            selected_table = table_model.find_by_id(table_id)

            if not selected_table:
                session.pop("customer_table_id", None)

        db = Database()
        try:
            menu_items = db.fetch_all("""
                SELECT id, name, price, description, image, available
                FROM menu_items
                WHERE available = 1
                ORDER BY name
            """)
        except Exception as e:
            print("Menu load error:", e)
            menu_items = []
        finally:
            db.close()

        cart = session.get("customer_cart", {})
        total = self._calculate_cart_total(cart)

        return render_template(
            "customer/dashboard.html",
            selected_table=selected_table,
            menu_items=menu_items,
            cart=cart,
            total=total
        )

    # =========================================================
    # QR CODE ENTRY
    # =========================================================

    def scan_qr(self, table_id):
        table_model = Table()
        table = table_model.find_by_id(table_id)

        if not table:
            flash("This table does not exist.", "error")
            return redirect(url_for("auth.login"))

        session["customer_table_id"] = table["id"]

        if "customer_cart" not in session:
            session["customer_cart"] = {}

        session.modified = True

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # MENU
    # =========================================================

    def menu(self):
        db = Database()
        try:
            menu_items = db.fetch_all("""
                SELECT id, name, price, description, image, available
                FROM menu_items
                WHERE available = 1
                ORDER BY name
            """)
        except Exception as e:
            print("Menu error:", e)
            menu_items = []
        finally:
            db.close()

        return render_template(
            "customer/dashboard.html",
            selected_table=self._get_selected_table(),
            menu_items=menu_items,
            cart=session.get("customer_cart", {}),
            total=self._calculate_cart_total(
                session.get("customer_cart", {})
            )
        )

    # =========================================================
    # ADD TO CART
    # =========================================================

    def add_to_cart(self, item_id):
        table_id = session.get("customer_table_id")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not table_id:
            if is_ajax:
                return jsonify({"success": False, "message": "Please scan the QR code on your table first."}), 400
            flash("Please scan the QR code on your table first.", "error")
            return redirect(url_for("customer.dashboard"))

        db = Database()
        try:
            item = db.fetch_one("""
                SELECT id, name, price, available
                FROM menu_items
                WHERE id = %s AND available = 1
            """, (item_id,))
        except Exception as e:
            print("Add to cart error:", e)
            item = None
        finally:
            db.close()

        if not item:
            if is_ajax:
                return jsonify({"success": False, "message": "Food item not found or unavailable."}), 404
            flash("Food item not found or unavailable.", "error")
            return redirect(url_for("customer.dashboard"))

        cart = session.get("customer_cart", {})
        item_key = str(item_id)

        if item_key in cart:
            cart[item_key]["quantity"] += 1
        else:
            cart[item_key] = {
                "id": item["id"],
                "name": item["name"],
                "price": float(item["price"] or 0),
                "quantity": 1
            }

        session["customer_cart"] = cart
        session.modified = True
        total = self._calculate_cart_total(cart)

        if is_ajax:
            return jsonify({
                "success": True,
                "message": f"{item['name']} added to your order.",
                "total": total,
                "item_count": sum(int(i.get("quantity", 0) or 0) for i in cart.values())
            })

        return redirect(url_for("customer.dashboard"))

    # =========================================================
    # VIEW CART
    # =========================================================

    def cart(self):
        db = Database()
        try:
            menu_items = db.fetch_all("SELECT * FROM menu_items")
        except Exception:
            menu_items = []
        finally:
            db.close()

        selected_table = self._get_selected_table()
        cart = session.get("customer_cart", {})
        total = self._calculate_cart_total(cart)

        return render_template(
            "customer/dashboard.html",
            selected_table=selected_table,
            menu_items=menu_items,
            cart=cart,
            total=total
        )

    # =========================================================
    # UPDATE CART
    # =========================================================

    def update_cart(self, item_id):
        cart = session.get("customer_cart", {})
        item_key = str(item_id)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if item_key not in cart:
            if is_ajax:
                return jsonify({"success": False, "message": "Item is not in your cart."}), 404
            flash("Item is not in your cart.", "error")
            return redirect(url_for("customer.dashboard"))

        quantity = request.form.get("quantity", type=int)
        if quantity is None:
            quantity = 1

        if quantity <= 0:
            cart.pop(item_key)
        else:
            cart[item_key]["quantity"] = quantity

        session["customer_cart"] = cart
        session.modified = True
        total = self._calculate_cart_total(cart)

        if is_ajax:
            return jsonify({
                "success": True,
                "total": total,
                "item_count": sum(int(i.get("quantity", 0) or 0) for i in cart.values())
            })

        return redirect(url_for("customer.dashboard"))

    # =========================================================
    # REMOVE FROM CART
    # =========================================================

    def remove_from_cart(self, item_id):
        cart = session.get("customer_cart", {})
        item_key = str(item_id)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if item_key in cart:
            removed_item = cart[item_key]["name"]
            cart.pop(item_key)
            session["customer_cart"] = cart
            session.modified = True

            total = self._calculate_cart_total(cart)

            if is_ajax:
                return jsonify({
                    "success": True,
                    "message": f"{removed_item} removed from your order.",
                    "total": total,
                    "item_count": sum(int(i.get("quantity", 0) or 0) for i in cart.values())
                })

            flash("Item removed from your order.", "success")

        if is_ajax:
            return jsonify({
                "success": True,
                "total": self._calculate_cart_total(cart),
                "item_count": sum(int(i.get("quantity", 0) or 0) for i in cart.values())
            })

        return redirect(url_for("customer.dashboard"))

    # =========================================================
    # CLEAR CART
    # =========================================================

    def clear_cart(self):
        session["customer_cart"] = {}
        session.modified = True
        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # SELECT TABLE
    # =========================================================

    def select_table(self, table_id):
        table_model = Table()
        table = table_model.find_by_id(table_id)

        if not table:
            flash("Table not found.", "error")
            return redirect(url_for("customer.dashboard"))

        session["customer_table_id"] = table["id"]
        session.modified = True

        return redirect(
            url_for("customer.dashboard")
        )

    # =========================================================
    # PLACE ORDER
    # =========================================================

    def place_order(self):
        table_id = session.get("customer_table_id")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not table_id:
            if is_ajax:
                return jsonify({"success": False, "message": "Please scan your table QR code first."}), 400
            flash("Please scan your table QR code first.", "error")
            return redirect(url_for("customer.dashboard"))

        cart = session.get("customer_cart", {})

        if not cart:
            if is_ajax:
                return jsonify({"success": False, "message": "Your cart is empty."}), 400
            flash("Your cart is empty.", "error")
            return redirect(url_for("customer.dashboard"))

        db = Database()

        try:
            db.execute(
                """
                INSERT INTO orders
                (user_id, table_id, status)
                VALUES (%s, %s, %s)
                """,
                (None, table_id, "pending")
            )

            order = db.fetch_one("SELECT LAST_INSERT_ID() AS order_id")

            if not order or not order.get("order_id"):
                raise Exception("Could not retrieve the new order ID.")

            order_id = order["order_id"]

            for item in cart.values():
                db.execute(
                    """
                    INSERT INTO order_items
                    (order_id, item_id, quantity, price_at_order)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["id"],
                        int(item["quantity"]),
                        float(item["price"])
                    )
                )

            session["customer_cart"] = {}
            session.modified = True

            if is_ajax:
                return jsonify({
                    "success": True,
                    "message": f"Order #{order_id} placed successfully!",
                    "order_id": order_id
                })

            flash("Your order has been placed successfully!", "success")
            return redirect(url_for("customer.view_order", order_id=order_id))

        except Exception as e:
            print("ORDER PLACEMENT ERROR:", e)

            if is_ajax:
                return jsonify({
                    "success": False,
                    "message": "Unable to place your order. Please try again."
                }), 500

            flash("Unable to place your order. Please try again.", "error")
            return redirect(url_for("customer.dashboard"))

        finally:
            db.close()

    # =========================================================
    # ORDER HISTORY
    # =========================================================

    def orders(self):
        table_id = session.get("customer_table_id")
        db = Database()

        try:
            if table_id:
                orders = db.fetch_all("""
                    SELECT
                        o.id,
                        o.table_id,
                        t.name AS table_name,
                        o.status,
                        o.created_at

                    FROM orders o

                    LEFT JOIN restaurant_tables t
                        ON t.id = o.table_id

                    WHERE o.table_id = %s

                    ORDER BY o.id DESC
                """, (table_id,))
            else:
                orders = []

            for order in orders:
                items = db.fetch_all("""
                    SELECT quantity, price_at_order
                    FROM order_items
                    WHERE order_id = %s
                """, (order["id"],))

                # Safe total calculation
                total = 0
                for i in items:
                    try:
                        price = float(i.get("price_at_order", 0) or 0)
                        qty = int(i.get("quantity", 0) or 0)
                        total += price * qty
                    except (ValueError, TypeError):
                        pass
                order["total_amount"] = total

        finally:
            db.close()

        return render_template(
            "customer/orders.html",
            orders=orders
        )

    # =========================================================
    # VIEW SINGLE ORDER
    # =========================================================

    def view_order(self, order_id):
        table_id = session.get("customer_table_id")
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
                    ON t.id = o.table_id

                WHERE o.id = %s
                AND o.table_id = %s
            """, (order_id, table_id))

            if not order:
                flash("Order not found.", "error")
                return redirect(url_for("customer.orders"))

            order_items = db.fetch_all("""
                SELECT
                    oi.id,
                    oi.item_id AS menu_item_id,
                    oi.quantity,
                    oi.price_at_order AS price,
                    m.name

                FROM order_items oi

                LEFT JOIN menu_items m
                    ON m.id = oi.item_id

                WHERE oi.order_id = %s

                ORDER BY oi.id ASC
            """, (order_id,))

            # Safe total calculation
            total = 0
            for i in order_items:
                try:
                    price = float(i.get("price", 0) or 0)
                    qty = int(i.get("quantity", 0) or 0)
                    total += price * qty
                except (ValueError, TypeError):
                    pass
            order["total_amount"] = total

        finally:
            db.close()

        return render_template(
            "customer/orders.html",
            orders=[order],
            selected_order=order,
            order_items=order_items
        )

    # =========================================================
    # MOBILE
    # =========================================================

    def mobile(self):
        return redirect(url_for("customer.dashboard"))

    # =========================================================
    # PRIVATE: SELECTED TABLE
    # =========================================================

    def _get_selected_table(self):
        table_id = session.get("customer_table_id")
        if not table_id:
            return None
        return Table().find_by_id(table_id)

    # =========================================================
    # PRIVATE: CART TOTAL
    # =========================================================

    def _calculate_cart_total(self, cart):
        total = 0
        for item in cart.values():
            try:
                price = float(item.get("price", 0) or 0)
                quantity = int(item.get("quantity", 0) or 0)
                total += price * quantity
            except (ValueError, TypeError):
                pass
        return total
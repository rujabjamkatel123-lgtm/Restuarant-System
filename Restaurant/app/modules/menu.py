from app.modules.database import Database


class MenuItem:

    def __init__(
        self,
        name=None,
        price=None,
        half_plate_price=None,
        category_id=None,
        description=None,
        image=None,
        available=None
    ):
        self.name = name
        self.price = price
        self.half_plate_price = half_plate_price
        self.category_id = category_id
        self.description = description
        self.image = image
        self.available = available

    # =========================================================
    # GET ALL
    # =========================================================

    def get_all(self):

        db = Database()

        try:

            menu_items = db.fetch_all("""
                SELECT *
                FROM menu_items
                ORDER BY id DESC
            """)

        finally:

            db.close()

        return menu_items

    # =========================================================
    # FIND BY ID
    # =========================================================

    def find_by_id(self, item_id):

        db = Database()

        try:

            menu_item = db.fetch_one("""
                SELECT *
                FROM menu_items
                WHERE id = %s
            """, (
                item_id,
            ))

        finally:

            db.close()

        return menu_item

    # =========================================================
    # SAVE / INSERT
    # =========================================================

    def save(
        self,
        name=None,
        price=None,
        half_plate_price=None,
        category_id=None,
        description=None,
        image=None,
        available=None
    ):

        name = (
            name
            if name is not None
            else self.name
        )

        price = (
            price
            if price is not None
            else self.price
        )

        half_plate_price = (
            half_plate_price
            if half_plate_price is not None
            else self.half_plate_price
        )

        category_id = (
            category_id
            if category_id is not None
            else self.category_id
        )

        description = (
            description
            if description is not None
            else self.description
        )

        image = (
            image
            if image is not None
            else self.image
        )

        available = (
            available
            if available is not None
            else 1
        )

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
                    image,
                    available
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                name,
                price,
                half_plate_price,
                category_id,
                description,
                image,
                available
            ))

        finally:

            db.close()

    # =========================================================
    # UPDATE
    # =========================================================

    def update(
        self,
        item_id,
        name,
        price,
        half_plate_price,
        category_id,
        description,
        image=None,
        available=None
    ):

        db = Database()

        try:

            if image:

                db.execute("""
                    UPDATE menu_items

                    SET
                        name = %s,
                        price = %s,
                        half_plate_price = %s,
                        category_id = %s,
                        description = %s,
                        image = %s,
                        available = %s

                    WHERE id = %s
                """, (
                    name,
                    price,
                    half_plate_price,
                    category_id,
                    description,
                    image,
                    available,
                    item_id
                ))

            else:

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
                    price,
                    half_plate_price,
                    category_id,
                    description,
                    available,
                    item_id
                ))

        finally:

            db.close()

    # =========================================================
    # DELETE
    # =========================================================

    def delete(self, item_id):

        db = Database()

        try:

            db.execute("""
                DELETE FROM menu_items
                WHERE id = %s
            """, (
                item_id,
            ))

        finally:

            db.close()
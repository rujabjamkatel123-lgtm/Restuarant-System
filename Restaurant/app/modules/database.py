import pymysql
import config


class Database:
    def __init__(self):
        """Open a database connection when object is created."""
        try:
            self.__connection = pymysql.connect(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor,
                ssl={"ssl": {}}
            )

            print("Database connected successfully!")

        except pymysql.MySQLError as e:
            print("Database connection failed!")
            print("Error:", e)

    def fetch_one(self, query, params=None):
        """Run a query and return ONE result."""

        cursor = self.__connection.cursor()

        cursor.execute(query, params)

        result = cursor.fetchone()

        cursor.close()

        return result

    def fetch_all(self, query, params=None):
        """Run a query and return ALL results."""

        cursor = self.__connection.cursor()

        cursor.execute(query, params)

        results = cursor.fetchall()

        cursor.close()

        return results

    def execute(self, query, params=None):
        """Run INSERT, UPDATE, DELETE, CREATE, ALTER queries."""

        cursor = self.__connection.cursor()

        cursor.execute(query, params)

        self.__connection.commit()

        cursor.close()

    def close(self):
        """Close the database connection."""

        self.__connection.close()

    @staticmethod
    def create_tables():
        """
        Create restaurant database tables if they don't exist.

        Tables:
            users
            menu_categories
            menu_items
            restaurant_tables
            orders
            order_items
            payments
        """

        db = Database()

        # =====================================================
        # USERS TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,

                name VARCHAR(100) NOT NULL,

                email VARCHAR(100) NOT NULL UNIQUE,

                password VARCHAR(255) NOT NULL,

                role VARCHAR(20) NOT NULL DEFAULT 'customer',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # MENU CATEGORIES TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS menu_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,

                name VARCHAR(100) NOT NULL UNIQUE,

                description TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # MENU ITEMS TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INT AUTO_INCREMENT PRIMARY KEY,

                name VARCHAR(150) NOT NULL,

                price DECIMAL(10, 2) NOT NULL,

                category_id INT NOT NULL,

                description TEXT,

                image VARCHAR(255),

                available BOOLEAN NOT NULL DEFAULT TRUE,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (category_id)
                    REFERENCES menu_categories(id)
                    ON DELETE CASCADE
            )
        """)

        # =====================================================
        # RESTAURANT TABLES TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_tables (
                id INT AUTO_INCREMENT PRIMARY KEY,

                name VARCHAR(50) NOT NULL UNIQUE,

                status VARCHAR(30) NOT NULL DEFAULT 'available',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # ORDERS TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,

                user_id INT,

                table_id INT NOT NULL,

                status VARCHAR(30) NOT NULL DEFAULT 'pending',

                total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL,

                FOREIGN KEY (table_id)
                    REFERENCES restaurant_tables(id)
                    ON DELETE RESTRICT
            )
        """)

        # =====================================================
        # ORDER ITEMS TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,

                order_id INT NOT NULL,

                item_id INT NOT NULL,

                quantity INT NOT NULL DEFAULT 1,

                price_at_order DECIMAL(10, 2) NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (item_id)
                    REFERENCES menu_items(id)
                    ON DELETE RESTRICT
            )
        """)

        # =====================================================
        # PAYMENTS TABLE
        # =====================================================

        db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,

                order_id INT NOT NULL,

                amount DECIMAL(10, 2) NOT NULL,

                payment_method VARCHAR(30) NOT NULL DEFAULT 'cash',

                payment_status VARCHAR(30) NOT NULL DEFAULT 'pending',

                paid_at DATETIME,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE
            )
        """)

        # =====================================================
        # CREATE 5 RESTAURANT TABLES
        # =====================================================

        for table_number in range(1, 6):

            table_name = f"Table {table_number}"

            existing_table = db.fetch_one(
                """
                SELECT id
                FROM restaurant_tables
                WHERE name = %s
                """,
                (table_name,)
            )

            if not existing_table:

                db.execute(
                    """
                    INSERT INTO restaurant_tables
                    (name, status)
                    VALUES (%s, %s)
                    """,
                    (
                        table_name,
                        "available"
                    )
                )

        # =====================================================
        # CREATE DEFAULT CATEGORIES
        # =====================================================

        categories = [
            ("Main Course", "Main restaurant dishes"),
            ("Momo", "Different types of momo"),
            ("Drinks", "Cold and hot beverages"),
            ("Dessert", "Sweet dishes and desserts")
        ]

        for category_name, description in categories:

            existing_category = db.fetch_one(
                """
                SELECT id
                FROM menu_categories
                WHERE name = %s
                """,
                (category_name,)
            )

            if not existing_category:

                db.execute(
                    """
                    INSERT INTO menu_categories
                    (name, description)
                    VALUES (%s, %s)
                    """,
                    (
                        category_name,
                        description
                    )
                )

        # =====================================================
        # CREATE DEFAULT MANAGER
        # =====================================================

        manager = db.fetch_one(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            ("manager@restaurant.com",)
        )

        if not manager:

            from werkzeug.security import generate_password_hash

            db.execute(
                """
                INSERT INTO users
                (name, email, password, role)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    "Restaurant Manager",
                    "manager@restaurant.com",
                    generate_password_hash("manager123", method="pbkdf2:sha256"),
                    "manager"
                )
            )

            print("Default manager created successfully.")

        # =====================================================
        # CREATE DEFAULT RECEPTIONIST
        # =====================================================

        receptionist = db.fetch_one(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            ("receptionist@restaurant.com",)
        )

        if not receptionist:

            from werkzeug.security import generate_password_hash

            db.execute(
                """
                INSERT INTO users
                (name, email, password, role)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    "Restaurant Receptionist",
                    "receptionist@restaurant.com",
                    generate_password_hash("receptionist123", method="pbkdf2:sha256"),
                    "receptionist"
                )
            )

            print("Default receptionist created successfully.")

        # =====================================================
        # CLOSE DATABASE
        # =====================================================

        db.close()

        print("Restaurant database tables created successfully!")
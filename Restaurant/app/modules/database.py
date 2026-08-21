"""
=============================================================
Restaurant Management System
Database Module
=============================================================

This file handles:

    - MySQL connection
    - SELECT queries
    - INSERT / UPDATE / DELETE queries
    - Database/table creation
    - Small database migrations

IMPORTANT FOR VERCEL:

    Database tables are NOT automatically created when the
    Flask application starts.

    This prevents database initialization from crashing the
    Vercel serverless function during startup.

    Run create_tables() manually when you need to initialize
    a new database.
=============================================================
"""

import pymysql
import config


class Database:

    # =========================================================
    # DATABASE CONNECTION
    # =========================================================

    def __init__(self):

        self.__connection = None

        try:

            self.__connection = pymysql.connect(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor,

                # Your hosted MySQL database currently uses SSL.
                ssl={"ssl": {}}
            )

            print("Database connected successfully!")

        except pymysql.MySQLError as e:

            print("========================================")
            print("DATABASE CONNECTION FAILED")
            print("========================================")
            print("Error:", e)
            print("Host:", config.MYSQL_HOST)
            print("Port:", config.MYSQL_PORT)
            print("Database:", config.MYSQL_DATABASE)
            print("========================================")

            # Do not continue with a broken connection.
            raise RuntimeError(
                "Unable to connect to the MySQL database."
            ) from e

    # =========================================================
    # FETCH ONE
    # =========================================================

    def fetch_one(self, query, params=None):

        cursor = self.__connection.cursor()

        try:

            cursor.execute(
                query,
                params
            )

            return cursor.fetchone()

        finally:

            cursor.close()

    # =========================================================
    # FETCH ALL
    # =========================================================

    def fetch_all(self, query, params=None):

        cursor = self.__connection.cursor()

        try:

            cursor.execute(
                query,
                params
            )

            return cursor.fetchall()

        finally:

            cursor.close()

    # =========================================================
    # EXECUTE
    # =========================================================

    def execute(self, query, params=None):

        cursor = self.__connection.cursor()

        try:

            cursor.execute(
                query,
                params
            )

            self.__connection.commit()

        except Exception:

            self.__connection.rollback()
            raise

        finally:

            cursor.close()

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        if self.__connection:

            try:
                self.__connection.close()
            except Exception:
                pass

            self.__connection = None

    # =========================================================
    # CREATE TABLES
    # =========================================================

    @staticmethod
    def create_tables():

        db = Database()

        try:

            # =================================================
            # USERS
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS users (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    name VARCHAR(100) NOT NULL,

                    email VARCHAR(100) NOT NULL UNIQUE,

                    password VARCHAR(255) NOT NULL,

                    role VARCHAR(20)
                        NOT NULL
                        DEFAULT 'customer',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # MENU CATEGORIES
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS menu_categories (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    name VARCHAR(100)
                        NOT NULL UNIQUE,

                    description TEXT,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # MENU ITEMS
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS menu_items (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    name VARCHAR(150) NOT NULL,

                    price DECIMAL(10, 2) NOT NULL,

                    half_plate_price DECIMAL(10, 2)
                        NULL,

                    category_id INT NOT NULL,

                    description TEXT,

                    image VARCHAR(255),

                    available BOOLEAN
                        NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (category_id)
                        REFERENCES menu_categories(id)
                        ON DELETE CASCADE
                )
            """)

            # =================================================
            # MIGRATION
            #
            # Your existing database was originally created
            # WITHOUT half_plate_price.
            #
            # This adds it if the existing table does not have
            # the column.
            # =================================================

            column_exists = db.fetch_one("""
                SELECT COUNT(*) AS total

                FROM INFORMATION_SCHEMA.COLUMNS

                WHERE TABLE_SCHEMA = %s

                AND TABLE_NAME = 'menu_items'

                AND COLUMN_NAME = 'half_plate_price'
            """, (
                config.MYSQL_DATABASE,
            ))

            if not column_exists or int(
                column_exists["total"]
            ) == 0:

                db.execute("""
                    ALTER TABLE menu_items

                    ADD COLUMN half_plate_price
                    DECIMAL(10, 2) NULL

                    AFTER price
                """)

                print(
                    "Added half_plate_price column."
                )

            # =================================================
            # RESTAURANT TABLES
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS restaurant_tables (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    name VARCHAR(50)
                        NOT NULL UNIQUE,

                    status VARCHAR(30)
                        NOT NULL
                        DEFAULT 'available',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # ORDERS
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS orders (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    user_id INT NULL,

                    table_id INT NOT NULL,

                    status VARCHAR(30)
                        NOT NULL
                        DEFAULT 'pending',

                    total_amount DECIMAL(10, 2)
                        NOT NULL
                        DEFAULT 0.00,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL,

                    FOREIGN KEY (table_id)
                        REFERENCES restaurant_tables(id)
                        ON DELETE RESTRICT
                )
            """)

            # =================================================
            # ORDER ITEMS
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS order_items (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    order_id INT NOT NULL,

                    item_id INT NOT NULL,

                    quantity INT
                        NOT NULL
                        DEFAULT 1,

                    price_at_order DECIMAL(10, 2)
                        NOT NULL,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (order_id)
                        REFERENCES orders(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (item_id)
                        REFERENCES menu_items(id)
                        ON DELETE RESTRICT
                )
            """)

            # =================================================
            # PAYMENTS
            # =================================================

            db.execute("""
                CREATE TABLE IF NOT EXISTS payments (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    order_id INT NOT NULL,

                    amount DECIMAL(10, 2)
                        NOT NULL,

                    payment_method VARCHAR(30)
                        NOT NULL
                        DEFAULT 'cash',

                    payment_status VARCHAR(30)
                        NOT NULL
                        DEFAULT 'pending',

                    paid_at DATETIME,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (order_id)
                        REFERENCES orders(id)
                        ON DELETE CASCADE
                )
            """)

            # =================================================
            # DEFAULT RESTAURANT TABLES
            # =================================================

            for table_number in range(1, 6):

                table_name = (
                    f"Table {table_number}"
                )

                existing_table = db.fetch_one("""
                    SELECT id

                    FROM restaurant_tables

                    WHERE name = %s
                """, (
                    table_name,
                ))

                if not existing_table:

                    db.execute("""
                        INSERT INTO restaurant_tables
                        (
                            name,
                            status
                        )

                        VALUES
                        (
                            %s,
                            %s
                        )
                    """, (
                        table_name,
                        "available"
                    ))

            # =================================================
            # DEFAULT CATEGORIES
            # =================================================

            categories = [

                (
                    "Main Course",
                    "Main restaurant dishes"
                ),

                (
                    "Momo",
                    "Different types of momo"
                ),

                (
                    "Drinks",
                    "Cold and hot beverages"
                ),

                (
                    "Dessert",
                    "Sweet dishes and desserts"
                )
            ]

            for category_name, description in categories:

                existing_category = db.fetch_one("""
                    SELECT id

                    FROM menu_categories

                    WHERE name = %s
                """, (
                    category_name,
                ))

                if not existing_category:

                    db.execute("""
                        INSERT INTO menu_categories
                        (
                            name,
                            description
                        )

                        VALUES
                        (
                            %s,
                            %s
                        )
                    """, (
                        category_name,
                        description
                    ))

            # =================================================
            # DEFAULT MANAGER
            # =================================================

            manager = db.fetch_one("""
                SELECT id

                FROM users

                WHERE email = %s
            """, (
                "manager@restaurant.com",
            ))

            if not manager:

                from werkzeug.security import (
                    generate_password_hash
                )

                db.execute("""
                    INSERT INTO users
                    (
                        name,
                        email,
                        password,
                        role
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    "Restaurant Manager",
                    "manager@restaurant.com",
                    generate_password_hash(
                        "manager123",
                        method="pbkdf2:sha256"
                    ),
                    "manager"
                ))

            # =================================================
            # DEFAULT RECEPTIONIST
            # =================================================

            receptionist = db.fetch_one("""
                SELECT id

                FROM users

                WHERE email = %s
            """, (
                "receptionist@restaurant.com",
            ))

            if not receptionist:

                from werkzeug.security import (
                    generate_password_hash
                )

                db.execute("""
                    INSERT INTO users
                    (
                        name,
                        email,
                        password,
                        role
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    "Restaurant Receptionist",
                    "receptionist@restaurant.com",
                    generate_password_hash(
                        "receptionist123",
                        method="pbkdf2:sha256"
                    ),
                    "receptionist"
                ))

            print(
                "Restaurant database initialization completed."
            )

        finally:

            db.close()
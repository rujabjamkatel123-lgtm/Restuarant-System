"""
=============================================================
  OOP Concept: INHERITANCE, ENCAPSULATION & POLYMORPHISM
=============================================================
  Restaurant Management System

  User Model represents a user of the restaurant system.

  User roles:
      - customer
      - receptionist
      - manager

  Inheritance:
      User inherits common database methods from BaseModel.

  Encapsulation:
      User password is kept private using __password.

  Polymorphism:
      User provides its own save(), update(), and find_all()
      methods while also using methods inherited from BaseModel.
=============================================================
"""

from werkzeug.security import generate_password_hash, check_password_hash

from app.modules.base_modules import BaseModel
from app.modules.database import Database


class User(BaseModel):
    """
    User Model — represents a single restaurant system user.
    """

    # ── Tell BaseModel which database table to use ─────────

    @property
    def table(self):
        return "users"

    # ── Create User Object ─────────────────────────────────

    def __init__(
        self,
        name=None,
        email=None,
        password=None,
        role="customer"
    ):
        self.name = name
        self.email = email

        # Private password attribute
        self.__password = None

        self.role = role

        if password:
            self.set_password(password)

    # ── Password Methods ───────────────────────────────────

    def set_password(self, plain_password):
        """
        Convert the normal password into a secure hash.

        We never store the user's actual password in MySQL.
        """

        self.__password = generate_password_hash(
            plain_password,
            method="pbkdf2:sha256"
        )

    def check_password(self, plain_password):
        """
        Check whether the entered password matches
        the stored password hash.
        """

        if self.__password is None:
            return False

        return check_password_hash(
            self.__password,
            plain_password
        )

    # ── Create User ─────────────────────────────────────────

    def save(self):
        """
        Create a new user in the users table.
        """

        db = Database()

        db.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (%s, %s, %s, %s)
            """,
            (
                self.name,
                self.email,
                self.__password,
                self.role
            )
        )

        db.close()

    # ── Update User ─────────────────────────────────────────

    def update(self, user_id, update_password=False):
        """
        Update user information.

        If update_password is True,
        the password will also be updated.
        """

        db = Database()

        if update_password:

            db.execute(
                """
                UPDATE users
                SET name = %s,
                    email = %s,
                    password = %s,
                    role = %s
                WHERE id = %s
                """,
                (
                    self.name,
                    self.email,
                    self.__password,
                    self.role,
                    user_id
                )
            )

        else:

            db.execute(
                """
                UPDATE users
                SET name = %s,
                    email = %s,
                    role = %s
                WHERE id = %s
                """,
                (
                    self.name,
                    self.email,
                    self.role,
                    user_id
                )
            )

        db.close()

    # ── Update Customer Profile ─────────────────────────────

    def update_profile(self, user_id, update_password=False):
        """
        Update a user's own profile.

        This does not allow changing the user's role.
        """

        db = Database()

        if update_password:

            db.execute(
                """
                UPDATE users
                SET name = %s,
                    email = %s,
                    password = %s
                WHERE id = %s
                """,
                (
                    self.name,
                    self.email,
                    self.__password,
                    user_id
                )
            )

        else:

            db.execute(
                """
                UPDATE users
                SET name = %s,
                    email = %s
                WHERE id = %s
                """,
                (
                    self.name,
                    self.email,
                    user_id
                )
            )

        db.close()

    # ── Check Email ─────────────────────────────────────────

    def email_exists(self, exclude_id=None):
        """
        Check whether an email already exists.

        exclude_id is useful when updating an existing user.
        """

        db = Database()

        if exclude_id:

            result = db.fetch_one(
                """
                SELECT id
                FROM users
                WHERE email = %s
                AND id != %s
                """,
                (
                    self.email,
                    exclude_id
                )
            )

        else:

            result = db.fetch_one(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (self.email,)
            )

        db.close()

        return result is not None

    # ── Find User By Email ──────────────────────────────────

    def find_by_email(self, email):
        """
        Find a user using their email address.

        Used during login.
        """

        db = Database()

        user = db.fetch_one(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        db.close()

        return user

    # ── Custom Find All ─────────────────────────────────────

    def find_all(self, order_by="id"):
        """
        Get all users.

        Used mainly by the Manager dashboard.

        Unlike the Library project, there is no 'admin'
        role being excluded here. Our restaurant roles are:

            customer
            receptionist
            manager
        """

        db = Database()

        results = db.fetch_all(
            f"""
            SELECT *
            FROM {self.table}
            ORDER BY {order_by}
            """
        )

        db.close()

        return results

    # ── Convert Database Row Into User Object ───────────────

    @classmethod
    def from_db(cls, data):
        """
        Convert a MySQL dictionary into a User object.
        """

        if data is None:
            return None

        user = cls()

        user.name = data["name"]
        user.email = data["email"]

        user.__password = data["password"]

        user.role = data["role"]

        return user

    # ── String Representation ───────────────────────────────

    def __str__(self):
        return (
            f"User("
            f"name={self.name}, "
            f"email={self.email}, "
            f"role={self.role}"
            f")"
        )

    def __repr__(self):
        return f"<User email={self.email}>"
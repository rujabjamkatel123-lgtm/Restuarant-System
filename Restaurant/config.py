import os


# =========================================================
# FLASK SECRET KEY
# =========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "random-secret-key"
)


# =========================================================
# MYSQL DATABASE CONFIGURATION
# =========================================================

MYSQL_HOST = os.environ.get(
    "MYSQL_HOST"
)

MYSQL_PORT = int(
    os.environ.get(
        "MYSQL_PORT",
        "3306"
    )
)

MYSQL_USER = os.environ.get(
    "MYSQL_USER"
)

MYSQL_PASSWORD = os.environ.get(
    "MYSQL_PASSWORD"
)

MYSQL_DATABASE = os.environ.get(
    "MYSQL_DATABASE"
)
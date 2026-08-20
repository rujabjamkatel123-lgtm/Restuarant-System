import os

# Flask secret key
SECRET_KEY = os.environ.get("SECRET_KEY", "random-secret-key")

# MySQL DATABASE CONFIGURATION (Reads from Vercel Environment Variables)
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "@rujab0011@")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "restaurant_management")
"""
=============================================================
  Restaurant Management System - Authentication
=============================================================

  This file contains decorators used to protect routes.

  Available roles:
    - customer
    - receptionist
    - manager

  login_required:
    Checks whether the user is logged in.

  role_required:
    Checks whether the logged-in user has permission
    to access a particular dashboard.
=============================================================
"""

from functools import wraps

from flask import session, redirect, url_for, flash


# =============================================================
# LOGIN REQUIRED
# =============================================================

def login_required(f):
    """
    Allow access only to logged-in users.

    If the user is not logged in:
        - Show a warning message
        - Redirect to the login page
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        return f(*args, **kwargs)

    return decorated


# =============================================================
# ROLE REQUIRED
# =============================================================

def role_required(*allowed_roles):
    """
    Allow access only to users with specific roles.

    Example:

        @role_required("manager")
        def dashboard():
            ...

    Multiple roles can also be allowed:

        @role_required("manager", "receptionist")
        def orders():
            ...
    """

    def decorator(f):

        @wraps(f)
        def decorated(*args, **kwargs):

            # ── Check Login ────────────────────────────────

            if "user_id" not in session:

                flash(
                    "Please login first.",
                    "warning"
                )

                return redirect(
                    url_for("auth.login")
                )


            # ── Check Role ─────────────────────────────────

            user_role = session.get("role")

            if user_role not in allowed_roles:

                flash(
                    "You do not have permission to access this page.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )

            return f(*args, **kwargs)

        return decorated

    return decorator


# =============================================================
# CUSTOMER REQUIRED
# =============================================================

def customer_required(f):
    """
    Allow access only to customers.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        if session.get("role") != "customer":

            flash(
                "Customer access required.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        return f(*args, **kwargs)

    return decorated


# =============================================================
# RECEPTIONIST REQUIRED
# =============================================================

def receptionist_required(f):
    """
    Allow access only to receptionists.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        if session.get("role") != "receptionist":

            flash(
                "Receptionist access required.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        return f(*args, **kwargs)

    return decorated


# =============================================================
# MANAGER REQUIRED
# =============================================================

def manager_required(f):
    """
    Allow access only to managers.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        if session.get("role") != "manager":

            flash(
                "Manager access required.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        return f(*args, **kwargs)

    return decorated
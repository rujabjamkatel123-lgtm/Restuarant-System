# In app/controllers/customer.py, change these redirect targets so
# every cart action lands back on the one dashboard page instead of
# the old separate menu/cart routes.

# ---- add_to_cart(): change the success redirect ----
#   was:  return redirect(url_for("customer.menu"))
    return redirect(url_for("customer.dashboard"))


# ---- remove_from_cart(): change the redirect ----
#   was:  return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.dashboard"))


# ---- update_cart(): change the redirect ----
#   was:  return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.dashboard"))


# ---- clear_cart(): change the redirect ----
#   was:  return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.dashboard"))


# ---- place_order(): change BOTH redirects (success and the except block) ----
#   was:  return redirect(url_for("customer.orders"))
    return redirect(url_for("customer.dashboard"))

#   was (in the except block):  return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.dashboard"))

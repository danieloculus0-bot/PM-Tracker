"""Fail-closed, server-verified operator login for PM Tracker.

PM_USERS_JSON maps usernames to {"password_hash": Werkzeug hash, "role": ...}.
The signing key and user database MUST be injected through environment secrets.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import secrets
from html import escape

from flask import g, redirect, request, session, url_for
from werkzeug.security import check_password_hash

ROLES = {"viewer", "operator", "admin"}


def _users():
    try:
        users = json.loads(os.environ.get("PM_USERS_JSON", "{}"))
    except (ValueError, TypeError):
        return {}
    return users if isinstance(users, dict) else {}


def current_user() -> str:
    """Return the server-authenticated username; never read the operator form field."""
    return str(g.user)


def install_auth(app):
    secret = os.environ.get("PM_SESSION_SECRET", "")
    if len(secret) >= 32:
        app.secret_key = secret
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.environ.get("PM_COOKIE_SECURE", "0") == "1",
    )

    def _csrf():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_urlsafe(32)
        return session["_csrf"]

    @app.route("/login", methods=["GET", "POST"])
    def pm_login():
        if not app.secret_key or not _users():
            return "PM Tracker login is not configured. Set PM_SESSION_SECRET and PM_USERS_JSON.", 503
        error = ""
        if request.method == "POST":
            supplied = str(request.form.get("_csrf", ""))
            if not hmac.compare_digest(supplied, _csrf()):
                return "Invalid login CSRF token.", 403
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = _users().get(username)
            if (isinstance(user, dict) and user.get("role") in ROLES
                    and isinstance(user.get("password_hash"), str)
                    and check_password_hash(user["password_hash"], password)):
                session.clear()
                session["user"] = username
                session["_csrf"] = secrets.token_urlsafe(32)
                return redirect("/")
            error = "Invalid credentials"
        return (f'<html><head><title>PM Tracker Login</title></head><body>'
                f'<h1>PM Tracker Login</h1><p>{escape(error)}</p>'
                f'<form method="post"><label>User <input name="username" required></label>'
                f'<label>Password <input name="password" type="password" required></label>'
                f'<input type="hidden" name="_csrf" value="{escape(_csrf())}">'
                f'<button type="submit">Sign in</button></form></body></html>')

    @app.post("/logout")
    def pm_logout():
        session.clear()
        return redirect(url_for("pm_login"))

    @app.before_request
    def require_authentication():
        if not app.secret_key or not _users():
            return "PM Tracker authentication is not configured.", 503
        if request.endpoint == "pm_login":
            return None
        user = session.get("user")
        principal = _users().get(user)
        if not isinstance(principal, dict) or principal.get("role") not in ROLES:
            return redirect(url_for("pm_login")) if request.method == "GET" else ("Authentication required.", 401)
        g.user = user
        g.role = principal["role"]
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if g.role == "viewer":
                return "Operator permission required.", 403
            if (request.path == "/import" or request.path.endswith("/close")) and g.role != "admin":
                return "Administrator permission required.", 403
            supplied = str(request.form.get("_csrf") or request.headers.get("X-CSRF-Token") or "")
            if not hmac.compare_digest(supplied, _csrf()):
                return "Invalid CSRF token.", 403
        return None

    @app.after_request
    def insert_csrf_form_field(response):
        # Existing plain HTML forms receive the CSRF field server-side.
        if app.secret_key and response.mimetype == "text/html" and response.status_code < 400:
            body = response.get_data(as_text=True)
            if re.search(r"<form\b", body, re.I):
                token = escape(_csrf())
                body = re.sub(
                    r'(<form\b[^>]*\bmethod\s*=\s*["\']?post["\']?[^>]*>)',
                    lambda m: m.group(1) + '<input type="hidden" name="_csrf" value="' + token + '">',
                    body,
                    flags=re.I,
                )
                response.set_data(body)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

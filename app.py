"""
Main Flask application entry point.

Handles authentication, authorization, session management,
and blueprint registration.
"""

import logging
import re
import time
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from db import get_db_connection

# Blueprints
from admin_modules import (
    admin_bp,
    instructors_bp,
    subjects_bp,
    rooms_bp,
    schedules_bp,
    auto_scheduler_bp,
    conflicts_bp,
    feedback_bp,
    load_bp,
    dashboard_bp,
    courses_bp,
)
from instructor_module import instructor_bp, room_bp, instructor_dashboard_bp

# ============================================================
# CONFIGURATION
# ============================================================

class SecurityConfig:
    """Security-related configuration."""
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME = 900  # seconds
    USERNAME_PATTERN = r"^[a-zA-Z0-9_]{3,50}$"


class AppConfig:
    """Application configuration."""
    SECRET_KEY = "your_secret_key_here"


# ============================================================
# INPUT VALIDATION
# ============================================================

class InputValidator:
    """Handles all input validation and sanitization."""

    @staticmethod
    def validate_username(username: str) -> bool:
        if not username or len(username) > 50:
            return False
        return bool(re.match(SecurityConfig.USERNAME_PATTERN, username))

    @staticmethod
    def sanitize_input(value: str, max_length: int = 255) -> str:
        if not value:
            return ""
        sanitized = re.sub(r'[<>"\']', "", value)
        return sanitized[:max_length]

    @staticmethod
    def validate_login_inputs(username: str, password: str):
        if not username or not password:
            return "Username and password are required."
        if not InputValidator.validate_username(username):
            return "Invalid username format."
        return None


# ============================================================
# RATE LIMITING
# ============================================================

class RateLimiter:
    """Controls login rate limiting."""

    @staticmethod
    def check_attempts(sess) -> tuple[bool, str]:
        attempts = sess.get("login_attempts", 0)
        lockout_time = sess.get("lockout_time", 0)

        current_time = time.time()
        if lockout_time > current_time:
            remaining = int((lockout_time - current_time) / 60)
            return False, f"Too many login attempts. Try again in {remaining} minutes."

        if attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            sess["lockout_time"] = current_time + SecurityConfig.LOCKOUT_TIME
            return False, "Too many login attempts. Account temporarily locked."

        return True, ""

    @staticmethod
    def increment_attempts(sess) -> None:
        sess["login_attempts"] = sess.get("login_attempts", 0) + 1


# ============================================================
# DATABASE SERVICE
# ============================================================

class DatabaseService:
    """Handles all database interactions."""

    @staticmethod
    def get_connection():
        try:
            return get_db_connection()
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(
                "Database connection failed: %s", type(exc).__name__
            )
            return None

    @staticmethod
    def close_connection(conn, cursor=None) -> None:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(
                "Error closing DB resources: %s", type(exc).__name__
            )

    @staticmethod
    def get_user_by_username(username: str):
        conn = DatabaseService.get_connection()
        if not conn:
            return None, None

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT instructor_id, username, password, role
                FROM instructors
                WHERE username = %s
                """,
                (username,),
            )
            return cursor.fetchone(), (conn, cursor)
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(
                "Database query error: %s", type(exc).__name__
            )
            DatabaseService.close_connection(conn, cursor)
            return None, None

    @staticmethod
    def get_instructor_name(user_id: int):
        conn = DatabaseService.get_connection()
        if not conn:
            return None

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT name FROM instructors WHERE instructor_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            return row["name"] if row else None
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(
                "Instructor name fetch error: %s", type(exc).__name__
            )
            return None
        finally:
            DatabaseService.close_connection(conn, cursor)


# ============================================================
# SESSION SERVICE
# ============================================================

class SessionService:
    """Manages Flask session state."""

    @staticmethod
    def setup_user_session(user: dict, sess) -> None:
        sess.clear()
        sess["user_id"] = user["instructor_id"]
        sess["username"] = user["username"]
        sess["role"] = user["role"]
        sess["last_activity"] = time.time()
        SessionService.clear_login_attempts(sess)

    @staticmethod
    def clear_login_attempts(sess) -> None:
        sess.pop("login_attempts", None)
        sess.pop("lockout_time", None)

    @staticmethod
    def is_user_logged_in(sess) -> bool:
        return "user_id" in sess

    @staticmethod
    def get_user_role(sess):
        return sess.get("role")


# ============================================================
# AUTHENTICATION
# ============================================================

class AuthenticationService:
    """Handles authentication logic."""

    @staticmethod
    def authenticate(username: str, password: str, sess):
        user, db_resources = DatabaseService.get_user_by_username(username)
        try:
            if user and check_password_hash(user["password"], password):
                SessionService.setup_user_session(user, sess)
                logging.getLogger(__name__).info(
                    "Successful login for user: %s", username
                )
                return user, None

            RateLimiter.increment_attempts(sess)
            logging.getLogger(__name__).warning(
                "Failed login attempt for username: %s", username
            )
            return None, "Invalid username or password"
        finally:
            if db_resources:
                DatabaseService.close_connection(*db_resources)

    @staticmethod
    def get_redirect_path(role: str):
        if role == "admin":
            return redirect(url_for("dashboard.admin_dashboard"))
        return redirect(url_for("instructor_dashboard.dashboard"))


# ============================================================
# LOGIN HANDLER
# ============================================================

class LoginHandler:
    """Coordinates the login workflow."""

    @staticmethod
    def process_login_request(req, sess):
        username = InputValidator.sanitize_input(
            req.form.get("username", "").strip()
        )
        password = req.form.get("password", "")

        error = InputValidator.validate_login_inputs(username, password)
        if error:
            return error, None

        allowed, rate_msg = RateLimiter.check_attempts(sess)
        if not allowed:
            return rate_msg, None

        return AuthenticationService.authenticate(username, password, sess)


# ============================================================
# FLASK APP SETUP
# ============================================================

app = Flask(__name__)
app.secret_key = AppConfig.SECRET_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)


# ============================================================
# DECORATORS
# ============================================================

def login_required(func):
    """Ensures user is authenticated."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not SessionService.is_user_logged_in(session):
            flash("Please log in to access this page.")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    """Ensures user has admin privileges."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not SessionService.is_user_logged_in(session):
            flash("Please log in to access this page.")
            return redirect(url_for("login"))
        if SessionService.get_user_role(session) != "admin":
            LOGGER.warning(
                "Unauthorized admin access by user: %s", session.get("user_id")
            )
            abort(403)
        return func(*args, **kwargs)
    return wrapper


# ============================================================
# BLUEPRINT PROTECTION
# ============================================================

def protect_blueprints():
    """Applies authentication checks to blueprints."""

    def require_admin():
        if not SessionService.is_user_logged_in(session):
            return redirect(url_for("login"))
        if SessionService.get_user_role(session) != "admin":
            abort(403)

    def require_user():
        if not SessionService.is_user_logged_in(session):
            return redirect(url_for("login"))

    for bp in [
        admin_bp, instructors_bp, subjects_bp, rooms_bp,
        schedules_bp, auto_scheduler_bp, conflicts_bp,
        feedback_bp, load_bp, dashboard_bp, courses_bp,
    ]:
        bp.before_request(require_admin)

    for bp in [instructor_bp, room_bp, instructor_dashboard_bp]:
        bp.before_request(require_user)


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if SessionService.is_user_logged_in(session):
        return AuthenticationService.get_redirect_path(
            SessionService.get_user_role(session)
        )

    if request.method == "POST":
        error, user = LoginHandler.process_login_request(request, session)
        if error:
            flash(error)
            return render_template("login.html")
        return AuthenticationService.get_redirect_path(user["role"])

    return render_template("login.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    session.clear()
    LOGGER.info("User %s logged out", user_id)
    flash("You have been successfully logged out.")
    return redirect(url_for("login"))


@app.before_request
def load_instructor_name():
    g.instructor_name = None
    user_id = session.get("user_id")
    if user_id:
        g.instructor_name = DatabaseService.get_instructor_name(user_id)


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found_error(_):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden_error(_):
    return render_template("403.html"), 403


@app.errorhandler(500)
def internal_error(error):
    LOGGER.error("Internal Server Error: %s", error)
    return render_template("500.html"), 500


# ============================================================
# APPLICATION INITIALIZATION
# ============================================================

def initialize_app():
    protect_blueprints()
    for bp in [
        admin_bp, instructors_bp, subjects_bp, rooms_bp,
        schedules_bp, auto_scheduler_bp, conflicts_bp,
        feedback_bp, load_bp, dashboard_bp, courses_bp,
        instructor_bp, room_bp, instructor_dashboard_bp,
    ]:
        app.register_blueprint(bp)


initialize_app()

if __name__ == "__main__":
    app.run(debug=True)

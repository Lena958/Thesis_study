"""
Feedback blueprint for managing room feedback in the admin panel.
Includes listing and deleting feedback entries.
"""

# ==================================================
# 1. Imports
# ==================================================
import mysql.connector
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, session


# ==================================================
# 2. Blueprint Definition
# ==================================================
feedback_bp = Blueprint("feedback", __name__, url_prefix="/admin/feedback")


# ==================================================
# 3. Database Configuration
# ==================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "iload",
}


# ==================================================
# 4. Database & Auth Helpers
# ==================================================
def get_db_connection():
    """Return a new database connection."""
    return mysql.connector.connect(**DB_CONFIG)


def is_admin():
    """Return True if current session user is an admin."""
    return session.get("role") == "admin"


def admin_required(fn):
    """Decorator to restrict routes to admin users only."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_admin():
            flash("Access denied. Admins only.", "danger")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# ==================================================
# 5. Context Processor
# ==================================================
@feedback_bp.context_processor
def inject_instructor_name():
    """Inject instructor info into templates for sidebar."""
    if "user_id" not in session:
        return {
            "instructor_name": None,
            "instructor_image": None,
        }

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, image FROM instructors WHERE instructor_id = %s",
        (session["user_id"],)
    )
    instructor = cursor.fetchone()
    cursor.close()
    conn.close()

    return {
        "instructor_name": instructor["name"] if instructor else None,
        "instructor_image": instructor["image"]
        if instructor and instructor["image"]
        else None,
    }


# ==================================================
# 6. Data Fetch Helpers
# ==================================================
def fetch_all_feedback():
    """Fetch all room feedback entries."""
    query = """
        SELECT f.feedback_id,
               r.room_number,
               r.room_type,
               i.name AS instructor_name,
               f.rating,
               f.comments,
               f.feedback_date
        FROM room_feedback f
        LEFT JOIN rooms r ON f.room_id = r.room_id
        LEFT JOIN instructors i ON f.instructor_id = i.instructor_id
        ORDER BY f.feedback_date DESC
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    feedbacks = cursor.fetchall()
    cursor.close()
    conn.close()

    return feedbacks


def delete_feedback_by_id(feedback_id):
    """Delete a feedback entry by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM room_feedback WHERE feedback_id = %s",
        (feedback_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()


# ==================================================
# 7. Routes
# ==================================================
@feedback_bp.route("/")
@admin_required
def list_feedback():
    """List all room feedback."""
    try:
        feedbacks = fetch_all_feedback()
    except mysql.connector.Error as err:
        print(f"Feedback fetch error: {err}")
        flash("Error loading feedback list.", "danger")
        feedbacks = []

    return render_template(
        "admin/feedback.html",
        feedbacks=feedbacks
    )


@feedback_bp.route("/delete/<int:feedback_id>", methods=["POST"])
@admin_required
def delete_feedback(feedback_id):
    """Delete a feedback entry."""
    try:
        delete_feedback_by_id(feedback_id)
        flash("Feedback deleted successfully.", "success")
    except mysql.connector.Error as err:
        print(f"Feedback delete error ({feedback_id}): {err}")
        flash("An error occurred while deleting feedback.", "danger")

    return redirect(url_for("feedback.list_feedback"))

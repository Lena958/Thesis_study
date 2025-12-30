"""
Dashboard module for admin routes.
Handles fetching stats, top instructors, room usage, and conflicts.
"""

# ==================================================
# 1. Imports
# ==================================================
import mysql.connector
from flask import Blueprint, render_template, session, redirect, url_for
from .admin_routes import get_instructor_name, db_config


# ==================================================
# 2. Blueprint Definition
# ==================================================
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/admin")


# ==================================================
# 3. Constants
# ==================================================
NO_INSTRUCTOR_INFO = {
    "instructor_name": None,
    "instructor_image": None
}


# ==================================================
# 4. Database & Auth Helpers
# ==================================================
def get_db_connection():
    """Return a new database connection."""
    return mysql.connector.connect(**db_config)


def is_admin():
    """Return True if current session user is an admin."""
    return session.get("role") == "admin"


# ==================================================
# 5. Context Processor
# ==================================================
@dashboard_bp.context_processor
def inject_instructor_name():
    """Inject instructor info into templates for sidebar."""
    if "user_id" not in session:
        return NO_INSTRUCTOR_INFO

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
        "instructor_image": instructor["image"] if instructor and instructor["image"] else None
    }


# ==================================================
# 6. Dashboard Data Fetch Helpers
# ==================================================
def fetch_basic_stats(cursor):
    """Fetch basic dashboard counts."""
    stats = {
        "total_instructors": 0,
        "total_rooms": 0,
        "total_subjects": 0,
        "conflicts": 0,
        "schedules": 0,
        "satisfied_feedback": 0,
        "unsatisfied_feedback": 0,
    }

    cursor.execute("SELECT COUNT(*) AS cnt FROM instructors")
    stats["total_instructors"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) AS cnt FROM rooms")
    stats["total_rooms"] = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) AS cnt FROM subjects")
    stats["total_subjects"] = cursor.fetchone()["cnt"]

    try:
        cursor.execute("SELECT COUNT(*) AS cnt FROM conflicts")
        stats["conflicts"] = cursor.fetchone()["cnt"]
    except mysql.connector.Error:
        stats["conflicts"] = 0

    cursor.execute("SELECT COUNT(*) AS cnt FROM schedules")
    stats["schedules"] = cursor.fetchone()["cnt"]

    return stats


def fetch_feedback_stats(cursor, stats):
    """Populate satisfied and unsatisfied feedback counts."""
    try:
        cursor.execute(
            "SELECT rating, COUNT(*) AS cnt FROM room_feedback GROUP BY rating"
        )
        for row in cursor.fetchall():
            if row["rating"] == "Satisfied":
                stats["satisfied_feedback"] = row["cnt"]
            elif row["rating"] == "Unsatisfied":
                stats["unsatisfied_feedback"] = row["cnt"]
    except mysql.connector.Error:
        pass


def fetch_instructor_load(cursor):
    """Fetch instructor load data."""
    cursor.execute("""
        SELECT i.name, i.max_load_units,
               IFNULL(SUM(sb.units), 0) AS current_units
        FROM instructors i
        LEFT JOIN subjects sb ON i.instructor_id = sb.instructor_id
        GROUP BY i.instructor_id
    """)
    return cursor.fetchall()


def fetch_room_usage(cursor):
    """Fetch room usage statistics."""
    cursor.execute("""
        SELECT r.room_number, r.room_type,
               COUNT(sc.schedule_id) AS schedules_count
        FROM rooms r
        LEFT JOIN schedules sc ON r.room_id = sc.room_id
        GROUP BY r.room_id
    """)
    return cursor.fetchall()


def fetch_recent_conflicts(cursor):
    """Fetch most recent conflicts."""
    try:
        cursor.execute("""
            SELECT conflict_type, description, status
            FROM conflicts
            ORDER BY conflict_id DESC
            LIMIT 5
        """)
        return cursor.fetchall()
    except mysql.connector.Error:
        return []


def fetch_top_instructors(cursor):
    """Fetch top instructors by load and attach subjects."""
    cursor.execute("""
        SELECT i.instructor_id, i.name, i.image, i.max_load_units,
               IFNULL(SUM(sb.units), 0) AS current_units
        FROM instructors i
        LEFT JOIN subjects sb ON i.instructor_id = sb.instructor_id
        GROUP BY i.instructor_id
        ORDER BY current_units DESC
        LIMIT 5
    """)
    instructors = cursor.fetchall()

    for instructor in instructors:
        cursor.execute(
            "SELECT name FROM subjects WHERE instructor_id = %s",
            (instructor["instructor_id"],)
        )
        instructor["subjects"] = [
            row["name"] for row in cursor.fetchall()
        ]

    return instructors


# ==================================================
# 7. Routes
# ==================================================
@dashboard_bp.route("/dashboard")
def admin_dashboard():
    """Render the admin dashboard."""
    if not is_admin():
        return redirect(url_for("login"))

    username = session.get("username")
    instructor_name = get_instructor_name(username)

    stats = {}
    instructor_load = []
    room_usage = []
    recent_conflicts = []
    top_instructors = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        stats = fetch_basic_stats(cursor)
        fetch_feedback_stats(cursor, stats)
        instructor_load = fetch_instructor_load(cursor)
        room_usage = fetch_room_usage(cursor)
        recent_conflicts = fetch_recent_conflicts(cursor)
        top_instructors = fetch_top_instructors(cursor)

    except mysql.connector.Error as err:
        print(f"Dashboard DB error: {err}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

    return render_template(
        "admin/admin_dashboard.html",
        username=username,
        instructor_name=instructor_name,
        stats=stats,
        instructor_load=instructor_load,
        room_usage=room_usage,
        recent_conflicts=recent_conflicts,
        top_instructors=top_instructors
    )

"""Schedule management routes for the admin panel.

Provides CRUD operations, approval, and conflict checking for schedules.
"""

# -------------------- Standard Imports --------------------
from functools import wraps
from contextlib import contextmanager
from datetime import datetime, timedelta

# -------------------- Third-party Imports --------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import mysql.connector

# -------------------- Blueprint & Config --------------------
schedules_bp = Blueprint('schedules', __name__, url_prefix='/admin/schedules')

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

SCHEDULES_LIST_ROUTE = 'schedules.list_schedules'


# -------------------- Helper Functions --------------------
def get_db_connection():
    """Return a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def is_admin():
    """Check if the current user is an admin."""
    return session.get('role') == 'admin'


def admin_required(f):
    """Decorator to protect admin routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@contextmanager
def db_cursor(dictionary=False):
    """Provide a database cursor with automatic commit and cleanup."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# -------------------- Context Processor --------------------
@schedules_bp.context_processor
def inject_instructor_name():
    """Inject instructor name and image into templates."""
    if 'user_id' not in session:
        return {"instructor_name": None, "instructor_image": None}

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT name, image FROM instructors WHERE instructor_id = %s",
            (session['user_id'],)
        )
        instructor = cursor.fetchone()

    return {
        "instructor_name": instructor['name'] if instructor else None,
        "instructor_image": instructor['image'] if instructor and instructor['image'] else None
    }


# -------------------- Time Formatting --------------------
def format_time_12hr(time_obj):
    """Return a 12-hour formatted string for a given time object or string."""
    if not time_obj:
        return ""
    if isinstance(time_obj, str):
        time_obj = datetime.strptime(time_obj, "%H:%M:%S").time()
    elif isinstance(time_obj, timedelta):
        total_seconds = int(time_obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        time_obj = datetime.strptime(f"{hours}:{minutes}", "%H:%M").time()
    return time_obj.strftime("%I:%M %p")


def format_time_24hr(time_obj):
    """Return a 24-hour formatted string for a given time object or string."""
    if isinstance(time_obj, str):
        time_obj = datetime.strptime(time_obj, "%H:%M:%S").time()
    elif isinstance(time_obj, timedelta):
        total_seconds = int(time_obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        time_obj = datetime.strptime(f"{hours}:{minutes}", "%H:%M").time()
    return time_obj.strftime("%H:%M")


# -------------------- Fetch Schedules --------------------
def fetch_schedules(approved=None, complete_only=False):
    """Fetch schedules with optional approval and completeness filters."""
    query = (
        "SELECT sc.schedule_id, sc.day_of_week, sc.start_time, sc.end_time, "
        "sb.subject_id, sb.code AS subject_code, sb.name AS subject_name, "
        "sb.year_level, sb.section, sb.course, "
        "ins.instructor_id, ins.name AS instructor_name, "
        "rm.room_id, rm.room_number, rm.room_type "
        "FROM schedules sc "
        "LEFT JOIN subjects sb ON sc.subject_id = sb.subject_id "
        "LEFT JOIN instructors ins ON sc.instructor_id = ins.instructor_id "
        "LEFT JOIN rooms rm ON sc.room_id = rm.room_id"
    )
    conditions = []
    params = []

    if approved is not None:
        conditions.append("sc.approved = %s")
        params.append(approved)

    if complete_only:
        conditions.append(
            "sc.subject_id IS NOT NULL AND sb.subject_id IS NOT NULL "
            "AND sc.instructor_id IS NOT NULL AND ins.instructor_id IS NOT NULL "
            "AND sc.room_id IS NOT NULL AND rm.room_id IS NOT NULL "
            "AND sc.start_time IS NOT NULL AND sc.end_time IS NOT NULL"
        )

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY sc.day_of_week, sc.start_time"

    with db_cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        schedules = cursor.fetchall()

    for sched in schedules:
        sched['start_time_12'] = format_time_12hr(sched['start_time'])
        sched['end_time_12'] = format_time_12hr(sched['end_time'])

    return schedules


# -------------------- Routes --------------------
@schedules_bp.route('/')
@admin_required
def list_schedules():
    """List pending schedules (not approved)."""
    schedules = fetch_schedules(approved=0)
    return render_template("admin/schedules.html", schedules=schedules)


@schedules_bp.route('/view')
@admin_required
def view_all_schedules():
    """View all approved schedules (complete only)."""
    schedules = fetch_schedules(approved=1, complete_only=True)
    return render_template("schedules/view.html", schedules=schedules)


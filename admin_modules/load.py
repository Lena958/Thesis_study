"""
Module for managing schedules and instructor-related views in iLoad admin.
"""

# ------------------------
# Standard library imports
# ------------------------
from functools import wraps
from contextlib import contextmanager
from datetime import datetime, timedelta, time
import re

# ------------------------
# Third-party imports
# ------------------------
from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector
from mysql.connector.cursor import MySQLCursorDict
from mysql.connector import Error

# ------------------------
# DB / Blueprint
# ------------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}


def get_db_connection():
    """Return a new MySQL database connection using DB_CONFIG."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None


def is_admin():
    """Return True if current session belongs to admin."""
    return session.get('role') == 'admin'


@contextmanager
def db_cursor(dictionary=False):
    """Context manager to yield a database cursor and commit/close connection."""
    conn = get_db_connection()
    if not conn:
        yield None
        return
    cursor = conn.cursor(cursor_class=MySQLCursorDict) if dictionary else conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Error as e:
        conn.rollback()
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


# ------------------------
# Blueprint
# ------------------------
load_bp = Blueprint('load', __name__, url_prefix='/view')


# ------------------------
# Context processors
# ------------------------
@load_bp.context_processor
def inject_instructor_name():
    """Inject instructor's name and image into templates for sidebar."""
    if 'user_id' not in session:
        return {"instructor_name": None, "instructor_image": None}

    with db_cursor(dictionary=True) as cursor:
        if not cursor:
            return {"instructor_name": None, "instructor_image": None}
        cursor.execute(
            "SELECT name, image FROM instructors WHERE instructor_id = %s",
            (session['user_id'],)
        )
        instructor = cursor.fetchone()

    return {
        "instructor_name": instructor['name'] if instructor else None,
        "instructor_image": instructor['image'] if instructor and instructor['image'] else None
    }


# ------------------------
# Helpers
# ------------------------
def admin_required(f):
    """Decorator to restrict route access to admin only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def format_time_12hr(time_obj):
    """Convert a time or timedelta object to 12-hour format string."""
    if not time_obj:
        return ""
    try:
        if isinstance(time_obj, str):
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    time_obj = datetime.strptime(time_obj, fmt).time()
                    break
                except ValueError:
                    continue
        elif isinstance(time_obj, timedelta):
            total_seconds = int(time_obj.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_obj = time(hour=hours, minute=minutes)
        return time_obj.strftime("%I:%M %p")
    except Exception:
        return ""


def normalize_day(d):
    """Normalize day abbreviations or names to full day name."""
    if not d:
        return None
    s = str(d).strip().lower()
    map_ = {
        'm': 'Monday','mon':'Monday','monday':'Monday',
        't': 'Tuesday','tue':'Tuesday','tues':'Tuesday','tuesday':'Tuesday',
        'w': 'Wednesday','wed':'Wednesday','wednesday':'Wednesday',
        'th': 'Thursday','thu':'Thursday','thursday':'Thursday',
        'f': 'Friday','fri':'Friday','friday':'Friday',
        'sat':'Saturday','saturday':'Saturday',
        'sun':'Sunday','sunday':'Sunday'
    }
    return map_.get(s, s.capitalize())


def prettify_search_title(raw_title: str) -> str:
    """Format search titles nicely (capitalize words, strip extra spaces)."""
    if not raw_title:
        return ""
    return " ".join(word.capitalize() for word in raw_title.strip().split())


def convert_timedelta_to_time(td):
    """Convert timedelta to time object."""
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        return time(total_seconds // 3600, (total_seconds % 3600) // 60)
    return td


def build_time_slots(start=7, end=20):
    """Generate half-hour time slots from start hour to end hour."""
    slots = []
    for h in range(start, end):
        slots.append(time(h, 0))
        slots.append(time(h, 30))
    return slots


def initialize_grid(days, slots_len):
    """Create an empty schedule grid for given days and number of time slots."""
    return {day: [None] * slots_len for day in days}


def find_index(time_slots, t):
    """Find index of the first slot >= t."""
    try:
        return next(i for i, slot in enumerate(time_slots) if slot >= t)
    except StopIteration:
        return len(time_slots)


def insert_schedule_into_grid(grid, sched, days, time_slots):
    """Insert a schedule entry into the half-hour grid."""
    start = sched.get('start_time')
    end = sched.get('end_time')
    day = sched.get('day_of_week')
    if not start or not end or day not in days:
        return
    start_idx = find_index(time_slots, start)
    end_idx = find_index(time_slots, end)
    duration = end_idx - start_idx
    if duration <= 0:
        return
    grid[day][start_idx] = {**sched, "rowspan": duration}
    for i in range(start_idx + 1, end_idx):
        grid[day][i] = "skip"


# ------------------------
# Fetch schedules
# ------------------------
def fetch_all_schedules(search_query=None):
    """Fetch all approved schedules, optionally filtered by search query."""
    sql = """
        SELECT sc.schedule_id, sc.day_of_week, sc.start_time, sc.end_time,
               sb.subject_id, sb.code AS subject_code, sb.name AS subject_name, IFNULL(sb.units,0) AS units,
               sb.year_level, sb.section, sb.course,
               ins.instructor_id, ins.name AS instructor_name,
               rm.room_id, rm.room_number, rm.room_type
        FROM schedules sc
        JOIN subjects sb ON sc.subject_id = sb.subject_id
        JOIN instructors ins ON sc.instructor_id = ins.instructor_id
        JOIN rooms rm ON sc.room_id = rm.room_id
        WHERE sc.approved = 1
          AND sb.name IS NOT NULL
          AND sb.code IS NOT NULL
          AND sb.year_level IS NOT NULL
          AND sb.section IS NOT NULL
          AND sb.course IS NOT NULL
          AND ins.name IS NOT NULL
          AND rm.room_number IS NOT NULL
          AND rm.room_type IS NOT NULL
    """
    params = []
    if search_query:
        keywords = re.split(r"[\s\-]+", search_query.lower().strip())
        for kw in keywords:
            kw_like = f"%{kw}%"
            sql += """
              AND (
                  LOWER(ins.name) LIKE %s
                  OR LOWER(rm.room_number) LIKE %s
                  OR LOWER(sb.course) LIKE %s
                  OR LOWER(CONCAT(REPLACE(sb.year_level,'-',''), REPLACE(sb.section,'-',''))) LIKE %s
                  OR LOWER(sb.name) LIKE %s
                  OR LOWER(sb.code) LIKE %s
              )
            """
            params.extend([kw_like]*6)

    sql += " ORDER BY FIELD(sc.day_of_week, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), sc.start_time"

    with db_cursor(dictionary=True) as cursor:
        if not cursor:
            return []
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    for r in rows:
        r['day_of_week'] = normalize_day(r.get('day_of_week'))
        r['start_time'] = convert_timedelta_to_time(r['start_time'])
        r['end_time'] = convert_timedelta_to_time(r['end_time'])
        r['start_time_12'] = format_time_12hr(r['start_time'])
        r['end_time_12'] = format_time_12hr(r['end_time'])
    return rows


# ------------------------
# Routes
# ------------------------
@load_bp.route('/', methods=['GET'])
@admin_required
def view_all_schedules():
    """View all schedules with optional search query."""
    q = request.args.get("q", "").strip()
    schedules = fetch_all_schedules(search_query=q if q else None)
    return render_template(
        "schedules/view.html",
        schedules=schedules,
        search_title=q if q else None
    )


@load_bp.route('/final', methods=['GET'])
@admin_required
def view_final_schedule():
    """View final timetable grid for approved schedules."""
    schedules = fetch_all_schedules()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    grid = {d: [] for d in days}
    for s in schedules:
        if s['day_of_week'] in grid:
            grid[s['day_of_week']].append(s)
    time_slots = [{"time": time(h, 0), "label": f"{h:02d}:00"} for h in range(7, 20)]
    return render_template(
        "schedules/view.html",
        grid=grid,
        days=days,
        time_slots=time_slots
    )


@load_bp.route('/copy', methods=['GET'])
@admin_required
def view_copy():
    """View copy of searched schedules in half-hour grid format."""
    q = request.args.get("q", "").strip()
    schedules = fetch_all_schedules(search_query=q if q else None)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    time_slots = build_time_slots()
    grid = initialize_grid(days, len(time_slots))

    for sched in schedules:
        sched['start_time'] = convert_timedelta_to_time(sched['start_time'])
        sched['end_time'] = convert_timedelta_to_time(sched['end_time'])
        insert_schedule_into_grid(grid, sched, days, time_slots)

    return render_template(
        "schedules/copy.html",
        days=days,
        time_slots=time_slots,
        grid=grid,
        search_title=prettify_search_title(q) if q else None
    )


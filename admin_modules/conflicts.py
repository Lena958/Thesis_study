"""
Conflicts blueprint for detecting and managing schedule conflicts.
Includes conflict detection, resolution, display functionality,
input validation, error handling, and unit tests.
"""

# ==========================================================
# STANDARD LIBRARY IMPORTS
# ==========================================================

from datetime import datetime, time, timedelta
import unittest

# ==========================================================
# THIRD-PARTY IMPORTS
# ==========================================================

import mysql.connector
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# ==========================================================
# BLUEPRINT DEFINITION
# ==========================================================

conflicts_bp = Blueprint('conflicts', __name__, url_prefix='/admin/conflicts')

# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

# ==========================================================
# CONSTANTS & ENUM-LIKE MAPS
# ==========================================================

FLASH_CATEGORIES = {
    'success': 'success'
}

ERROR_MESSAGES = {
    'conflict_resolved': 'Conflict #{conflict_id} marked as resolved.',
    'instructor_conflict_desc': (
        "Instructor {instructor_name} has overlapping classes: "
        "'{subject1}' and '{subject2}' on {day} "
        "{start1} - {end1} and {start2} - {end2}"
    ),
    'instructor_conflict_rec': (
        "Reassign one of the overlapping classes for {instructor_name} "
        "to another instructor or move it to a different time."
    ),
    'room_conflict_desc': (
        "Room {room_number} has overlapping classes: "
        "'{subject1}' and '{subject2}' on {day} "
        "{start1} - {end1} and {start2} - {end2}"
    ),
    'room_conflict_rec': (
        "Move one of the classes to another available room or adjust the schedule."
    ),
    'invalid_time_format': 'Invalid time format: {value}',
    'db_connection_error': 'Database connection failed: {error}'
}

DB_TABLES = {
    'conflicts': 'conflicts',
    'schedules': 'schedules',
    'subjects': 'subjects',
    'instructors': 'instructors',
    'rooms': 'rooms'
}

DB_FIELDS = {
    'conflict_id': 'conflict_id',
    'schedule1_id': 'schedule1_id',
    'schedule2_id': 'schedule2_id',
    'conflict_type': 'conflict_type',
    'description': 'description',
    'recommendation': 'recommendation',
    'status': 'status',
    'schedule_id': 'schedule_id',
    'day_of_week': 'day_of_week',
    'start_time': 'start_time',
    'end_time': 'end_time',
    'subject_name': 'subject_name',
    'year_level': 'year_level',
    'section': 'section',
    'course': 'course',
    'instructor_name': 'instructor_name',
    'instructor_id': 'instructor_id',
    'room_number': 'room_number',
    'room_type': 'room_type',
    'room_id': 'room_id',
    'name': 'name',
    'image': 'image',
    'subject_id': 'subject_id'
}

CONFLICT_TYPES = {
    'instructor': 'Instructor Double Booking',
    'room': 'Room Double Booking'
}

STATUS_TYPES = {
    'unresolved': 'Unresolved',
    'resolved': 'Resolved'
}

TIME_FORMATS = {
    '24h': "%H:%M:%S",
    '12h': "%I:%M %p"
}

# ==========================================================
# DATABASE & SECURITY UTILITIES
# ==========================================================

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        raise ConnectionError(
            ERROR_MESSAGES['db_connection_error'].format(error=str(e))
        )


def is_admin():
    return session.get('role') == 'admin'


@conflicts_bp.context_processor
def inject_instructor_name():
    if 'user_id' not in session:
        return {
            DB_FIELDS['instructor_name']: None,
            DB_FIELDS['image']: None
        }

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = (
            f"SELECT {DB_FIELDS['name']}, {DB_FIELDS['image']} "
            f"FROM {DB_TABLES['instructors']} "
            f"WHERE {DB_FIELDS['instructor_id']} = %s"
        )
        cursor.execute(query, (session['user_id'],))
        instructor = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return {
        DB_FIELDS['instructor_name']:
            instructor[DB_FIELDS['name']] if instructor else None,
        DB_FIELDS['image']:
            instructor[DB_FIELDS['image']]
            if instructor and instructor[DB_FIELDS['image']] else None
    }

# ==========================================================
# TIME HANDLING UTILITIES
# ==========================================================

def timedelta_to_time(td):
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        return time(
            hour=total_seconds // 3600,
            minute=(total_seconds % 3600) // 60,
            second=total_seconds % 60
        )
    return td


def parse_time(value):
    try:
        if isinstance(value, datetime):
            return value.time()
        if isinstance(value, timedelta):
            return timedelta_to_time(value)
        if isinstance(value, str):
            return datetime.strptime(value, TIME_FORMATS['24h']).time()
    except Exception:
        raise ValueError(
            ERROR_MESSAGES['invalid_time_format'].format(value=value)
        )
    return value


def format_time_12h(value):
    return value.strftime(TIME_FORMATS['12h']) if isinstance(value, time) else str(value)

# ==========================================================
# LOW-LEVEL CONFLICT HELPERS
# ==========================================================

def schedules_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def same_instructor(s1, s2):
    return s1[DB_FIELDS['instructor_id']] == s2[DB_FIELDS['instructor_id']]


def same_room(s1, s2):
    return s1[DB_FIELDS['room_id']] == s2[DB_FIELDS['room_id']]

# ==========================================================
# INPUT VALIDATION
# ==========================================================

def validate_schedule(schedule):
    required_fields = [
        DB_FIELDS['schedule_id'],
        DB_FIELDS['day_of_week'],
        DB_FIELDS['start_time'],
        DB_FIELDS['end_time'],
        DB_FIELDS['instructor_id'],
        DB_FIELDS['room_id'],
        DB_FIELDS['subject_name'],
        DB_FIELDS['instructor_name'],
        DB_FIELDS['room_number']
    ]

    for field in required_fields:
        if field not in schedule or schedule[field] is None:
            raise ValueError(f"Missing or invalid schedule field: {field}")

# ==========================================================
# DATABASE WRITE OPERATIONS
# ==========================================================

def save_conflict_to_db(
    schedule1_id,
    schedule2_id,
    conflict_type,
    description,
    recommendation
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT COUNT(*) FROM {DB_TABLES['conflicts']}
            WHERE {DB_FIELDS['schedule1_id']} = %s
            AND {DB_FIELDS['schedule2_id']} = %s
        """
        cursor.execute(query, (schedule1_id, schedule2_id))

        if cursor.fetchone()[0] == 0:
            insert_query = f"""
                INSERT INTO {DB_TABLES['conflicts']}
                ({DB_FIELDS['schedule1_id']},
                 {DB_FIELDS['schedule2_id']},
                 {DB_FIELDS['conflict_type']},
                 {DB_FIELDS['description']},
                 {DB_FIELDS['recommendation']},
                 {DB_FIELDS['status']})
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    schedule1_id,
                    schedule2_id,
                    conflict_type,
                    description,
                    recommendation,
                    STATUS_TYPES['unresolved']
                )
            )
            conn.commit()
    finally:
        cursor.close()
        conn.close()

# ==========================================================
# CONFLICT DETECTION LOGIC
# ==========================================================

def detect_instructor_conflict(s1, s2, day, start1, end1, start2, end2):
    description = ERROR_MESSAGES['instructor_conflict_desc'].format(
        instructor_name=s1[DB_FIELDS['instructor_name']],
        subject1=s1[DB_FIELDS['subject_name']],
        subject2=s2[DB_FIELDS['subject_name']],
        day=day,
        start1=format_time_12h(start1),
        end1=format_time_12h(end1),
        start2=format_time_12h(start2),
        end2=format_time_12h(end2)
    )

    recommendation = ERROR_MESSAGES['instructor_conflict_rec'].format(
        instructor_name=s1[DB_FIELDS['instructor_name']]
    )

    save_conflict_to_db(
        s1[DB_FIELDS['schedule_id']],
        s2[DB_FIELDS['schedule_id']],
        CONFLICT_TYPES['instructor'],
        description,
        recommendation
    )


def detect_room_conflict(s1, s2, day, start1, end1, start2, end2):
    description = ERROR_MESSAGES['room_conflict_desc'].format(
        room_number=s1[DB_FIELDS['room_number']],
        subject1=s1[DB_FIELDS['subject_name']],
        subject2=s2[DB_FIELDS['subject_name']],
        day=day,
        start1=format_time_12h(start1),
        end1=format_time_12h(end1),
        start2=format_time_12h(start2),
        end2=format_time_12h(end2)
    )

    save_conflict_to_db(
        s1[DB_FIELDS['schedule_id']],
        s2[DB_FIELDS['schedule_id']],
        CONFLICT_TYPES['room'],
        description,
        ERROR_MESSAGES['room_conflict_rec']
    )


def detect_and_save_conflicts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT sc.{DB_FIELDS['schedule_id']},
                   sc.{DB_FIELDS['day_of_week']},
                   sc.{DB_FIELDS['start_time']},
                   sc.{DB_FIELDS['end_time']},
                   sb.{DB_FIELDS['name']} AS {DB_FIELDS['subject_name']},
                   sb.{DB_FIELDS['year_level']},
                   sb.{DB_FIELDS['section']},
                   sb.{DB_FIELDS['course']},
                   ins.{DB_FIELDS['name']} AS {DB_FIELDS['instructor_name']},
                   ins.{DB_FIELDS['instructor_id']},
                   rm.{DB_FIELDS['room_number']},
                   rm.{DB_FIELDS['room_type']},
                   rm.{DB_FIELDS['room_id']}
            FROM {DB_TABLES['schedules']} sc
            LEFT JOIN {DB_TABLES['subjects']} sb
                ON sc.{DB_FIELDS['subject_id']} = sb.{DB_FIELDS['subject_id']}
            LEFT JOIN {DB_TABLES['instructors']} ins
                ON sc.{DB_FIELDS['instructor_id']} = ins.{DB_FIELDS['instructor_id']}
            LEFT JOIN {DB_TABLES['rooms']} rm
                ON sc.{DB_FIELDS['room_id']} = rm.{DB_FIELDS['room_id']}
            ORDER BY sc.{DB_FIELDS['day_of_week']},
                     sc.{DB_FIELDS['start_time']}
        """
        cursor.execute(query)
        schedules = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    for i, s1 in enumerate(schedules):
        validate_schedule(s1)

        day = s1[DB_FIELDS['day_of_week']]
        start1 = parse_time(s1[DB_FIELDS['start_time']])
        end1 = parse_time(s1[DB_FIELDS['end_time']])

        for s2 in schedules[i + 1:]:
            if day != s2[DB_FIELDS['day_of_week']]:
                continue

            validate_schedule(s2)

            start2 = parse_time(s2[DB_FIELDS['start_time']])
            end2 = parse_time(s2[DB_FIELDS['end_time']])

            if not schedules_overlap(start1, end1, start2, end2):
                continue

            if same_instructor(s1, s2):
                detect_instructor_conflict(
                    s1, s2, day, start1, end1, start2, end2
                )

            if same_room(s1, s2):
                detect_room_conflict(
                    s1, s2, day, start1, end1, start2, end2
                )

# ==========================================================
# ROUTES
# ==========================================================

@conflicts_bp.route('/')
def list_conflicts():
    if not is_admin():
        return redirect(url_for('login'))

    detect_and_save_conflicts()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT c.*,
                   s1.{DB_FIELDS['start_time']} AS s1_start,
                   s1.{DB_FIELDS['end_time']} AS s1_end,
                   s2.{DB_FIELDS['start_time']} AS s2_start,
                   s2.{DB_FIELDS['end_time']} AS s2_end
            FROM {DB_TABLES['conflicts']} c
            JOIN {DB_TABLES['schedules']} s1
                ON c.{DB_FIELDS['schedule1_id']} = s1.{DB_FIELDS['schedule_id']}
            JOIN {DB_TABLES['schedules']} s2
                ON c.{DB_FIELDS['schedule2_id']} = s2.{DB_FIELDS['schedule_id']}
            ORDER BY c.{DB_FIELDS['conflict_id']} DESC
        """
        cursor.execute(query)
        conflicts = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template("admin/conflicts.html", conflicts=conflicts)


@conflicts_bp.route('/resolve/<int:conflict_id>', methods=['POST'])
def resolve_conflict(conflict_id):
    if not is_admin():
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = (
            f"UPDATE {DB_TABLES['conflicts']} "
            f"SET {DB_FIELDS['status']} = %s "
            f"WHERE {DB_FIELDS['conflict_id']} = %s"
        )
        cursor.execute(query, (STATUS_TYPES['resolved'], conflict_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    flash(
        ERROR_MESSAGES['conflict_resolved'].format(conflict_id=conflict_id),
        FLASH_CATEGORIES['success']
    )
    return redirect(url_for('conflicts.list_conflicts'))

# ==========================================================
# TESTING & MANUAL VERIFICATION
# ==========================================================

if __name__ == "__main__":
    print("Interactive and automatic quick tests for conflicts_bp.py\n")

    schedule_a = {
        DB_FIELDS['schedule_id']: 1,
        DB_FIELDS['day_of_week']: 'Monday',
        DB_FIELDS['start_time']: '09:00:00',
        DB_FIELDS['end_time']: '10:00:00',
        DB_FIELDS['instructor_id']: 1,
        DB_FIELDS['room_id']: 101,
        DB_FIELDS['subject_name']: 'Math',
        DB_FIELDS['instructor_name']: 'John Doe',
        DB_FIELDS['room_number']: 'A101'
    }

    schedule_b = {
        DB_FIELDS['schedule_id']: 2,
        DB_FIELDS['day_of_week']: 'Monday',
        DB_FIELDS['start_time']: '09:30:00',
        DB_FIELDS['end_time']: '10:30:00',
        DB_FIELDS['instructor_id']: 1,
        DB_FIELDS['room_id']: 101,
        DB_FIELDS['subject_name']: 'Physics',
        DB_FIELDS['instructor_name']: 'John Doe',
        DB_FIELDS['room_number']: 'A101'
    }

    schedule_c = {
        DB_FIELDS['schedule_id']: 3,
        DB_FIELDS['day_of_week']: 'Monday',
        DB_FIELDS['start_time']: '10:30:00',
        DB_FIELDS['end_time']: '11:30:00',
        DB_FIELDS['instructor_id']: 2,
        DB_FIELDS['room_id']: 102,
        DB_FIELDS['subject_name']: 'Chemistry',
        DB_FIELDS['instructor_name']: 'Jane Smith',
        DB_FIELDS['room_number']: 'A102'
    }

    print("=== AUTOMATIC TESTS ===")

    start_a = parse_time(schedule_a[DB_FIELDS['start_time']])
    end_a = parse_time(schedule_a[DB_FIELDS['end_time']])
    start_b = parse_time(schedule_b[DB_FIELDS['start_time']])
    end_b = parse_time(schedule_b[DB_FIELDS['end_time']])
    start_c = parse_time(schedule_c[DB_FIELDS['start_time']])
    end_c = parse_time(schedule_c[DB_FIELDS['end_time']])

    print(f"Overlap A&B: {'PASS' if schedules_overlap(start_a, end_a, start_b, end_b) else 'FAIL'}")
    print(f"Overlap A&C: {'PASS' if not schedules_overlap(start_a, end_a, start_c, end_c) else 'FAIL'}")

    print(f"Same instructor A&B: {'PASS' if same_instructor(schedule_a, schedule_b) else 'FAIL'}")
    print(f"Same instructor A&C: {'PASS' if not same_instructor(schedule_a, schedule_c) else 'FAIL'}")

    print(f"Same room A&B: {'PASS' if same_room(schedule_a, schedule_b) else 'FAIL'}")
    print(f"Same room A&C: {'PASS' if not same_room(schedule_a, schedule_c) else 'FAIL'}")

    print("\nInteractive tests completed!")

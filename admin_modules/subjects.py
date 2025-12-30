"""Subjects management routes for the admin panel."""

# -------------------- Standard Imports --------------------
from contextlib import contextmanager
import re

# -------------------- Third-party Imports --------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector

# -------------------- Blueprint & Config --------------------
subjects_bp = Blueprint('subjects', __name__, url_prefix='/admin/subjects')

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

LOGIN_ROUTE = 'login'
LIST_SUBJECTS_ROUTE = 'subjects.list_subjects'

# ============================================================
# DATABASE LAYER
# ============================================================

@contextmanager
def db_cursor():
    """Provide a MySQL cursor with automatic commit and cleanup."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def query_db(query, args=(), one=False):
    """Execute a query and return result(s)."""
    with db_cursor() as cursor:
        cursor.execute(query, args)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            if one:
                return rows[0] if rows else None
            return rows

# ============================================================
# AUTHENTICATION & USER ROLE
# ============================================================

def is_admin():
    """Return True if current user is an admin."""
    return session.get('role') == 'admin'

# ============================================================
# CONTEXT PROCESSORS
# ============================================================

@subjects_bp.context_processor
def inject_instructor_name():
    """Inject instructor's name and image into templates."""
    if 'user_id' not in session:
        return {'instructor_name': None, 'instructor_image': None}

    instructor = query_db(
        "SELECT name, image FROM instructors WHERE instructor_id = %s",
        (session['user_id'],),
        one=True
    )

    return {
        'instructor_name': instructor['name'] if instructor else None,
        'instructor_image': instructor['image'] if instructor and instructor['image'] else None
    }

# ============================================================
# AJAX ENDPOINTS
# ============================================================

@subjects_bp.route('/subject-info')
def subject_info():
    code = request.args.get('code')
    if not code:
        return jsonify({})
    subject = query_db("SELECT name FROM subjects WHERE code = %s", (code,), one=True)
    return jsonify(subject or {})

@subjects_bp.route('/instructors-by-course')
def instructors_by_course():
    course = request.args.get('course')
    if not course:
        return jsonify([])
    instructors = query_db(
        "SELECT instructor_id, name FROM instructors WHERE program = %s", (course,)
    )
    return jsonify(instructors)

# ============================================================
# SUBJECT CRUD OPERATIONS
# ============================================================

def get_subject(subject_id):
    """Retrieve a single subject with instructor name."""
    return query_db("""
        SELECT s.*, i.name AS instructor_name
        FROM subjects s
        LEFT JOIN instructors i ON s.instructor_id = i.instructor_id
        WHERE s.subject_id = %s
    """, (subject_id,), one=True)

def get_all_subjects():
    """Retrieve all subjects with instructor names."""
    return query_db("""
        SELECT s.*, i.name AS instructor_name
        FROM subjects s
        LEFT JOIN instructors i ON s.instructor_id = i.instructor_id
    """)

@subjects_bp.route('/')
def list_subjects():
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))
    subjects = get_all_subjects()
    return render_template("admin/subjects.html", subjects=subjects)

@subjects_bp.route('/add', methods=['GET', 'POST'])
def add_subject():
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    instructors = query_db("SELECT instructor_id, name FROM instructors")
    courses = query_db("SELECT DISTINCT course_code, course_name, program FROM courses")

    if request.method == 'POST':
        query_db("""
            INSERT INTO subjects (code, name, units, year_level, section, course, instructor_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['code'],
            request.form['name'],
            request.form['units'],
            request.form['year_level'],
            request.form['section'],
            request.form['course'],
            request.form.get('instructor_id') or None
        ))
        flash("Subject added successfully")
        return redirect(url_for(LIST_SUBJECTS_ROUTE))

    return render_template("admin/add_subject.html", instructors=instructors, courses=courses)

@subjects_bp.route('/edit/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    subject = query_db("SELECT * FROM subjects WHERE subject_id=%s", (subject_id,), one=True)

    if request.method == 'POST':
        query_db("""
            UPDATE subjects
            SET code=%s, name=%s, units=%s, year_level=%s, section=%s, course=%s, instructor_id=%s
            WHERE subject_id=%s
        """, (
            request.form['code'],
            request.form['name'],
            request.form['units'],
            request.form['year_level'],
            request.form['section'],
            request.form['course'],
            request.form.get('instructor_id') or None,
            subject_id
        ))
        flash("Subject updated successfully")
        return redirect(url_for(LIST_SUBJECTS_ROUTE))

    return render_template("admin/edit_subject.html", subject=subject)

@subjects_bp.route('/delete/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))
    query_db("DELETE FROM subjects WHERE subject_id=%s", (subject_id,))
    flash("Subject deleted successfully")
    return redirect(url_for(LIST_SUBJECTS_ROUTE))

@subjects_bp.route('/view/<int:subject_id>')
def view_subject(subject_id):
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))
    subject = get_subject(subject_id)
    return render_template("admin/view_subject.html", subject=subject)

# ============================================================
# INPUT VALIDATION HELPERS
# ============================================================

def sanitize_subject_code(value):
    if not isinstance(value, str):
        return None
    value = value.strip().upper()
    return value if re.fullmatch(r"[A-Z0-9\-]{2,15}", value) else None

def sanitize_subject_name(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if re.fullmatch(r"[A-Za-z0-9\s\-&]{3,100}", value) else None

def validate_units(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= 10 else None

def sanitize_year_level(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= 5 else None

def sanitize_section(value):
    if not isinstance(value, str):
        return None
    value = value.strip().upper()
    return value if re.fullmatch(r"[A-Z0-9]{1,5}", value) else None

def sanitize_course_name(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if re.fullmatch(r"[A-Za-z\s&\-]{2,100}", value) else None

def sanitize_instructor_name(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if re.fullmatch(r"[A-Za-z\s\-']{2,100}", value) else None

# ============================================================
# TEST CASES (MATCHING YOUR FORMAT)
# ============================================================

if __name__ == "__main__":
    print("Interactive and automatic quick tests for subjects_routes.py\n")

    test_codes = ["CS101", "IT-202", "bad@", ""]
    for code in test_codes:
        print(f"Code test: '{code}' -> {sanitize_subject_code(code)}")

    test_names = ["Data Structures", "AI & ML", "@@@", ""]
    for name in test_names:
        print(f"Name test: '{name}' -> {sanitize_subject_name(name)}")

    test_units = ["3", "0", "11", "abc"]
    for unit in test_units:
        print(f"Units test: '{unit}' -> {validate_units(unit)}")

    test_years = ["1", "5", "0", "6"]
    for year in test_years:
        print(f"Year test: '{year}' -> {sanitize_year_level(year)}")

    test_sections = ["A", "B1", "SEC#", ""]
    for sec in test_sections:
        print(f"Section test: '{sec}' -> {sanitize_section(sec)}")

    test_instr = ["John Doe", "Anne-Marie O'Neill", "Dr123", ""]
    for i in test_instr:
        print(f"Instructor test: '{i}' -> {sanitize_instructor_name(i)}")

    print("\nAll tests completed!")


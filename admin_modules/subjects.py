"""Subjects management routes for the admin panel."""

# -------------------- Standard Imports --------------------
from contextlib import contextmanager

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


# -------------------- Database Context Manager --------------------
@contextmanager
def db_cursor():
    """Provide a MySQL cursor with automatic commit and cleanup."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# -------------------- Helper Functions --------------------
def is_admin():
    """Return True if current user is an admin."""
    return session.get('role') == 'admin'


def query_db(query, args=(), one=False):
    """Execute a query and return result(s)."""
    with db_cursor() as cursor:
        cursor.execute(query, args)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            if one:
                if rows:
                    return rows[0]
                return None
            return rows


# -------------------- Context Processor --------------------
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

    name = instructor['name'] if instructor else None
    image = instructor['image'] if instructor and instructor['image'] else None
    return {'instructor_name': name, 'instructor_image': image}


# -------------------- AJAX Endpoints --------------------
@subjects_bp.route('/subject-info')
def subject_info():
    """Return JSON info for a given subject code."""
    code = request.args.get('code')
    if not code:
        return jsonify({})

    subject = query_db("SELECT name FROM subjects WHERE code = %s", (code,), one=True)
    if subject:
        return jsonify(subject)
    return jsonify({})


@subjects_bp.route('/instructors-by-course')
def instructors_by_course():
    """Return JSON list of instructors for a given course/program."""
    course = request.args.get('course')
    if not course:
        return jsonify([])

    instructors = query_db(
        "SELECT instructor_id, name FROM instructors WHERE program = %s", (course,)
    )
    return jsonify(instructors)


# -------------------- Subject CRUD --------------------
@subjects_bp.route('/')
def list_subjects():
    """List all subjects (admin only)."""
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    subjects = query_db("""
        SELECT s.*, i.name AS instructor_name
        FROM subjects s
        LEFT JOIN instructors i ON s.instructor_id = i.instructor_id
    """)
    return render_template("admin/subjects.html", subjects=subjects)


@subjects_bp.route('/add', methods=['GET', 'POST'])
def add_subject():
    """Add a new subject (admin only)."""
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    instructors = query_db("SELECT instructor_id, name FROM instructors")
    courses = query_db("SELECT DISTINCT course_code, course_name, program FROM courses")
    subjects = query_db("SELECT code, units, year_level, section FROM subjects")

    # Unique programs
    programs_raw = query_db("SELECT program FROM courses")
    programs = []
    seen = set()
    for row in programs_raw:
        if row['program'] not in seen:
            programs.append({'program': row['program']})
            seen.add(row['program'])

    # Other dropdown options
    units_list = [row['units'] for row in query_db("SELECT DISTINCT units FROM subjects")]
    year_levels_list = [row['year_level'] for row in query_db("SELECT DISTINCT year_level FROM subjects")]
    sections_list = [row['section'] for row in query_db("SELECT DISTINCT section FROM subjects")]

    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        units = request.form['units']
        year_level = request.form['year_level']
        section = request.form['section']
        course = request.form['course']
        instructor_id = request.form.get('instructor_id') or None

        query_db("""
            INSERT INTO subjects (code, name, units, year_level, section, course, instructor_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (code, name, units, year_level, section, course, instructor_id))

        flash("Subject added successfully")
        return redirect(url_for(LIST_SUBJECTS_ROUTE))

    return render_template(
        "admin/add_subject.html",
        instructors=instructors,
        courses=courses,
        programs=programs,
        subjects=subjects,
        units_list=units_list,
        year_levels_list=year_levels_list,
        sections_list=sections_list
    )


@subjects_bp.route('/edit/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    """Edit an existing subject (admin only)."""
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    instructors = query_db("SELECT instructor_id, name, program FROM instructors")
    courses = query_db("SELECT DISTINCT course_code, course_name, program FROM courses")

    # Unique programs
    programs_raw = query_db("SELECT program FROM courses")
    programs = []
    seen = set()
    for row in programs_raw:
        if row['program'] not in seen:
            programs.append({'program': row['program']})
            seen.add(row['program'])

    # Other dropdown options
    units_list = [row['units'] for row in query_db("SELECT DISTINCT units FROM subjects")]
    year_levels_list = [row['year_level'] for row in query_db("SELECT DISTINCT year_level FROM subjects")]
    sections_list = [row['section'] for row in query_db("SELECT DISTINCT section FROM subjects")]

    subject = query_db("SELECT * FROM subjects WHERE subject_id = %s", (subject_id,), one=True)

    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        units = request.form['units']
        year_level = request.form['year_level']
        section = request.form['section']
        course = request.form['course']
        instructor_id = request.form.get('instructor_id') or None

        query_db("""
            UPDATE subjects
            SET code=%s, name=%s, units=%s, year_level=%s, section=%s, course=%s, instructor_id=%s
            WHERE subject_id=%s
        """, (code, name, units, year_level, section, course, instructor_id, subject_id))

        flash("Subject updated successfully")
        return redirect(url_for(LIST_SUBJECTS_ROUTE))

    return render_template(
        "admin/edit_subject.html",
        subject=subject,
        instructors=instructors,
        courses=courses,
        programs=programs,
        units_list=units_list,
        year_levels_list=year_levels_list,
        sections_list=sections_list
    )


@subjects_bp.route('/delete/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    """Delete a subject (admin only)."""
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    query_db("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
    flash("Subject deleted successfully")
    return redirect(url_for(LIST_SUBJECTS_ROUTE))


@subjects_bp.route('/view/<int:subject_id>')
def view_subject(subject_id):
    """View details of a single subject (admin only)."""
    if not is_admin():
        return redirect(url_for(LOGIN_ROUTE))

    subject = query_db("""
        SELECT s.*, i.name AS instructor_name
        FROM subjects s
        LEFT JOIN instructors i ON s.instructor_id = i.instructor_id
        WHERE s.subject_id = %s
    """, (subject_id,), one=True)

    return render_template("admin/view_subject.html", subject=subject)

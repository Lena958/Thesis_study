"""
Courses blueprint for managing courses in the admin panel.
Includes listing, adding, editing, and deleting courses.
"""

# ==================================================
# 1. Imports
# ==================================================
from datetime import datetime
import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# ==================================================
# 2. Blueprint Definition
# ==================================================
courses_bp = Blueprint('courses', __name__, url_prefix='/admin/courses')

# ==================================================
# 3. Database Configuration
# ==================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

COURSES_LIST_ROUTE = 'courses.list_courses'  # Constant for repeated redirect target


def get_db_connection():
    """Return a new database connection."""
    return mysql.connector.connect(**DB_CONFIG)


# ==================================================
# 4. Utility Functions
# ==================================================
def is_admin():
    """Return True if current session user is an admin."""
    return session.get('role') == 'admin'


def get_school_years():
    """Return a list of school years from DB or generate next 5 years."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT school_year FROM courses ORDER BY school_year DESC")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        return [row['school_year'] for row in rows if row['school_year']]
    current_year = datetime.now().year
    return [f"{y}-{y+1}" for y in range(current_year, current_year + 5)]


def get_instructor_info(user_id):
    """Fetch instructor name and image for sidebar."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, image FROM instructors WHERE instructor_id = %s",
        (user_id,)
    )
    instructor = cursor.fetchone()
    conn.close()
    return {
        'instructor_name': instructor['name'] if instructor else None,
        'instructor_image': instructor['image'] if instructor and instructor['image'] else None
    }


def fetch_distinct_values(field):
    """Fetch distinct values of a column from courses table."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT DISTINCT {field} FROM courses ORDER BY {field} ASC")
    values = [row[field] for row in cursor.fetchall() if row[field]]
    conn.close()
    return values


def fetch_courses(filters=None):
    """Fetch courses based on optional filters."""
    filters = filters or {}
    query = (
        "SELECT course_id, course_code, course_name, course_type, school_year "
        "FROM courses WHERE 1=1"
    )
    params = []

    for field in ['program', 'school_year', 'semester', 'course_type']:
        if filters.get(field):
            query += f" AND {field} = %s"
            params.append(filters[field])

    query += " ORDER BY course_code ASC"
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, tuple(params))
    courses = cursor.fetchall()
    conn.close()
    return courses


def get_course_by_id(course_id):
    """Fetch a single course by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
    course = cursor.fetchone()
    conn.close()
    return course


def save_course(course_data, course_id=None):
    """Insert or update a course depending on presence of course_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if course_id:
        query = (
            "UPDATE courses "
            "SET course_code=%s, course_name=%s, program=%s, "
            "school_year=%s, semester=%s, course_type=%s "
            "WHERE course_id=%s"
        )
        params = (*course_data.values(), course_id)
    else:
        query = (
            "INSERT INTO courses (course_code, course_name, program, school_year, semester, course_type) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        params = tuple(course_data.values())

    cursor.execute(query, params)
    conn.commit()
    conn.close()


# ==================================================
# 5. Context Processor
# ==================================================
@courses_bp.context_processor
def inject_instructor_name():
    """Inject instructor info into templates."""
    if 'user_id' not in session:
        return {'instructor_name': None, 'instructor_image': None}
    return get_instructor_info(session['user_id'])


# ==================================================
# 6. Routes
# ==================================================
@courses_bp.route('/', methods=['GET', 'POST'])
def list_courses():
    """List all courses with optional filters."""
    if not is_admin():
        return redirect(url_for('login'))

    filters = {
        field: request.form.get(field)
        for field in ['program', 'school_year', 'semester', 'course_type']
    } if request.method == 'POST' else {}

    context = {
        'courses': fetch_courses(filters),
        'programs': fetch_distinct_values('program'),
        'school_years': get_school_years(),
        'semesters': fetch_distinct_values('semester'),
        'course_types': fetch_distinct_values('course_type'),
        **{f'selected_{k}': v for k, v in filters.items()}
    }
    return render_template('admin/courses.html', **context)


@courses_bp.route('/add', methods=['GET', 'POST'])
def add_course():
    """Add a new course."""
    if not is_admin():
        return redirect(url_for('login'))

    context = {
        'course_types': ['Major', 'GEC', 'GEE'],
        'school_years': get_school_years(),
        'programs': fetch_distinct_values('program')
    }

    if request.method == 'POST':
        course_data = {
            k: request.form.get(k, '').strip()
            for k in ['course_code', 'course_name', 'program', 'school_year', 'semester', 'course_type']
        }
        if not all(course_data.values()):
            flash("⚠️ All fields are required.", "danger")
            return redirect(url_for('courses.add_course'))

        save_course(course_data)
        flash("✅ Course added successfully.", "success")
        return redirect(url_for(COURSES_LIST_ROUTE))

    return render_template('admin/add_course.html', **context)


@courses_bp.route('/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    """Edit an existing course."""
    if not is_admin():
        return redirect(url_for('login'))

    course = get_course_by_id(course_id)
    if not course:
        flash("⚠️ Course not found.", "danger")
        return redirect(url_for(COURSES_LIST_ROUTE))

    context = {
        'course': course,
        'course_types': ['Major', 'GEC', 'GEE'],
        'school_years': get_school_years(),
        'programs': fetch_distinct_values('program')
    }

    if request.method == 'POST':
        course_data = {
            k: request.form.get(k, '').strip()
            for k in ['course_code', 'course_name', 'program', 'school_year', 'semester', 'course_type']
        }
        if not all(course_data.values()):
            flash("⚠️ All fields are required.", "danger")
            return redirect(url_for('courses.edit_course', course_id=course_id))

        try:
            save_course(course_data, course_id=course_id)
            flash("✅ Course updated successfully.", "success")
        except mysql.connector.Error as e:
            flash(f"❌ Database error updating course: {e}", "danger")

        return redirect(url_for(COURSES_LIST_ROUTE))

    return render_template('admin/edit_course.html', **context)


@courses_bp.route('/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    """Delete a course."""
    if not is_admin():
        return redirect(url_for('login'))

    course = get_course_by_id(course_id)
    if not course:
        flash("⚠️ Course not found.", "danger")
        return redirect(url_for(COURSES_LIST_ROUTE))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
        conn.commit()
        conn.close()
        flash("🗑️ Course deleted successfully.", "success")
    except mysql.connector.Error as e:
        flash(f"❌ Database error deleting course: {e}", "danger")

    return redirect(url_for(COURSES_LIST_ROUTE))
# ... [rest of your courses_bp code stays the same] ...

# ==================================================
# 7. QUICK AUTOMATIC AND INTERACTIVE TESTS
# ==================================================

if __name__ == "__main__":
    print("Interactive and automatic quick tests for courses_bp.py\n")

    # ----------------------------
    # AUTOMATIC INPUT VALIDATION TESTS
    # ----------------------------
    test_courses = [
        {
            'course_code': 'CS101',
            'course_name': 'Intro to CS',
            'program': 'Computer Science',
            'school_year': '2025-2026',
            'semester': '1',
            'course_type': 'Major'
        },
        {
            'course_code': '',  # Missing field
            'course_name': 'Data Structures',
            'program': 'Computer Science',
            'school_year': '2025-2026',
            'semester': '1',
            'course_type': 'Major'
        },
        {
            'course_code': 'MATH200',
            'course_name': '',
            'program': 'Math',
            'school_year': '2025-2026',
            'semester': '2',
            'course_type': 'GEC'
        }
    ]

    for i, course in enumerate(test_courses, start=1):
        print(f"Test course #{i}: ", end='')
        if all(course.values()):
            print("PASS")
        else:
            print(f"FAIL (missing fields: {[k for k, v in course.items() if not v]})")

    # ----------------------------
    # AUTOMATIC SAVE/RETRIEVE TEST (mocked, no DB commit)
    # ----------------------------
    try:
        print("\nTesting fetch_distinct_values and fetch_courses...")
        programs = fetch_distinct_values('program')
        print(f"Distinct programs fetched: {programs} -> PASS")
        courses = fetch_courses()
        print(f"Total courses fetched: {len(courses)} -> PASS")
    except Exception as e:
        print(f"FAIL ({e})")

    # ----------------------------
    # INTERACTIVE TESTS
    # ----------------------------
    print("\n=== INTERACTIVE TESTS ===")
    course_code = input("Enter course code to test validation: ").strip()
    course_name = input("Enter course name to test validation: ").strip()
    program = input("Enter program to test validation: ").strip()
    school_year = input("Enter school year to test validation: ").strip()
    semester = input("Enter semester to test validation: ").strip()
    course_type = input("Enter course type (Major/GEC/GEE) to test validation: ").strip()

    test_course = {
        'course_code': course_code,
        'course_name': course_name,
        'program': program,
        'school_year': school_year,
        'semester': semester,
        'course_type': course_type
    }

    if all(test_course.values()):
        print(f"Validation PASS -> {test_course}")
    else:
        missing = [k for k, v in test_course.items() if not v]
        print(f"Validation FAIL, missing fields: {missing}")

    print("\nInteractive tests completed!")


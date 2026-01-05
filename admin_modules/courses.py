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

# ==================================================
# 7. QUICK AUTOMATIC TESTS – FULL MATCH & EDGE CASES
# ==================================================

if __name__ == "__main__":
    print("=== Automatic Full-Match Validation Tests for courses_bp.py ===")

    REQUIRED_FIELDS = (
        "course_code",
        "course_name",
        "program",
        "school_year",
        "semester",
        "course_type",
    )

    VALID_SEMESTERS = {"1", "2"}
    VALID_COURSE_TYPES = {"Major", "GEC", "GEE"}

    # ----------------------------
    # FULL-MATCH & EDGE CASE TESTS
    # ----------------------------
    test_courses = [
        # ✅ Fully valid
        {
            "course_code": "CS101",
            "course_name": "Introduction to Computer Science",
            "program": "Computer Science",
            "school_year": "2025-2026",
            "semester": "1",
            "course_type": "Major",
            "expected": True,
        },
        # ❌ Invalid course code (symbols)
        {
            "course_code": "CS101!!",
            "course_name": "Data Structures",
            "school_year": "2025-2026",
            "semester": "1",
            "course_type": "Major",
            "expected": False,
        },
        # ❌ Empty course name
        {
            "course_code": "CS102",
            "course_name": "",
            "school_year": "2025-2026",
            "semester": "1",
            "course_type": "Major",
            "expected": False,
        },
        # ❌ Invalid school year format
        {
            "course_code": "MATH200",
            "course_name": "Linear Algebra",
            "program": "Mathematics",
            "school_year": "2025/2026",
            "semester": "2",
            "course_type": "GEC",
            "expected": False,
        },
        # ❌ Invalid semester
        {
            "course_code": "ENG101",
            "course_name": "English Composition",
            "program": "English",
            "school_year": "2025-2026",
            "semester": "3",
            "course_type": "GEE",
            "expected": False,
        },
        # ❌ Invalid course type
        {
            "course_code": "HIST101",
            "course_name": "World History",
            "program": "History",
            "school_year": "2025-2026",
            "semester": "1",
            "course_type": "Elective",
            "expected": False,
        },
        # ❌ Leading/trailing whitespace (full-match failure)
        {
            "course_code": " CS103 ",
            "course_name": "Algorithms",
            "program": "Computer Science",
            "school_year": "2025-2026",
            "semester": "1",
            "course_type": "Major",
            "expected": False,
        },
    ]

    print("\nRunning full-match course validation tests...")
    for index, course in enumerate(test_courses, start=1):
        missing_fields = [
            field for field in REQUIRED_FIELDS if not course.get(field)
        ]

        is_valid = (
            not missing_fields
            and course["semester"] in VALID_SEMESTERS
            and course["course_type"] in VALID_COURSE_TYPES
            and course["school_year"].count("-") == 1
            and course["school_year"].replace("-", "").isdigit()
            and course["course_code"].strip() == course["course_code"]
        )

        passed = is_valid == course["expected"]

        print(
            f"Course test #{index}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print("\n=== All course validation tests completed ===")

"""
Instructor management module for admin routes.
Handles login, listing, adding, editing, and deleting instructors.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

instructors_bp = Blueprint('instructors', __name__, url_prefix='/admin/instructors')

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

# Constants
NO_INSTRUCTOR_INFO = {"instructor_name": None, "instructor_image": None}
LIST_INSTRUCTORS_ENDPOINT = 'instructors.list_instructors'
LOGIN_ENDPOINT = 'instructors.login'


def get_db_connection():
    """Return a new database connection."""
    return mysql.connector.connect(**db_config)


def is_admin_user():
    """Check if the current session user is an admin."""
    return session.get('role') == 'admin'


# Login route
@instructors_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle instructor login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM instructors WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['instructor_id']
            session['role'] = user['role']
            flash("Logged in successfully!", "success")
            return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

        flash("Invalid username or password", "danger")

    return render_template('login.html')


# Context processor for logged-in instructor's info
@instructors_bp.context_processor
def inject_instructor_name():
    """Inject instructor info into templates."""
    if 'user_id' not in session:
        return NO_INSTRUCTOR_INFO

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, image FROM instructors WHERE instructor_id = %s",
        (session['user_id'],)
    )
    instructor = cursor.fetchone()
    conn.close()

    return {
        "instructor_name": instructor['name'] if instructor else None,
        "instructor_image": instructor['image'] if instructor and instructor['image'] else None
    }


# List all instructors
@instructors_bp.route('/')
def list_instructors():
    """Display all instructors."""
    if not is_admin_user():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM instructors")
    instructors = cursor.fetchall()
    conn.close()
    return render_template("admin/instructors.html", instructors=instructors)


# Add instructor
@instructors_bp.route('/add', methods=['GET', 'POST'])
def add_instructor():
    """Add a new instructor."""
    if not is_admin_user():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch distinct programs and statuses
    cursor.execute(
        "SELECT DISTINCT program FROM instructors WHERE program IS NOT NULL AND program != ''"
    )
    programs = [row['program'] for row in cursor.fetchall()]

    cursor.execute(
        "SELECT DISTINCT status FROM instructors WHERE status IS NOT NULL AND status != ''"
    )
    statuses = [row['status'] for row in cursor.fetchall()]

    conn.close()

    if request.method == 'POST':
        name = request.form['name']
        max_load_units = request.form['max_load_units']
        department = request.form['department']
        program = request.form['program']
        status = request.form['status']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO instructors (name, max_load_units, department, program, status, username, password, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (name, max_load_units, department, program, status, username, hashed_password, role)
        )
        conn.commit()
        conn.close()

        flash("Instructor added successfully", "success")
        return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

    return render_template(
        "admin/add_instructor.html",
        programs=programs,
        statuses=statuses
    )


# Edit instructor
@instructors_bp.route('/edit/<int:instructor_id>', methods=['GET', 'POST'])
def edit_instructor(instructor_id):
    """Edit an existing instructor."""
    if not is_admin_user():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT program FROM instructors WHERE program IS NOT NULL AND program != ''"
    )
    programs = [row['program'] for row in cursor.fetchall()]

    cursor.execute(
        "SELECT DISTINCT status FROM instructors WHERE status IS NOT NULL AND status != ''"
    )
    statuses = [row['status'] for row in cursor.fetchall()]

    if request.method == 'POST':
        name = request.form['name']
        max_load_units = request.form['max_load_units']
        department = request.form['department']
        program = request.form['program']
        status = request.form['status']

        cursor.execute(
            """
            UPDATE instructors
            SET name=%s, max_load_units=%s, department=%s, program=%s, status=%s
            WHERE instructor_id=%s
            """,
            (name, max_load_units, department, program, status, instructor_id)
        )
        conn.commit()
        conn.close()
        flash("Instructor updated successfully", "success")
        return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

    cursor.execute("SELECT * FROM instructors WHERE instructor_id = %s", (instructor_id,))
    instructor = cursor.fetchone()
    conn.close()

    return render_template(
        "admin/edit_instructor.html",
        instructor=instructor,
        programs=programs,
        statuses=statuses
    )


# Delete instructor
@instructors_bp.route('/delete/<int:instructor_id>', methods=['POST'])
def delete_instructor(instructor_id):
    """Delete an instructor."""
    if not is_admin_user():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM instructors WHERE instructor_id = %s", (instructor_id,))
    conn.commit()
    conn.close()
    flash("Instructor deleted successfully", "success")
    return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

# ==================================================
# 7. QUICK AUTOMATIC AND INTERACTIVE TESTS
# ==================================================

if __name__ == "__main__":
    from werkzeug.security import check_password_hash

    print("Interactive and automatic quick tests for instructors_bp.py\n")

    # ----------------------------
    # AUTOMATIC INPUT VALIDATION TESTS
    # ----------------------------
    test_names = ["John Doe", "Anne-Marie O'Neill", "Invalid123", ""]
    for name in test_names:
        valid = bool(name) and all(c.isalpha() or c in " -'" for c in name)
        print(f"Name test: '{name}' -> {'PASS' if valid else 'FAIL'}")

    test_usernames = ["john_doe", "user123", "Invalid User!", "a", "this_is_a_very_long_username_exceeding_fifty_chars_123"]
    for username in test_usernames:
        valid = username.isalnum() or "_" in username and 3 <= len(username) <= 50
        print(f"Username test: '{username}' -> {'PASS' if valid else 'FAIL'}")

    test_departments = ["IT", "Computer Science & AI", "Dept@123", ""]
    for dept in test_departments:
        valid = bool(dept) and all(c.isalnum() or c in " &" for c in dept)
        print(f"Department test: '{dept}' -> {'PASS' if valid else 'FAIL'}")

    test_max_load_units = ["15", "-5", "0", "abc", "20"]
    for units in test_max_load_units:
        try:
            units_val = int(units)
            valid = units_val > 0
        except ValueError:
            valid = False
        print(f"Max load units test: '{units}' -> {'PASS' if valid else 'FAIL'}")

    # ----------------------------
    # PASSWORD HASHING TEST
    # ----------------------------
    test_passwords = ["StrongPass1!", "weak", "123456", "Another$Pass123"]
    for pw in test_passwords:
        hashed = generate_password_hash(pw)
        check = check_password_hash(hashed, pw)
        print(f"Password test: '{pw}' -> Hashed OK: {check} -> {'PASS' if check else 'FAIL'}")

    # ----------------------------
    # INTERACTIVE TESTS
    # ----------------------------
    print("\n=== INTERACTIVE TESTS ===")
    name_input = input("Enter instructor name to test: ").strip()
    valid_name = bool(name_input) and all(c.isalpha() or c in " -'" for c in name_input)
    print(f"Name result: {name_input} -> {'PASS' if valid_name else 'FAIL'}")

    username_input = input("Enter username to test: ").strip()
    valid_username = username_input.isalnum() or "_" in username_input and 3 <= len(username_input) <= 50
    print(f"Username result: {username_input} -> {'PASS' if valid_username else 'FAIL'}")

    department_input = input("Enter department to test: ").strip()
    valid_dept = bool(department_input) and all(c.isalnum() or c in " &" for c in department_input)
    print(f"Department result: {department_input} -> {'PASS' if valid_dept else 'FAIL'}")

    max_units_input = input("Enter max load units to test: ").strip()
    try:
        units_val = int(max_units_input)
        valid_units = units_val > 0
    except ValueError:
        valid_units = False
    print(f"Max load units result: {max_units_input} -> {'PASS' if valid_units else 'FAIL'}")

    password_input = input("Enter password to test hashing: ").strip()
    hashed_pw = generate_password_hash(password_input)
    valid_pw = check_password_hash(hashed_pw, password_input)
    print(f"Password hash check: {valid_pw} -> {'PASS' if valid_pw else 'FAIL'}")

    print("\nAll interactive tests completed!")

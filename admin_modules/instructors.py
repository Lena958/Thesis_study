"""
Instructor management module for admin routes.
Handles login, listing, adding, editing, and deleting instructors.
"""

# ==================================================
# 1. Imports
# ==================================================
import mysql.connector
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash


# ==================================================
# 2. Blueprint Definition
# ==================================================
instructors_bp = Blueprint(
    "instructors",
    __name__,
    url_prefix="/admin/instructors",
)


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
# 4. Constants
# ==================================================
NO_INSTRUCTOR_INFO = {
    "instructor_name": None,
    "instructor_image": None,
}

LIST_INSTRUCTORS_ENDPOINT = "instructors.list_instructors"
LOGIN_ENDPOINT = "instructors.login"


# ==================================================
# 5. Database & Auth Helpers
# ==================================================
def get_db_connection():
    """Return a new database connection."""
    return mysql.connector.connect(**DB_CONFIG)


def is_admin():
    """Return True if current session user is an admin."""
    return session.get("role") == "admin"


# ==================================================
# 6. Context Processor
# ==================================================
@instructors_bp.context_processor
def inject_instructor_name():
    """Inject instructor info into templates."""
    if "user_id" not in session:
        return NO_INSTRUCTOR_INFO

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, image FROM instructors WHERE instructor_id = %s",
        (session["user_id"],),
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
# 7. Authentication Routes
# ==================================================
@instructors_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle instructor login."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM instructors WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["instructor_id"]
            session["role"] = user["role"]
            flash("Logged in successfully.", "success")
            return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# ==================================================
# 8. Instructor CRUD Routes
# ==================================================
@instructors_bp.route("/")
def list_instructors():
    """List all instructors."""
    if not is_admin():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM instructors")
    instructors = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "admin/instructors.html",
        instructors=instructors,
    )


@instructors_bp.route("/add", methods=["GET", "POST"])
def add_instructor():
    """Add a new instructor."""
    if not is_admin():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT program FROM instructors "
        "WHERE program IS NOT NULL AND program != ''"
    )
    programs = [row["program"] for row in cursor.fetchall()]

    cursor.execute(
        "SELECT DISTINCT status FROM instructors "
        "WHERE status IS NOT NULL AND status != ''"
    )
    statuses = [row["status"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    if request.method == "POST":
        data = {
            "name": request.form.get("name", "").strip(),
            "max_load_units": request.form.get("max_load_units"),
            "department": request.form.get("department", "").strip(),
            "program": request.form.get("program", "").strip(),
            "status": request.form.get("status", "").strip(),
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", ""),
            "role": request.form.get("role", "").strip(),
        }

        hashed_password = generate_password_hash(data["password"])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO instructors
            (name, max_load_units, department, program, status,
             username, password, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["name"],
                data["max_load_units"],
                data["department"],
                data["program"],
                data["status"],
                data["username"],
                hashed_password,
                data["role"],
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Instructor added successfully.", "success")
        return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

    return render_template(
        "admin/add_instructor.html",
        programs=programs,
        statuses=statuses,
    )


@instructors_bp.route("/edit/<int:instructor_id>", methods=["GET", "POST"])
def edit_instructor(instructor_id):
    """Edit an existing instructor."""
    if not is_admin():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT program FROM instructors "
        "WHERE program IS NOT NULL AND program != ''"
    )
    programs = [row["program"] for row in cursor.fetchall()]

    cursor.execute(
        "SELECT DISTINCT status FROM instructors "
        "WHERE status IS NOT NULL AND status != ''"
    )
    statuses = [row["status"] for row in cursor.fetchall()]

    if request.method == "POST":
        cursor.execute(
            """
            UPDATE instructors
            SET name=%s, max_load_units=%s, department=%s,
                program=%s, status=%s
            WHERE instructor_id=%s
            """,
            (
                request.form.get("name"),
                request.form.get("max_load_units"),
                request.form.get("department"),
                request.form.get("program"),
                request.form.get("status"),
                instructor_id,
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Instructor updated successfully.", "success")
        return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))

    cursor.execute(
        "SELECT * FROM instructors WHERE instructor_id = %s",
        (instructor_id,),
    )
    instructor = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template(
        "admin/edit_instructor.html",
        instructor=instructor,
        programs=programs,
        statuses=statuses,
    )


@instructors_bp.route("/delete/<int:instructor_id>", methods=["POST"])
def delete_instructor(instructor_id):
    """Delete an instructor."""
    if not is_admin():
        return redirect(url_for(LOGIN_ENDPOINT))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM instructors WHERE instructor_id = %s",
        (instructor_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("Instructor deleted successfully.", "success")
    return redirect(url_for(LIST_INSTRUCTORS_ENDPOINT))


# ==================================================
# 9. QUICK AUTOMATIC AND INTERACTIVE TESTS
# ==================================================
if __name__ == "__main__":
    print("Interactive and automatic quick tests for instructors_bp.py\n")

    test_instructors = [
        {"name": "Alice Johnson", "program": "Math", "loads": 3, "status": "active"},
        {"name": "", "program": "Science", "loads": 2, "status": "active"},
        {"name": "Bob Smith", "program": "", "loads": 0, "status": "inactive"},
        {"name": "Carol Lee", "program": "History", "loads": 5, "status": "active"},
    ]

    valid_statuses = {"active", "inactive"}

    for inst in test_instructors:
        name_valid = bool(inst["name"].strip())
        program_valid = bool(inst["program"].strip())
        loads_valid = isinstance(inst["loads"], int) and inst["loads"] >= 0
        status_valid = inst["status"] in valid_statuses

        all_valid = name_valid and program_valid and loads_valid and status_valid
        print(
            f"Instructor test '{inst['name']}' -> "
            f"{'PASS' if all_valid else 'FAIL'} "
            f"(Name: {'OK' if name_valid else 'FAIL'}, "
            f"Program: {'OK' if program_valid else 'FAIL'}, "
            f"Loads: {'OK' if loads_valid else 'FAIL'}, "
            f"Status: {'OK' if status_valid else 'FAIL'})"
        )

    print("\nAll tests completed.")

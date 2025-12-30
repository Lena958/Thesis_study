"""Instructor profile management routes."""

from flask import Blueprint, render_template, session, redirect, url_for, flash
import mysql.connector
from contextlib import contextmanager
from mysql.connector.cursor import MySQLCursorDict

profile_bp = Blueprint('profile', __name__, url_prefix='/instructor')

# ------------------------
# Constants
# ------------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}
LOGIN_ROUTE = 'login'


# ------------------------
# Database context manager
# ------------------------

@contextmanager
def db_cursor():
    """Context manager for MySQL dictionary cursor."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = MySQLCursorDict(conn)
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()


# ------------------------
# Context processor for sidebar
# ------------------------
@profile_bp.context_processor
def inject_instructor_info():
    """Inject instructor name and image for templates."""
    if 'user_id' not in session:
        return {'instructor_name': None, 'instructor_image': None}

    with db_cursor() as cursor:
        cursor.execute(
            "SELECT name, image FROM instructors WHERE instructor_id = %s",
            (session['user_id'],)
        )
        instructor = cursor.fetchone()

    return {
        'instructor_name': instructor['name'] if instructor else None,
        'instructor_image': instructor['image'] if instructor and instructor['image'] else None
    }


# ------------------------
# Profile view
# ------------------------
@profile_bp.route('/profile')
def profile():
    """Display the logged-in instructor's profile."""
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for(LOGIN_ROUTE))

    with db_cursor() as cursor:
        cursor.execute(
            "SELECT instructor_id, name, max_load_units, department, username, role "
            "FROM instructors WHERE instructor_id = %s",
            (session['user_id'],)
        )
        instructor = cursor.fetchone()

    if not instructor:
        flash("Instructor not found.", "danger")
        return redirect(url_for(LOGIN_ROUTE))

    return render_template('admin/profile.html', instructor=instructor)


# ============================================================
# ADDITIONAL INPUT VALIDATION & ERROR HANDLING (SAFE ADD-ON)
# ============================================================

import re


def sanitize_input(value, field_type):
    """
    Validate and sanitize string inputs based on field type.
    Returns sanitized value or None if invalid.
    """
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    patterns = {
        "name": r"^[A-Za-z\s\-']{2,100}$",
        "username": r"^[A-Za-z0-9_]{3,50}$",
        "department": r"^[A-Za-z\s&]{2,100}$"
    }

    pattern = patterns.get(field_type)
    if not pattern:
        return None

    if not re.fullmatch(pattern, value):
        return None

    return value


def validate_password_strength(password):
    """
    Validate password strength.
    Returns (True, message) or (False, reason).
    """
    if not isinstance(password, str):
        return False, "Password must be a string"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, "Password is strong"


def validate_load_units(units):
    """
    Validate max load units.
    Returns integer value or None if invalid.
    """
    try:
        units = int(units)
    except (TypeError, ValueError):
        return None

    if 1 <= units <= 100:
        return units

    return None


# ============================================================
# TEST CASES (Standalone – Matches Provided Format)
# ============================================================

if __name__ == "__main__":
    print("Interactive and automatic quick tests for profile_routes.py\n")

    # ----------------------------
    # SANITIZE INPUT TESTS
    # ----------------------------
    test_names = ["John Doe", "Anne-Marie O'Neill", "Invalid123", ""]
    for name in test_names:
        result = sanitize_input(name, "name")
        print(f"Name test: '{name}' -> {result} -> {'PASS' if result else 'FAIL'}")

    test_usernames = [
        "john_doe", "user123", "Invalid User!", "a",
        "this_is_a_very_long_username_exceeding_fifty_chars_123"
    ]
    for username in test_usernames:
        result = sanitize_input(username, "username")
        print(f"Username test: '{username}' -> {result} -> {'PASS' if result else 'FAIL'}")

    test_departments = ["IT", "Computer Science & AI", "Dept@123", ""]
    for dept in test_departments:
        result = sanitize_input(dept, "department")
        print(f"Department test: '{dept}' -> {result} -> {'PASS' if result else 'FAIL'}")

    # ----------------------------
    # PASSWORD STRENGTH TESTS
    # ----------------------------
    test_passwords = [
        "Abc123!@", "weakpass", "NoNumber!",
        "noupper1!", "NOLOWER1!", "Short1!", "ValidPass1!"
    ]
    for pw in test_passwords:
        valid, message = validate_password_strength(pw)
        print(f"Password test: '{pw}' -> Valid: {valid}, Message: {message} -> {'PASS' if valid else 'FAIL'}")

    # ----------------------------
    # LOAD UNITS TESTS
    # ----------------------------
    test_load_units = ["50", "-5", "200", "0", "100", "abc"]
    for units in test_load_units:
        result = validate_load_units(units)
        print(f"Load units test: '{units}' -> {result} -> {'PASS' if result is not None else 'FAIL'}")

    # ----------------------------
    # INTERACTIVE TESTS
    # ----------------------------
    print("\nNow you can try interactive input tests:")

    name_input = input("Enter a name to test sanitize_input: ")
    result = sanitize_input(name_input, "name")
    print(f"Result: {result} -> {'PASS' if result else 'FAIL'}")

    username_input = input("Enter a username to test sanitize_input: ")
    result = sanitize_input(username_input, "username")
    print(f"Result: {result} -> {'PASS' if result else 'FAIL'}")

    password_input = input("Enter a password to test validate_password_strength: ")
    valid, message = validate_password_strength(password_input)
    print(f"Valid: {valid}, Message: {message} -> {'PASS' if valid else 'FAIL'}")

    load_input = input("Enter max load units to test validate_load_units: ")
    result = validate_load_units(load_input)
    print(f"Result: {result} -> {'PASS' if result is not None else 'FAIL'}")

    print("\nAll interactive tests completed!")

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


"""
Admin blueprint for handling administrator profile management.
Includes profile viewing, updating, and image upload functionality.
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple

import mysql.connector
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, request, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

# ==========================================================
# CONFIGURATION
# ==========================================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

PASSWORD_MIN_LENGTH = 8
MAX_LOAD_UNITS = 100
MIN_LOAD_UNITS = 0

FLASH_CATEGORIES = {
    'danger': 'danger',
    'success': 'success',
    'warning': 'warning',
    'info': 'info'
}

ERROR_MESSAGES = {
    'user_not_found': 'User not found.',
    'current_password_incorrect': 'Current password is incorrect.',
    'password_mismatch': 'New password and confirmation do not match.',
    'general_error': 'An error occurred while processing your request.',
    'password_error': 'Password strength error: {}',
    'password_too_short': 'Password must be at least {} characters long.',
    'password_missing_uppercase': 'Password must contain at least one uppercase letter.',
    'password_missing_lowercase': 'Password must contain at least one lowercase letter.',
    'password_missing_number': 'Password must contain at least one number.',
    'password_missing_special': 'Password must contain at least one special character.',
    'invalid_name': 'Invalid name.',
    'invalid_department': 'Invalid department.',
    'invalid_load_units': 'Invalid load units.'
}

SQL_QUERIES = {
    'select_password': 'SELECT password FROM instructors WHERE username = %s',
    'update_instructors': 'UPDATE instructors SET {} WHERE username = %s'
}

VALIDATION_PATTERNS = {
    'name': re.compile(r"^[A-Za-z\s\-\.']{1,100}$"),
    'username': re.compile(r'^\w{3,50}$'),  # changed [A-Za-z0-9_] to \w
    'department': re.compile(r'^[A-Za-z0-9\s\-\.&,]{1,100}$')
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================================
# HELPERS
# ==========================================================

def sanitize_input(value: Optional[str], value_type: str = 'string') -> Optional[str]:
    """Sanitize and validate input."""
    if value is None:
        return None

    value = str(value).strip()

    if value_type == 'name' and not VALIDATION_PATTERNS['name'].match(value):
        return None
    if value_type == 'department' and not VALIDATION_PATTERNS['department'].match(value):
        return None
    if value_type == 'username' and not VALIDATION_PATTERNS['username'].match(value):
        return None

    return value


def validate_load_units(units: Optional[str]) -> Optional[int]:
    """Validate max load units."""
    try:
        parsed = int(units)
        if MIN_LOAD_UNITS <= parsed <= MAX_LOAD_UNITS:
            return parsed
        return None
    except (TypeError, ValueError):
        return None


def safe_db_operation(operation):
    """Safely execute DB operation."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()  # removed dictionary=True
        result = operation(cursor)
        connection.commit()
        return result
    except mysql.connector.Error as exc:
        if connection:
            connection.rollback()
        logger.error("Database error: %s", exc)
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def fetchone_dict(cursor):
    """Fetch one row as dict to mimic dictionary=True behavior."""
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password complexity."""
    checks = [
        (len(password) >= PASSWORD_MIN_LENGTH,
         ERROR_MESSAGES['password_too_short'].format(PASSWORD_MIN_LENGTH)),
        (re.search(r'[A-Z]', password),
         ERROR_MESSAGES['password_missing_uppercase']),
        (re.search(r'[a-z]', password),
         ERROR_MESSAGES['password_missing_lowercase']),
        (re.search(r'\d', password),
         ERROR_MESSAGES['password_missing_number']),
        (re.search(r'[!@#$%^&*(),.?":{}|<>]', password),
         ERROR_MESSAGES['password_missing_special']),
    ]

    errors = [msg for passed, msg in checks if not passed]
    return not errors, ' '.join(errors)

# ==========================================================
# PASSWORD PROCESSING
# ==========================================================

def _validate_password_inputs(
    current_pw: Optional[str],
    new_pw: Optional[str],
    confirm_pw: Optional[str]
) -> Optional[str]:
    if not any((current_pw, new_pw, confirm_pw)):
        return None
    if not all((current_pw, new_pw, confirm_pw)):
        return 'All password fields are required.'
    if not all(isinstance(pw, str) for pw in (current_pw, new_pw, confirm_pw)):
        return 'Invalid password format.'
    return None


def _validate_new_password(
    stored_hash: str,
    new_pw: str,
    confirm_pw: str
) -> Optional[str]:
    if new_pw != confirm_pw:
        return ERROR_MESSAGES['password_mismatch']
    if check_password_hash(stored_hash, new_pw):
        return 'New password must differ from old password.'

    valid, message = validate_password_strength(new_pw)
    if not valid:
        return ERROR_MESSAGES['password_error'].format(message)
    return None


def process_password_change(
    username: str,
    current_pw: Optional[str],
    new_pw: Optional[str],
    confirm_pw: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Process password change request."""
    sanitized_username = sanitize_input(username, 'username')
    if not sanitized_username:
        return None, 'Invalid username.'

    error = _validate_password_inputs(current_pw, new_pw, confirm_pw)
    if error:
        return None, error

    if not any((current_pw, new_pw, confirm_pw)):
        return None, None

    def operation(cursor):
        cursor.execute(SQL_QUERIES['select_password'], (sanitized_username,))
        user = fetchone_dict(cursor)  # fetch as dict
        if not user:
            return None, ERROR_MESSAGES['user_not_found']

        stored_hash = user['password']
        if not check_password_hash(stored_hash, current_pw):
            return None, ERROR_MESSAGES['current_password_incorrect']

        validation_error = _validate_new_password(
            stored_hash, new_pw, confirm_pw
        )
        if validation_error:
            return None, validation_error

        return generate_password_hash(new_pw), None

    try:
        return safe_db_operation(operation)
    except mysql.connector.Error:
        return None, ERROR_MESSAGES['general_error']

# ==========================================================
# FORM COLLECTION
# ==========================================================

def _collect_text(
    form,
    field: str,
    field_type: str,
    error_message: str
) -> Tuple[Optional[str], Optional[str]]:
    value = sanitize_input(form.get(field), field_type)
    if value is None:
        return None, None
    if not value:
        return None, error_message
    return value, None


def collect_form_data(username: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Collect and validate form data."""
    update_data: Dict[str, Any] = {}
    errors = []

    name, err = _collect_text(
        request.form, 'name', 'name', ERROR_MESSAGES['invalid_name']
    )
    if err:
        errors.append(err)
    elif name:
        update_data['name'] = name

    department, err = _collect_text(
        request.form, 'department', 'department',
        ERROR_MESSAGES['invalid_department']
    )
    if err:
        errors.append(err)
    elif department:
        update_data['department'] = department

    units = request.form.get('max_load_units')
    if units is not None:
        validated = validate_load_units(units)
        if validated is None:
            errors.append(ERROR_MESSAGES['invalid_load_units'])
        else:
            update_data['max_load_units'] = validated

    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')

    if any((current_pw, new_pw, confirm_pw)):
        hashed, err = process_password_change(
            username, current_pw, new_pw, confirm_pw
        )
        if err:
            errors.append(err)
        elif hashed:
            update_data['hashed_password'] = hashed

    if errors:
        return {}, ' '.join(errors)

    return update_data, None

# ==========================================================
# TESTING
# ==========================================================

if __name__ == "__main__":
    print("Interactive and automatic quick tests for admin_routes.py\n")

    # ----------------------------
    # SANITIZE INPUT TESTS
    # ----------------------------
    test_names = ["John Doe", "Anne-Marie O'Neill", "Invalid123", ""]
    for name in test_names:
        result = sanitize_input(name, "name")
        print(f"Name test: '{name}' -> {result} -> {'PASS' if result else 'FAIL'}")

    test_usernames = ["john_doe", "user123", "Invalid User!", "a", "this_is_a_very_long_username_exceeding_fifty_chars_123"]
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
    test_passwords = ["Abc123!@", "weakpass", "NoNumber!", "noupper1!", "NOLOWER1!", "Short1!", "ValidPass1!"]
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

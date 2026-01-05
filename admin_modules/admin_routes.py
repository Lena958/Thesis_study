"""
Admin blueprint for handling administrator profile management.
Includes profile viewing, updating, and image upload functionality.
"""

# ==========================================================
# STANDARD LIBRARY IMPORTS
# ==========================================================

import re
import logging
from typing import Optional, Dict, Any, Tuple

# ==========================================================
# THIRD-PARTY IMPORTS
# ==========================================================

import mysql.connector
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, request, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

# ==========================================================
# APPLICATION CONFIGURATION
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
    'username': re.compile(r'^\w{3,50}$'),
    'department': re.compile(r'^[A-Za-z0-9\s\-\.&,]{1,100}$')
}

# ==========================================================
# LOGGING SETUP
# ==========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================================
# INPUT SANITIZATION & VALIDATION HELPERS
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
# DATABASE ACCESS HELPERS
# ==========================================================

def safe_db_operation(operation):
    """Safely execute DB operation."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
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

# ==========================================================
# PASSWORD CHANGE INTERNAL VALIDATION
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

# ==========================================================
# PASSWORD CHANGE PROCESSING
# ==========================================================

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
        user = fetchone_dict(cursor)
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
# FORM DATA COLLECTION & VALIDATION
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
# LOCAL TESTING & MANUAL VERIFICATION (SONARQUBE COMPLIANT)
# ==========================================================

if __name__ == "__main__":
    print("=== Automatic Validation Tests ===")

    MAX_NAME_LENGTH = 100
    MAX_USERNAME_LENGTH = 50
    MIN_USERNAME_LENGTH = 2

    # ------------------------------------------------------
    # NAME FULL-MATCH TESTS
    # ------------------------------------------------------
    print("\nRunning full-match name tests...")
    name_tests = {
        "John Doe": True,
        "Anne-Marie O'Neill": True,
        "Élodie Dupont": True,
        "John123": False,
        "John@Doe": False,
        "": False,
        "   ": False,
        "A" * (MAX_NAME_LENGTH + 1): False,
    }

    for name, expected in name_tests.items():
        result = sanitize_input(name, "name")
        passed = bool(result) == expected
        print(f"Name '{name}': {'PASS' if passed else 'FAIL'}")

    # ------------------------------------------------------
    # USERNAME FULL-MATCH & EDGE CASE TESTS
    # ------------------------------------------------------
    print("\nRunning full-match username tests...")
    username_tests = {
        "john_doe": True,
        "user123": True,
        "a": False,
        "ab": True,
        "valid_user_99": True,
        "Invalid User": False,
        "user!name": False,
        "user-name": False,
        "123456": True,
        "a" * MAX_USERNAME_LENGTH: True,
        "a" * (MAX_USERNAME_LENGTH + 1): False,
        "_username": False,
        "username_": False,
    }

    for username, expected in username_tests.items():
        result = sanitize_input(username, "username")
        passed = bool(result) == expected
        print(f"Username '{username}': {'PASS' if passed else 'FAIL'}")

    # ------------------------------------------------------
    # PASSWORD FULL-MATCH & SECURITY EDGE TESTS
    # ------------------------------------------------------
    print("\nRunning full-match password tests...")
    password_tests = {
        "Abc123!@": True,
        "ValidPass1!": True,
        "Aa1!Aa1!": True,
        "weakpass": False,
        "NoNumber!": False,
        "NOLOWER1!": False,
        "noupper1!": False,
        "Short1!": False,
        "Abcdefgh1": False,
        "Abc!@#": False,
        "A1!" * 10: False,
        "Pass word1!": False,
    }

    for password, expected in password_tests.items():
        valid, _message = validate_password_strength(password)
        passed = valid == expected
        print(f"Password '{password}': {'PASS' if passed else 'FAIL'}")

    # ------------------------------------------------------
    # LOAD UNITS EDGE & BOUNDARY TESTS
    # ------------------------------------------------------
    print("\nRunning load unit tests...")
    load_unit_tests = {
        "0": False,
        "1": True,
        "50": True,
        "100": True,
        "101": False,
        "-1": False,
        "abc": False,
        "10.5": False,
        " ": False,
    }

    for units, expected in load_unit_tests.items():
        result = validate_load_units(units)
        passed = (result is not None) == expected
        print(f"Load '{units}': {'PASS' if passed else 'FAIL'}")

    print("\n=== All automatic validation tests completed ===")

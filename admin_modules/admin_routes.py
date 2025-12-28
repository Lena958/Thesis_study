"""
Admin blueprint for handling administrator profile management.
Includes profile viewing, updating, and image upload functionality.
"""

import os
import re
from typing import Optional, Dict, Any, Tuple

import mysql.connector
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    flash,
    current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

# Blueprint initialization
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PASSWORD_MIN_LENGTH = 8

# Flash message categories
FLASH_CATEGORIES = {
    'danger': 'danger',
    'success': 'success'
}

# Error messages
ERROR_MESSAGES = {
    'invalid_image': 'Invalid image format! Allowed types: PNG, JPG, JPEG, GIF',
    'user_not_found': 'User not found.',
    'current_password_incorrect': 'Current password is incorrect.',
    'password_mismatch': 'New password and confirmation do not match.',
    'profile_not_found': 'Instructor profile not found.',
    'general_error': 'An error occurred while processing your request.',
    'profile_updated': 'Profile updated successfully!',
    'password_error': 'Password strength error: {}',
    'password_too_short': 'Password must be at least {} characters long.',
    'password_missing_uppercase': 'Password must contain at least one uppercase letter.',
    'password_missing_lowercase': 'Password must contain at least one lowercase letter.',
    'password_missing_number': 'Password must contain at least one number.',
    'password_missing_special': 'Password must contain at least one special character.'
}

# Database field names
DB_FIELDS = {
    'name': 'name',
    'department': 'department',
    'max_load_units': 'max_load_units',
    'image': 'image',
    'username': 'username',
    'password': 'password'
}

# SQL queries
SQL_QUERIES = {
    'select_name': 'SELECT {} FROM instructors WHERE {} = %s'.format(
        DB_FIELDS['name'], DB_FIELDS['username']
    ),
    'select_profile': '''
        SELECT {name}, {department}, {max_load_units}, {username}, {image} 
        FROM instructors 
        WHERE {username} = %s
    '''.format(
        name=DB_FIELDS['name'],
        department=DB_FIELDS['department'],
        max_load_units=DB_FIELDS['max_load_units'],
        username=DB_FIELDS['username'],
        image=DB_FIELDS['image']
    ),
    'select_password': 'SELECT {} FROM instructors WHERE {} = %s'.format(
        DB_FIELDS['password'], DB_FIELDS['username']
    ),
    'update_instructors': 'UPDATE instructors SET {} WHERE {} = %s'
}


def is_admin() -> bool:
    """Check if the current user has admin role."""
    return session.get('role') == 'admin'


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    """Create and return a database connection."""
    return mysql.connector.connect(**DB_CONFIG)


def get_instructor_name(username: str) -> Optional[str]:
    """Retrieve instructor name by username."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(SQL_QUERIES['select_name'], (username,))
        result = cursor.fetchone()

        return result[DB_FIELDS['name']] if result else None

    except mysql.connector.Error as err:
        current_app.logger.error('Database error in get_instructor_name: %s', err)
        return None

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    error_messages = []
    
    if len(password) < PASSWORD_MIN_LENGTH:
        error_messages.append(
            ERROR_MESSAGES['password_too_short'].format(PASSWORD_MIN_LENGTH)
        )
    
    if not re.search(r'[A-Z]', password):
        error_messages.append(ERROR_MESSAGES['password_missing_uppercase'])
    
    if not re.search(r'[a-z]', password):
        error_messages.append(ERROR_MESSAGES['password_missing_lowercase'])
    
    if not re.search(r'\d', password):  # Concise version of [0-9]
        error_messages.append(ERROR_MESSAGES['password_missing_number'])
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        error_messages.append(ERROR_MESSAGES['password_missing_special'])
    
    if error_messages:
        return False, ' '.join(error_messages)
    
    return True, ''


def handle_image_upload(image_file) -> Optional[str]:
    """
    Handle image file upload and return the saved filename.
    
    Returns:
        Filename if successful, None otherwise.
    """
    if not image_file or image_file.filename == '':
        return None
    
    if not allowed_file(image_file.filename):
        flash(ERROR_MESSAGES['invalid_image'], FLASH_CATEGORIES['danger'])
        return None
    
    filename = secure_filename(image_file.filename)
    upload_folder = os.path.join(current_app.root_path, 'static/uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    image_path = os.path.join(upload_folder, filename)
    image_file.save(image_path)
    
    return filename


def process_password_change(username: str, current_pw: str,
                            new_pw: str, confirm_pw: str) -> Optional[str]:
    """
    Process password change request.
    
    Returns:
        Hashed password if change is valid, None otherwise.
    """
    if not all([current_pw, new_pw, confirm_pw]):
        return None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(SQL_QUERIES['select_password'], (username,))
        user = cursor.fetchone()
        
        if not user:
            flash(ERROR_MESSAGES['user_not_found'], FLASH_CATEGORIES['danger'])
            return None
        
        if not check_password_hash(user[DB_FIELDS['password']], current_pw):
            flash(ERROR_MESSAGES['current_password_incorrect'], FLASH_CATEGORIES['danger'])
            return None
        
        if new_pw != confirm_pw:
            flash(ERROR_MESSAGES['password_mismatch'], FLASH_CATEGORIES['danger'])
            return None
        
        is_valid, error_msg = validate_password_strength(new_pw)
        if not is_valid:
            flash(
                ERROR_MESSAGES['password_error'].format(error_msg),
                FLASH_CATEGORIES['danger']
            )
            return None
        
        return generate_password_hash(new_pw)
        
    except mysql.connector.Error as err:
        current_app.logger.error('Database error in process_password_change: %s', err)
        flash(ERROR_MESSAGES['general_error'], FLASH_CATEGORIES['danger'])
        return None
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


def build_profile_update_query(update_data: Dict[str, Any]) -> Tuple[str, list]:
    """
    Build SQL UPDATE query and parameters based on provided data.
    
    Returns:
        Tuple of (query_string, parameter_list)
    """
    update_fields = []
    update_values = []
    
    field_mappings = {
        'name': DB_FIELDS['name'],
        'department': DB_FIELDS['department'],
        'max_load_units': DB_FIELDS['max_load_units'],
        'image_filename': DB_FIELDS['image'],
        'hashed_password': DB_FIELDS['password']
    }
    
    for data_key, db_field in field_mappings.items():
        if data_key in update_data and update_data[data_key] is not None:
            update_fields.append(f'{db_field} = %s')
            update_values.append(update_data[data_key])
    
    query = SQL_QUERIES['update_instructors'].format(
        ', '.join(update_fields),
        DB_FIELDS['username']
    )
    return query, update_values


@admin_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Handle admin profile viewing and updating."""
    if not is_admin():
        return redirect(url_for('login'))
    
    username = session.get('username')
    
    if request.method == 'POST':
        return handle_profile_update(username)
    
    return handle_profile_view(username)


def handle_profile_view(username: str):
    """Handle GET request for profile viewing."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(SQL_QUERIES['select_profile'], (username,))
        instructor = cursor.fetchone()
        
        if not instructor:
            flash(ERROR_MESSAGES['profile_not_found'], FLASH_CATEGORIES['danger'])
            return redirect(url_for('login'))
        
        return render_template(
            'admin/profile.html',
            instructor_name=instructor[DB_FIELDS['name']],
            instructor_username=instructor[DB_FIELDS['username']],
            instructor_department=instructor[DB_FIELDS['department']],
            instructor_max_load=instructor[DB_FIELDS['max_load_units']],
            instructor_image=instructor[DB_FIELDS['image']]
        )
        
    except mysql.connector.Error as err:
        current_app.logger.error('Database error in handle_profile_view: %s', err)
        flash(ERROR_MESSAGES['general_error'], FLASH_CATEGORIES['danger'])
        return redirect(url_for('admin.profile'))
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


def handle_profile_update(username: str):
    """Handle POST request for profile updating."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        update_data = collect_form_data(username)
        
        if update_data.get('image_upload_failed'):
            return redirect(url_for('admin.profile'))
        
        update_query, update_values = build_profile_update_query(update_data)
        
        if update_values:
            update_values.append(username)
            cursor.execute(update_query, tuple(update_values))
            connection.commit()
            flash(ERROR_MESSAGES['profile_updated'], FLASH_CATEGORIES['success'])
        
        return redirect(url_for('admin.profile'))
        
    except mysql.connector.Error as err:
        if 'connection' in locals():
            connection.rollback()
        current_app.logger.error('Database error in handle_profile_update: %s', err)
        flash(ERROR_MESSAGES['general_error'], FLASH_CATEGORIES['danger'])
        return redirect(url_for('admin.profile'))
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


def collect_form_data(username: str) -> Dict[str, Any]:
    """Collect and validate form data for profile update."""
    update_data = {}
    
    update_data['name'] = request.form.get(DB_FIELDS['name'])
    update_data['department'] = request.form.get(DB_FIELDS['department'])
    update_data['max_load_units'] = request.form.get(DB_FIELDS['max_load_units'])
    
    image_file = request.files.get(DB_FIELDS['image'])
    image_filename = handle_image_upload(image_file)
    
    if image_file and image_file.filename != '' and image_filename is None:
        update_data['image_upload_failed'] = True
    else:
        update_data['image_filename'] = image_filename
        update_data['image_upload_failed'] = False
    
    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')
    
    hashed_password = process_password_change(username, current_pw, new_pw, confirm_pw)
    if hashed_password is not None:
        update_data['hashed_password'] = hashed_password
    
    return update_data
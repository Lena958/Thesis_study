"""
Rooms management module for admin routes.
Handles listing, adding, editing, deleting rooms with image upload support.
"""

# ------------------------
# Standard library imports
# ------------------------
import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import mysql.connector

# ------------------------
# Blueprint & Config
# ------------------------
rooms_bp = Blueprint('rooms', __name__, url_prefix='/admin/rooms')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ROOMS_LIST_ROUTE = 'rooms.list_rooms'

# ------------------------
# Helper Functions
# ------------------------
def get_db_connection():
    """Establish a database connection."""
    return mysql.connector.connect(**db_config)

def is_admin():
    """Check if the current user is an admin."""
    return session.get('role') == 'admin'

def allowed_file(filename):
    """Check if the uploaded file is allowed based on extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_programs(program_input):
    """Split input into multiple programs (separated by '/' or ',')."""
    if not program_input:
        return []
    return [p.strip() for p in program_input.replace(',', '/').split('/') if p.strip()]

def save_image_file(image_file):
    """Save uploaded image to static folder and return filename."""
    if not image_file or not allowed_file(image_file.filename):
        return None
    filename = secure_filename(image_file.filename)
    upload_folder = os.path.join(current_app.root_path, 'static', 'room_images')
    os.makedirs(upload_folder, exist_ok=True)
    image_file.save(os.path.join(upload_folder, filename))
    return filename

def fetch_program_suggestions():
    """Fetch distinct program names from room_programs."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT program_name FROM room_programs")
    programs = [row['program_name'] for row in cursor.fetchall()]
    conn.close()
    return programs

def fetch_room_programs(room_id):
    """Fetch program names assigned to a specific room."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT program_name FROM room_programs WHERE room_id=%s", (room_id,))
    programs = [row['program_name'] for row in cursor.fetchall()]
    conn.close()
    return programs

# ------------------------
# Context Processor
# ------------------------
@rooms_bp.context_processor
def inject_instructor_name():
    """Inject instructor info into templates."""
    if 'user_id' not in session:
        return {"instructor_name": None, "instructor_image": None}
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, image FROM instructors WHERE instructor_id=%s", 
        (session['user_id'],)
    )
    instructor = cursor.fetchone()
    conn.close()
    return {
        "instructor_name": instructor['name'] if instructor else None,
        "instructor_image": instructor['image'] if instructor and instructor['image'] else None
    }

# ------------------------
# Room Management Routes
# ------------------------
@rooms_bp.route('/')
def list_rooms():
    if not is_admin():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()

    for room in rooms:
        room['programs'] = fetch_room_programs(room['room_id'])
    conn.close()

    all_programs = sorted({prog for room in rooms for prog in room['programs']})
    return render_template("admin/rooms.html", rooms=rooms, programs=all_programs)

@rooms_bp.route('/add', methods=['GET', 'POST'])
def add_room():
    if not is_admin():
        return redirect(url_for('login'))

    programs = fetch_program_suggestions()
    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        programs_list = parse_programs(request.form.get('program'))
        image_filename = save_image_file(request.files.get('image'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rooms (room_number, room_type, image) VALUES (%s, %s, %s)",
            (room_number, room_type, image_filename)
        )
        room_id = cursor.lastrowid

        for program_name in programs_list:
            cursor.execute(
                "INSERT INTO room_programs (room_id, program_name) VALUES (%s, %s)",
                (room_id, program_name)
            )

        conn.commit()
        conn.close()
        flash("Room added successfully", "success")
        return redirect(url_for(ROOMS_LIST_ROUTE))

    return render_template("admin/add_room.html", programs=programs)

@rooms_bp.route('/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    if not is_admin():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms WHERE room_id=%s", (room_id,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        flash("Room not found", "error")
        return redirect(url_for(ROOMS_LIST_ROUTE))

    programs = fetch_program_suggestions()
    room_programs = fetch_room_programs(room_id)
    current_program = '/'.join(room_programs)

    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        programs_list = parse_programs(request.form.get('program'))
        image_filename = save_image_file(request.files.get('image')) or room['image']

        cursor.execute(
            "UPDATE rooms SET room_number=%s, room_type=%s, image=%s WHERE room_id=%s",
            (room_number, room_type, image_filename, room_id)
        )
        cursor.execute("DELETE FROM room_programs WHERE room_id=%s", (room_id,))
        for program_name in programs_list:
            cursor.execute(
                "INSERT INTO room_programs (room_id, program_name) VALUES (%s, %s)",
                (room_id, program_name)
            )

        conn.commit()
        conn.close()
        flash("Room updated successfully", "success")
        return redirect(url_for(ROOMS_LIST_ROUTE))

    conn.close()
    return render_template(
        "admin/edit_room.html",
        room=room,
        programs=programs,
        room_programs=room_programs,
        current_program=current_program
    )

@rooms_bp.route('/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if not is_admin():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms WHERE room_id=%s", (room_id,))
    conn.commit()
    conn.close()
    flash("Room deleted successfully", "success")
    return redirect(url_for(ROOMS_LIST_ROUTE))

# ------------------------
# Input Validation
# ------------------------
def sanitize_room_number(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9\-]{1,20}", value):
        return None
    return value

def sanitize_room_type(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or not re.fullmatch(r"[A-Za-z\s]{3,50}", value):
        return None
    return value

def sanitize_program_name(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or not re.fullmatch(r"[A-Za-z\s&\-]{2,100}", value):
        return None
    return value

def validate_image_filename(filename):
    if not isinstance(filename, str):
        return False
    return allowed_file(filename)

# ------------------------
# Test Cases
# ------------------------
if __name__ == "__main__":
    print("Interactive and automatic quick tests for rooms_routes.py\n")

    # Room number tests
    for rn in ["A101", "LAB-2", "203", "Room#1", ""]:
        result = sanitize_room_number(rn)
        print(f"Room number test: '{rn}' -> {result} -> {'PASS' if result else 'FAIL'}")

    # Room type tests
    for rt in ["Lecture", "Computer Lab", "Lab123", "", "A"]:
        result = sanitize_room_type(rt)
        print(f"Room type test: '{rt}' -> {result} -> {'PASS' if result else 'FAIL'}")

    # Program name tests
    for prog in ["Computer Science", "IT & AI", "Prog@123", ""]:
        result = sanitize_program_name(prog)
        print(f"Program test: '{prog}' -> {result} -> {'PASS' if result else 'FAIL'}")

    # Image extension tests
    for img in ["room.png", "photo.jpg", "image.jpeg", "file.gif", "doc.pdf"]:
        result = validate_image_filename(img)
        print(f"Image test: '{img}' -> {result} -> {'PASS' if result else 'FAIL'}")

    # Interactive tests
    print("\nInteractive input tests:")
    rn_input = input("Enter room number: "); print(sanitize_room_number(rn_input))
    rt_input = input("Enter room type: "); print(sanitize_room_type(rt_input))
    prog_input = input("Enter program name: "); print(sanitize_program_name(prog_input))
    img_input = input("Enter image filename: "); print(validate_image_filename(img_input))
    print("\nAll interactive tests completed!")

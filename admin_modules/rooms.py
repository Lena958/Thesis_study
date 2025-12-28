from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import mysql.connector
import os
from werkzeug.utils import secure_filename

# -------------------- Blueprint & Config --------------------
rooms_bp = Blueprint('rooms', __name__, url_prefix='/admin/rooms')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ROOMS_LIST_ROUTE = 'rooms.list_rooms'  # Constant to avoid repeated literal

# -------------------- Helper Functions --------------------

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

# -------------------- Context Processor --------------------

@rooms_bp.context_processor
def inject_instructor_name():
    if 'user_id' not in session:
        return {"instructor_name": None, "instructor_image": None}
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

# -------------------- ROOM MANAGEMENT ROUTES --------------------

# List All Rooms
@rooms_bp.route('/')
def list_rooms():
    if not is_admin():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()

    # Attach programs
    for room in rooms:
        room['programs'] = fetch_room_programs(room['room_id'])
    conn.close()

    all_programs = sorted({prog for room in rooms for prog in room['programs']})
    return render_template("admin/rooms.html", rooms=rooms, programs=all_programs)

# Add Room
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

# Edit Room
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

# Delete Room
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

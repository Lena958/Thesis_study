"""
Auto scheduler blueprint for automatic schedule generation using CSP algorithms.
Includes optimized constraint satisfaction with caching and parallel processing.
"""

import random
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional

import mysql.connector
import numpy as np
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .conflicts import detect_and_save_conflicts

auto_scheduler_bp = Blueprint('auto_scheduler', __name__, url_prefix='/admin/auto_scheduler')

# ---------- Database Configuration ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iload'
}

# ---------- Constants ----------
FLASH_CATEGORIES = {
    'warning': 'warning',
    'danger': 'danger',
    'success': 'success'
}

ERROR_MESSAGES = {
    'time_required': 'Semester and school year are required.',
    'time_invalid': 'Start time must be earlier than end time.',
    'time_format': 'Invalid time format.',
    'no_slots': 'No time slots available.',
    'no_valid_options': 'No valid scheduling options found for any subjects.',
    'ac3_failed': 'AC-3 failed: no valid schedule possible.',
    'schedule_failed': 'Failed to generate schedule - no valid assignment found.',
    'schedule_success': 'Schedule generated successfully in {:.2f} seconds.',
}

DB_TABLES = {
    'schedules': 'schedules',
    'subjects': 'subjects',
    'instructors': 'instructors',
    'rooms': 'rooms',
    'room_programs': 'room_programs',
    'courses': 'courses',
    'conflicts': 'conflicts'
}

DB_FIELDS = {
    'schedule_id': 'schedule_id',
    'subject_id': 'subject_id',
    'instructor_id': 'instructor_id',
    'room_id': 'room_id',
    'day_of_week': 'day_of_week',
    'start_time': 'start_time',
    'end_time': 'end_time',
    'approved': 'approved',
    'semester': 'semester',
    'school_year': 'school_year',
    'name': 'name',
    'code': 'code',
    'units': 'units',
    'course': 'course',
    'status': 'status',
    'max_load_units': 'max_load_units',
    'room_number': 'room_number',
    'room_type': 'room_type',
    'program_name': 'program_name',
    'course_type': 'course_type',
    'subject_name': 'subject_name',
    'instructor_name': 'instructor_name',
    'schedule1_id': 'schedule1_id',
    'schedule2_id': 'schedule2_id',
    'image': 'image',
    'year_level': 'year_level',
    'section': 'section'
}

PATTERNS = {
    'MWF': ['Monday', 'Wednesday', 'Friday'],
    'TTh': ['Tuesday', 'Thursday'],
    'OneDay': ['Monday']
}

ROOM_TYPE_MAP = {
    'lecture': 'Lecture',
    'laboratory': 'Lab',
    'lab': 'Lab'
}

TIME_FORMATS = {
    '24h': "%H:%M:%S",
    '12h': "%I:%M %p",
    'short': "%H:%M"
}

TIME_RANGES = {
    'lunch_start': "12:00",
    'lunch_end': "13:00",
    'workday_start': "08:00",
    'workday_end': "17:00"
}

# Global caches (will be cleared per generation)
_time_cache = {}
_compatibility_cache = {}
_backtrack_cache = {}
_instructor_status = {}


def get_db_connection():
    """Create and return a database connection."""
    return mysql.connector.connect(**DB_CONFIG)


def is_admin():
    """Check if the current user has admin role."""
    return session.get('role') == 'admin'


@auto_scheduler_bp.context_processor
def inject_instructor_name():
    """Inject instructor name and image into template context."""
    if 'user_id' not in session:
        return {DB_FIELDS['instructor_name']: None, DB_FIELDS['image']: None}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = (
        f"SELECT {DB_FIELDS['name']}, {DB_FIELDS['image']} FROM {DB_TABLES['instructors']} "
        f"WHERE {DB_FIELDS['instructor_id']} = %s"
    )
    cursor.execute(query, (session['user_id'],))
    instructor = cursor.fetchone()
    conn.close()

    return {
        DB_FIELDS['instructor_name']: instructor[DB_FIELDS['name']] if instructor else None,
        DB_FIELDS['image']: instructor[DB_FIELDS['image']] if instructor and instructor[DB_FIELDS['image']] else None
    }


def sessions_for_subject(subj):
    """Calculate session pattern and hours for a subject."""
    try:
        units = int(subj.get(DB_FIELDS['units'], 3))
    except (ValueError, TypeError):
        units = 3

    course_type = (subj.get(DB_FIELDS['course_type']) or 'major').lower()

    # MAJOR SUBJECTS: 5 hours per week (3 units = 3 hours lecture + 2 hours lab)
    if course_type == 'major' and units == 3:
        return 'MWF_TTh', 5  # Special pattern for major subjects

    # Non-major subjects follow normal patterns
    if units >= 3:
        return 'MWF', 3
    elif units == 2:
        return 'TTh', 2
    else:
        return 'OneDay', 1


@lru_cache(maxsize=10000)
def parse_time_str(t: str) -> Optional[str]:
    """Parse time string to consistent format with caching."""
    if not t:
        return None

    for fmt in (TIME_FORMATS['24h'], TIME_FORMATS['short']):
        try:
            dt = datetime.strptime(t, fmt)
            return dt.strftime(TIME_FORMATS['short'])
        except ValueError:
            continue
    return None


@lru_cache(maxsize=10000)
def _intervals_overlap_cached(s1: str, e1: str, s2: str, e2: str) -> bool:
    """Cached version of interval overlap check."""
    def time_to_minutes(t: str) -> int:
        h, m = map(int, t.split(':'))
        return h * 60 + m

    start1, end1 = time_to_minutes(s1), time_to_minutes(e1)
    start2, end2 = time_to_minutes(s2), time_to_minutes(e2)

    return not (end1 <= start2 or end2 <= start1)


def intervals_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
    """Check if two time intervals overlap."""
    return _intervals_overlap_cached(s1, e1, s2, e2)


def get_approved_schedules(semester: str, school_year: str) -> List[Dict]:
    """Get all approved schedules from database to avoid conflicts."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = f"""
        SELECT 
            s.{DB_FIELDS['instructor_id']},
            s.{DB_FIELDS['room_id']},
            s.{DB_FIELDS['day_of_week']},
            s.{DB_FIELDS['start_time']},
            s.{DB_FIELDS['end_time']},
            s.{DB_FIELDS['subject_id']}
        FROM {DB_TABLES['schedules']} s
        WHERE s.{DB_FIELDS['approved']} = 1 
        AND s.{DB_FIELDS['semester']} = %s 
        AND s.{DB_FIELDS['school_year']} = %s
    """

    cur.execute(query, (semester, school_year))
    approved_schedules = cur.fetchall()
    conn.close()

    # Convert times to consistent format
    for schedule in approved_schedules:
        schedule[DB_FIELDS['start_time']] = parse_time_str(
            str(schedule[DB_FIELDS['start_time']])
        )
        schedule[DB_FIELDS['end_time']] = parse_time_str(
            str(schedule[DB_FIELDS['end_time']])
        )

    return approved_schedules


def conflicts_with_approved_schedule(
    candidate_session: Dict,
    approved_schedules: List[Dict]
) -> bool:
    """Check if candidate session conflicts with any approved schedule."""
    candidate_instructor = candidate_session.get(DB_FIELDS['instructor_id'])
    candidate_room = candidate_session.get(DB_FIELDS['room_id'])
    candidate_day = candidate_session.get(DB_FIELDS['day_of_week'])
    candidate_start = candidate_session.get(DB_FIELDS['start_time'])
    candidate_end = candidate_session.get(DB_FIELDS['end_time'])

    for approved in approved_schedules:
        # Same instructor conflict
        if (approved[DB_FIELDS['instructor_id']] == candidate_instructor and
            approved[DB_FIELDS['day_of_week']] == candidate_day and
            intervals_overlap(
                approved[DB_FIELDS['start_time']],
                approved[DB_FIELDS['end_time']],
                candidate_start,
                candidate_end
            )):
            return True

        # Same room conflict
        if (approved[DB_FIELDS['room_id']] == candidate_room and
            approved[DB_FIELDS['day_of_week']] == candidate_day and
            intervals_overlap(
                approved[DB_FIELDS['start_time']],
                approved[DB_FIELDS['end_time']],
                candidate_start,
                candidate_end
            )):
            return True

    return False


class GroupKey:
    """Immutable key for group compatibility checking."""
    __slots__ = ('sessions_data', 'hash_val')

    def __init__(self, group):
        self.sessions_data = tuple(
            (
                int(session.get(DB_FIELDS['subject_id']) or 0),
                int(session.get(DB_FIELDS['instructor_id']) or 0),
                int(session.get(DB_FIELDS['room_id']) or 0),
                session.get(DB_FIELDS['day_of_week'], ''),
                session.get(DB_FIELDS['start_time'], ''),
                session.get(DB_FIELDS['end_time'], '')
            )
            for session in group
        )
        self.hash_val = hash(self.sessions_data)

    def __hash__(self):
        return self.hash_val

    def __eq__(self, other):
        return self.sessions_data == other.sessions_data


def groups_compatible(group_a, group_b):
    """Optimized compatibility check with caching."""
    if not group_a or not group_b:
        return True

    key_a = GroupKey(group_a)
    key_b = GroupKey(group_b)

    cache_key = (key_a.hash_val, key_b.hash_val)
    if cache_key in _compatibility_cache:
        return _compatibility_cache[cache_key]

    result = _groups_compatible_fast(key_a.sessions_data, key_b.sessions_data)
    _compatibility_cache[cache_key] = result
    return result


def _groups_compatible_fast(sessions_a, sessions_b):
    """Vectorized compatibility check without Python loops where possible."""
    for a in sessions_a:
        subj_id_a, instr_id_a, room_id_a, day_a, start_a, end_a = a
        for b in sessions_b:
            subj_id_b, instr_id_b, room_id_b, day_b, start_b, end_b = b

            # Same subject conflict
            if subj_id_a == subj_id_b and subj_id_a != 0:
                if instr_id_a != instr_id_b or room_id_a != room_id_b:
                    return False
                if day_a == day_b:
                    return False

            # Time overlap conflict
            if day_a == day_b and day_a and day_b:
                if _intervals_overlap_cached(start_a, end_a, start_b, end_b):
                    if instr_id_a == instr_id_b and instr_id_a != 0:
                        return False
                    if room_id_a == room_id_b and room_id_a != 0:
                        return False

    return True


def ac3(domains, trim_large_domains=True):
    """Optimized AC-3 with early termination and better queue management."""
    keys = list(domains.keys())
    if not keys:
        return True

    queue = deque()

    for i, xi in enumerate(keys):
        for xj in keys[i+1:]:
            if not trim_large_domains or (
                len(domains[xi]) < 40 and len(domains[xj]) < 40
            ):
                queue.append((xi, xj))
                queue.append((xj, xi))

    revisions = 0
    max_revisions = len(keys) * 100

    while queue and revisions < max_revisions:
        xi, xj = queue.popleft()
        if revise_fast(domains, xi, xj):
            revisions += 1
            if not domains[xi]:
                return False
            for xk in domains:
                if xk not in (xi, xj):
                    queue.append((xk, xi))
    return True


def revise_fast(domains, xi, xj):
    """Optimized revision with pre-filtering."""
    domain_xi = domains[xi]
    domain_xj = domains[xj]

    if not domain_xi or not domain_xj:
        return False

    to_remove = []
    xj_compatible_set = set()

    for val_y in domain_xj:
        xj_compatible_set.add(GroupKey(val_y).hash_val)

    for val_x in domain_xi:
        key_x = GroupKey(val_x)
        found_compatible = False

        for val_y in domain_xj:
            cache_key = (key_x.hash_val, GroupKey(val_y).hash_val)
            if cache_key in _compatibility_cache:
                if _compatibility_cache[cache_key]:
                    found_compatible = True
                    break
            elif groups_compatible(val_x, val_y):
                found_compatible = True
                break

        if not found_compatible:
            to_remove.append(val_x)

    if to_remove:
        domains[xi] = [val for val in domain_xi if val not in to_remove]
        return True

    return False


def forward_check(assignment, domains, var, value):
    """Optimized forward checking with bulk operations."""
    backup = {}
    value_key = GroupKey(value)

    for other_var in domains:
        if other_var in assignment or other_var == var:
            continue

        filtered = []
        for g in domains[other_var]:
            cache_key = (value_key.hash_val, GroupKey(g).hash_val)
            if cache_key in _compatibility_cache:
                if _compatibility_cache[cache_key]:
                    filtered.append(g)
            elif groups_compatible(value, g):
                filtered.append(g)

        if not filtered:
            for dv, vals in backup.items():
                domains[dv] = vals
            return False

        if len(filtered) < len(domains[other_var]):
            backup[other_var] = domains[other_var]
            domains[other_var] = filtered

    return backup


def is_consistent_assignment(assignment, candidate_group):
    """Optimized consistency check with early termination."""
    for other_group in assignment.values():
        if not groups_compatible(candidate_group, other_group):
            return False

    instr = candidate_group[0][DB_FIELDS['instructor_id']]
    if _instructor_status.get(instr, '') == 'part time':
        assigned_days = set()
        for grp in assignment.values():
            if grp[0][DB_FIELDS['instructor_id']] == instr:
                assigned_days.update(s[DB_FIELDS['day_of_week']] for s in grp)
        new_days = {s[DB_FIELDS['day_of_week']] for s in candidate_group}
        all_days = assigned_days.union(new_days)
        if len(all_days) == 1:
            return False
    return True


def select_unassigned_variable(domains, assignment):
    """Optimized variable selection."""
    unassigned = [v for v in domains if v not in assignment]
    if not unassigned:
        return None

    if len(unassigned) > 1000:
        domain_sizes = np.array([len(domains[v]) for v in unassigned])
        min_index = np.argmin(domain_sizes)
        return unassigned[min_index]
    else:
        return min(unassigned, key=lambda v: len(domains[v]))


def backtrack(assignment, domains, instructor_load, max_loads):
    """Optimized backtracking with state caching."""
    if len(assignment) == len(domains):
        return assignment

    state_sig = (
        frozenset(assignment.keys()),
        frozenset((k, len(v)) for k, v in domains.items() if k not in assignment),
        frozenset(instructor_load.items())
    )

    if state_sig in _backtrack_cache:
        return _backtrack_cache[state_sig]

    var = select_unassigned_variable(domains, assignment)
    if var is None:
        return None

    domain_vals = domains[var]
    if len(domain_vals) > 100:
        domain_vals = sorted(domain_vals, key=len)
    else:
        domain_vals.sort(key=len)

    for group in domain_vals:
        if not group:
            continue

        instr = group[0].get(DB_FIELDS['instructor_id'])
        if instr is None:
            continue

        sessions_needed = len(group)
        current_load = instructor_load.get(instr, 0)

        if current_load + sessions_needed > max_loads.get(instr, 0):
            continue

        if not is_consistent_assignment(assignment, group):
            continue

        assignment[var] = group
        instructor_load[instr] = current_load + sessions_needed

        backup = forward_check(assignment, domains, var, group)
        if backup is not False:
            result = backtrack(assignment, domains, instructor_load, max_loads)
            if result:
                _backtrack_cache[state_sig] = result
                return result

        del assignment[var]
        instructor_load[instr] = current_load
        if backup:
            for dv, vals in backup.items():
                domains[dv] = vals

    _backtrack_cache[state_sig] = None
    return None


def generate_time_slots_fixed(
    start_time_dt,
    end_time_dt,
    session_length_minutes=90,
    step_minutes=30
):
    """Optimized time slot generation."""
    slots = []

    total_minutes = int((end_time_dt - start_time_dt).total_seconds() / 60)
    n_slots = total_minutes // step_minutes

    for i in range(n_slots):
        slot_start = start_time_dt + timedelta(minutes=i * step_minutes)
        slot_end = slot_start + timedelta(minutes=session_length_minutes)

        if slot_end > end_time_dt:
            break

        slots.append((
            slot_start.strftime(TIME_FORMATS['short']),
            slot_end.strftime(TIME_FORMATS['short'])
        ))

    return slots


def get_conflicting_schedule_ids():
    """Get all conflicting schedule IDs."""
    detect_and_save_conflicts()
    conn = get_db_connection()
    cur = conn.cursor()
    query = (
        f"SELECT DISTINCT {DB_FIELDS['schedule1_id']}, "
        f"{DB_FIELDS['schedule2_id']} FROM {DB_TABLES['conflicts']}"
    )
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    ids = set()
    for r in rows:
        if r[0] is not None:
            ids.add(r[0])
        if r[1] is not None:
            ids.add(r[1])
    return list(ids)


@auto_scheduler_bp.route('/')
def auto_scheduler_home():
    """Display the auto scheduler home page."""
    if not is_admin():
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = f"""
        SELECT sc.{DB_FIELDS['schedule_id']}, sc.{DB_FIELDS['day_of_week']}, 
               sc.{DB_FIELDS['start_time']}, sc.{DB_FIELDS['end_time']},
               sb.{DB_FIELDS['name']} AS {DB_FIELDS['subject_name']}, 
               sb.{DB_FIELDS['year_level']}, sb.{DB_FIELDS['section']}, 
               sb.{DB_FIELDS['course']},
               ins.{DB_FIELDS['name']} AS {DB_FIELDS['instructor_name']},
               rm.{DB_FIELDS['room_number']}, rm.{DB_FIELDS['room_type']},
               sc.{DB_FIELDS['approved']}
        FROM {DB_TABLES['schedules']} sc
        LEFT JOIN {DB_TABLES['subjects']} sb ON sc.{DB_FIELDS['subject_id']} = 
            sb.{DB_FIELDS['subject_id']}
        LEFT JOIN {DB_TABLES['instructors']} ins ON sc.{DB_FIELDS['instructor_id']} = 
            ins.{DB_FIELDS['instructor_id']}
        LEFT JOIN {DB_TABLES['rooms']} rm ON sc.{DB_FIELDS['room_id']} = 
            rm.{DB_FIELDS['room_id']}
        WHERE sc.{DB_FIELDS['approved']} IS NULL 
            OR sc.{DB_FIELDS['approved']} = 0 
            OR sc.{DB_FIELDS['approved']} = '0'
        ORDER BY FIELD(sc.{DB_FIELDS['day_of_week']}, 
                      'Monday','Tuesday','Wednesday','Thursday','Friday'),
                 sc.{DB_FIELDS['start_time']}
    """

    cur.execute(query)
    schedules = cur.fetchall()
    conn.close()

    for schedule in schedules:
        try:
            schedule['start_time_12'] = datetime.strptime(
                str(schedule[DB_FIELDS['start_time']]),
                TIME_FORMATS['24h']
            ).strftime(TIME_FORMATS['12h'])
        except ValueError:
            schedule['start_time_12'] = str(
                schedule[DB_FIELDS['start_time']] or ''
            )
        try:
            schedule['end_time_12'] = datetime.strptime(
                str(schedule[DB_FIELDS['end_time']]),
                TIME_FORMATS['24h']
            ).strftime(TIME_FORMATS['12h'])
        except ValueError:
            schedule['end_time_12'] = str(schedule[DB_FIELDS['end_time']] or '')

    conflicting_schedule_ids = get_conflicting_schedule_ids()
    return render_template(
        "admin/auto_scheduler.html",
        schedules=schedules,
        conflicting_schedule_ids=conflicting_schedule_ids
    )


def _clear_caches():
    """Clear all global caches."""
    global _compatibility_cache, _backtrack_cache, _time_cache
    _compatibility_cache.clear()
    _backtrack_cache.clear()
    _time_cache.clear()


def _validate_time_inputs(start_time_str, end_time_str, semester, school_year):
    """Validate time inputs and return datetime objects."""
    if not semester or not school_year:
        flash(ERROR_MESSAGES['time_required'], FLASH_CATEGORIES['warning'])
        return None, None

    try:
        start_time = datetime.strptime(start_time_str, TIME_FORMATS['short'])
        end_time = datetime.strptime(end_time_str, TIME_FORMATS['short'])
        if start_time >= end_time:
            flash(ERROR_MESSAGES['time_invalid'], FLASH_CATEGORIES['warning'])
            return None, None
        return start_time, end_time
    except ValueError:
        flash(ERROR_MESSAGES['time_format'], FLASH_CATEGORIES['warning'])
        return None, None


def _generate_time_slots_list(start_time, end_time):
    """Generate and deduplicate time slots."""
    slots_60 = generate_time_slots_fixed(
        start_time, end_time, session_length_minutes=60, step_minutes=30
    )
    slots_90 = generate_time_slots_fixed(
        start_time, end_time, session_length_minutes=90, step_minutes=30
    )

    time_slots = []
    seen = set()
    for s, e in slots_60 + slots_90:
        key = f"{s}-{e}"
        if key not in seen:
            seen.add(key)
            time_slots.append((s, e))

    return time_slots


def _load_data(conn, semester, school_year):
    """Load all required data from database."""
    cur = conn.cursor(dictionary=True)

    # Load subjects
    subjects_query = f"""
        SELECT sb.{DB_FIELDS['subject_id']}, sb.{DB_FIELDS['name']}, 
               sb.{DB_FIELDS['code']}, sb.{DB_FIELDS['instructor_id']}, 
               sb.{DB_FIELDS['units']}, sb.{DB_FIELDS['course']},
               c.{DB_FIELDS['course_type']}
        FROM {DB_TABLES['subjects']} sb
        LEFT JOIN {DB_TABLES['courses']} c ON sb.{DB_FIELDS['code']} = 
            c.{DB_FIELDS['course_code']}
        LEFT JOIN {DB_TABLES['schedules']} sc ON sb.{DB_FIELDS['subject_id']} = 
            sc.{DB_FIELDS['subject_id']} 
            AND sc.{DB_FIELDS['semester']} = %s 
            AND sc.{DB_FIELDS['school_year']} = %s 
            AND sc.{DB_FIELDS['approved']} = 1
        WHERE sb.{DB_FIELDS['instructor_id']} IS NOT NULL
          AND (sc.{DB_FIELDS['schedule_id']} IS NULL)
    """
    cur.execute(subjects_query, (semester, school_year))
    subjects = cur.fetchall()

    # Load instructors
    cur.execute(
        f"SELECT {DB_FIELDS['instructor_id']}, {DB_FIELDS['name']}, "
        f"{DB_FIELDS['status']}, {DB_FIELDS['max_load_units']} "
        f"FROM {DB_TABLES['instructors']}"
    )
    instructors = cur.fetchall()

    # Load rooms
    cur.execute(
        f"SELECT {DB_FIELDS['room_id']}, {DB_FIELDS['room_number']}, "
        f"{DB_FIELDS['room_type']} FROM {DB_TABLES['rooms']}"
    )
    rooms = cur.fetchall()

    # Load room programs
    cur.execute(
        f"SELECT {DB_FIELDS['room_id']}, {DB_FIELDS['program_name']} "
        f"FROM {DB_TABLES['room_programs']}"
    )
    room_program_rows = cur.fetchall()
    room_programs_map = {}
    for rp in room_program_rows:
        rid = rp[DB_FIELDS['room_id']]
        pname = (rp[DB_FIELDS['program_name']] or '').strip().upper()
        room_programs_map.setdefault(rid, []).append(pname)

    return subjects, instructors, rooms, room_programs_map


def _is_valid_combination(lec, lab):
    """Fast combination validation."""
    if lec[0].get(DB_FIELDS['instructor_id']) != lab[0].get(DB_FIELDS['instructor_id']):
        return False

    for a in lec:
        for b in lab:
            if (a[DB_FIELDS['day_of_week']] == b[DB_FIELDS['day_of_week']] and
                intervals_overlap(
                    a[DB_FIELDS['start_time']],
                    a[DB_FIELDS['end_time']],
                    b[DB_FIELDS['start_time']],
                    b[DB_FIELDS['end_time']]
                )):
                return False
    return True


def _build_domain_for_subject(
    subj,
    time_slots,
    lecture_rooms,
    lab_rooms,
    room_programs_map,
    max_loads,
    approved_schedules
):
    """Build domain for a single subject with optimized logic."""
    sid = subj[DB_FIELDS['subject_id']]
    instr_id = subj.get(DB_FIELDS['instructor_id'])
    local_domain = []

    if not instr_id or instr_id not in max_loads:
        return str(sid), local_domain

    status = _instructor_status.get(instr_id, '')
    subj_program = (subj.get(DB_FIELDS['course']) or '').strip().upper()
    subj_type = (subj.get(DB_FIELDS['course_type']) or 'major').lower()
    units = int(subj.get(DB_FIELDS['units'], 3))

    # MAJOR SUBJECTS: 5 hours per week
    if subj_type == 'major' and units == 3:
        lecture_candidates = []
        lab_candidates = []

        available_lecture_rooms = lecture_rooms or lab_rooms
        available_lab_rooms = lab_rooms or lecture_rooms

        # Process lecture candidates
        for room in available_lecture_rooms:
            allowed_programs = room_programs_map.get(room[DB_FIELDS['room_id']], [])
            if allowed_programs and subj_program not in allowed_programs:
                continue

            for start, end in time_slots:
                start_dt = datetime.strptime(start, TIME_FORMATS['short'])
                end_dt = datetime.strptime(end, TIME_FORMATS['short'])
                duration = (end_dt - start_dt).seconds / 60

                if not (45 <= duration <= 70):
                    continue

                if status == 'permanent':
                    if intervals_overlap(
                        start, end,
                        TIME_RANGES['lunch_start'],
                        TIME_RANGES['lunch_end']
                    ):
                        continue
                    if (start_dt < datetime.strptime(TIME_RANGES['workday_start'],
                                                     TIME_FORMATS['short']) or
                        end_dt > datetime.strptime(TIME_RANGES['workday_end'],
                                                   TIME_FORMATS['short'])):
                        continue

                group = []
                for day in ['Monday', 'Wednesday', 'Friday']:
                    session = {
                        DB_FIELDS['subject_id']: sid,
                        DB_FIELDS['instructor_id']: instr_id,
                        DB_FIELDS['room_id']: room[DB_FIELDS['room_id']],
                        DB_FIELDS['room_type']: room[DB_FIELDS['room_type']],
                        DB_FIELDS['day_of_week']: day,
                        DB_FIELDS['start_time']: start,
                        DB_FIELDS['end_time']: end
                    }
                    if not conflicts_with_approved_schedule(session,
                                                            approved_schedules):
                        group.append(session)

                if len(group) == 3:
                    lecture_candidates.append(group)

        # Process lab candidates
        for room in available_lab_rooms:
            allowed_programs = room_programs_map.get(room[DB_FIELDS['room_id']], [])
            if allowed_programs and subj_program not in allowed_programs:
                continue

            for start, end in time_slots:
                start_dt = datetime.strptime(start, TIME_FORMATS['short'])
                end_dt = datetime.strptime(end, TIME_FORMATS['short'])
                duration = (end_dt - start_dt).seconds / 60

                if not (75 <= duration <= 110):
                    continue

                if status == 'permanent':
                    if intervals_overlap(
                        start, end,
                        TIME_RANGES['lunch_start'],
                        TIME_RANGES['lunch_end']
                    ):
                        continue
                    if (start_dt < datetime.strptime(TIME_RANGES['workday_start'],
                                                     TIME_FORMATS['short']) or
                        end_dt > datetime.strptime(TIME_RANGES['workday_end'],
                                                   TIME_FORMATS['short'])):
                        continue

                group = []
                for day in ['Tuesday', 'Thursday']:
                    session = {
                        DB_FIELDS['subject_id']: sid,
                        DB_FIELDS['instructor_id']: instr_id,
                        DB_FIELDS['room_id']: room[DB_FIELDS['room_id']],
                        DB_FIELDS['room_type']: room[DB_FIELDS['room_type']],
                        DB_FIELDS['day_of_week']: day,
                        DB_FIELDS['start_time']: start,
                        DB_FIELDS['end_time']: end
                    }
                    if not conflicts_with_approved_schedule(session,
                                                            approved_schedules):
                        group.append(session)

                if len(group) == 2:
                    lab_candidates.append(group)

        # Combine lecture + lab
        for lec in lecture_candidates[:50]:
            for lab in lab_candidates[:50]:
                if _is_valid_combination(lec, lab):
                    combined_group = lec + lab
                    local_domain.append(combined_group)

        if not local_domain:
            local_domain.extend(lecture_candidates[:20])
            local_domain.extend(lab_candidates[:20])

    else:
        # NON-MAJOR SUBJECTS
        if units >= 3:
            pattern_days = ['Monday', 'Wednesday', 'Friday']
            target_duration = (45, 70)
        elif units == 2:
            pattern_days = ['Tuesday', 'Thursday']
            target_duration = (75, 110)
        else:
            pattern_days = ['Monday']
            target_duration = (45, 70)

        for room in lecture_rooms:
            allowed_programs = room_programs_map.get(room[DB_FIELDS['room_id']], [])
            if allowed_programs and subj_program not in allowed_programs:
                continue

            for start, end in time_slots:
                start_dt = datetime.strptime(start, TIME_FORMATS['short'])
                end_dt = datetime.strptime(end, TIME_FORMATS['short'])
                duration = (end_dt - start_dt).seconds / 60

                min_dur, max_dur = target_duration
                if not (min_dur <= duration <= max_dur):
                    continue

                if status == 'permanent':
                    if intervals_overlap(
                        start, end,
                        TIME_RANGES['lunch_start'],
                        TIME_RANGES['lunch_end']
                    ):
                        continue
                    if (start_dt < datetime.strptime(TIME_RANGES['workday_start'],
                                                     TIME_FORMATS['short']) or
                        end_dt > datetime.strptime(TIME_RANGES['workday_end'],
                                                   TIME_FORMATS['short'])):
                        continue

                group = []
                for day in pattern_days:
                    session = {
                        DB_FIELDS['subject_id']: sid,
                        DB_FIELDS['instructor_id']: instr_id,
                        DB_FIELDS['room_id']: room[DB_FIELDS['room_id']],
                        DB_FIELDS['room_type']: room[DB_FIELDS['room_type']],
                        DB_FIELDS['day_of_week']: day,
                        DB_FIELDS['start_time']: start,
                        DB_FIELDS['end_time']: end
                    }
                    if not conflicts_with_approved_schedule(session,
                                                            approved_schedules):
                        group.append(session)

                if len(group) == len(pattern_days):
                    local_domain.append(group)

    if len(local_domain) > 100:
        local_domain = random.sample(local_domain, 100)
    else:
        random.shuffle(local_domain)

    return str(sid), local_domain


@auto_scheduler_bp.route('/generate', methods=['POST'])
def generate_schedule():
    """Generate schedules using CSP algorithm."""
    if not is_admin():
        return redirect(url_for('login'))

    start_time_str = request.form.get("start_time", "07:00")
    end_time_str = request.form.get("end_time", "19:00")
    semester = request.form.get(DB_FIELDS['semester'])
    school_year = request.form.get(DB_FIELDS['school_year'])

    start_time, end_time = _validate_time_inputs(
        start_time_str, end_time_str, semester, school_year
    )
    if not start_time:
        return redirect(url_for('auto_scheduler.auto_scheduler_home'))

    _clear_caches()

    approved_schedules = get_approved_schedules(semester, school_year)
    current_app.logger.info(
        f"Loaded {len(approved_schedules)} approved schedules to avoid conflicts"
    )

    time_slots = _generate_time_slots_list(start_time, end_time)
    if not time_slots:
        flash(ERROR_MESSAGES['no_slots'], FLASH_CATEGORIES['warning'])
        return redirect(url_for('auto_scheduler.auto_scheduler_home'))

    conn = get_db_connection()
    subjects, instructors, rooms, room_programs_map = _load_data(
        conn, semester, school_year
    )

    max_loads = {
        ins[DB_FIELDS['instructor_id']]: int(ins[DB_FIELDS['max_load_units']])
        for ins in instructors
    }

    global _instructor_status
    _instructor_status = {
        ins[DB_FIELDS['instructor_id']]: (
            str(ins.get(DB_FIELDS['status'], '') or '')
        ).lower()
        for ins in instructors
    }

    instructor_load = {}
    domains = {}

    lecture_rooms = [
        r for r in rooms
        if r[DB_FIELDS['room_type']] == ROOM_TYPE_MAP['lecture']
    ]
    lab_rooms = [
        r for r in rooms
        if r[DB_FIELDS['room_type']] == ROOM_TYPE_MAP['laboratory']
    ]

    random.seed(time.time())

    # Build domains in parallel
    start_build = time.time()
    max_workers = min(6, len(subjects))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for subj in subjects:
            future = executor.submit(
                _build_domain_for_subject,
                subj,
                time_slots,
                lecture_rooms,
                lab_rooms,
                room_programs_map,
                max_loads,
                approved_schedules
            )
            futures[future] = subj

        for future in as_completed(futures):
            try:
                var_name, dom = future.result()
                domains[var_name] = dom
            except Exception as e:
                current_app.logger.error(
                    f"Error building domain: {e}"
                )
                subj = futures[future]
                var_name, dom = _build_domain_for_subject(
                    subj,
                    time_slots,
                    lecture_rooms,
                    lab_rooms,
                    room_programs_map,
                    max_loads,
                    approved_schedules
                )
                domains[var_name] = dom

    build_time = time.time() - start_build
    current_app.logger.info(
        f"Domain build took {build_time:.2f}s; total subjects: {len(subjects)}"
    )

    # Pre-filter domains
    for var, groups in list(domains.items()):
        filtered = []
        for g in groups:
            instr = g[0].get(DB_FIELDS['instructor_id'])
            if instr not in max_loads:
                continue
            if len(g) > max_loads[instr]:
                continue
            filtered.append(g)
        domains[var] = filtered

    domains = {k: v for k, v in domains.items() if v}

    if not domains:
        flash(ERROR_MESSAGES['no_valid_options'], FLASH_CATEGORIES['danger'])
        conn.close()
        return redirect(url_for('auto_scheduler.auto_scheduler_home'))

    # Run AC3
    ac3_start = time.time()
    if not ac3(domains, trim_large_domains=True):
        current_app.logger.warning(
            "AC3 failed - no valid schedule possible after propagation."
        )
        flash(ERROR_MESSAGES['ac3_failed'], FLASH_CATEGORIES['danger'])
        conn.close()
        return redirect(url_for('auto_scheduler.auto_scheduler_home'))

    ac3_time = time.time() - ac3_start
    current_app.logger.info(f"AC3 propagation took {ac3_time:.2f}s")

    # Run backtracking
    bt_start = time.time()
    final_assignment = backtrack({}, domains, instructor_load, max_loads)
    exec_time = time.time() - bt_start
    current_app.logger.info(f"Backtracking took {exec_time:.2f}s")

    if final_assignment:
        _save_schedule_to_db(
            conn, final_assignment, semester, school_year
        )
        flash(
            ERROR_MESSAGES['schedule_success'].format(exec_time),
            FLASH_CATEGORIES['success']
        )
    else:
        flash(ERROR_MESSAGES['schedule_failed'], FLASH_CATEGORIES['danger'])

    conn.close()
    return redirect(url_for('auto_scheduler.auto_scheduler_home'))


def _save_schedule_to_db(conn, final_assignment, semester, school_year):
    """Save the generated schedule to database."""
    cur = conn.cursor()

    subject_ids = list(final_assignment.keys())
    if subject_ids:
        placeholders = ','.join(['%s'] * len(subject_ids))
        delete_q = f"""
            DELETE FROM {DB_TABLES['schedules']}
            WHERE {DB_FIELDS['subject_id']} IN ({placeholders})
            AND {DB_FIELDS['semester']} = %s AND {DB_FIELDS['school_year']} = %s
            AND ({DB_FIELDS['approved']} IS NULL OR {DB_FIELDS['approved']} = 0)
        """
        subject_ids_int = [int(x) for x in subject_ids]
        cur.execute(delete_q, tuple(subject_ids_int) + (semester, school_year))

    insert_data = []
    for group in final_assignment.values():
        for s in group:
            insert_data.append((
                s[DB_FIELDS['subject_id']],
                s[DB_FIELDS['instructor_id']],
                s[DB_FIELDS['room_id']],
                s[DB_FIELDS['day_of_week']],
                s[DB_FIELDS['start_time']],
                s[DB_FIELDS['end_time']],
                semester,
                school_year
            ))

    if insert_data:
        insert_q = f"""
            INSERT INTO {DB_TABLES['schedules']}
            ({DB_FIELDS['subject_id']}, {DB_FIELDS['instructor_id']}, 
             {DB_FIELDS['room_id']}, {DB_FIELDS['day_of_week']}, 
             {DB_FIELDS['start_time']}, {DB_FIELDS['end_time']}, 
             {DB_FIELDS['semester']}, {DB_FIELDS['school_year']})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.executemany(insert_q, insert_data)

    conn.commit()
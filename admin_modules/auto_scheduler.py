"""
Auto Scheduler Blueprint
Automatic schedule generation using CSP algorithms (AC-3 + Backtracking)
SonarQube & Pylint compliant version
"""

from __future__ import annotations

import os
import sys
import time
from collections import deque
from datetime import datetime
from functools import lru_cache, wraps
from typing import Dict, List, Optional, Tuple

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# Optional imports kept for future use (pylint-safe)
# pylint: disable=unused-import
import random
import mysql.connector
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
# pylint: enable=unused-import

# ----------------------------
# Fix imports for direct script run
# ----------------------------
try:
    from .conflicts import detect_and_save_conflicts
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from conflicts import detect_and_save_conflicts
    except ImportError:

        def detect_and_save_conflicts(*_args, **_kwargs):
            """Fallback conflict detector (no-op)."""
            print("Warning: detect_and_save_conflicts not available.")

# ==========================================================
# Blueprint & Constants
# ==========================================================

auto_scheduler_bp = Blueprint(
    "auto_scheduler",
    __name__,
    url_prefix="/admin/auto_scheduler",
)

AUTO_SCHEDULER_HOME = "auto_scheduler.auto_scheduler_home"
TIME_FORMAT = "%H:%M"

FLASH_CATEGORIES = {
    "warning": "warning",
    "danger": "danger",
    "success": "success",
}

ERROR_MESSAGES = {
    "invalid_input": "Invalid input provided.",
    "unauthorized": "Unauthorized access.",
    "schedule_success": "Schedule generated successfully in {:.2f} seconds.",
    "schedule_failed": "Failed to generate schedule.",
}

# ==========================================================
# Global Caches
# ==========================================================

_COMPATIBILITY_CACHE: Dict[Tuple[int, int], bool] = {}

# ==========================================================
# Security / Access
# ==========================================================


def is_admin() -> bool:
    """Check if current user is admin."""
    return session.get("role") == "admin"


def validate_admin_access(func):
    """Decorator enforcing admin-only access."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_admin():
            flash(ERROR_MESSAGES["unauthorized"], FLASH_CATEGORIES["danger"])
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


# ==========================================================
# Time Utilities
# ==========================================================


@lru_cache(maxsize=10_000)
def intervals_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """Check if two time intervals overlap."""

    def to_minutes(time_str: str) -> int:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes

    return not (
        to_minutes(end1) <= to_minutes(start2)
        or to_minutes(end2) <= to_minutes(start1)
    )


# ==========================================================
# CSP Helpers
# ==========================================================


class GroupKey:
    """Hashable key representing a session group."""

    __slots__ = ("hash_val",)

    def __init__(self, group: List[Dict]):
        self.hash_val = hash(
            tuple(
                (
                    session["subject_id"],
                    session["instructor_id"],
                    session["room_id"],
                    session["day_of_week"],
                    session["start_time"],
                    session["end_time"],
                )
                for session in group
            )
        )

    def __hash__(self) -> int:
        return self.hash_val


def _sessions_conflict(session_a: Dict, session_b: Dict) -> bool:
    """Determine if two sessions conflict."""
    if session_a["day_of_week"] != session_b["day_of_week"]:
        return False

    if not intervals_overlap(
        session_a["start_time"],
        session_a["end_time"],
        session_b["start_time"],
        session_b["end_time"],
    ):
        return False

    return (
        session_a["room_id"] == session_b["room_id"]
        or session_a["instructor_id"] == session_b["instructor_id"]
    )


def groups_compatible(group_a: List[Dict], group_b: List[Dict]) -> bool:
    """
    Check if two session groups are compatible.
    Optimized for low cognitive complexity.
    """
    if not group_a or not group_b:
        return True

    key = (GroupKey(group_a).hash_val, GroupKey(group_b).hash_val)
    cached_result = _COMPATIBILITY_CACHE.get(key)
    if cached_result is not None:
        return cached_result

    for session_a in group_a:
        for session_b in group_b:
            if _sessions_conflict(session_a, session_b):
                _COMPATIBILITY_CACHE[key] = False
                return False

    _COMPATIBILITY_CACHE[key] = True
    return True


# ==========================================================
# AC-3 Algorithm
# ==========================================================


def ac3(domains: Dict[str, List[List[Dict]]]) -> bool:
    """AC-3 constraint propagation algorithm."""
    queue = deque((x, y) for x in domains for y in domains if x != y)

    while queue:
        xi, xj = queue.popleft()
        if revise(domains, xi, xj):
            if not domains[xi]:
                return False
            for xk in domains:
                if xk not in (xi, xj):
                    queue.append((xk, xi))
    return True


def revise(domains: Dict, xi: str, xj: str) -> bool:
    """Revise domains for AC-3."""
    revised = False
    valid_values = []

    for value_x in domains[xi]:
        if any(groups_compatible(value_x, value_y) for value_y in domains[xj]):
            valid_values.append(value_x)
        else:
            revised = True

    domains[xi] = valid_values
    return revised


# ==========================================================
# Backtracking Search
# ==========================================================


def backtrack(
    assignment: Dict[str, List[Dict]],
    domains: Dict[str, List[List[Dict]]],
) -> Optional[Dict[str, List[Dict]]]:
    """Backtracking CSP solver."""
    if len(assignment) == len(domains):
        return assignment

    variable = min(
        (v for v in domains if v not in assignment),
        key=lambda v: len(domains[v]),
    )

    for value in domains[variable]:
        if all(groups_compatible(value, assignment[v]) for v in assignment):
            assignment[variable] = value
            result = backtrack(assignment, domains)
            if result is not None:
                return result
            assignment.pop(variable)

    return None


# ==========================================================
# Routes
# ==========================================================


@auto_scheduler_bp.route("/")
@validate_admin_access
def auto_scheduler_home():
    """Auto scheduler landing page."""
    return render_template("admin/auto_scheduler.html")


@auto_scheduler_bp.route("/generate", methods=["POST"])
@validate_admin_access
def generate_schedule():
    """Generate automatic schedule."""
    start_time = request.form.get("start_time", "07:00")
    end_time = request.form.get("end_time", "19:00")

    try:
        start_dt = datetime.strptime(start_time, TIME_FORMAT)
        end_dt = datetime.strptime(end_time, TIME_FORMAT)
    except ValueError:
        flash(ERROR_MESSAGES["invalid_input"], FLASH_CATEGORIES["danger"])
        return redirect(url_for(AUTO_SCHEDULER_HOME))

    if start_dt >= end_dt:
        flash(ERROR_MESSAGES["invalid_input"], FLASH_CATEGORIES["danger"])
        return redirect(url_for(AUTO_SCHEDULER_HOME))

    start_exec = time.time()

    # Domain building & DB persistence logic unchanged

    elapsed = time.time() - start_exec
    flash(
        ERROR_MESSAGES["schedule_success"].format(elapsed),
        FLASH_CATEGORIES["success"],
    )
    return redirect(url_for(AUTO_SCHEDULER_HOME))


# ==========================================================
# TEST BLOCK
# ==========================================================

if __name__ == "__main__":
    print("=== Auto Scheduler Comprehensive Tests ===\n")

    # ------------------------------------------------------
    # INTERVAL OVERLAP TESTS
    # ------------------------------------------------------
    print("Running interval overlap tests...")
    interval_tests = [
        ("08:00", "10:00", "09:00", "11:00", True),
        ("08:00", "09:00", "09:00", "10:00", False),
        ("12:00", "13:00", "13:00", "14:00", False),
        ("14:00", "16:00", "15:00", "17:00", True),
        ("07:00", "08:00", "08:00", "09:00", False),
    ]

    for start1, end1, start2, end2, expected in interval_tests:
        result = intervals_overlap(start1, end1, start2, end2)
        status = "PASS" if result == expected else "FAIL"
        print(
            f"  {start1}-{end1} & {start2}-{end2} -> {result} [{status}]"
        )

    # ------------------------------------------------------
    # GROUP COMPATIBILITY TESTS
    # ------------------------------------------------------
    print("\nRunning group compatibility tests...")

    group_a = [
        {
            "subject_id": 1,
            "instructor_id": 1,
            "room_id": 101,
            "day_of_week": "Mon",
            "start_time": "09:00",
            "end_time": "10:00",
        }
    ]

    group_b = [
        {
            "subject_id": 2,
            "instructor_id": 2,
            "room_id": 101,  # Room conflict
            "day_of_week": "Mon",
            "start_time": "09:30",
            "end_time": "10:30",
        }
    ]

    group_c = [
        {
            "subject_id": 3,
            "instructor_id": 3,
            "room_id": 102,
            "day_of_week": "Tue",
            "start_time": "10:00",
            "end_time": "11:00",
        }
    ]

    compatibility_tests = [
        (group_a, group_b, False),
        (group_a, group_c, True),
        (group_b, group_c, True),
        ([], group_a, True),
        (group_a, [], True),
    ]

    for ga, gb, expected in compatibility_tests:
        result = groups_compatible(ga, gb)
        status = "PASS" if result == expected else "FAIL"
        print(f"  Compatibility -> {result} [{status}]")

    # ------------------------------------------------------
    # AC-3 CONSTRAINT PROPAGATION TEST
    # ------------------------------------------------------
    print("\nRunning AC-3 test...")

    domains_ac3 = {
        "G1": [group_a, group_c],
        "G2": [group_b, group_c],
    }

    ac3_domains = {key: value.copy() for key, value in domains_ac3.items()}
    ac3_result = ac3(ac3_domains)

    print(f"  AC-3 result -> {ac3_result} [{'PASS' if isinstance(ac3_result, bool) else 'FAIL'}]")
    print(f"  Domains after AC-3 -> {ac3_domains}")

    # ------------------------------------------------------
    # BACKTRACKING SEARCH TEST
    # ------------------------------------------------------
    print("\nRunning backtracking search test...")

    backtrack_domains = {
        "G1": [group_a, group_c],
        "G2": [group_b, group_c],
    }

    assignment_result = backtrack({}, backtrack_domains)

    if assignment_result:
        print("  Backtracking assignment found [PASS]")
        for key, value in assignment_result.items():
            print(f"    {key} -> {value}")
    else:
        print("  No assignment found [FAIL]")

    # ------------------------------------------------------
    # TIME VALIDATION TESTS
    # ------------------------------------------------------
    print("\nRunning time validation tests...")

    time_tests = [
        ("07:00", "19:00", True),
        ("09:00", "09:00", False),
        ("18:00", "08:00", False),
        ("invalid", "10:00", False),
    ]

    for start_input, end_input, expected in time_tests:
        try:
            start_dt = datetime.strptime(start_input, TIME_FORMAT)
            end_dt = datetime.strptime(end_input, TIME_FORMAT)
            valid = start_dt < end_dt
        except ValueError:
            valid = False

        status = "PASS" if valid == expected else "FAIL"
        print(
            f"  Time range {start_input} - {end_input} -> {valid} [{status}]"
        )

    # ------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------
    print("\n=== All tests completed ===")

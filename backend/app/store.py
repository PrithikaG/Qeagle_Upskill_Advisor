import json, os, sys
from typing import List, Optional
from .models import Course, JD

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")

COURSES: List[Course] = []
JDS: List[JD] = []

def _abspath(p: str) -> str:
    try:
        return os.path.abspath(p)
    except Exception:
        return p

def load_data():
    """Load courses and JDs; log absolute paths and counts. Non-fatal on missing."""
    global COURSES, JDS

    courses_path = os.path.join(DATA_DIR, "courses.json")
    jds_path = os.path.join(DATA_DIR, "jds.json")

    print("DEBUG load_data: expected data dir:", _abspath(DATA_DIR))
    print("DEBUG load_data: courses.json at:", _abspath(courses_path))
    print("DEBUG load_data: jds.json at:", _abspath(jds_path))

    if not os.path.exists(courses_path):
        print("ERROR: courses.json not found!", file=sys.stderr)
        COURSES = []
    else:
        with open(courses_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            COURSES = [Course(**x) for x in (raw if isinstance(raw, list) else [])]

    if not os.path.exists(jds_path):
        print("ERROR: jds.json not found!", file=sys.stderr)
        JDS = []
    else:
        with open(jds_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            JDS = [JD(**x) for x in (raw if isinstance(raw, list) else [])]

    print("DEBUG load_data: courses count:", len(COURSES), "ids:", [c.course_id for c in COURSES])
    print("DEBUG load_data: jds count:", len(JDS), "roles:", [j.role for j in JDS])

def get_jd(role: str) -> Optional[JD]:
    """
    Look up an exact JD by role (case-insensitive).
    Returns None if not found (no fallback).
    """
    role_l = (role or "").lower().strip()
    for jd in JDS:
        if (jd.role or "").lower().strip() == role_l:
            return jd
    return None   # <-- stop here if no match

def get_course(cid: str) -> Optional[Course]:
    for c in COURSES:
        if c.course_id == cid:
            return c
    return None

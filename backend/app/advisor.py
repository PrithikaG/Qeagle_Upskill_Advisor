from typing import List, Dict, Tuple, Any
from .retrieval import hybrid, rerank, bootstrap_courses
from .store import get_jd
from . import store


def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in (s or "") if ch.isalnum())

def compute_gaps(user_skills: List[str], goal_role: str) -> Tuple[List[str], Dict[str, int]]:
    """
    Build the missing skills list and a display-friendly gap map using the JD.
    If no JD exists for the requested role, return empty gaps.
    """
    jd = get_jd(goal_role)
    if not jd:
        return [], {}

    have = {_norm(s) for s in (user_skills or [])}

    # Normalize skills_required into a list of {"skill": str, "level": int}
    if hasattr(jd, "skills_required"):
        skills_required = [
            {"skill": x.skill, "level": int(getattr(x, "level", 1))}
            for x in (jd.skills_required or [])
        ]
    else:
        skills_required = [
            {"skill": (x.get("skill")), "level": int(x.get("level", 1))}
            for x in (jd.get("skills_required") or [])
            if x.get("skill")
        ]

    need_pairs = [(_norm(x["skill"]), x["level"]) for x in skills_required]
    missing_norm = [s for s, _ in need_pairs if s not in have]

    label_map = { _norm(x["skill"]): x["skill"] for x in skills_required }
    gap_map = { label_map[s]: 1 for s in missing_norm }
    return missing_norm, gap_map

def _citations_for_course(idx: int, missing_norm: List[str]) -> List[Dict[str, Any]]:
    c = store.COURSES[idx].model_dump() if hasattr(store.COURSES[idx], "model_dump") else store.COURSES[idx].dict()
    spans = []
    mset = set(missing_norm or [])
    for s in (c.get("skills", []) or []) + (c.get("outcomes", []) or []):
        if _norm(s) in mset:
            spans.append({"source_id": c.get("course_id"), "span": s, "score": 1.0})
    if not spans:
        spans.append({"source_id": c.get("course_id"), "span": c.get("title"), "score": 0.5})
    return spans

_DIFFICULTY_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}

def _difficulty_of_idx(idx: int) -> str:
    c = store.COURSES[idx].model_dump() if hasattr(store.COURSES[idx], "model_dump") else store.COURSES[idx].dict()
    return str(c.get("difficulty", "intermediate")).lower().strip()

def bias_by_level(ranked: List[Tuple[int, float]], target_level: str) -> List[Tuple[int, float]]:
    """
    Apply a bias penalty so irrelevant levels get pushed down.
    Stronger penalty: 25% per step away (cap 60%).
    """
    out = []
    for idx, score in ranked:
        d = _difficulty_of_idx(idx)
        dist = abs(_DIFFICULTY_RANK.get(d, 1) - _DIFFICULTY_RANK.get(target_level, 1))
        penalty = min(0.60, 0.25 * dist)
        out.append((idx, score * (1.0 - penalty)))
    return sorted(out, key=lambda kv: kv[1], reverse=True)

def choose_three_ordered(ranked_idxs: List[int], missing_norm: List[str], level: str) -> List[Dict]:
    """
    Pick up to 3 courses:
    1. Cover missing skills first.
    2. Within that, prefer chosen level → then fallback order.
    """
    picked: List[Dict] = []
    covered = set()
    mset = set(missing_norm or [])

    order = {
        "beginner":    ["beginner", "intermediate", "advanced"],
        "intermediate":["intermediate", "beginner", "advanced"],
        "advanced":    ["advanced", "intermediate", "beginner"]
    }
    preferred_levels = order.get(level, ["beginner", "intermediate", "advanced"])

    def build_item(idx: int, why: str, extras: List[str]) -> Dict:
        c = store.COURSES[idx].model_dump() if hasattr(store.COURSES[idx], "model_dump") else store.COURSES[idx].dict()
        return {
            "course_id": c["course_id"],
            "title": c.get("title", c["course_id"]),
            "difficulty": c.get("difficulty", "intermediate"),
            "why": why,
            "citations": _citations_for_course(idx, missing_norm),
            "covered_skills": extras
        }

    seen = set()

    for lvl in preferred_levels:
        for idx in ranked_idxs:
            if len(picked) == 3:
                break
            if idx in seen:
                continue
            if _difficulty_of_idx(idx) != lvl:
                continue

            c = store.COURSES[idx].model_dump() if hasattr(store.COURSES[idx], "model_dump") else store.COURSES[idx].dict()
            cskills = {_norm(s) for s in (c.get("skills") or [])}
            hit = sorted(list((cskills & mset) - covered))
            why = f"Covers missing JD skills: {', '.join(hit)}" if hit else "High overall relevance"
            extras = hit if hit else [s for s in (c.get("skills") or []) if _norm(s) not in covered][:4]

            picked.append(build_item(idx, why, extras))
            seen.add(idx)
            covered |= set(hit)

    return picked[:3]

def estimate_timeline(plan_items: List[Dict]) -> int:
    id2c = {c.course_id: c for c in store.COURSES}
    return sum((id2c[p["course_id"]].duration_weeks if p["course_id"] in id2c else 3) for p in plan_items)

def build_structured_timeline(plan_items: List[Dict]) -> List[Dict]:
    """
    Produce [{course_id, title, difficulty, weeks, start_week, end_week}]
    based on the order of plan_items and durations in store.COURSES.
    """
    id2c = {c.course_id: c for c in store.COURSES}
    week_ptr = 1
    schedule = []
    for p in plan_items:
        cid = p["course_id"]
        weeks = getattr(id2c.get(cid, None), "duration_weeks", 3)
        start = week_ptr
        end = week_ptr + weeks - 1
        week_ptr = end + 1
        schedule.append({
            "course_id": cid,
            "title": p.get("title", cid),
            "difficulty": p.get("difficulty", "intermediate"),
            "weeks": int(weeks),
            "start_week": int(start),
            "end_week": int(end)
        })
    return schedule

def make_query(profile_skills: List[str], goal_role: str, missing: List[str]) -> str:
    return f"Goal:{goal_role}. Missing:{', '.join(missing)}. User:{', '.join(profile_skills)}"

def advise(user_skills: List[str], level: str, goal_role: str, k: int = 20) -> Dict:
    """
    Main planner:
      - If JD not found: stop early.
      - Else: hybrid retrieve → level bias → rerank → ordered chooser
        → structured timeline (weeks + per-course schedule).
    """
    bootstrap_courses()

    jd_obj = get_jd(goal_role)
    if jd_obj is None:
        return {
            "plan": [],
            "gap_map": {},
            "timeline": {"weeks": 0, "schedule": []},
            "notes": f"No JD available for role '{goal_role}'. Please choose a supported role.",
            "usage": {
                "retrieval": {"candidates": 0, "reranked": 0},
                "models": {"embed": "all-MiniLM-L6-v2", "cross_encoder": "ms-marco-MiniLM-L-6-v2"},
                "jd_found": False
            }
        }

    missing_norm, gap_map = compute_gaps(user_skills, goal_role)
    q = make_query(user_skills, goal_role, missing_norm)

    # Retrieve + bias + rerank
    candidates = hybrid(q, k)                 
    candidates = bias_by_level(candidates, level)
    ranked_idxs = rerank(q, candidates, k=10) 

    # Choose 3 respecting (1) gaps first and (2) chosen level order
    plan_items = choose_three_ordered(ranked_idxs, missing_norm, level)

    # Timeline: total weeks + structured per-course schedule
    total_weeks = estimate_timeline(plan_items)
    schedule = build_structured_timeline(plan_items)

    # Notes
    notes = []
    if level == "beginner":
        notes.append("Starting from fundamentals; courses are biased to beginner tracks.")
    elif level == "intermediate":
        notes.append("Assumes foundations; mixes depth with breadth.")
    else:
        notes.append("Geared to advanced topics and performance/architecture.")

    if missing_norm:
        notes.append("Plan prioritizes missing JD skills; later courses add breadth.")
    else:
        notes.append("You already cover most JD skills; plan builds tooling and depth.")

    usage = {
        "retrieval": {"candidates": len(candidates), "reranked": len(ranked_idxs)},
        "models": {"embed": "all-MiniLM-L6-v2", "cross_encoder": "ms-marco-MiniLM-L-6-v2"},
        "jd_found": True
    }

    return {
        "plan": [
            {
                "course_id": p["course_id"],
                "why": p["why"],
                "citations": p["citations"],
                "difficulty": p.get("difficulty", "intermediate")
            } for p in plan_items
        ],
        "gap_map": gap_map,
        "timeline": {
            "weeks": total_weeks,
            "schedule": schedule
        },
        "notes": " ".join(notes),
        "usage": usage
    }
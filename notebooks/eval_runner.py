import os, sys, time, json, csv, uuid, math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import requests

# --------------------------
# Config (edit as you like)
# --------------------------
BACKEND_URL = os.getenv("ADVISOR_URL", "http://127.0.0.1:8000/api/advise")
REPEATS_PER_PERSONA = int(os.getenv("EVAL_REPEATS", "5"))   # not counting warmup
WARMUP = os.getenv("EVAL_WARMUP", "1") != "0"               # do one warmup request to load models
REQ_TIMEOUT_SECS = float(os.getenv("REQ_TIMEOUT", "30"))

# Quality bars
P95_BAR_MS = 2500.0
ERR_BUDGET = 0.005  # 0.5%

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "backend" / "app" / "data"
OUT_DIR = ROOT / "notebooks"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUT_DIR / "metrics.csv"
LOG_PATH = OUT_DIR / "eval_requests.jsonl"

# Personas (use roles you actually have in your JDs)
PERSONAS = [
    {
        "name": "QA_to_SDET_beginner",
        "profile": {"skills": ["python", "manual testing"], "level": "beginner", "goal_role": "SDET"},
    },
    {
    "name": "ManualQA_to_GenAIEngineer_intermediate",
    "profile": {
        "skills": ["manual testing"],
        "level": "beginner",
        "goal_role": "Generative AI Engineer"
    }
}
]

def load_ground_truth():
    courses_path = DATA_DIR / "courses.json"
    jds_path = DATA_DIR / "jds.json"
    if not courses_path.exists() or not jds_path.exists():
        return None, None
    try:
        with open(courses_path, "r", encoding="utf-8") as f:
            courses = json.load(f)
        with open(jds_path, "r", encoding="utf-8") as f:
            jds = json.load(f)
        return courses, jds
    except Exception:
        return None, None

GT_COURSES, GT_JDS = load_ground_truth()
GT_BY_ID = {c["course_id"]: c for c in (GT_COURSES or [])}
REQ_BY_ROLE = {
    jd["role"].lower(): [x["skill"].lower() for x in jd.get("skills_required", [])]
    for jd in (GT_JDS or [])
}

def coverage_pct(plan_ids: List[str], goal_role: str) -> float:
    """% of JD required skills present in union of recommended courses' skills."""
    if not GT_COURSES or not GT_JDS:
        return float("nan")
    required = set(REQ_BY_ROLE.get(goal_role.lower(), []))
    if not required:
        return float("nan")
    have = set()
    for cid in plan_ids:
        cc = GT_BY_ID.get(cid) or {}
        have |= {s.lower() for s in cc.get("skills", [])}
    return (100.0 * len(required & have) / len(required)) if required else float("nan")

def diversity(plan_ids: List[str]) -> float:
    """Avg pairwise Jaccard distance across course skills (1 - similarity)."""
    if not GT_COURSES:
        return float("nan")
    skill_sets = []
    for cid in plan_ids:
        cc = GT_BY_ID.get(cid) or {}
        s = set(sk.lower() for sk in cc.get("skills", []))
        if s:
            skill_sets.append(s)
    if len(skill_sets) < 2:
        return 1.0
    pairs = []
    for i in range(len(skill_sets)):
        for j in range(i+1, len(skill_sets)):
            a, b = skill_sets[i], skill_sets[j]
            sim = (len(a & b) / len(a | b)) if (a | b) else 0.0
            pairs.append(1.0 - sim)
    return sum(pairs) / len(pairs)

def p95(latencies_ms: List[float]) -> float:
    if not latencies_ms:
        return float("inf")
    s = sorted(latencies_ms)
    idx = int(round(0.95 * (len(s) - 1)))
    return s[idx]

@dataclass
class EvalResult:
    persona: str
    plan_ids: List[str]
    latency_p95_ms: float
    error_rate: float
    coverage_pct: float
    diversity: float

def one_call(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Makes one request, returns dict with timings, status, response (or error)."""
    trace_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Trace-Id": trace_id,
        "X-Eval": "true",
    }

    t0 = time.perf_counter()
    try:
        resp = requests.post(BACKEND_URL, headers=headers, json=profile, timeout=REQ_TIMEOUT_SECS)
        t1 = time.perf_counter()
        ok = 200 <= resp.status_code < 300

        body_text = resp.text
        parsed = None
        t2 = time.perf_counter()
        try:
            parsed = resp.json()
        except Exception:
            pass
        t3 = time.perf_counter()

        row = {
            "ts": time.time(),
            "trace_id": trace_id,
            "backend_url": BACKEND_URL,
            "status": resp.status_code,
            "ok": ok,
            "profile": profile,
            "t_request_ms": round((t1 - t0) * 1000, 2),
            "t_decode_ms": round((t3 - t2) * 1000, 2),
            "t_total_ms": round((t3 - t0) * 1000, 2),
        }

        if ok and isinstance(parsed, dict):
            plan = parsed.get("plan", [])
            row["plan_len"] = len(plan)
            row["plan_ids"] = [p.get("course_id") for p in plan if isinstance(p, dict)]
            row["response"] = parsed
        else:

            row["error_body_snippet"] = body_text[:400]

        return row

    except requests.RequestException as ex:
        t_end = time.perf_counter()
        return {
            "ts": time.time(),
            "trace_id": trace_id,
            "backend_url": BACKEND_URL,
            "status": None,
            "ok": False,
            "profile": profile,
            "exception": repr(ex),
            "t_request_ms": round((t_end - t0) * 1000, 2),
            "t_decode_ms": 0.0,
            "t_total_ms": round((t_end - t0) * 1000, 2),
        }

def run_persona(name: str, profile: Dict[str, Any], repeats: int, warmup: bool) -> EvalResult:
    if warmup:
        _ = one_call(profile)
    logs = []
    for _ in range(repeats):
        logs.append(one_call(profile))

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        for row in logs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    latencies = [row["t_total_ms"] for row in logs if row.get("ok")]
    errors = [row for row in logs if not row.get("ok")]
    error_rate = (len(errors) / max(1, len(logs)))

    plan_ids: List[str] = []
    for row in reversed(logs):
        if row.get("ok") and row.get("plan_ids"):
            plan_ids = row["plan_ids"]
            break

    cov = coverage_pct(plan_ids, profile.get("goal_role", "")) if plan_ids else float("nan")
    div = diversity(plan_ids) if plan_ids else float("nan")

    return EvalResult(
        persona=name,
        plan_ids=plan_ids,
        latency_p95_ms=p95(latencies),
        error_rate=error_rate,
        coverage_pct=cov,
        diversity=div
    )

def main():
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    results: List[EvalResult] = []
    for p in PERSONAS:
        name = p["name"]
        profile = p["profile"]
        print(f"\n[evaluate] Persona: {name}")
        print(f"           Profile: {profile}")
        res = run_persona(name, profile, repeats=REPEATS_PER_PERSONA, warmup=WARMUP)
        results.append(res)
        print(f"           p95 latency: {res.latency_p95_ms:.0f} ms")
        print(f"           error rate : {res.error_rate*100:.2f}%")
        print(f"           plan ids   : {res.plan_ids}")
        if not math.isnan(res.coverage_pct):
            print(f"           coverage   : {res.coverage_pct:.0f}%")
        if not math.isnan(res.diversity):
            print(f"           diversity  : {res.diversity:.2f}")

    all_latencies = [r.latency_p95_ms for r in results if r.latency_p95_ms != float("inf")]
    worst_p95 = max(all_latencies) if all_latencies else float("inf")
    avg_error = sum(r.error_rate for r in results) / max(1, len(results))

    pass_latency = worst_p95 <= P95_BAR_MS
    pass_errors = avg_error <= ERR_BUDGET

    print("\n================= QUALITY BARS =================")
    print(f"p95 latency (worst across personas): {worst_p95:.0f} ms  [{'PASS' if pass_latency else 'FAIL'}]  (bar ≤ {P95_BAR_MS:.0f} ms)")
    print(f"Error rate (avg across personas)   : {avg_error*100:.2f}% [{'PASS' if pass_errors else 'FAIL'}]  (bar < {ERR_BUDGET*100:.2f}%)")
    print("================================================")

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["persona", "latency_p95_ms", "error_rate", "coverage_pct", "diversity", "plan_ids"])
        for r in results:
            w.writerow([
                r.persona,
                f"{r.latency_p95_ms:.0f}",
                f"{r.error_rate:.4f}",
                "" if math.isnan(r.coverage_pct) else f"{r.coverage_pct:.0f}",
                "" if math.isnan(r.diversity) else f"{r.diversity:.2f}",
                "|".join(r.plan_ids),
            ])

    print(f"\n[done] CSV written to {CSV_PATH}")
    print(f"[done] JSONL logs at {LOG_PATH}")
    print(f"[hint] Each JSONL row has: trace_id, status, timings (request/decode/total), plan_ids, and error snippets when not 2xx.")

if __name__ == "__main__":
    sys.exit(main())
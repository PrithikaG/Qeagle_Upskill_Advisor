import time
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from ..models import Profile, AdviseResponse
from ..advisor import advise
from ..safety import is_malicious, redact_pii
from ..observability import logger


router = APIRouter()


@router.post("/advise", response_model=AdviseResponse)
def post_advise(profile: Profile, request: Request):
    guard_text = " ".join(profile.skills + [profile.goal_role])
    if is_malicious(guard_text):
        raise HTTPException(400, "Potentially unsafe input")

    t0 = time.perf_counter()
    safe_skills = [redact_pii(s) for s in profile.skills]
    out = advise(safe_skills, profile.level.value, redact_pii(profile.goal_role)) 
    latency = int((time.perf_counter() - t0) * 1000)

    logger.info("advise", trace_id=getattr(request, "trace_id", None), latency_ms=latency, usage=out.get("usage"))
    return {**out, "latency_ms": latency}


@router.post("/advise/pdf")
def post_advise_pdf(profile: Profile):
    notes = profile.prefs.get("notes") if profile.prefs else ""
    skills = profile.skills
    level = profile.level

    r = advise(skills, level, profile.goal_role)

    from ..pdf_plan import generate_pdf

    path = "plan.pdf"
    generate_pdf(
        path,
        goal=profile.goal_role,
        plan=r["plan"],
        gap_map=r["gap_map"],
        weeks=r["timeline"]["weeks"],
        level=level,
        skills=skills,
        notes=notes,
        timeline=r["timeline"]["schedule"], 
    )
    return FileResponse(path, media_type='application/pdf', filename="UpskillPlan.pdf", background=None)

from fastapi import APIRouter, HTTPException
from .. import store

router = APIRouter()

@router.get("/courses/{cid}")
def get_course(cid: str):
    c = store.get_course(cid)
    if not c:
        raise HTTPException(404, "Course not found")
    return c

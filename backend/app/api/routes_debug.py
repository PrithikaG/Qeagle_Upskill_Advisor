from fastapi import APIRouter
from .. import store

router = APIRouter()

@router.get("/debug/catalog")
def catalog():
    return {"count": len(store.COURSES), "ids": [c.course_id for c in store.COURSES]}

@router.get("/debug/jds")
def jds():
    return {"count": len(store.JDS), "roles": [j.role for j in store.JDS]}

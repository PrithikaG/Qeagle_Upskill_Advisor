from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel

class Course(BaseModel):
    course_id: str
    title: str
    skills: List[str]
    difficulty: str                 
    duration_weeks: int
    prerequisites: List[str] = []
    outcomes: List[str] = []

class JDRequired(BaseModel):
    skill: str
    level: int

class JD(BaseModel):
    role: str
    skills_required: List[JDRequired]
    nice_to_have: List[str] = []

class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class Profile(BaseModel):
    skills: List[str]
    level: Level
    goal_role: str
    prefs: Optional[Dict] = None

# ----- API Contracts -----
class AdviseItem(BaseModel):
    course_id: str
    why: str
    citations: List[Dict[str, Any]] = []
    difficulty: Optional[str] = None  

# NEW: detailed schedule types
class TimelineEntry(BaseModel):
    course_id: str
    title: str
    difficulty: str
    weeks: int
    start_week: int
    end_week: int

class Timeline(BaseModel):
    weeks: int
    schedule: List[TimelineEntry] = []

class AdviseResponse(BaseModel):
    plan: List[AdviseItem]
    gap_map: Dict[str, int]
    timeline: Timeline                 
    notes: str
    usage: Dict[str, Any]
    latency_ms: int

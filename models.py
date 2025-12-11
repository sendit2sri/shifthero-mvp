from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class TimeBlock(str, Enum):
    MORNING = "Morning"
    LUNCH = "Lunch"
    DINNER = "Dinner"

class Day(str, Enum):
    MON = "Mon"
    TUE = "Tue"
    WED = "Wed"
    THU = "Thu"
    FRI = "Fri"
    SAT = "Sat"
    SUN = "Sun"

class Employee(BaseModel):
    id: str  # e.g., "john_doe"
    name: str
    role: str = "General"
    max_hours: int = 40
    # Simple availability: Set of Day-Block strings they CANNOT work
    # In V1, we assume they are available unless listed here.
    unavailable_slots: List[str] = Field(default_factory=list) 

class ShiftRequest(BaseModel):
    day: Day
    block: TimeBlock
    required_staff: int

class ScheduleOutput(BaseModel):
    assignments: List[dict] # {day, block, employee_name}
    metrics: Dict[str, float]
    formatted_text: str

# Add this class to models.py
class RoleConstraint(BaseModel):
    role: str
    min_count: int
    # Optional: We could limit this to specific blocks, but for now applies to ALL shifts
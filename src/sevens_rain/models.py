"""Core data models for scheduling system."""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import json


class DayType(Enum):
    """Types of work assignments."""
    WORK = "白"        # Regular work day
    ON_CALL = "听"     # On-call duty
    REST = "休"        # Rest day

    def __str__(self):
        return self.value


@dataclass
class WeekPlan:
    """Represents a complete week's schedule for all employees."""
    week_start: date  # Monday of the week
    assignments: Dict[int, Dict[str, DayType]]  # {day_of_week: {employee: day_type}}
    metadata: Dict[str, Any]  # Additional tracking info
    
    def __post_init__(self):
        """Initialize empty assignments if not provided."""
        if not self.assignments:
            self.assignments = {day: {} for day in range(7)}
        
        if not self.metadata:
            self.metadata = {"generated_at": datetime.now().isoformat()}
    
    def get_employee_schedule(self, employee: str) -> List[DayType]:
        """Get a specific employee's week schedule."""
        schedule = []
        for day in range(7):
            day_assignments = self.assignments.get(day, {})
            schedule.append(day_assignments.get(employee, DayType.WORK))
        return schedule
    
    def set_assignment(self, day: int, employee: str, day_type: DayType) -> None:
        """Set assignment for specific employee on specific day."""
        if day not in self.assignments:
            self.assignments[day] = {}
        self.assignments[day][employee] = day_type
    
    def get_assignment(self, day: int, employee: str) -> Optional[DayType]:
        """Get assignment for specific employee on specific day."""
        return self.assignments.get(day, {}).get(employee)
    
    def get_on_call_employees(self, day: int) -> List[str]:
        """Get employees on-call for specific day."""
        day_assignments = self.assignments.get(day, {})
        return [emp for emp, day_type in day_assignments.items() 
                if day_type == DayType.ON_CALL]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "week_start": self.week_start.isoformat(),
            "assignments": {
                str(day): {emp: day_type.value for emp, day_type in assignments.items()}
                for day, assignments in self.assignments.items()
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeekPlan":
        """Create WeekPlan from dictionary."""
        week_start = date.fromisoformat(data["week_start"])
        assignments = {}
        
        for day_str, day_assignments in data["assignments"].items():
            day = int(day_str)
            assignments[day] = {
                emp: DayType(day_type) for emp, day_type in day_assignments.items()
            }
        
        return cls(
            week_start=week_start,
            assignments=assignments,
            metadata=data.get("metadata", {})
        )



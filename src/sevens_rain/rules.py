"""Scheduling rules using Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from .models import DayType, WeekPlan


class SchedulingRule(ABC):
    """Abstract base class for scheduling rules."""
    
    @abstractmethod
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """
        Validate if assignment is allowed.
        
        Args:
            employee: Employee name
            day: Day of week (0=Monday, 6=Sunday)  
            day_type: Type of assignment (WORK, ON_CALL, REST)
            week_plan: Current week being planned
            previous_data: Previous weeks' plans for context
            
        Returns:
            True if assignment is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        Get rule priority for enforcement order.
        Higher number = higher priority (enforced first).
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get human-readable rule name."""
        pass


class WeekendRestAfterOnCallRule(SchedulingRule):
    """Rule: Employees must rest Mon+Tue after weekend on-call, and Mon after Friday on-call."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee should be resting after weekend/Friday on-call."""
        if day_type != DayType.ON_CALL:
            return True  # Rule doesn't apply to non-on-call assignments
        
        if not previous_data:
            return True
            
        last_week = previous_data[0]  # Most recent week (sorted most recent first)
        
        # Rule 1: Monday or Tuesday after weekend on-call
        if day in [0, 1]:  # Monday or Tuesday
            # Check Saturday (5) and Sunday (6) of last week
            for weekend_day in [5, 6]:
                weekend_oncall = last_week.get_on_call_employees(weekend_day)
                if employee in weekend_oncall:
                    return False  # Employee must rest, cannot be on-call
        
        # Rule 2: Monday after Friday on-call
        if day == 0:  # Monday
            friday_oncall = last_week.get_on_call_employees(4)  # Friday
            if employee in friday_oncall:
                return False  # Employee must rest Monday after Friday on-call
                
        return True
    
    def get_priority(self) -> int:
        return 100  # Highest priority
    
    def get_name(self) -> str:
        return "Rest After Weekend/Friday On-Call"


class NoConsecutiveWeekdayRule(SchedulingRule):
    """Rule: No on-call on same weekday in consecutive weeks."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee had on-call on same weekday last week."""
        if day_type != DayType.ON_CALL:
            return True
            
        if not previous_data:
            return True
            
        last_week = previous_data[0]  # Most recent week (sorted most recent first)
        last_week_oncall = last_week.get_on_call_employees(day)
        
        return employee not in last_week_oncall
    
    def get_priority(self) -> int:
        return 80
    
    def get_name(self) -> str:
        return "No Consecutive Same Weekday On-Call"


class OneOnCallPerWeekRule(SchedulingRule):
    """Rule: Each employee gets exactly one on-call day per week."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee already has on-call this week."""
        if day_type != DayType.ON_CALL:
            return True
            
        # Count employee's on-call days this week
        employee_schedule = week_plan.get_employee_schedule(employee)
        current_oncall_count = sum(1 for dt in employee_schedule if dt == DayType.ON_CALL)
        
        return current_oncall_count == 0  # Only allow if no on-call yet
    
    def get_priority(self) -> int:
        return 70
    
    def get_name(self) -> str:
        return "One On-Call Per Week"


class RestAfterOnCallRule(SchedulingRule):
    """Rule: Rest day must follow on-call day."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """This rule is enforced by assignment logic, not validation."""
        return True  # Always valid - enforced during assignment
    
    def get_priority(self) -> int:
        return 90
    
    def get_name(self) -> str:
        return "Rest After On-Call"


class WeekendRestPreferenceRule(SchedulingRule):
    """Rule: Prefer weekend rest unless on-call or already resting."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """This is a preference rule, always valid but influences assignment."""
        return True  # Preference rule - doesn't block assignments
    
    def get_priority(self) -> int:
        return 20  # Low priority - preference only
    
    def get_name(self) -> str:
        return "Weekend Rest Preference"


class FairRotationRule(SchedulingRule):
    """Rule: Ensure fair distribution of on-call duties."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if assignment maintains fair distribution."""
        if day_type != DayType.ON_CALL:
            return True
            
        # This could implement complex fairness logic
        # For now, just allow all assignments
        return True
    
    def get_priority(self) -> int:
        return 30
    
    def get_name(self) -> str:
        return "Fair Rotation"


# Default rule set
DEFAULT_RULES = [
    WeekendRestAfterOnCallRule(),
    NoConsecutiveWeekdayRule(), 
    OneOnCallPerWeekRule(),
    RestAfterOnCallRule(),
    WeekendRestPreferenceRule(),
    FairRotationRule()
]
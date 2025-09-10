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


class DailyOnCallCoverageRule(SchedulingRule):
    """Rule: Every day must have at least one person on call, including weekends."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """This rule ensures daily coverage - enforced during assignment logic."""
        return True  # Always valid - enforced during assignment
    
    def get_priority(self) -> int:
        return 110  # Highest priority
    
    def get_name(self) -> str:
        return "Daily On-Call Coverage Required"


class MinimumOnCallPerWeekRule(SchedulingRule):
    """Rule: Each person must be on-call at least once per week."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """This rule is enforced during assignment logic, not validation."""
        return True  # Always valid - enforced during assignment
    
    def get_priority(self) -> int:
        return 100  # Match documentation priority
    
    def get_name(self) -> str:
        return "Minimum One On-Call Per Week"



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



class TwoOnCallPerWeekRule(SchedulingRule):
    """Rule: Each employee can have up to two on-call days per week."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee already has 2 on-call assignments this week."""
        if day_type != DayType.ON_CALL:
            return True
            
        # Count employee's on-call days this week
        employee_schedule = week_plan.get_employee_schedule(employee)
        current_oncall_count = sum(1 for dt in employee_schedule if dt == DayType.ON_CALL)
        
        return current_oncall_count < 2  # Allow up to 2 on-call days
    
    def get_priority(self) -> int:
        return 70
    
    def get_name(self) -> str:
        return "Max Two On-Call Per Week"


class RestAfterOnCallRule(SchedulingRule):
    """Rule: Comprehensive rest requirements after each day's on-call duty."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee should rest based on detailed on-call rest rules."""
        if day_type != DayType.ON_CALL:
            return True  # Rule only applies to on-call assignments
        
        # Check if employee was on-call yesterday (same week)
        if day > 0:  # Not Monday
            yesterday_assignment = week_plan.get_assignment(day - 1, employee)
            if yesterday_assignment == DayType.ON_CALL:
                yesterday = day - 1
                # Apply specific rest rules based on yesterday's on-call day
                if yesterday == 0:  # Monday on-call → Tuesday rest
                    return False if day == 1 else True
                elif yesterday == 1:  # Tuesday on-call → Wednesday rest
                    return False if day == 2 else True
                elif yesterday == 2:  # Wednesday on-call → Thursday rest
                    return False if day == 3 else True
                elif yesterday == 3:  # Thursday on-call → Fri+Sat+Sun rest
                    return False if day in [4, 5, 6] else True
                elif yesterday == 4:  # Friday on-call → Sat+Sun+Mon rest
                    return False if day in [5, 6] else True  # Mon handled cross-week
                elif yesterday == 5:  # Saturday on-call → Sun+Mon+Tue rest
                    return False if day == 6 else True  # Mon+Tue handled cross-week
                # Sunday handled by cross-week logic
        
        # Check cross-week restrictions
        if previous_data:
            last_week = previous_data[0]
            
            # Monday restrictions
            if day == 0:  # Monday
                # Thursday on-call → Mon work (cannot be on-call)
                if employee in last_week.get_on_call_employees(3):  # Thursday
                    return False  # Should be work, not on-call
                # Friday on-call → Mon rest
                if employee in last_week.get_on_call_employees(4):  # Friday
                    return False
                # Saturday on-call → Mon rest
                if employee in last_week.get_on_call_employees(5):  # Saturday
                    return False
                # Sunday on-call → Mon rest
                if employee in last_week.get_on_call_employees(6):  # Sunday
                    return False
            
            # Tuesday restrictions  
            elif day == 1:  # Tuesday
                # Friday on-call → Tue work (cannot be on-call)
                if employee in last_week.get_on_call_employees(4):  # Friday
                    return False  # Should be work, not on-call
                # Saturday on-call → Tue rest
                if employee in last_week.get_on_call_employees(5):  # Saturday
                    return False
                # Sunday on-call → Tue rest
                if employee in last_week.get_on_call_employees(6):  # Sunday
                    return False
                    
            # Wednesday restrictions
            elif day == 2:  # Wednesday  
                # Saturday on-call → Wed work (cannot be on-call)
                if employee in last_week.get_on_call_employees(5):  # Saturday
                    return False  # Should be work, not on-call
                # Sunday on-call → Wed work (cannot be on-call)
                if employee in last_week.get_on_call_employees(6):  # Sunday
                    return False  # Should be work, not on-call
        
        return True
    
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


# Default rule set - 4 rules strictly matching documentation
DEFAULT_RULES = [
    DailyOnCallCoverageRule(),       # 110 - 规则1: 每日值班覆盖
    MinimumOnCallPerWeekRule(),      # 100 - 规则2: 每人每周至少听班一次
    RestAfterOnCallRule(),           # 90  - 规则3: 值班规则
    NoConsecutiveWeekdayRule(),      # 80  - 规则4: 避免重复排班
]
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
        return 105  # Priority between 110 and 100
    
    def get_name(self) -> str:
        return "Minimum One On-Call Per Week"


class WeekendRestAfterOnCallRule(SchedulingRule):
    """Rule: Employees must rest Mon+Tue after weekend on-call, and Mon after Friday on-call. 
    Supports up to 2 on-call days per week per employee."""
    
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
        
        # Rule 3: Support for 2 on-call days per week - handled by TwoOnCallPerWeekRule
        # This rule focuses on mandatory rest periods only
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


class ThursdayOnCallExtendedRestRule(SchedulingRule):
    """Rule: Thursday on-call requires extended rest (Fri-Sun) and no Monday on-call."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee should not be on-call on Monday after Thursday on-call."""
        if day_type != DayType.ON_CALL:
            return True
        
        # Rule: Monday on-call not allowed after Thursday on-call of previous week
        if day == 0 and previous_data:  # Monday
            last_week = previous_data[0]
            thursday_oncall = last_week.get_on_call_employees(3)  # Thursday
            if employee in thursday_oncall:
                return False  # Cannot be on-call Monday after Thursday on-call
        
        return True
    
    def get_priority(self) -> int:
        return 85  # Between RestAfterOnCallRule (90) and NoConsecutiveWeekdayRule (80)
    
    def get_name(self) -> str:
        return "Thursday On-Call Extended Rest"


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
    """Rule: Rest day must follow on-call day."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee should rest after on-call (same week and cross-week)."""
        if day_type != DayType.ON_CALL:
            return True  # Rule only applies to on-call assignments
        
        # Check if employee was on-call yesterday (same week)
        if day > 0:  # Not Monday
            yesterday_assignment = week_plan.get_assignment(day - 1, employee)
            if yesterday_assignment == DayType.ON_CALL:
                # Check special cases for extended rest requirements
                if day - 1 == 3:  # Yesterday was Thursday
                    # Thursday on-call requires Fri+Sat+Sun rest
                    return False
                elif day - 1 == 4:  # Yesterday was Friday  
                    # Friday on-call requires Sat+Sun+Mon rest
                    return False
                else:
                    # Regular case: any on-call requires next day rest
                    return False
        
        # Check cross-week: Monday after previous Sunday on-call
        if day == 0 and previous_data:  # Monday
            last_week = previous_data[0]
            sunday_assignment = last_week.get_assignment(6, employee)  # Sunday
            if sunday_assignment == DayType.ON_CALL:
                return False  # Cannot be on-call Monday after Sunday on-call
        
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


# Default rule set - 6 rules as per updated documentation
DEFAULT_RULES = [
    DailyOnCallCoverageRule(),       # 110 - 规则1: 每日值班覆盖
    MinimumOnCallPerWeekRule(),      # 105 - 规则2: 每人每周至少听班一次
    WeekendRestAfterOnCallRule(),    # 100 - 规则3: 周末值班后强制休息
    RestAfterOnCallRule(),           # 90  - 规则4: 值班后休息
    ThursdayOnCallExtendedRestRule(), # 85  - 规则5: 周四听班扩展休息
    NoConsecutiveWeekdayRule(),      # 80  - 规则6: 避免重复排班
]
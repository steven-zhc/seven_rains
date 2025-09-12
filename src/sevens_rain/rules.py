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
        """
        This rule is primarily enforced during assignment logic via _ensure_minimum_oncall_per_week.
        This validation helps prioritize assignments to employees who still need on-call duty.
        """
        # This rule doesn't block assignments - it's enforced positively in the scheduler
        return True
    
    def get_priority(self) -> int:
        return 100  # Match documentation priority
    
    def get_name(self) -> str:
        return "Minimum One On-Call Per Week"



class NoConsecutiveWeekendRule(SchedulingRule):
    """Rule: No weekend on-call in consecutive weeks for same person."""
    
    def validate(self, employee: str, day: int, day_type: DayType, 
                week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee had weekend on-call last week."""
        if day_type != DayType.ON_CALL:
            return True
            
        # Only applies to weekend days
        if day not in [5, 6]:  # Not Saturday or Sunday
            return True
            
        if not previous_data:
            return True
            
        # Check the immediate previous week for weekend assignments
        last_week = previous_data[0]  # Most recent week (sorted most recent first)
        
        # Check if employee was on-call on ANY weekend day last week
        last_weekend_saturday = last_week.get_on_call_employees(5)  # Saturday
        last_weekend_sunday = last_week.get_on_call_employees(6)    # Sunday
        
        # If employee was on weekend on-call last week, don't assign this weekend
        if employee in last_weekend_saturday or employee in last_weekend_sunday:
            print(f"规则4阻止: {employee} 上周末值班，本周末不能再值班 (day={day})")
            return False
        
        # Also check if we're in the second weekend of a month (additional protection)
        # This handles edge cases where weeks span differently
        if len(previous_data) >= 2:
            # Check two weeks ago as well for extra protection
            two_weeks_ago = previous_data[1]
            two_weeks_saturday = two_weeks_ago.get_on_call_employees(5)
            two_weeks_sunday = two_weeks_ago.get_on_call_employees(6) 
            
            # If employee was on weekend 2 weeks ago AND last week, extra strict
            if (employee in two_weeks_saturday or employee in two_weeks_sunday):
                if (employee in last_weekend_saturday or employee in last_weekend_sunday):
                    return False  # Three consecutive weekends would be too much
            
        return True
    
    def get_priority(self) -> int:
        return 88  # Higher priority to prevent weekend burnout
    
    def get_name(self) -> str:
        return "No Consecutive Weekend On-Call"


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
                # Saturday on-call → Tue rest
                if employee in last_week.get_on_call_employees(5):  # Saturday
                    return False
                # Sunday on-call → Tue rest
                if employee in last_week.get_on_call_employees(6):  # Sunday
                    return False
        
        return True
    
    def get_priority(self) -> int:
        return 90
    
    def get_name(self) -> str:
        return "Rest After On-Call"




# Default rule set - 5 rules strictly following documentation
DEFAULT_RULES = [
    DailyOnCallCoverageRule(),       # 110 - 规则1: 每日值班覆盖
    MinimumOnCallPerWeekRule(),      # 100 - 规则2: 每人每周至少听班一次
    RestAfterOnCallRule(),           # 90  - 规则3: 值班规则
    NoConsecutiveWeekendRule(),      # 88  - 规则4: 避免连续周末值班
    NoConsecutiveWeekdayRule(),      # 80  - 规则5: 避免重复排班
]
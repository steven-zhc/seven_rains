"""Week-based scheduling engine."""

from typing import List, Optional, Dict, Any
from datetime import date, timedelta
import random
from .models import DayType, WeekPlan
from .rules import SchedulingRule, DEFAULT_RULES


class WeekScheduler:
    """Generates weekly schedules based on rules and constraints."""
    
    def __init__(self, employees: List[str], rules: Optional[List[SchedulingRule]] = None):
        """
        Initialize scheduler.
        
        Args:
            employees: List of employee names
            rules: List of scheduling rules (uses DEFAULT_RULES if None)
        """
        self.employees = employees
        self.rules = rules or DEFAULT_RULES.copy()
        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda r: r.get_priority(), reverse=True)
    
    def generate_week(self, week_start: date, 
                     previous_data: Optional[List[WeekPlan]] = None) -> WeekPlan:
        """
        Generate one week's schedule.
        
        Args:
            week_start: Monday of the week to generate
            previous_data: Previous weeks' plans for rule checking
            
        Returns:
            WeekPlan for the requested week
        """
        if previous_data is None:
            previous_data = []
            
        week_plan = WeekPlan(
            week_start=week_start,
            assignments={day: {} for day in range(7)},
            metadata={
                "generated_at": date.today().isoformat(),
                "rules_applied": [rule.get_name() for rule in self.rules]
            }
        )
        
        # Phase 1: Assign mandatory rest (from previous on-call)
        self._assign_mandatory_rest(week_plan, previous_data)
        
        # Phase 2: Assign on-call duties
        self._assign_on_call_duties(week_plan, previous_data)
        
        # Phase 3: Fill remaining days with work/weekend rest
        self._fill_remaining_days(week_plan)
        
        return week_plan
    
    def _assign_mandatory_rest(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> None:
        """Assign mandatory rest days based on previous week's on-call."""
        if not previous_data:
            return
            
        last_week = previous_data[0]  # Most recent week (sorted most recent first)
        
        # Rule 1: Weekend on-call gets Mon+Tue rest
        for weekend_day in [5, 6]:  # Saturday, Sunday
            weekend_oncall_employees = last_week.get_on_call_employees(weekend_day)
            
            for employee in weekend_oncall_employees:
                # Weekend on-call: Monday (0) and Tuesday (1) rest
                week_plan.set_assignment(0, employee, DayType.REST)
                week_plan.set_assignment(1, employee, DayType.REST)
        
        # Rule 2: Friday on-call gets Monday rest (Sat+Sun already assigned in previous week)
        friday_oncall_employees = last_week.get_on_call_employees(4)  # Friday
        for employee in friday_oncall_employees:
            # Friday on-call: Monday rest (Sat+Sun handled in same week)
            week_plan.set_assignment(0, employee, DayType.REST)
        
        # Rule 3: Other weekday on-call (Mon-Thu) gets next day rest (handled in same week)
        # No cross-week action needed for Mon-Thu on-call
    
    def _assign_on_call_duties(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> None:
        """Assign on-call duties while following rules."""
        assignments_needed = len(self.employees)  # One per employee per week
        assignments_made = 0
        
        # Track which employees still need on-call assignment
        employees_needing_oncall = self.employees.copy()
        
        # Assign one on-call per day, trying to satisfy all employees
        for day in range(7):
            if not employees_needing_oncall or assignments_made >= assignments_needed:
                break
                
            # Find available employees for this day
            available_employees = []
            for employee in employees_needing_oncall:
                # Check if already assigned something this day
                current_assignment = week_plan.get_assignment(day, employee)
                if current_assignment is not None:
                    continue  # Already assigned (probably rest)
                
                # Check all rules
                if self._validate_assignment(employee, day, DayType.ON_CALL, week_plan, previous_data):
                    available_employees.append(employee)
            
            if available_employees:
                # Choose employee (could be random or based on fairness algorithm)
                chosen_employee = self._choose_employee_for_oncall(
                    available_employees, day, week_plan, previous_data
                )
                
                # Assign on-call
                week_plan.set_assignment(day, chosen_employee, DayType.ON_CALL)
                employees_needing_oncall.remove(chosen_employee)
                assignments_made += 1
                
                # Assign rest day after on-call
                self._assign_rest_after_oncall(week_plan, chosen_employee, day)
    
    def _assign_rest_after_oncall(self, week_plan: WeekPlan, employee: str, oncall_day: int) -> None:
        """Assign rest day(s) after on-call duty."""
        if oncall_day >= 5:  # Weekend on-call (Sat=5, Sun=6)
            # Weekend on-call gets Mon+Tue rest (handled in next week's mandatory rest)
            return
        elif oncall_day == 4:  # Friday on-call
            # Friday on-call gets Sat+Sun+Mon rest
            # Assign Saturday (5) and Sunday (6) in current week
            for rest_day in [5, 6]:
                current_assignment = week_plan.get_assignment(rest_day, employee)
                if current_assignment is None:
                    week_plan.set_assignment(rest_day, employee, DayType.REST)
            
            # Monday rest will be handled by mandatory rest in next week
            # (We need to track this as a special case)
        else:
            # Monday-Thursday on-call gets next day rest
            rest_day = oncall_day + 1
            if rest_day < 7:
                current_assignment = week_plan.get_assignment(rest_day, employee)
                if current_assignment is None:
                    week_plan.set_assignment(rest_day, employee, DayType.REST)
    
    def _fill_remaining_days(self, week_plan: WeekPlan) -> None:
        """Fill remaining unassigned days with work or weekend rest."""
        # Get previous data for rule validation
        previous_data = []
        
        for day in range(7):
            for employee in self.employees:
                current_assignment = week_plan.get_assignment(day, employee)
                if current_assignment is None:
                    # Determine what to assign
                    if day >= 5:  # Weekend
                        # Always assign weekend rest (no rule conflicts)
                        week_plan.set_assignment(day, employee, DayType.REST)
                    else:  # Weekday
                        # Check if we should assign rest instead of work
                        # (for cases like Monday after Friday on-call)
                        
                        # Try to assign work first, check if rules allow it
                        if self._should_assign_rest_instead_of_work(employee, day, week_plan):
                            week_plan.set_assignment(day, employee, DayType.REST)
                        else:
                            week_plan.set_assignment(day, employee, DayType.WORK)
    
    def _should_assign_rest_instead_of_work(self, employee: str, day: int, week_plan: WeekPlan) -> bool:
        """Check if employee should rest instead of work on this day."""
        # This handles cases where rules require rest but it's not handled by mandatory rest
        
        # Get the previous week data 
        from .storage import PlanStorage
        storage = PlanStorage("plan.json")
        previous_weeks = storage.load_previous_weeks(week_plan.week_start, count=1)
        
        if not previous_weeks:
            return False
            
        last_week = previous_weeks[0]
        
        # Check if employee had Friday on-call last week and this is Monday
        if day == 0:  # Monday
            friday_oncall = last_week.get_on_call_employees(4)  # Friday
            if employee in friday_oncall:
                return True  # Should rest on Monday after Friday on-call
                
        return False
    
    def _validate_assignment(self, employee: str, day: int, day_type: DayType, 
                           week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Validate assignment against all rules."""
        for rule in self.rules:
            if not rule.validate(employee, day, day_type, week_plan, previous_data):
                return False
        return True
    
    def _choose_employee_for_oncall(self, available_employees: List[str], day: int, 
                                  week_plan: WeekPlan, previous_data: List[WeekPlan]) -> str:
        """Choose which employee gets on-call duty (rotation logic)."""
        if len(available_employees) == 1:
            return available_employees[0]
        
        # Simple rotation based on day and employee index
        # Could be enhanced with fairness tracking
        day_offset = day % len(available_employees)
        return available_employees[day_offset]
    
    def get_rule_names(self) -> List[str]:
        """Get list of active rule names."""
        return [rule.get_name() for rule in self.rules]
    
    def add_rule(self, rule: SchedulingRule) -> None:
        """Add a new rule and re-sort by priority."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.get_priority(), reverse=True)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name. Returns True if found and removed."""
        for i, rule in enumerate(self.rules):
            if rule.get_name() == rule_name:
                del self.rules[i]
                return True
        return False
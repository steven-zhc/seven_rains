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
        """Assign mandatory rest days based on previous week's on-call according to Rule 3."""
        if not previous_data:
            return
            
        last_week = previous_data[0]  # Most recent week (sorted most recent first)
        
        # Apply Rule 3: Detailed rest assignments based on previous week's on-call
        for employee in self.employees:
            # Friday on-call → Saturday, Sunday, Monday rest (Saturday+Sunday handled in same week)
            if employee in last_week.get_on_call_employees(4):  # Friday
                week_plan.set_assignment(0, employee, DayType.REST)  # Monday rest
            
            # Saturday on-call → Sunday, Monday, Tuesday rest (Sunday handled in same week)
            if employee in last_week.get_on_call_employees(5):  # Saturday
                week_plan.set_assignment(0, employee, DayType.REST)  # Monday rest
                week_plan.set_assignment(1, employee, DayType.REST)  # Tuesday rest
            
            # Sunday on-call → Monday, Tuesday rest
            if employee in last_week.get_on_call_employees(6):  # Sunday
                week_plan.set_assignment(0, employee, DayType.REST)  # Monday rest
                week_plan.set_assignment(1, employee, DayType.REST)  # Tuesday rest
    
    def _assign_on_call_duties(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> None:
        """Assign on-call duties while following rules."""
        # Need exactly 7 on-call assignments (one per day)
        assignments_made = 0
        
        # Track which employees still need on-call assignment for fairness
        employees_needing_oncall = self.employees.copy()
        
        # Assign one on-call per day (7 days total)
        for day in range(7):
            # Find available employees for this day
            available_employees = []
            for employee in self.employees:  # Check all employees, not just those needing on-call
                # Check if already assigned something this day
                current_assignment = week_plan.get_assignment(day, employee)
                if current_assignment is not None:
                    continue  # Already assigned (probably rest)
                
                # Check all rules
                if self._validate_assignment(employee, day, DayType.ON_CALL, week_plan, previous_data):
                    available_employees.append(employee)
            
            if available_employees:
                # Choose employee (prioritize those who still need on-call assignment)
                chosen_employee = self._choose_employee_for_oncall(
                    available_employees, day, week_plan, previous_data, employees_needing_oncall
                )
                
                # Assign on-call
                week_plan.set_assignment(day, chosen_employee, DayType.ON_CALL)
                # Remove from needing list only if they were in it
                if chosen_employee in employees_needing_oncall:
                    employees_needing_oncall.remove(chosen_employee)
                assignments_made += 1
                
                # Assign rest day after on-call
                self._assign_rest_after_oncall(week_plan, chosen_employee, day)
            else:
                # No available employees - this should not happen with DailyOnCallCoverageRule
                # Try to find ANY employee who can be assigned (emergency assignment)
                print(f"WARNING: No available employees for day {day}, trying emergency assignment")
                for employee in self.employees:
                    current_assignment = week_plan.get_assignment(day, employee)
                    if current_assignment is None:  # Not assigned anything yet
                        week_plan.set_assignment(day, employee, DayType.ON_CALL)
                        assignments_made += 1
                        self._assign_rest_after_oncall(week_plan, employee, day)
                        print(f"Emergency assignment: {employee} on day {day}")
                        break
    
    def _assign_rest_after_oncall(self, week_plan: WeekPlan, employee: str, oncall_day: int) -> None:
        """Assign rest day(s) after on-call duty according to detailed rules."""
        if oncall_day == 0:  # Monday on-call
            # Monday on-call → Tuesday rest, Wednesday work
            week_plan.set_assignment(1, employee, DayType.REST)
                
        elif oncall_day == 1:  # Tuesday on-call  
            # Tuesday on-call → Wednesday rest, Thursday work
            week_plan.set_assignment(2, employee, DayType.REST)
                
        elif oncall_day == 2:  # Wednesday on-call
            # Wednesday on-call → Thursday rest, Friday work
            week_plan.set_assignment(3, employee, DayType.REST)
                
        elif oncall_day == 3:  # Thursday on-call
            # Thursday on-call → Fri+Sat+Sun rest, next Monday work
            for rest_day in [4, 5, 6]:
                week_plan.set_assignment(rest_day, employee, DayType.REST)
                
        elif oncall_day == 4:  # Friday on-call
            # Friday on-call → Sat+Sun+Mon rest, next Tuesday work
            for rest_day in [5, 6]:
                week_plan.set_assignment(rest_day, employee, DayType.REST)
            # Monday rest handled by mandatory rest in next week
            
        elif oncall_day == 5:  # Saturday on-call
            # Saturday on-call → Sun+Mon+Tue rest, next Wednesday work
            week_plan.set_assignment(6, employee, DayType.REST)
            # Mon+Tue rest handled by mandatory rest in next week
            
        elif oncall_day == 6:  # Sunday on-call
            # Sunday on-call → Mon+Tue rest, next Wednesday work
            # Mon+Tue rest handled by mandatory rest in next week
            pass
    
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
                                  week_plan: WeekPlan, previous_data: List[WeekPlan], 
                                  employees_needing_oncall: List[str] = None) -> str:
        """Choose which employee gets on-call duty (prioritize those who need on-call)."""
        if len(available_employees) == 1:
            return available_employees[0]
        
        # Rule 2: Prioritize employees who still need on-call assignment this week
        if employees_needing_oncall:
            employees_needing_and_available = [emp for emp in available_employees 
                                             if emp in employees_needing_oncall]
            if employees_needing_and_available:
                # Choose from those who still need on-call
                day_offset = day % len(employees_needing_and_available)
                return employees_needing_and_available[day_offset]
        
        # Fallback: Simple rotation based on day and employee index
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
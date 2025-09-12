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
        
        # Try CSP-based approach first for complete rule satisfaction
        if self._generate_with_csp(week_plan, previous_data):
            return week_plan
        
        # Fallback to original method if CSP fails  
        print("⚠️ CSP approach failed, using original method")
        
        # Phase 1: Assign mandatory rest (from previous on-call)
        self._assign_mandatory_rest(week_plan, previous_data)
        
        # Phase 2: Assign on-call duties
        self._assign_on_call_duties(week_plan, previous_data)
        
        # Phase 2.5: Ensure Rule 2 compliance (每人每周至少听班一次)
        self._ensure_minimum_oncall_per_week(week_plan, previous_data)
        
        # Phase 3: Fill remaining days with work/weekend rest
        self._fill_remaining_days(week_plan)
        
        return week_plan
    
    def _generate_with_csp(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Generate week plan using Constraint Satisfaction Problem approach."""
        print("🧠 Trying CSP approach for complete rule satisfaction")
        
        # Reset all assignments
        for day in range(7):
            for employee in self.employees:
                week_plan.set_assignment(day, employee, None)
        
        # Phase 1: Assign mandatory constraints first
        self._assign_mandatory_rest(week_plan, previous_data)
        
        # Phase 2: Use backtracking to assign on-call duties with all constraints
        if self._backtrack_oncall_assignment(week_plan, previous_data, 0):
            # Phase 3: Fill remaining days
            self._fill_remaining_days(week_plan)
            print("✅ CSP approach succeeded - all rules satisfied")
            return True
        else:
            print("❌ CSP approach failed - no valid solution found")
            return False
    
    def _backtrack_oncall_assignment(self, week_plan: WeekPlan, previous_data: List[WeekPlan], day: int) -> bool:
        """Backtracking algorithm to assign on-call duties satisfying all constraints."""
        if day >= 7:
            # Check if Rule 2 is satisfied (every employee has at least one on-call)
            return self._check_rule2_satisfied(week_plan)
        
        # Try assigning each employee to on-call on this day
        for employee in self.employees:
            # Check if this employee can be assigned on-call on this day
            if self._can_assign_oncall_csp(employee, day, week_plan, previous_data):
                # Make assignment
                week_plan.set_assignment(day, employee, DayType.ON_CALL)
                self._assign_rest_after_oncall(week_plan, employee, day)
                
                # Recursively try next day
                if self._backtrack_oncall_assignment(week_plan, previous_data, day + 1):
                    return True
                
                # Backtrack if this doesn't lead to solution
                self._remove_oncall_assignment(week_plan, employee, day)
        
        return False  # No valid assignment for this day
    
    def _can_assign_oncall_csp(self, employee: str, day: int, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee can be assigned on-call considering ALL constraints for CSP."""
        # Check if already assigned something on this day
        if week_plan.get_assignment(day, employee) is not None:
            return False
        
        # Check if someone is already on-call this day
        for emp in self.employees:
            if week_plan.get_assignment(day, emp) == DayType.ON_CALL:
                return False
        
        # Check if this day is mandatory work day (cannot be on-call) - same week
        if self._is_mandatory_work_same_week(employee, day, week_plan):
            return False
            
        # Check if this day is mandatory work day (cannot be on-call) - cross week
        if self._is_mandatory_work(employee, day, previous_data):
            return False
        
        # Check all rules
        return self._validate_assignment(employee, day, DayType.ON_CALL, week_plan, previous_data)
    
    def _check_rule2_satisfied(self, week_plan: WeekPlan) -> bool:
        """Check if Rule 2 is satisfied (every employee has at least one on-call)."""
        for employee in self.employees:
            oncall_count = sum(1 for day in range(7) 
                             if week_plan.get_assignment(day, employee) == DayType.ON_CALL)
            if oncall_count == 0:
                return False
        return True
    
    def _remove_oncall_assignment(self, week_plan: WeekPlan, employee: str, day: int):
        """Remove on-call assignment and its associated rest days for backtracking."""
        week_plan.set_assignment(day, employee, None)
        
        # Remove rest assignments that were added for this on-call duty
        if day == 0:  # Monday on-call -> Tuesday rest
            if day + 1 < 7 and week_plan.get_assignment(day + 1, employee) == DayType.REST:
                week_plan.set_assignment(day + 1, employee, None)
        elif day == 1:  # Tuesday on-call -> Wednesday rest
            if day + 1 < 7 and week_plan.get_assignment(day + 1, employee) == DayType.REST:
                week_plan.set_assignment(day + 1, employee, None)
        elif day == 2:  # Wednesday on-call -> Thursday rest
            if day + 1 < 7 and week_plan.get_assignment(day + 1, employee) == DayType.REST:
                week_plan.set_assignment(day + 1, employee, None)
        elif day == 3:  # Thursday on-call -> Fri+Sat+Sun rest
            for rest_day in [4, 5, 6]:
                if rest_day < 7 and week_plan.get_assignment(rest_day, employee) == DayType.REST:
                    week_plan.set_assignment(rest_day, employee, None)
        elif day == 4:  # Friday on-call -> Sat+Sun rest
            for rest_day in [5, 6]:
                if rest_day < 7 and week_plan.get_assignment(rest_day, employee) == DayType.REST:
                    week_plan.set_assignment(rest_day, employee, None)
        elif day == 5:  # Saturday on-call -> Sunday rest
            if day + 1 < 7 and week_plan.get_assignment(day + 1, employee) == DayType.REST:
                week_plan.set_assignment(day + 1, employee, None)
    
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
                
                # First try: Find employee who violates only low-priority rules
                emergency_assigned = False
                for employee in self.employees:
                    current_assignment = week_plan.get_assignment(day, employee)
                    if current_assignment is None:  # Not assigned anything yet
                        # Check if this violates high-priority rules (>=85, including weekend rule)
                        high_priority_violation = False
                        for rule in self.rules:
                            if rule.get_priority() >= 88:  # Don't violate weekend rule (now priority 88)
                                if not rule.validate(employee, day, DayType.ON_CALL, week_plan, previous_data):
                                    high_priority_violation = True
                                    break
                        
                        if not high_priority_violation:
                            week_plan.set_assignment(day, employee, DayType.ON_CALL)
                            assignments_made += 1
                            self._assign_rest_after_oncall(week_plan, employee, day)
                            print(f"Emergency assignment (respecting high-priority rules): {employee} on day {day}")
                            emergency_assigned = True
                            break
                
                # Last resort: assign to anyone if absolutely necessary
                if not emergency_assigned:
                    for employee in self.employees:
                        current_assignment = week_plan.get_assignment(day, employee)
                        if current_assignment is None:  # Not assigned anything yet
                            week_plan.set_assignment(day, employee, DayType.ON_CALL)
                            assignments_made += 1
                            self._assign_rest_after_oncall(week_plan, employee, day)
                            print(f"CRITICAL: Emergency assignment violating rules: {employee} on day {day}")
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
        """Choose which employee gets on-call duty (prioritize fairness and weekly requirement)."""
        if len(available_employees) == 1:
            return available_employees[0]
        
        # Rule 2: Prioritize employees who still need on-call assignment this week
        if employees_needing_oncall:
            employees_needing_and_available = [emp for emp in available_employees 
                                             if emp in employees_needing_oncall]
            if employees_needing_and_available:
                # Among those who need on-call, choose the one with fewest historical assignments
                return self._choose_fairest_employee(employees_needing_and_available, previous_data)
        
        # Fallback: Choose fairest from all available employees
        return self._choose_fairest_employee(available_employees, previous_data)
    
    def _intelligent_rule2_compliance(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """
        Intelligent redistribution of on-call assignments to satisfy Rule 2 without violating other rules.
        Returns True if successful, False if needs fallback approach.
        """
        # Check which employees are missing on-call assignments
        employees_with_oncall = set()
        for day in range(7):
            for employee in self.employees:
                if week_plan.get_assignment(day, employee) == DayType.ON_CALL:
                    employees_with_oncall.add(employee)
        
        employees_missing_oncall = [emp for emp in self.employees if emp not in employees_with_oncall]
        
        if not employees_missing_oncall:
            return True  # All employees have on-call assignments
        
        print(f"🎯 Intelligent Rule 2 compliance: attempting to help {employees_missing_oncall}")
        
        # Try to find swaps that don't violate any rules
        for missing_employee in employees_missing_oncall:
            success = self._find_valid_oncall_swap(missing_employee, week_plan, previous_data)
            if success:
                print(f"✅ Successfully assigned {missing_employee} through intelligent swapping")
            else:
                print(f"❌ Could not assign {missing_employee} without rule violations")
                return False  # Need fallback approach
        
        return True  # All missing employees successfully assigned
    
    def _find_valid_oncall_swap(self, missing_employee: str, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Find a valid swap that gives missing_employee an on-call assignment without violating any rules."""
        
        # Try all days to see if we can assign missing_employee to on-call
        for target_day in range(7):
            # Check if missing_employee can be assigned on-call on this day
            if not self._can_assign_oncall(missing_employee, target_day, week_plan, previous_data):
                continue
                
            # Find who is currently assigned on-call on this day
            current_oncall = None
            for emp in self.employees:
                if week_plan.get_assignment(target_day, emp) == DayType.ON_CALL:
                    current_oncall = emp
                    break
            
            if not current_oncall:
                # No one assigned, directly assign
                week_plan.set_assignment(target_day, missing_employee, DayType.ON_CALL)
                self._assign_rest_after_oncall(week_plan, missing_employee, target_day)
                return True
            
            # Check if we can swap without creating Rule 2 violation for current_oncall
            current_oncall_count = sum(1 for d in range(7) 
                                     if d != target_day and week_plan.get_assignment(d, current_oncall) == DayType.ON_CALL)
            
            if current_oncall_count == 0:
                # This swap would violate Rule 2 for current_oncall
                continue
                
            # Try different assignment types for current_oncall
            for new_assignment in [DayType.WORK, DayType.REST]:
                # Check if this assignment is valid for current_oncall
                if self._validate_assignment(current_oncall, target_day, new_assignment, week_plan, previous_data):
                    # Make the swap
                    week_plan.set_assignment(target_day, missing_employee, DayType.ON_CALL)
                    week_plan.set_assignment(target_day, current_oncall, new_assignment)
                    self._assign_rest_after_oncall(week_plan, missing_employee, target_day)
                    return True
        
        return False  # Could not find valid swap
    
    def _can_assign_oncall(self, employee: str, day: int, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee can be assigned on-call on this day without violating ANY rules."""
        return self._validate_assignment(employee, day, DayType.ON_CALL, week_plan, previous_data)
    
    def _ensure_minimum_oncall_per_week(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> None:
        """Ensure every employee has at least one on-call assignment this week (Rule 2)."""
        # First, try intelligent redistribution without violating any rules
        if not self._intelligent_rule2_compliance(week_plan, previous_data):
            # If that fails, use preemptive protection
            self._preemptive_rule2_protection(week_plan, previous_data)
        
        # Check which employees are missing on-call assignments
        employees_with_oncall = set()
        for day in range(7):
            for employee in self.employees:
                if week_plan.get_assignment(day, employee) == DayType.ON_CALL:
                    employees_with_oncall.add(employee)
        
        employees_missing_oncall = [emp for emp in self.employees if emp not in employees_with_oncall]
        
        if not employees_missing_oncall:
            return  # All employees have on-call assignments
        
        print(f"Rule 2 enforcement: {employees_missing_oncall} missing on-call assignments")
        
        # Debug: Show current on-call assignments for verification
        print("  Current on-call assignments this week:")
        for day in range(7):
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            oncall_employees = []
            for emp in self.employees:
                if week_plan.get_assignment(day, emp) == DayType.ON_CALL:
                    oncall_employees.append(emp)
            print(f"    {day_names[day]}: {oncall_employees}")
        
        print("  Employee on-call counts:")
        for emp in self.employees:
            count = sum(1 for day in range(7) if week_plan.get_assignment(day, emp) == DayType.ON_CALL)
            status = "❌" if count == 0 else "✅"
            print(f"    {emp}: {count} times {status}")
        
        # Try to give missing employees on-call assignments
        # Use a smarter approach: distribute missing employees across different days
        print(f"  Attempting to distribute {len(employees_missing_oncall)} missing employees across different days...")
        
        for missing_employee in employees_missing_oncall:
            assigned = False
            # Try each day to find a slot for this employee
            for day in range(7):
                current_assignment = week_plan.get_assignment(day, missing_employee)
                if current_assignment is not None:
                    continue  # Already assigned something this day
                
                # First try: Check if we can assign on-call here with relaxed rules
                if self._can_assign_for_minimum_oncall(missing_employee, day, week_plan, previous_data):
                    # Find who is currently assigned on-call this day
                    current_oncall_employee = None
                    for emp in self.employees:
                        if week_plan.get_assignment(day, emp) == DayType.ON_CALL:
                            current_oncall_employee = emp
                            break
                    
                    if current_oncall_employee:
                        # Check if current employee already has another on-call day this week
                        current_emp_oncall_count = sum(1 for d in range(7) 
                                                     if week_plan.get_assignment(d, current_oncall_employee) == DayType.ON_CALL)
                        
                        if current_emp_oncall_count > 1:
                            # Rule 2 has priority 100, but should respect Rule 4 (88) for weekend fairness
                            # Check Rule 1 (110) and Rule 4 (88+) to maintain weekend fairness
                            temp_violations = False
                            for rule in self.rules:
                                if rule.get_priority() >= 88:  # Rule 1 (110) and Rule 4 (88)
                                    if not rule.validate(missing_employee, day, DayType.ON_CALL, week_plan, previous_data):
                                        temp_violations = True
                                        print(f"Rule 2 swap blocked by {rule.get_name()} for {missing_employee} on day {day}")
                                        break
                            
                            if not temp_violations:
                                # Check if current employee would become violating Rule 2 after swap
                                current_emp_remaining_oncall = sum(1 for d in range(7) 
                                                                   if d != day and week_plan.get_assignment(d, current_oncall_employee) == DayType.ON_CALL)
                                
                                if current_emp_remaining_oncall == 0:
                                    print(f"Rule 2 swap BLOCKED: {current_oncall_employee} would have 0 on-call days after giving day {day} to {missing_employee}")
                                    continue  # Don't make this swap, it would create another Rule 2 violation
                                
                                # Swap assignments: give on-call to missing employee, work to current employee
                                week_plan.set_assignment(day, missing_employee, DayType.ON_CALL)
                                week_plan.set_assignment(day, current_oncall_employee, DayType.WORK)
                                
                                # Adjust rest assignments
                                self._assign_rest_after_oncall(week_plan, missing_employee, day)
                                
                                print(f"Rule 2 fix: Assigned {missing_employee} on-call on day {day}, {current_oncall_employee} to work")
                                assigned = True
                                break
                            else:
                                print(f"Rule 2 swap blocked by higher priority rules for {missing_employee} on day {day}")
                        else:
                            # Current employee only has 1 on-call, but we still need to respect weekend fairness
                            # Check Rule 1 (110) and Rule 4 (88+) to maintain weekend fairness
                            temp_violations = False
                            for rule in self.rules:
                                if rule.get_priority() >= 88:  # Rule 1 (110) and Rule 4 (88)
                                    if not rule.validate(missing_employee, day, DayType.ON_CALL, week_plan, previous_data):
                                        temp_violations = True
                                        print(f"Rule 2 forced assignment blocked by {rule.get_name()} for {missing_employee} on day {day}")
                                        break
                            
                            if not temp_violations:
                                # Force assignment: give on-call to missing employee, work to current employee
                                # But this would leave current employee with 0 on-call days, violating Rule 2
                                print(f"Rule 2 FORCED assignment BLOCKED: {current_oncall_employee} would have 0 on-call days")
                                continue  # This would create another Rule 2 violation
                    else:
                        # No current on-call employee, directly assign but respect weekend fairness
                        # Check Rule 1 (110) and Rule 4 (88+) to maintain weekend fairness
                        temp_violations = False
                        for rule in self.rules:
                            if rule.get_priority() >= 88:  # Rule 1 (110) and Rule 4 (88)
                                if not rule.validate(missing_employee, day, DayType.ON_CALL, week_plan, previous_data):
                                    temp_violations = True
                                    print(f"Rule 2 direct assignment blocked by {rule.get_name()} for {missing_employee} on day {day}")
                                    break
                        
                        if not temp_violations:
                            week_plan.set_assignment(day, missing_employee, DayType.ON_CALL)
                            self._assign_rest_after_oncall(week_plan, missing_employee, day)
                            print(f"Rule 2 fix: Directly assigned {missing_employee} on-call on day {day}")
                            assigned = True
                            break
                        else:
                            print(f"Rule 2 direct assignment blocked by higher priority rules for {missing_employee} on day {day}")
                        
            if not assigned:
                print(f"CRITICAL: Rule 2 enforcement failed for {missing_employee} - trying LAST RESORT")
                # Last resort: Force assign by taking over ANY day, but respect mandatory REST
                for day in range(7):
                    current_assignment = week_plan.get_assignment(day, missing_employee)
                    if current_assignment == DayType.ON_CALL:
                        continue  # Already on-call, skip
                    
                    # Check if this is mandatory REST due to Rule 3 - don't override
                    if (current_assignment == DayType.REST and 
                        self._is_mandatory_rest(missing_employee, day, previous_data)):
                        continue  # Don't override mandatory rest assignments
                    
                    # Check if this employee must work (cannot be on-call) due to Rule 3 - don't assign on-call
                    if self._is_mandatory_work(missing_employee, day, previous_data):
                        continue  # Don't assign on-call if employee must work
                    
                    # We can override WORK and non-mandatory REST assignments for Rule 2
                    
                    # Find who is currently assigned on-call this day
                    current_oncall_employee = None
                    for emp in self.employees:
                        if week_plan.get_assignment(day, emp) == DayType.ON_CALL:
                            current_oncall_employee = emp
                            break
                    
                    if current_oncall_employee:
                        # Don't take from employees who also need on-call assignments
                        current_emp_oncall_count = sum(1 for d in range(7) 
                                                     if week_plan.get_assignment(d, current_oncall_employee) == DayType.ON_CALL)
                        
                        if current_emp_oncall_count <= 1:  # This would be their only on-call assignment
                            print(f"LAST RESORT: Cannot take from {current_oncall_employee} - they need their on-call assignment too")
                            continue  # Find a different day/employee
                        
                        print(f"LAST RESORT: Taking day {day} from {current_oncall_employee} for {missing_employee}")
                        # For Rule 2 enforcement, only respect Rule 1 (daily coverage) and Rule 4 (weekend fairness)
                        # Check only the most critical rules
                        critical_violation = False
                        # Strict rule compliance: respect ALL rules, never violate any rule
                        # This ensures we maintain integrity of all 5 rules
                        rule_violation = False
                        for rule in self.rules:
                            if not rule.validate(missing_employee, day, DayType.ON_CALL, week_plan, previous_data):
                                rule_violation = True
                                print(f"STRICT COMPLIANCE: Cannot assign {missing_employee} on day {day} due to {rule.get_name()}")
                                break
                        
                        if not rule_violation:
                            week_plan.set_assignment(day, missing_employee, DayType.ON_CALL)
                            week_plan.set_assignment(day, current_oncall_employee, DayType.WORK)
                            self._assign_rest_after_oncall(week_plan, missing_employee, day)
                            assigned = True
                            print(f"✅ STRICT COMPLIANCE SUCCESS: {missing_employee} assigned on-call on day {day}")
                            break
                        else:
                            continue  # Try next day
                
                if not assigned:
                    print(f"⚠️ STRICT COMPLIANCE: Cannot satisfy Rule 2 for {missing_employee} without violating other rules")
    
    def _is_mandatory_rest(self, employee: str, day: int, previous_data: List[WeekPlan]) -> bool:
        """Check if this employee must rest on this day due to Rule 3 cross-week constraints."""
        if not previous_data:
            return False
            
        last_week = previous_data[0]
        
        # Monday rest is mandatory if employee was on-call Friday, Saturday, or Sunday last week
        if day == 0:  # Monday
            return (employee in last_week.get_on_call_employees(4) or  # Friday
                   employee in last_week.get_on_call_employees(5) or   # Saturday  
                   employee in last_week.get_on_call_employees(6))     # Sunday
        
        # Tuesday rest is mandatory if employee was on-call Saturday or Sunday last week
        elif day == 1:  # Tuesday
            return (employee in last_week.get_on_call_employees(5) or   # Saturday
                   employee in last_week.get_on_call_employees(6))     # Sunday
        
        return False  # Other days don't have mandatory cross-week rest
    
    def _is_mandatory_work(self, employee: str, day: int, previous_data: List[WeekPlan]) -> bool:
        """Check if this employee must work (cannot be on-call) on this day due to Rule 3 cross-week constraints."""
        if not previous_data:
            return False
            
        last_week = previous_data[0]
        
        # Cross-week mandatory work constraints from Rule 3:
        if day == 0:  # Monday - mandatory work if Thursday on-call last week
            return employee in last_week.get_on_call_employees(3)  # Thursday
        elif day == 1:  # Tuesday - mandatory work if Friday on-call last week  
            return employee in last_week.get_on_call_employees(4)  # Friday
        elif day == 2:  # Wednesday - mandatory work if Saturday or Sunday on-call last week
            return (employee in last_week.get_on_call_employees(5) or   # Saturday
                   employee in last_week.get_on_call_employees(6))     # Sunday
        
        return False  # Other days don't have mandatory cross-week work restrictions
    
    def _is_mandatory_work_same_week(self, employee: str, day: int, week_plan: WeekPlan) -> bool:
        """Check if this employee must work (cannot be on-call) on this day due to same-week Rule 3 constraints."""
        # Same-week mandatory work constraints from Rule 3:
        if day == 2:  # Wednesday - mandatory work if Monday on-call same week
            return week_plan.get_assignment(0, employee) == DayType.ON_CALL
        elif day == 3:  # Thursday - mandatory work if Tuesday on-call same week  
            return week_plan.get_assignment(1, employee) == DayType.ON_CALL
        elif day == 4:  # Friday - mandatory work if Wednesday on-call same week
            return week_plan.get_assignment(2, employee) == DayType.ON_CALL
        
        return False
    
    def _preemptive_rule2_protection(self, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> None:
        """Proactively identify employees at risk of Rule 2 violation and try to secure slots for them."""
        if not previous_data:
            return
            
        last_week = previous_data[0]
        
        # Identify employees who will have severely limited options this week due to Rule 3 and 4
        high_risk_employees = []
        
        # print(f"🔍 预防性规则2保护分析 - 第{len(previous_data)+1}周")
        
        for employee in self.employees:
            available_days = 0
            restricted_days = []
            
            # Removed debug code for 包汀池
            
            for day in range(7):
                # Check if this day is already assigned
                if week_plan.get_assignment(day, employee) is not None:
                    continue
                    
                # Check if this employee can be assigned on-call on this day
                can_assign = True
                blocking_rule = None
                for rule in self.rules:
                    if rule.get_priority() >= 88:  # High priority rules (Rule 1, 4)
                        if not rule.validate(employee, day, DayType.ON_CALL, week_plan, previous_data):
                            can_assign = False
                            blocking_rule = rule.get_name()
                            restricted_days.append(day)
                            break
                
                # Removed debug code
                
                # Also check mandatory work constraint (Rule 3)  
                if can_assign and self._is_mandatory_work(employee, day, previous_data):
                    can_assign = False
                    restricted_days.append(day)
                    # Removed debug code
                
                if can_assign:
                    available_days += 1
            
            # If employee has very limited options (≤2 days available), mark as high risk
            if available_days <= 2:
                high_risk_employees.append((employee, available_days, restricted_days))
                print(f"DEBUG: {employee} identified as high-risk for Rule 2, only {available_days} available days")
        
        # Try to reserve slots for high-risk employees
        high_risk_employees.sort(key=lambda x: x[1])  # Sort by available days (most constrained first)
        
        for employee, available_days, restricted_days in high_risk_employees:
            if available_days == 0:
                print(f"WARNING: {employee} has no available days for Rule 2 compliance")
                continue
                
            # Try to secure at least one on-call assignment for this high-risk employee
            for day in range(7):
                current_assignment = week_plan.get_assignment(day, employee)
                if current_assignment is not None:
                    continue  # Already assigned
                    
                if day in restricted_days:
                    continue  # This day is restricted for this employee
                    
                # Check if we can assign this employee on-call on this day
                if self._validate_assignment(employee, day, DayType.ON_CALL, week_plan, previous_data):
                    # Find current on-call employee for this day
                    current_oncall = None
                    for emp in self.employees:
                        if week_plan.get_assignment(day, emp) == DayType.ON_CALL:
                            current_oncall = emp
                            break
                    
                    if current_oncall:
                        # Check if current employee has multiple on-call assignments
                        current_oncall_count = sum(1 for d in range(7) 
                                                 if week_plan.get_assignment(d, current_oncall) == DayType.ON_CALL)
                        
                        if current_oncall_count > 1:
                            # Swap: give this day to high-risk employee
                            print(f"PREEMPTIVE: Reserving day {day} for high-risk {employee} (from {current_oncall})")
                            week_plan.set_assignment(day, employee, DayType.ON_CALL)
                            week_plan.set_assignment(day, current_oncall, DayType.WORK)
                            self._assign_rest_after_oncall(week_plan, employee, day)
                            break  # Found a slot for this employee
    
    def _can_assign_for_minimum_oncall(self, employee: str, day: int, week_plan: WeekPlan, previous_data: List[WeekPlan]) -> bool:
        """Check if employee can be assigned on-call for Rule 2 compliance."""
        # Rule 2 has priority 100, so it can override lower priority rules
        # Only enforce rules with priority > 100 (currently only Rule 1: Daily Coverage)
        
        higher_priority_rules = [rule for rule in self.rules if rule.get_priority() > 100]
        
        for rule in higher_priority_rules:
            if not rule.validate(employee, day, DayType.ON_CALL, week_plan, previous_data):
                return False
        
        return True
    
    def _choose_fairest_employee(self, available_employees: List[str], previous_data: List[WeekPlan]) -> str:
        """Choose employee with fewest historical on-call assignments for fairness."""
        # Count historical on-call assignments for each available employee
        historical_counts = {}
        for employee in available_employees:
            count = 0
            # Count from all previous weeks
            for week in previous_data:
                for day in range(7):
                    if employee in week.get_on_call_employees(day):
                        count += 1
            historical_counts[employee] = count
        
        # Find minimum count
        min_count = min(historical_counts.values())
        
        # Get all employees with minimum count
        fairest_employees = [emp for emp in available_employees 
                           if historical_counts[emp] == min_count]
        
        # If multiple employees have same minimal count, use alphabetical order for consistency
        fairest_employees.sort()
        return fairest_employees[0]
    
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
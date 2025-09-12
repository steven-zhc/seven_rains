#!/usr/bin/env python3

import sys
from src.sevens_rain.scheduler import WeekScheduler
from src.sevens_rain.storage import PlanStorage
from src.sevens_rain.models import WeekPlan, DayType
from datetime import datetime

def analyze_week2_constraints():
    """Analyze what's constraining 包汀池 in week 2."""
    
    # Load existing data  
    storage = PlanStorage()
    employees = ['姚强', '钱国祥', '包汀池', '孙震', '夏银龙', '张尧']
    scheduler = WeekScheduler(employees)
    
    # Get October data
    october_weeks = storage.get_month_weeks(2025, 10)
    if not october_weeks or len(october_weeks) < 2:
        print("Need to generate October data first")
        return
        
    print("=== 分析包汀池在第2周(10月13日)的限制 ===")
    
    week1 = october_weeks[0]  # First week of October
    week2 = october_weeks[1]  # Second week of October
    
    print("\n第1周(10月6日)包汀池的安排:")
    for day in range(7):
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"] 
        assignment = week1.get_assignment(day, '包汀池')
        if assignment:
            print(f"  {day_names[day]}: {assignment.value}")
    
    print("\n第2周(10月13日)包汀池的限制分析:")
    
    # Check each day of week 2 for 包汀池
    for day in range(7):
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        # Check if already assigned
        current_assignment = week2.get_assignment(day, '包汀池')
        if current_assignment is not None:
            print(f"  {day_names[day]}: 已分配 {current_assignment.value}")
            continue
            
        print(f"\n  {day_names[day]}:")
        
        # Check each rule
        for rule in scheduler.rules:
            if rule.get_priority() >= 88:  # High priority rules
                valid = rule.validate('包汀池', day, DayType.ON_CALL, week2, [week1])
                print(f"    {rule.get_name()}(优先级{rule.get_priority()}): {'✅' if valid else '❌'}")
        
        # Check mandatory work constraint
        is_mandatory_work = scheduler._is_mandatory_work('包汀池', day, [week1])
        print(f"    强制白班(规则3): {'❌' if is_mandatory_work else '✅'}")
        
        # Check if anyone is already on-call this day
        current_oncall = []
        for emp in employees:
            if week2.get_assignment(day, emp) == DayType.ON_CALL:
                current_oncall.append(emp)
        if current_oncall:
            print(f"    当前听班: {current_oncall}")
        else:
            print("    当前听班: 无")

if __name__ == "__main__":
    analyze_week2_constraints()
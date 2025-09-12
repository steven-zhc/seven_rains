#!/usr/bin/env python3
"""全面检查10月份排班数据是否符合SCHEDULING_RULES.md中的所有规则"""

import json
from datetime import date, timedelta
from collections import defaultdict, Counter

def load_october_data():
    """加载10月份排班数据"""
    with open('plan.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    october_weeks = []
    for week in data['weeks']:
        if week['week_start'].startswith('2025-10'):
            october_weeks.append(week)
    
    return october_weeks

def check_rule_1_daily_coverage(weeks):
    """规则1: 每日值班覆盖 - 每天必须有且仅有一个人听班，包括周末"""
    print("=" * 60)
    print("规则1检查: 每日值班覆盖 (优先级: 110)")
    print("- 每天必须有且仅有一个人听班，包括周末")
    print("=" * 60)
    
    violations = []
    for i, week in enumerate(weeks):
        week_start = week['week_start']
        print(f"\n第{i+1}周 ({week_start}):")
        
        for day in range(7):
            day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            oncall_employees = []
            
            for emp, duty in week['assignments'][str(day)].items():
                if duty == '听':
                    oncall_employees.append(emp)
            
            if len(oncall_employees) == 0:
                print(f"  {day_names[day]}: ❌ 无人值班")
                violations.append(f"第{i+1}周{day_names[day]}无人值班")
            elif len(oncall_employees) == 1:
                print(f"  {day_names[day]}: ✅ {oncall_employees[0]}")
            else:
                print(f"  {day_names[day]}: ❌ 多人值班: {oncall_employees}")
                violations.append(f"第{i+1}周{day_names[day]}多人值班: {oncall_employees}")
    
    if violations:
        print(f"\n❌ 规则1违反: {len(violations)}个问题")
        for v in violations:
            print(f"   - {v}")
        return False
    else:
        print(f"\n✅ 规则1完全符合: 每天都有且仅有一人值班")
        return True

def check_rule_2_minimum_oncall_per_week(weeks):
    """规则2: 每人每周至少听班一次"""
    print("\n" + "=" * 60)
    print("规则2检查: 每人每周至少听班一次 (优先级: 100)")
    print("=" * 60)
    
    employees = ['姚强', '钱国祥', '包汀池', '孙震', '夏银龙', '张尧']
    violations = []
    
    for i, week in enumerate(weeks):
        week_start = week['week_start']
        print(f"\n第{i+1}周 ({week_start}):")
        
        employee_oncall_count = {}
        for emp in employees:
            employee_oncall_count[emp] = 0
        
        for day in range(7):
            for emp, duty in week['assignments'][str(day)].items():
                if duty == '听':
                    employee_oncall_count[emp] += 1
        
        week_violations = []
        for emp, count in employee_oncall_count.items():
            if count == 0:
                week_violations.append(emp)
                violations.append(f"第{i+1}周: {emp} 没有听班")
            print(f"  {emp}: {count}次 {'❌' if count == 0 else '✅'}")
        
        if week_violations:
            print(f"  ⚠️  规则2违反: {week_violations}")
    
    if violations:
        print(f"\n❌ 规则2违反: {len(violations)}个问题")
        for v in violations:
            print(f"   - {v}")
        return False
    else:
        print(f"\n✅ 规则2完全符合: 每人每周都至少听班一次")
        return True

def check_rule_3_rest_after_oncall(weeks):
    """规则3: 值班规则 - 详细的值班后休息安排"""
    print("\n" + "=" * 60)
    print("规则3检查: 值班规则 (优先级: 90)")
    print("- 周一听班 → 周二休息，周三白班")
    print("- 周二听班 → 周三休息，周四白班") 
    print("- 周三听班 → 周四休息，周五白班")
    print("- 周四听班 → 周五、周六、周日休息，下周一白班")
    print("- 周五听班 → 周六、周日、下周一休息，周二白班")
    print("- 周六听班 → 周日、下周一、周二休息，周三白班")
    print("- 周日听班 → 下周一、周二休息，周三白班")
    print("=" * 60)
    
    violations = []
    employees = ['姚强', '钱国祥', '包汀池', '孙震', '夏银龙', '张尧']
    
    # 检查同一周内的休息规则
    for i, week in enumerate(weeks):
        week_start = week['week_start']
        print(f"\n第{i+1}周 ({week_start}) 周内休息规则:")
        
        for emp in employees:
            for day in range(7):
                if week['assignments'][str(day)].get(emp) == '听':
                    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    print(f"  {emp} {day_names[day]}听班:", end=" ")
                    
                    # 检查对应的休息要求
                    if day == 0:  # 周一听班 → 周二休息
                        if day + 1 < 7:
                            expected_rest = week['assignments'][str(day + 1)].get(emp)
                            if expected_rest != '休':
                                violations.append(f"第{i+1}周: {emp} 周一听班后周二应该休息，实际为{expected_rest}")
                                print("❌ 周二应休息")
                            else:
                                print("✅ 周二正确休息")
                    
                    elif day == 1:  # 周二听班 → 周三休息  
                        if day + 1 < 7:
                            expected_rest = week['assignments'][str(day + 1)].get(emp)
                            if expected_rest != '休':
                                violations.append(f"第{i+1}周: {emp} 周二听班后周三应该休息，实际为{expected_rest}")
                                print("❌ 周三应休息")
                            else:
                                print("✅ 周三正确休息")
                    
                    elif day == 2:  # 周三听班 → 周四休息
                        if day + 1 < 7:
                            expected_rest = week['assignments'][str(day + 1)].get(emp)
                            if expected_rest != '休':
                                violations.append(f"第{i+1}周: {emp} 周三听班后周四应该休息，实际为{expected_rest}")
                                print("❌ 周四应休息")
                            else:
                                print("✅ 周四正确休息")
                    
                    elif day == 3:  # 周四听班 → 周五、周六、周日休息
                        rest_days = [4, 5, 6]  # 周五、周六、周日
                        all_rest = True
                        for rest_day in rest_days:
                            if rest_day < 7:
                                expected_rest = week['assignments'][str(rest_day)].get(emp)
                                if expected_rest != '休':
                                    violations.append(f"第{i+1}周: {emp} 周四听班后{['周五','周六','周日'][rest_day-4]}应该休息，实际为{expected_rest}")
                                    all_rest = False
                        if all_rest:
                            print("✅ 周五六日正确休息")
                        else:
                            print("❌ 周五六日应全部休息")
                    
                    elif day == 4:  # 周五听班 → 周六、周日休息（下周一休息跨周检查）
                        rest_days = [5, 6]  # 周六、周日
                        all_rest = True
                        for rest_day in rest_days:
                            expected_rest = week['assignments'][str(rest_day)].get(emp)
                            if expected_rest != '休':
                                violations.append(f"第{i+1}周: {emp} 周五听班后{['周六','周日'][rest_day-5]}应该休息，实际为{expected_rest}")
                                all_rest = False
                        if all_rest:
                            print("✅ 周六日正确休息")
                        else:
                            print("❌ 周六日应休息")
                    
                    elif day == 5:  # 周六听班 → 周日休息（下周一二休息跨周检查）
                        expected_rest = week['assignments']['6'].get(emp)
                        if expected_rest != '休':
                            violations.append(f"第{i+1}周: {emp} 周六听班后周日应该休息，实际为{expected_rest}")
                            print("❌ 周日应休息")
                        else:
                            print("✅ 周日正确休息")
                    
                    elif day == 6:  # 周日听班 → 下周一二休息（跨周检查）
                        print("✅ (跨周休息规则)")
    
    # 检查跨周休息规则
    print(f"\n跨周休息规则检查:")
    for i in range(len(weeks) - 1):
        current_week = weeks[i]
        next_week = weeks[i + 1]
        
        print(f"第{i+1}周 → 第{i+2}周:")
        
        for emp in employees:
            # 检查周五听班 → 下周一休息
            if current_week['assignments']['4'].get(emp) == '听':  # 周五听班
                next_monday = next_week['assignments']['0'].get(emp)
                if next_monday != '休':
                    violations.append(f"第{i+1}周: {emp} 周五听班后第{i+2}周周一应该休息，实际为{next_monday}")
                    print(f"  ❌ {emp} 周五听班后下周一应休息，实际为{next_monday}")
                else:
                    print(f"  ✅ {emp} 周五听班后下周一正确休息")
            
            # 检查周六听班 → 下周一二休息
            if current_week['assignments']['5'].get(emp) == '听':  # 周六听班
                next_monday = next_week['assignments']['0'].get(emp)
                next_tuesday = next_week['assignments']['1'].get(emp)
                if next_monday != '休':
                    violations.append(f"第{i+1}周: {emp} 周六听班后第{i+2}周周一应该休息，实际为{next_monday}")
                    print(f"  ❌ {emp} 周六听班后下周一应休息，实际为{next_monday}")
                if next_tuesday != '休':
                    violations.append(f"第{i+1}周: {emp} 周六听班后第{i+2}周周二应该休息，实际为{next_tuesday}")
                    print(f"  ❌ {emp} 周六听班后下周二应休息，实际为{next_tuesday}")
                if next_monday == '休' and next_tuesday == '休':
                    print(f"  ✅ {emp} 周六听班后下周一二正确休息")
            
            # 检查周日听班 → 下周一二休息
            if current_week['assignments']['6'].get(emp) == '听':  # 周日听班
                next_monday = next_week['assignments']['0'].get(emp)
                next_tuesday = next_week['assignments']['1'].get(emp)
                if next_monday != '休':
                    violations.append(f"第{i+1}周: {emp} 周日听班后第{i+2}周周一应该休息，实际为{next_monday}")
                    print(f"  ❌ {emp} 周日听班后下周一应休息，实际为{next_monday}")
                if next_tuesday != '休':
                    violations.append(f"第{i+1}周: {emp} 周日听班后第{i+2}周周二应该休息，实际为{next_tuesday}")
                    print(f"  ❌ {emp} 周日听班后下周二应休息，实际为{next_tuesday}")
                if next_monday == '休' and next_tuesday == '休':
                    print(f"  ✅ {emp} 周日听班后下周一二正确休息")
    
    if violations:
        print(f"\n❌ 规则3违反: {len(violations)}个问题")
        for v in violations:
            print(f"   - {v}")
        return False
    else:
        print(f"\n✅ 规则3完全符合: 值班后休息安排正确")
        return True

def check_rule_4_no_consecutive_weekend(weeks):
    """规则4: 避免连续周末值班"""
    print("\n" + "=" * 60)
    print("规则4检查: 避免连续周末值班 (优先级: 88)")
    print("- 同一个人上周末安排听班，下周末不要安排听班")
    print("=" * 60)
    
    violations = []
    employees = ['姚强', '钱国祥', '包汀池', '孙震', '夏银龙', '张尧']
    
    for i in range(len(weeks) - 1):
        current_week = weeks[i]
        next_week = weeks[i + 1]
        
        print(f"\n第{i+1}周 → 第{i+2}周:")
        
        for emp in employees:
            # 检查当前周的周末值班
            current_weekend_oncall = []
            if current_week['assignments']['5'].get(emp) == '听':  # 周六
                current_weekend_oncall.append('周六')
            if current_week['assignments']['6'].get(emp) == '听':  # 周日
                current_weekend_oncall.append('周日')
            
            # 检查下一周的周末值班
            next_weekend_oncall = []
            if next_week['assignments']['5'].get(emp) == '听':  # 周六
                next_weekend_oncall.append('周六')
            if next_week['assignments']['6'].get(emp) == '听':  # 周日
                next_weekend_oncall.append('周日')
            
            if current_weekend_oncall and next_weekend_oncall:
                violations.append(f"{emp} 第{i+1}周{current_weekend_oncall}值班，第{i+2}周{next_weekend_oncall}又值班")
                print(f"  ❌ {emp}: 第{i+1}周{current_weekend_oncall} → 第{i+2}周{next_weekend_oncall}")
            elif current_weekend_oncall or next_weekend_oncall:
                if current_weekend_oncall:
                    print(f"  ✅ {emp}: 第{i+1}周{current_weekend_oncall}值班，第{i+2}周正确休息")
                else:
                    print(f"  ✅ {emp}: 第{i+2}周{next_weekend_oncall}值班，第{i+1}周正确休息")
    
    if violations:
        print(f"\n❌ 规则4违反: {len(violations)}个问题")
        for v in violations:
            print(f"   - {v}")
        return False
    else:
        print(f"\n✅ 规则4完全符合: 没有连续周末值班")
        return True

def check_rule_5_no_consecutive_weekday(weeks):
    """规则5: 避免重复排班 - 不在连续周的同一天听班"""
    print("\n" + "=" * 60)
    print("规则5检查: 避免重复排班 (优先级: 80)")
    print("- 不在连续周的同一天听班")
    print("=" * 60)
    
    violations = []
    employees = ['姚强', '钱国祥', '包汀池', '孙震', '夏银龙', '张尧']
    
    for i in range(len(weeks) - 1):
        current_week = weeks[i]
        next_week = weeks[i + 1]
        
        print(f"\n第{i+1}周 → 第{i+2}周:")
        
        for day in range(7):
            day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            
            current_oncall = None
            next_oncall = None
            
            for emp, duty in current_week['assignments'][str(day)].items():
                if duty == '听':
                    current_oncall = emp
                    break
            
            for emp, duty in next_week['assignments'][str(day)].items():
                if duty == '听':
                    next_oncall = emp
                    break
            
            if current_oncall and next_oncall and current_oncall == next_oncall:
                violations.append(f"{current_oncall} 连续两周{day_names[day]}值班")
                print(f"  ❌ {day_names[day]}: {current_oncall} 连续两周值班")
            else:
                if current_oncall and next_oncall:
                    print(f"  ✅ {day_names[day]}: {current_oncall} → {next_oncall}")
                elif current_oncall:
                    print(f"  ✅ {day_names[day]}: {current_oncall} → 其他人")
                elif next_oncall:
                    print(f"  ✅ {day_names[day]}: 其他人 → {next_oncall}")
    
    if violations:
        print(f"\n❌ 规则5违反: {len(violations)}个问题")
        for v in violations:
            print(f"   - {v}")
        return False
    else:
        print(f"\n✅ 规则5完全符合: 没有连续周同一天值班")
        return True

def main():
    print("🔍 全面检查10月份排班数据是否符合SCHEDULING_RULES.md规则")
    print("=" * 80)
    
    try:
        weeks = load_october_data()
        print(f"加载了{len(weeks)}周的10月份数据")
        
        results = []
        results.append(check_rule_1_daily_coverage(weeks))
        results.append(check_rule_2_minimum_oncall_per_week(weeks))
        results.append(check_rule_3_rest_after_oncall(weeks))
        results.append(check_rule_4_no_consecutive_weekend(weeks))
        results.append(check_rule_5_no_consecutive_weekday(weeks))
        
        print("\n" + "=" * 80)
        print("📊 最终检查结果汇总")
        print("=" * 80)
        
        rule_names = [
            "规则1: 每日值班覆盖",
            "规则2: 每人每周至少听班一次", 
            "规则3: 值班规则",
            "规则4: 避免连续周末值班",
            "规则5: 避免重复排班"
        ]
        
        all_passed = True
        for i, (rule_name, passed) in enumerate(zip(rule_names, results)):
            status = "✅ 通过" if passed else "❌ 违反"
            print(f"{rule_name}: {status}")
            if not passed:
                all_passed = False
        
        print("=" * 80)
        if all_passed:
            print("🎉 所有规则检查通过！10月份排班完全符合SCHEDULING_RULES.md规则")
        else:
            print("⚠️  发现规则违反，需要修复代码")
            
    except Exception as e:
        print(f"❌ 检查过程中出错: {e}")

if __name__ == "__main__":
    main()
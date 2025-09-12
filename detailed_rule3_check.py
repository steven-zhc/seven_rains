#!/usr/bin/env python3

import json
from datetime import date, timedelta

def analyze_rule3_violations():
    """详细分析规则3违反情况"""
    
    with open('plan.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    employees = ['姚强', '钱国祥', '包汀池', '孙震', '夏银龙', '张尧']
    day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    print("🔍 详细规则3检查: 值班后休息安排")
    print("=" * 80)
    
    violations = []
    
    # 检查每一周
    for i, week in enumerate(data['weeks']):
        week_start_str = week['week_start']
        week_start_date = date.fromisoformat(week_start_str)
        
        print(f"\n第{i+1}周 ({week_start_str}):")
        
        # 检查周内休息规则
        for employee in employees:
            for day in range(7):
                assignment = week['assignments'][str(day)].get(employee)
                if assignment == '听':  # 如果这天值班
                    date_obj = week_start_date + timedelta(days=day)
                    print(f"  {employee} {day_names[day]}({date_obj.strftime('%m月%d日')})听班", end="")
                    
                    # 检查对应的休息日
                    if day == 0:  # 周一听班 → 周二休
                        if day + 1 < 7:
                            next_assignment = week['assignments'][str(day + 1)].get(employee)
                            expected_date = date_obj + timedelta(days=1)
                            if next_assignment == '休':
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})正确休息 ✅")
                            else:
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})应该休息但安排了{next_assignment} ❌")
                                violations.append(f"{employee} {week_start_str}周{day_names[day]}听班后{day_names[day+1]}应该休息")
                    
                    elif day == 1:  # 周二听班 → 周三休
                        if day + 1 < 7:
                            next_assignment = week['assignments'][str(day + 1)].get(employee)
                            expected_date = date_obj + timedelta(days=1)
                            if next_assignment == '休':
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})正确休息 ✅")
                            else:
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})应该休息但安排了{next_assignment} ❌")
                                violations.append(f"{employee} {week_start_str}周{day_names[day]}听班后{day_names[day+1]}应该休息")
                    
                    elif day == 2:  # 周三听班 → 周四休
                        if day + 1 < 7:
                            next_assignment = week['assignments'][str(day + 1)].get(employee)
                            expected_date = date_obj + timedelta(days=1)
                            if next_assignment == '休':
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})正确休息 ✅")
                            else:
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})应该休息但安排了{next_assignment} ❌")
                                violations.append(f"{employee} {week_start_str}周{day_names[day]}听班后{day_names[day+1]}应该休息")
                    
                    elif day == 3:  # 周四听班 → 周五、六、日休
                        violations_found = []
                        for rest_day in [4, 5, 6]:
                            if rest_day < 7:
                                rest_assignment = week['assignments'][str(rest_day)].get(employee)
                                rest_date = date_obj + timedelta(days=rest_day-day)
                                if rest_assignment != '休':
                                    violations_found.append(f"{day_names[rest_day]}({rest_date.strftime('%m月%d日')})应该休息但安排了{rest_assignment}")
                        
                        if violations_found:
                            print(f" → ❌ {', '.join(violations_found)}")
                            violations.extend([f"{employee} {week_start_str}周{day_names[day]}听班后{v}" for v in violations_found])
                        else:
                            print(f" → 周五六日正确休息 ✅")
                    
                    elif day == 4:  # 周五听班 → 周六、日休
                        violations_found = []
                        for rest_day in [5, 6]:
                            if rest_day < 7:
                                rest_assignment = week['assignments'][str(rest_day)].get(employee)
                                rest_date = date_obj + timedelta(days=rest_day-day)
                                if rest_assignment != '休':
                                    violations_found.append(f"{day_names[rest_day]}({rest_date.strftime('%m月%d日')})应该休息但安排了{rest_assignment}")
                        
                        if violations_found:
                            print(f" → ❌ {', '.join(violations_found)}")
                            violations.extend([f"{employee} {week_start_str}周{day_names[day]}听班后{v}" for v in violations_found])
                        else:
                            print(f" → 周六日正确休息 ✅")
                    
                    elif day == 5:  # 周六听班 → 周日休
                        if day + 1 < 7:
                            next_assignment = week['assignments'][str(day + 1)].get(employee)
                            expected_date = date_obj + timedelta(days=1)
                            if next_assignment == '休':
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})正确休息 ✅")
                            else:
                                print(f" → {day_names[day+1]}({expected_date.strftime('%m月%d日')})应该休息但安排了{next_assignment} ❌")
                                violations.append(f"{employee} {week_start_str}周{day_names[day]}听班后{day_names[day+1]}应该休息")
                    
                    elif day == 6:  # 周日听班 → 跨周休息
                        print(f" → (跨周休息检查)")
    
    # 检查跨周休息规则
    print(f"\n" + "=" * 40)
    print("🔍 跨周休息规则检查:")
    print("=" * 40)
    
    for i in range(len(data['weeks']) - 1):
        current_week = data['weeks'][i]
        next_week = data['weeks'][i + 1]
        
        current_week_start = current_week['week_start']
        next_week_start = next_week['week_start']
        
        print(f"\n{current_week_start} → {next_week_start}:")
        
        for employee in employees:
            # 检查各种跨周休息规则
            
            # 周四听班 → 下周一白班
            if current_week['assignments']['3'].get(employee) == '听':
                next_monday = next_week['assignments']['0'].get(employee)
                if next_monday == '白':
                    print(f"  ✅ {employee} 周四听班后下周一正确白班")
                elif next_monday == '听':
                    print(f"  ❌ {employee} 周四听班后下周一应该白班但安排了听班")
                    violations.append(f"{employee} {current_week_start}周四听班后{next_week_start}周一应该白班")
                elif next_monday == '休':
                    print(f"  ❌ {employee} 周四听班后下周一应该白班但安排了休息")
                    violations.append(f"{employee} {current_week_start}周四听班后{next_week_start}周一应该白班")
            
            # 周五听班 → 下周一、二休息，周二白班
            if current_week['assignments']['4'].get(employee) == '听':
                next_monday = next_week['assignments']['0'].get(employee)
                next_tuesday = next_week['assignments']['1'].get(employee)
                next_wednesday = next_week['assignments']['2'].get(employee)
                
                violations_found = []
                if next_monday != '休':
                    violations_found.append(f"下周一应该休息但安排了{next_monday}")
                if next_tuesday == '听':  # 周二不能听班，应该白班
                    violations_found.append(f"下周二应该白班但安排了听班")
                
                if violations_found:
                    print(f"  ❌ {employee} 周五听班后: {', '.join(violations_found)}")
                    violations.extend([f"{employee} {current_week_start}周五听班后{v}" for v in violations_found])
                else:
                    print(f"  ✅ {employee} 周五听班后下周一休二白正确")
            
            # 周六听班 → 下周一、二休息，周三白班
            if current_week['assignments']['5'].get(employee) == '听':
                next_monday = next_week['assignments']['0'].get(employee)
                next_tuesday = next_week['assignments']['1'].get(employee)
                next_wednesday = next_week['assignments']['2'].get(employee)
                
                violations_found = []
                if next_monday != '休':
                    violations_found.append(f"下周一应该休息但安排了{next_monday}")
                if next_tuesday != '休':
                    violations_found.append(f"下周二应该休息但安排了{next_tuesday}")
                if next_wednesday == '听':  # 周三不能听班，应该白班
                    violations_found.append(f"下周三应该白班但安排了听班")
                
                if violations_found:
                    print(f"  ❌ {employee} 周六听班后: {', '.join(violations_found)}")
                    violations.extend([f"{employee} {current_week_start}周六听班后{v}" for v in violations_found])
                else:
                    print(f"  ✅ {employee} 周六听班后下周一二休三白正确")
            
            # 周日听班 → 下周一、二休息，周三白班
            if current_week['assignments']['6'].get(employee) == '听':
                next_monday = next_week['assignments']['0'].get(employee)
                next_tuesday = next_week['assignments']['1'].get(employee)
                next_wednesday = next_week['assignments']['2'].get(employee)
                
                violations_found = []
                if next_monday != '休':
                    violations_found.append(f"下周一应该休息但安排了{next_monday}")
                if next_tuesday != '休':
                    violations_found.append(f"下周二应该休息但安排了{next_tuesday}")
                if next_wednesday == '听':  # 周三不能听班，应该白班
                    violations_found.append(f"下周三应该白班但安排了听班")
                
                if violations_found:
                    print(f"  ❌ {employee} 周日听班后: {', '.join(violations_found)}")
                    violations.extend([f"{employee} {current_week_start}周日听班后{v}" for v in violations_found])
                else:
                    print(f"  ✅ {employee} 周日听班后下周一二休三白正确")
    
    # 总结
    print(f"\n" + "=" * 80)
    print("📊 规则3违反情况总结:")
    print("=" * 80)
    
    if violations:
        print(f"❌ 发现 {len(violations)} 个规则3违反:")
        for i, violation in enumerate(violations, 1):
            print(f"  {i}. {violation}")
    else:
        print("✅ 所有员工都符合规则3")
    
    return violations

if __name__ == "__main__":
    violations = analyze_rule3_violations()
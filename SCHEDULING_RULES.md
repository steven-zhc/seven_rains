# 七里河北控水务排班规则文档
# Seven Rain - Scheduling Rules Documentation

**项目**: Seven Rain Excel排班工具  
**版本**: v0.1.0  
**更新时间**: 2025-08-28  

---

## 📋 排班规则总览 (Scheduling Rules Overview)

### **规则 1: 每周值班分配 (Weekly On-Call Assignment)**
- 每个员工每周必须有**1天值班**（听）
- 值班日在7名员工中轮流分配
- 确保工作负担公平分配

**实施逻辑**: 每周为每个员工分配一个值班日

### **规则 2: 相同工作日避重复 (No Consecutive Same Weekday On-Call)**
- 员工在连续两周**不能**在同一个工作日值班
- 例如：张尧第1周星期一值班，第2周不能再在星期一值班
- 防止某员工总是在同一天值班

**实施逻辑**: 
```python
if employee in last_oncall_weekday and weekday == last_oncall_weekday[employee]:
    should_skip = True  # 跳过此日期
```

### **规则 3: 值班后强制休息 (Mandatory Rest After On-Call)**
- **工作日值班**: 次日获得1天休息
- **周末值班**: 获得**2天休息**（下周一+周二）
- 确保值班后员工得到充分休息

**休息分配**:
- 周一至周五值班 → 次日休息1天
- 周六或周日值班 → 下周一、二休息2天

### **规则 4: 周末值班休息限制 ⭐ (Weekend On-Call Rest Restriction)**
- 周末值班的员工在下周一、二**必须休息**
- 这两天**不能**再被分配值班任务
- 例如：张尧周日9/7值班 → 9/8(周一)和9/9(周二)**强制休息**

**实施逻辑**:
```python
if employee in weekend_oncall_rest_periods:
    monday_rest, tuesday_rest = weekend_oncall_rest_periods[employee]
    if current_date in [monday_rest, tuesday_rest]:
        should_skip = True  # 不能安排值班
```

### **规则 5: 周末休息优先 (Weekend Rest Priority)**
- 员工通常在周末休息（周六/周日），**除非**：
  - 被安排周末值班
  - 因前次值班已有安排的休息日

**优先级**: 值班安排 > 强制休息 > 周末休息

### **规则 6: 员工轮换机制 (Employee Rotation)**
- 值班任务在员工间轮流分配
- 使用取模轮换: `choice_idx = employee_index % available_days`
- 确保长期公平分配

---

## 🎯 规则执行优先级 (Rule Enforcement Priority)

1. **强制休息期** - 周末值班后的周一二休息（不可违反）
2. **避免重复** - 不在连续周的同一天值班
3. **每周值班** - 每人每周必须有值班日
4. **轮换公平** - 值班任务均匀分配
5. **周末休息** - 尽可能安排周末休息

---

## 📊 实际效果统计 (Current Statistics)

**2025年9月排班结果**:
```
姚强:  值班5天, 休息13天, 工作12天
钱国祥: 值班5天, 休息12天, 工作13天  
包汀池: 值班5天, 休息13天, 工作12天
孙震:  值班5天, 休息10天, 工作15天
赵兵:  值班4天, 休息11天, 工作15天
夏银龙: 值班5天, 休息12天, 工作13天
张尧:  值班5天, 休息12天, 工作13天
```

**符号说明**:
- **听** - 值班日 (On-call duty)
- **休** - 休息日 (Rest day)  
- **白** - 正常工作日 (Regular work day)

---

## ⚠️ 已知限制 (Known Limitations)

### **1. 月末排班混乱**
- 月末日期（如9/29-9/30）排班可能不规整
- 需要跨月处理逻辑

### **2. 跨月连续性缺失**
- 缺少月份间的元数据存储
- 下个月首周可能违反规则

### **3. 不完整周处理**
- 部分周可能值班分配不均
- 月初月末边界处理待优化

---

## 🔧 技术实现 (Technical Implementation)

### **数据结构**:
```python
# 员工列表
EMPLOYEES = ["姚强", "钱国祥", "包汀池", "孙震", "赵兵", "夏银龙", "张尧"]

# 跟踪上次值班日
last_oncall_weekday = {}  # employee -> weekday

# 跟踪周末值班休息期
weekend_oncall_rest_periods = {}  # employee -> (monday, tuesday)
```

### **核心算法**:
1. 按周处理（week_start += 7）
2. 为每个员工寻找可用值班日
3. 应用所有规则过滤
4. 分配值班并设置休息日
5. 清理过期的休息期记录

---

## 📝 更新日志 (Change Log)

**v0.1.0 (2025-08-28)**:
- ✅ 实现6条核心排班规则
- ✅ 修复周末值班休息日冲突
- ✅ 添加员工统计功能
- ✅ 美化Excel表格主题
- ⚠️ 月末跨月处理待完善

---

**文档维护**: 此文档随代码更新同步维护  
**联系方式**: 技术问题请查看项目CLAUDE.md文件
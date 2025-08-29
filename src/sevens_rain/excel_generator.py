"""Excel generation with beautiful formatting and cross-month week support."""

import xlsxwriter
from typing import List, Dict, Any
from datetime import date, timedelta
from pathlib import Path
from .models import DayType, WeekPlan
from .storage import PlanStorage
from .scheduler import WeekScheduler


class ExcelGenerator:
    """Generates beautiful Excel files from week plans with cross-month support."""
    
    def __init__(self, employees: List[str], storage: PlanStorage):
        """
        Initialize Excel generator.
        
        Args:
            employees: List of employee names
            storage: PlanStorage instance for accessing week data
        """
        self.employees = employees
        self.storage = storage
        self.scheduler = WeekScheduler(employees)
    
    def generate_month_schedule(self, year: int, month: int, 
                              output_path: str = None) -> str:
        """
        Generate Excel for month with complete weeks (including cross-month days).
        
        Args:
            year: Year
            month: Month (1-12)
            output_path: Output file path (auto-generated if None)
            
        Returns:
            Path to generated Excel file
        """
        if output_path is None:
            output_path = f"schedule-{year:04d}-{month:02d}.xlsx"
        
        # Get or generate all weeks that overlap with this month
        month_weeks = self._get_or_generate_month_weeks(year, month)
        
        # Generate Excel with beautiful formatting
        self._create_excel_file(month_weeks, year, month, output_path)
        
        return output_path
    
    def _get_or_generate_month_weeks(self, year: int, month: int) -> List[WeekPlan]:
        """Get or generate all weeks that overlap with given month."""
        month_weeks = []
        
        # Find first and last weeks that overlap with month
        first_day = date(year, month, 1)
        last_day = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
        
        # Start from Monday of first week
        first_monday = first_day - timedelta(days=first_day.weekday())
        current_monday = first_monday
        
        # Generate weeks until we cover the entire month
        while True:
            week_end = current_monday + timedelta(days=6)
            
            # Check if this week overlaps with the month
            if current_monday > last_day:
                break  # Week is completely after the month
            
            if week_end >= first_day:
                # Week overlaps with month, get or generate it
                week_plan = self.storage.load_week(current_monday)
                
                if week_plan is None:
                    # Generate new week
                    previous_data = self.storage.load_previous_weeks(current_monday, count=4)
                    week_plan = self.scheduler.generate_week(current_monday, previous_data)
                    self.storage.save_week(week_plan)
                
                month_weeks.append(week_plan)
            
            current_monday += timedelta(weeks=1)
        
        return month_weeks
    
    def _create_excel_file(self, month_weeks: List[WeekPlan], year: int, month: int, 
                          output_path: str) -> None:
        """Create Excel file with beautiful formatting."""
        workbook = xlsxwriter.Workbook(output_path)
        worksheet = workbook.add_worksheet('Schedule')
        
        # Beautiful theme colors
        primary_blue = '#2E86AB'
        light_blue = '#A5C4D4'
        weekend_blue = '#E3F2FD'
        accent_green = '#06A77D'
        warning_red = '#F24236'
        soft_gray = '#F5F5F5'
        dark_gray = '#424242'
        outside_month_gray = '#E0E0E0'
        
        # Create formats
        formats = self._create_formats(workbook, primary_blue, light_blue, weekend_blue, 
                                     accent_green, warning_red, soft_gray, dark_gray, 
                                     outside_month_gray)
        
        # Build complete day list from all weeks
        all_days = []
        for week in month_weeks:
            week_start = week.week_start
            for day_offset in range(7):
                current_date = week_start + timedelta(days=day_offset)
                all_days.append(current_date)
        
        total_cols = 2 + len(all_days)
        
        # Row 0: Title
        worksheet.merge_range(0, 0, 0, total_cols - 1, "七里河北控水务排班表", formats['title'])
        
        # Row 1: Year-Month info
        worksheet.merge_range(1, 0, 1, 1, f"{year}年{month}月", formats['date'])
        
        # Row 2: Date headers
        worksheet.write(2, 0, "序号", formats['header'])
        worksheet.write(2, 1, "姓名", formats['header'])
        
        for i, day in enumerate(all_days):
            col = i + 2
            date_str = f"{day.month}/{day.day}"
            is_weekend = day.weekday() >= 5
            is_outside_month = day.month != month
            
            # Choose format based on weekend and month
            if is_outside_month:
                fmt = formats['outside_month_header']
            elif is_weekend:
                fmt = formats['weekend_header']
            else:
                fmt = formats['header']
            
            worksheet.write(2, col, date_str, fmt)
        
        # Row 3: Weekday headers
        worksheet.write(3, 0, "", formats['header'])
        worksheet.write(3, 1, "", formats['header'])
        
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        for i, day in enumerate(all_days):
            col = i + 2
            weekday = weekday_names[day.weekday()]
            is_weekend = day.weekday() >= 5
            is_outside_month = day.month != month
            
            if is_outside_month:
                fmt = formats['outside_month_header']
            elif is_weekend:
                fmt = formats['weekend_header']
            else:
                fmt = formats['header']
            
            worksheet.write(3, col, weekday, fmt)
        
        # Employee data rows
        for emp_idx, employee in enumerate(self.employees):
            row = 4 + emp_idx
            worksheet.write(row, 0, emp_idx + 1, formats['cell'])
            worksheet.write(row, 1, employee, formats['cell'])
            
            for day_idx, day in enumerate(all_days):
                col = day_idx + 2
                
                # Find the week that contains this day
                day_type = self._get_day_type_for_date(day, employee, month_weeks)
                
                is_weekend = day.weekday() >= 5
                is_outside_month = day.month != month
                
                # Choose format based on day type, weekend, and month
                fmt = self._get_cell_format(day_type, is_weekend, is_outside_month, formats)
                
                worksheet.write(row, col, day_type.value, fmt)
        
        # Summary section
        self._add_summary_section(worksheet, month_weeks, formats, 4 + len(self.employees) + 2)
        
        # Set column widths and row heights
        self._format_layout(worksheet, total_cols, len(self.employees))
        
        workbook.close()
        print(f"Excel generated: {output_path}")
    
    def _create_formats(self, workbook, primary_blue, light_blue, weekend_blue, 
                       accent_green, warning_red, soft_gray, dark_gray, 
                       outside_month_gray) -> Dict[str, Any]:
        """Create all formatting styles."""
        return {
            'title': workbook.add_format({
                'font_size': 18, 'bold': True, 'align': 'center', 'valign': 'vcenter',
                'font_color': primary_blue, 'bg_color': soft_gray,
                'border': 2, 'border_color': primary_blue
            }),
            'date': workbook.add_format({
                'font_size': 14, 'bold': True, 'align': 'center', 'valign': 'vcenter',
                'font_color': primary_blue, 'bg_color': light_blue
            }),
            'header': workbook.add_format({
                'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': primary_blue, 'font_color': 'white', 'font_size': 11
            }),
            'weekend_header': workbook.add_format({
                'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': accent_green, 'font_color': 'white', 'font_size': 11
            }),
            'outside_month_header': workbook.add_format({
                'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': outside_month_gray, 'font_color': dark_gray, 'font_size': 11
            }),
            'cell': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'border_color': light_blue
            }),
            'weekend': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': weekend_blue, 'border_color': accent_green
            }),
            'outside_month': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': outside_month_gray, 'font_color': dark_gray
            }),
            'oncall': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'color': 'white', 'bold': True, 'bg_color': warning_red, 'font_size': 12
            }),
            'rest': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'color': 'white', 'bold': True, 'bg_color': accent_green, 'font_size': 12
            }),
            'weekend_oncall': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'color': warning_red, 'bold': True, 'bg_color': weekend_blue, 'font_size': 12
            }),
            'weekend_rest': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'color': accent_green, 'bold': True, 'bg_color': weekend_blue, 'font_size': 12
            }),
            'outside_month_oncall': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'color': warning_red, 'bold': True, 'bg_color': outside_month_gray, 'font_size': 12
            }),
            'outside_month_rest': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'color': accent_green, 'bold': True, 'bg_color': outside_month_gray, 'font_size': 12
            })
        }
    
    def _get_day_type_for_date(self, target_date: date, employee: str, 
                              month_weeks: List[WeekPlan]) -> DayType:
        """Get day type for specific employee on specific date."""
        for week in month_weeks:
            week_start = week.week_start
            week_end = week_start + timedelta(days=6)
            
            if week_start <= target_date <= week_end:
                day_of_week = target_date.weekday()
                return week.get_assignment(day_of_week, employee) or DayType.WORK
        
        return DayType.WORK  # Default fallback
    
    def _get_cell_format(self, day_type: DayType, is_weekend: bool, 
                        is_outside_month: bool, formats: Dict[str, Any]):
        """Get appropriate cell format based on conditions."""
        if is_outside_month:
            if day_type == DayType.ON_CALL:
                return formats['outside_month_oncall']
            elif day_type == DayType.REST:
                return formats['outside_month_rest']
            else:
                return formats['outside_month']
        elif is_weekend:
            if day_type == DayType.ON_CALL:
                return formats['weekend_oncall']
            elif day_type == DayType.REST:
                return formats['weekend_rest']
            else:
                return formats['weekend']
        else:
            if day_type == DayType.ON_CALL:
                return formats['oncall']
            elif day_type == DayType.REST:
                return formats['rest']
            else:
                return formats['cell']
    
    def _add_summary_section(self, worksheet, month_weeks: List[WeekPlan], 
                           formats: Dict[str, Any], start_row: int) -> None:
        """Add employee summary statistics section."""
        # Calculate statistics from all weeks
        employee_stats = {emp: {"听": 0, "休": 0, "白": 0} for emp in self.employees}
        
        for week in month_weeks:
            for day in range(7):
                for employee in self.employees:
                    day_type = week.get_assignment(day, employee)
                    if day_type:
                        employee_stats[employee][day_type.value] += 1
        
        # Summary header
        worksheet.write(start_row, 0, "员工统计:", formats['title'])
        
        # Summary table headers
        header_row = start_row + 1
        worksheet.write(header_row, 0, "姓名", formats['header'])
        worksheet.write(header_row, 1, "值班天数", formats['header'])
        worksheet.write(header_row, 2, "休息天数", formats['header'])
        worksheet.write(header_row, 3, "工作天数", formats['header'])
        worksheet.write(header_row, 4, "总天数", formats['header'])
        
        # Summary data
        for i, employee in enumerate(self.employees):
            row = header_row + 1 + i
            stats = employee_stats[employee]
            total = sum(stats.values())
            
            worksheet.write(row, 0, employee, formats['cell'])
            worksheet.write(row, 1, stats["听"], formats['oncall'])
            worksheet.write(row, 2, stats["休"], formats['rest'])
            worksheet.write(row, 3, stats["白"], formats['cell'])
            worksheet.write(row, 4, total, formats['header'])
    
    def _format_layout(self, worksheet, total_cols: int, num_employees: int) -> None:
        """Set column widths and row heights."""
        # Row heights
        worksheet.set_row(0, 25)  # Title
        worksheet.set_row(1, 20)  # Date
        worksheet.set_row(2, 18)  # Headers
        worksheet.set_row(3, 18)  # Weekdays
        
        # Employee rows
        for i in range(num_employees):
            worksheet.set_row(4 + i, 20)
        
        # Column widths
        worksheet.set_column(0, 0, 10)  # 序号
        worksheet.set_column(1, 1, 15)  # 姓名
        worksheet.set_column(2, total_cols - 1, 7)  # Date columns
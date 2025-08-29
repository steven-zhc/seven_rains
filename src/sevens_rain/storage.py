"""JSON storage for week plans and metadata."""

import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import date, timedelta
from .models import WeekPlan


class PlanStorage:
    """Handles persistence of week plans to JSON storage."""
    
    def __init__(self, storage_path: str = "plan.json"):
        """
        Initialize storage handler.
        
        Args:
            storage_path: Path to JSON file for storing plans
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_file()
    
    def _ensure_storage_file(self) -> None:
        """Create storage file if it doesn't exist."""
        if not self.storage_path.exists():
            self.storage_path.write_text(json.dumps({"weeks": []}))
    
    def save_week(self, week_plan: WeekPlan) -> None:
        """
        Save week plan to storage.
        
        Args:
            week_plan: WeekPlan to save
        """
        data = self._load_data()
        
        # Remove existing plan for same week (if any)
        week_start_str = week_plan.week_start.isoformat()
        data["weeks"] = [w for w in data["weeks"] if w["week_start"] != week_start_str]
        
        # Add new plan
        data["weeks"].append(week_plan.to_dict())
        
        # Sort by week_start for better organization
        data["weeks"].sort(key=lambda w: w["week_start"])
        
        self._save_data(data)
    
    def load_week(self, week_start: date) -> Optional[WeekPlan]:
        """
        Load specific week plan.
        
        Args:
            week_start: Monday of the week to load
            
        Returns:
            WeekPlan if found, None otherwise
        """
        data = self._load_data()
        week_start_str = week_start.isoformat()
        
        for week_data in data["weeks"]:
            if week_data["week_start"] == week_start_str:
                return WeekPlan.from_dict(week_data)
        
        return None
    
    def load_previous_weeks(self, from_date: date, count: int = 4) -> List[WeekPlan]:
        """
        Load previous weeks for rule checking.
        
        Args:
            from_date: Reference date to load weeks before
            count: Number of previous weeks to load
            
        Returns:
            List of WeekPlan objects (most recent first)
        """
        data = self._load_data()
        previous_weeks = []
        
        # Find weeks before from_date
        for week_data in data["weeks"]:
            week_start = date.fromisoformat(week_data["week_start"])
            if week_start < from_date:
                previous_weeks.append(WeekPlan.from_dict(week_data))
        
        # Sort by week_start (most recent first) and limit count
        previous_weeks.sort(key=lambda w: w.week_start, reverse=True)
        return previous_weeks[:count]
    
    def get_month_weeks(self, year: int, month: int) -> List[WeekPlan]:
        """
        Get all weeks that overlap with given month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            List of WeekPlan objects that overlap with the month
        """
        data = self._load_data()
        month_weeks = []
        
        # Define month boundaries
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        for week_data in data["weeks"]:
            week_start = date.fromisoformat(week_data["week_start"])
            week_end = week_start + timedelta(days=6)
            
            # Check if week overlaps with month
            if (week_start <= month_end and week_end >= month_start):
                month_weeks.append(WeekPlan.from_dict(week_data))
        
        # Sort by week_start
        month_weeks.sort(key=lambda w: w.week_start)
        return month_weeks
    
    def get_all_weeks(self) -> List[WeekPlan]:
        """
        Get all stored weeks.
        
        Returns:
            List of all WeekPlan objects sorted by week_start
        """
        data = self._load_data()
        all_weeks = []
        
        for week_data in data["weeks"]:
            all_weeks.append(WeekPlan.from_dict(week_data))
        
        all_weeks.sort(key=lambda w: w.week_start)
        return all_weeks
    
    def delete_week(self, week_start: date) -> bool:
        """
        Delete specific week plan.
        
        Args:
            week_start: Monday of the week to delete
            
        Returns:
            True if deleted, False if not found
        """
        data = self._load_data()
        week_start_str = week_start.isoformat()
        
        original_count = len(data["weeks"])
        data["weeks"] = [w for w in data["weeks"] if w["week_start"] != week_start_str]
        
        if len(data["weeks"]) < original_count:
            self._save_data(data)
            return True
        
        return False
    
    def clear_all(self) -> None:
        """Clear all stored plans."""
        self._save_data({"weeks": []})
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with statistics about stored data
        """
        data = self._load_data()
        weeks = data["weeks"]
        
        if not weeks:
            return {"total_weeks": 0, "date_range": None}
        
        week_starts = [date.fromisoformat(w["week_start"]) for w in weeks]
        
        return {
            "total_weeks": len(weeks),
            "earliest_week": min(week_starts).isoformat(),
            "latest_week": max(week_starts).isoformat(),
            "storage_file_size": self.storage_path.stat().st_size,
        }
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default structure if file is missing or corrupted
            default_data = {"weeks": []}
            self._save_data(default_data)
            return default_data
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def backup(self, backup_path: str) -> None:
        """
        Create backup of current storage.
        
        Args:
            backup_path: Path for backup file
        """
        data = self._load_data()
        backup_file = Path(backup_path)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def restore(self, backup_path: str) -> None:
        """
        Restore from backup file.
        
        Args:
            backup_path: Path to backup file
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._save_data(data)
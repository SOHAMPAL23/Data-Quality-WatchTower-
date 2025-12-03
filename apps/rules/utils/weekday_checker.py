import datetime
from django.utils import timezone


def is_weekday():
    """
    Check if today is a weekday (Monday through Friday)
    
    Returns:
        bool: True if today is a weekday, False if it's a weekend
    """
    # Get current day of week (0=Monday, 6=Sunday)
    current_day = timezone.now().weekday()
    
    # Monday through Friday are 0-4
    return current_day < 5


def is_weekday_date(date):
    """
    Check if a specific date is a weekday (Monday through Friday)
    
    Args:
        date (datetime.date): Date to check
        
    Returns:
        bool: True if date is a weekday, False if it's a weekend
    """
    # Get day of week (0=Monday, 6=Sunday)
    day_of_week = date.weekday()
    
    # Monday through Friday are 0-4
    return day_of_week < 5
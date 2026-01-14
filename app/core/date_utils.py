"""Date and time utility functions for the CMS."""

import calendar
from datetime import datetime


def add_months(dt: datetime, delta: int) -> datetime:
    """
    Add or subtract months from a datetime object.

    Handles edge cases like:
    - Year boundaries (e.g., Jan + 12 months = next Jan)
    - Month-end dates (e.g., Jan 31 + 1 month = Feb 28/29)

    Args:
        dt: The datetime to modify
        delta: Number of months to add (positive) or subtract (negative)

    Returns:
        A new datetime with the months added/subtracted

    Example:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 31)
        >>> add_months(dt, 1)  # Jan 31 + 1 month = Feb 29 (2024 is leap year)
        datetime(2024, 2, 29, 0, 0)
    """
    month = dt.month - 1 + delta
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)

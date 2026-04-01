from datetime import datetime
from decimal import Decimal


def record_to_dict(record):
    """Convert asyncpg Record to dict with datetime and Decimal serialization"""
    result = dict(record)
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
    return result

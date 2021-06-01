
import calendar
from datetime import datetime

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12 )
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime(year,month,day,23,00)

def add_month(d):
    year = d.year
    month = d.month
    month += 1
    if month == 13:
        month = 1
        year += 1
    day = min(d.day, calendar.monthrange(year,month)[1])
    return datetime(year, month, day)

def calculate_future_charges(now, charge_day, price):
    XXXX
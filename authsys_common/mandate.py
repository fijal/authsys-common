
import os
from fpdf import FPDF
from datetime import datetime, timedelta
from authsys_common.dates import add_month
import calendar

MAX_X = 210
MAX_Y = 297

def get_next_monday():
    today = datetime.now().replace(hour=0, minute=0, second=0)
    while today.weekday() != 0:
        today += timedelta(days=1)
    return today

def add_ending(day):
    if day in (1, 21):
        day = str(day) + 'st'
    elif day in (2, 22):
        day = str(day) + 'nd'
    else:
        day = str(day) + 'th'
    return day

def create_mandate(member_id, name, address, bank, branch_code, account_number, account_type,
                   price, phone, charge_day):
    f = FPDF('P', 'mm', 'A4')
    f.add_page()
    pth = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mandate3.png')
    f.image(pth, 0, 0, MAX_X, MAX_Y)
    f.set_font('Courier', '', 12)
    f.text(85, 68, name)
    f.text(33, 75, address)
    f.text(27, 81, bank)
    f.text(43, 88, branch_code)
    f.text(133, 88, account_number)
    if account_type != "1":
        f.line(45, 94.5, 80, 94.5)
    if account_type != "2":
        f.line(83, 94.5, 100, 94.5)
    if account_type != "3":
        f.line(101, 94.5, 125, 94.5)
    now = datetime.now()
    f.text(31, 101, "R" + str(price))
    f.text(86, 101, now.strftime("%d/%b/%Y"))
    f.text(164, 101, phone)
    f.text(140, 122, now.strftime("%d/%b/%Y"))

    # calculate detailed charges
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    #price_per_day = price / days_in_month
    first_charge = price # price_per_day * (days_in_month - now.day)
    first_charge_day = datetime.now().replace(minute=0, hour=0, second=0, day=charge_day)
    if charge_day < datetime.now().day + 5:
        # should be always true
        # first_charge += price
        first_charge_day = add_month(first_charge_day)

    f.text(74, 146, "R%.2f" % first_charge)
    f.text(123, 146, first_charge_day.strftime("%d/%b/%Y"))

    f.text(84, 151, "R%.2f" % price)
    f.text(122, 151, add_ending(charge_day))
    f.text(30, 160.5, add_ending(charge_day))

    f.text(30, 257, "Cape Town")
    f.text(75, 257, add_ending(now.day))
    f.text(100, 257, now.strftime("%B"))
    f.text(60, 278.6, "B11-" + str(member_id))
#    f.set_font('Arial', '', 6)
#    f.text()
    
    return f.output(dest='S')

if __name__ == '__main__':
    s = create_mandate(member_id=123, name='Maciej Fijalkowski', address="Pizdowo 16",
        bank='First National Bank', branch_code='123456', account_number='4353234432',
        account_type="1", price=450, phone="12334435", charge_day=13)
    open("out.pdf", "w").write(s)
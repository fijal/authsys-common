
""" some common queries that can be done on the data
"""
import time
import datetime
import calendar

from sqlalchemy import select, desc, outerjoin, and_, func, delete

from .model import members, entries, tokens, subscriptions, daily_passes

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12 )
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.datetime(year,month,day,23,00)

def get_member_list(con):
    """ List all the members with whether they paid or not
    """
    s = select([members, tokens]).where(
        and_(members.c.id == tokens.c.member_id, tokens.c.valid))
    return [(x[0], x[1]) for x in con.execute(s)]

def get_member_data(con, no):
    """ Get the subscription data for a single member
    """
    max_timestamp = list(con.execute(
        select([func.max(subscriptions.c.end_timestamp)]).where(
        subscriptions.c.member_id == no)))[0][0]
    if max_timestamp is None:
        m_id, name, tstamp = list(con.execute(select(
            [members.c.id, members.c.name, members.c.timestamp]).where(
            members.c.id == no)))[0]
        return (m_id, name, tstamp, None, None)
    return [(x[0], x[1], x[2], x[3], x[4]) for x in con.execute(
        select([members.c.id, members.c.name, members.c.timestamp, subscriptions.c.type,
        subscriptions.c.end_timestamp]).where(
        and_(and_(members.c.id == no, subscriptions.c.member_id == no),
            subscriptions.c.end_timestamp == max_timestamp)))][0]

def day_start_end():
    now = datetime.datetime.now()
    day_start = time.mktime(now.replace(hour=0, minute=0).timetuple())
    day_end = time.mktime(now.replace(hour=23, minute=0).timetuple())
    return day_start, day_end

def list_indemnity_forms(con):
    """ List all the indemnity forms that have no assigned tokens
    """
    day_start, day_end = day_start_end()
    oj = outerjoin(
        outerjoin(members, tokens, members.c.id == tokens.c.member_id), daily_passes,
        and_(members.c.id == daily_passes.c.member_id,
            and_(daily_passes.c.timestamp > day_start, daily_passes.c.timestamp < day_end)))
    return [(a, b, c, d, e) for a, b, c, d, e in con.execute(select(
        [members.c.id, members.c.name, members.c.id_number,
        members.c.timestamp, daily_passes.c.timestamp]).select_from(oj).order_by(desc(members.c.timestamp)))]

def daypass_change(con, no):
    day_start, day_end = day_start_end()
    lst = list(con.execute(select([daily_passes]).where(and_(and_(daily_passes.c.timestamp > day_start,
        daily_passes.c.timestamp < day_end), daily_passes.c.member_id == no))))
    if len(lst) == 0:
        con.execute(daily_passes.insert().values(timestamp = int(time.time()), member_id=no))
    else:
        con.execute(daily_passes.delete().where(daily_passes.c.id == lst[0][0]))

def get_form(con, no):
    """ Get indemnity form for a member 'no'
    """
    return list(list(con.execute(select([members.c.id,
        members.c.name,
        members.c.id_number]).where(members.c.id == no)))[0])

def unrecognized_entries_after(con, timestamp):
    """ List all unrecognized entries after 'timestamp'
    """
    oj = outerjoin(entries, tokens, entries.c.token_id == tokens.c.id)
    s = select([entries.c.token_id]).select_from(oj).where(
        and_(entries.c.timestamp >= timestamp, tokens.c.id == None)).order_by(
        desc(entries.c.timestamp))
    return [x[0] for x in con.execute(s)]

def add_one_month_subscription(con, no, type='regular'):
    t0 = list(con.execute(
        select([func.max(subscriptions.c.end_timestamp)]).where(
        subscriptions.c.member_id == no)))[0][0]
    if t0 is None:
        t0 = time.time()
    end_t = time.mktime(add_months(datetime.datetime.fromtimestamp(t0), 1).timetuple())
    con.execute(subscriptions.insert().values({
        'member_id': no,
        'type': type,
        'start_timestamp': time.time(),
        'end_timestamp': end_t,
        }))

def remove_subscription(con, no):
    t0 = list(con.execute(
        select([func.max(subscriptions.c.end_timestamp)]).where(
        subscriptions.c.member_id == no)))[0][0]
    if t0 is None or t0 < time.time():
        return
    id = list(con.execute(select([subscriptions.c.id]).where(
        subscriptions.c.end_timestamp == t0)))[0][0]
    con.execute(delete(subscriptions, subscriptions.c.id == id))

def change_date(con, no, year, month, day):
    tstamp = time.mktime(datetime.datetime(int(year), int(month), int(day), 23, 00).timetuple())
    lst = list(con.execute(select([subscriptions.c.id]).where(and_(subscriptions.c.end_timestamp > time.time(),
        subscriptions.c.member_id == no)).order_by(desc(subscriptions.c.end_timestamp))))
    id = lst[0][0]
    con.execute(subscriptions.update().where(subscriptions.c.id==id).values(end_timestamp=tstamp))

def entries_after(con, timestamp):
    """ List all the entries after 'timestamp' with extra information
    about the subscription and validity
    """
    oj = outerjoin(outerjoin(outerjoin(entries, tokens, and_(
        entries.c.token_id == tokens.c.id, tokens.c.valid)),
        members, members.c.id == tokens.c.member_id),
        subscriptions, and_(subscriptions.c.member_id == members.c.id,
            subscriptions.c.end_timestamp >= entries.c.timestamp))
    r = con.execute(select([entries.c.token_id, members.c.name,
        entries.c.timestamp, subscriptions.c.end_timestamp, subscriptions.c.type]).select_from(oj).where(
        entries.c.timestamp >= timestamp).order_by(desc(entries.c.timestamp)))
    l = []
    last_token_id = None
    for (token_id, b, c, d, tp) in r:
        if tp == 'regular' and token_id == last_token_id:
            l.pop()
        last_token_id = token_id
        l.append((token_id, b, c, d, tp))
    return l

def is_valid_token(con, token_id, t):
    r = [(a, b, c, d) for a, b, c, d in
    list(con.execute(select([members.c.name, tokens.c.id, subscriptions.c.start_timestamp,
        subscriptions.c.end_timestamp]).where(and_(tokens.c.id == token_id,
        members.c.id == tokens.c.member_id, tokens.c.valid,
        subscriptions.c.member_id == members.c.id, subscriptions.c.end_timestamp > t,
        subscriptions.c.start_timestamp - 3600 * 24 < t))))]
    return len(r) == 1

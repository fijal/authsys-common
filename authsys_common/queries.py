
""" some common queries that can be done on the data
"""
import time
import datetime
import calendar

from sqlalchemy import select, desc, outerjoin, and_, func, delete

from .model import members, entries, tokens, subscriptions

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

def list_indemnity_forms(con):
    """ List all the indemnity forms that have no assigned tokens
    """
    oj = outerjoin(members, tokens, members.c.id == tokens.c.member_id)
    return [(a, b, c, d) for a, b, c, d in con.execute(select(
        [members.c.id, members.c.name, members.c.id_number,
        members.c.timestamp]).select_from(oj).where(
        tokens.c.id == None).order_by(entries.c.timestamp))]

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

def entries_after(con, timestamp):
    """ List all the entries after 'timestamp' with extra information
    about the subscription and validity
    """
    oj = outerjoin(outerjoin(outerjoin(entries, tokens, and_(
        entries.c.token_id == tokens.c.id, tokens.c.valid)),
        members, members.c.id == tokens.c.member_id),
        subscriptions, and_(subscriptions.c.member_id == members.c.id,
            subscriptions.c.end_timestamp >= entries.c.timestamp))
    return [(a, b, c, d, e) for a, b, c, d, e in
        con.execute(select([entries.c.token_id, members.c.name,
        entries.c.timestamp, subscriptions.c.end_timestamp, subscriptions.c.type]).select_from(oj).where(
        entries.c.timestamp >= timestamp).order_by(desc(entries.c.timestamp)))]

def is_valid_token(con, token_id, t):
    r = [(a, b, c, d) for a, b, c, d in
    list(con.execute(select([members.c.name, tokens.c.id, subscriptions.c.start_timestamp,
        subscriptions.c.end_timestamp]).where(and_(tokens.c.id == token_id,
        members.c.id == tokens.c.member_id, tokens.c.valid,
        subscriptions.c.member_id == members.c.id, subscriptions.c.end_timestamp > t,
        subscriptions.c.start_timestamp - 3600 * 24 < t))))]
    return len(r) == 1

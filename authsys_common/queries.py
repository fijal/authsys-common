
""" some common queries that can be done on the data
"""
import time
import datetime
import calendar

from sqlalchemy import select, desc, outerjoin, and_, func, delete, or_

from .model import members, entries, tokens, subscriptions, daily_passes, payment_history,\
    free_passes

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
        m_id, name, tstamp, memb_type = list(con.execute(select(
            [members.c.id, members.c.name, members.c.timestamp, members.c.member_type]).where(
            members.c.id == no)))[0]
        return {'member_id': m_id, 'name': name, 'subscription_type': None,
                'start_timestamp': tstamp, 'credit_card_token': None, 'member_type': memb_type,
                'subscription_ends': None}
    return [{'member_id' : x[0], 'name': x[1], 'subscription_type': x[3],
        'start_timestamp': x[2], 'subscription_starts': x[4],
        'subscription_ends' : x[5], 'member_type': x[6],
        'credit_card_token' : x[7]} for x in con.execute(
        select([members.c.id, members.c.name, members.c.timestamp, subscriptions.c.type,
        subscriptions.c.start_timestamp, subscriptions.c.end_timestamp, members.c.member_type,
        members.c.credit_card_id]).where(
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
    oj = outerjoin(outerjoin(
        outerjoin(members, tokens, members.c.id == tokens.c.member_id), daily_passes,
        and_(members.c.id == daily_passes.c.member_id,
            and_(daily_passes.c.timestamp > day_start, daily_passes.c.timestamp < day_end))),
        free_passes, members.c.id == free_passes.c.member_id)
    return [(a, b, c, d, e, f) for a, b, c, d, e, f in con.execute(select(
        [members.c.id, members.c.name, members.c.id_number,
        members.c.timestamp, daily_passes.c.timestamp,
        free_passes.c.timestamp]).select_from(oj).order_by(desc(members.c.timestamp)))]

def daypass_change(con, no):
    day_start, day_end = day_start_end()
    lst = list(con.execute(select([daily_passes]).where(and_(and_(daily_passes.c.timestamp > day_start,
        daily_passes.c.timestamp < day_end), daily_passes.c.member_id == no))))
    if len(lst) == 0:
        con.execute(daily_passes.insert().values(timestamp = int(time.time()), member_id=no))
    else:
        con.execute(daily_passes.delete().where(daily_passes.c.id == lst[0][0]))

def freepass_change(con, no):
    lst = list(con.execute(select([free_passes]).where(free_passes.c.member_id == no)))
    if len(lst) == 0:
        con.execute(free_passes.insert().values(timestamp = int(time.time()), member_id=no))
    else:
        con.execute(free_passes.delete().where(free_passes.c.id == lst[0][0]))

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

def add_one_month_subscription(con, no, type='regular', t0=None):
    if t0 is None:
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
        and_(subscriptions.c.end_timestamp == t0, subscriptions.c.member_id == no))))[0][0]
    con.execute(delete(subscriptions, subscriptions.c.id == id))

def change_date(con, no, year, month, day):
    tstamp = time.mktime(datetime.datetime(int(year), int(month), int(day), 23, 00).timetuple())
    lst = list(con.execute(select([subscriptions.c.id]).where(and_(subscriptions.c.end_timestamp > time.time(),
        subscriptions.c.member_id == no)).order_by(desc(subscriptions.c.end_timestamp))))
    id = lst[0][0]
    con.execute(subscriptions.update().where(subscriptions.c.id==id).values(end_timestamp=tstamp))

def add_till(con, tp, no, year, month, day):
    tstamp = time.mktime(datetime.datetime(int(year), int(month), int(day), 23, 00).timetuple())
    lst = list(con.execute(select([subscriptions.c.id]).where(and_(subscriptions.c.end_timestamp > tstamp,
        subscriptions.c.member_id == no)).order_by(desc(subscriptions.c.end_timestamp))))
    if len(lst) > 0:
        return change_date(con, no, year, month, day)
    con.execute(subscriptions.insert().values({
        'member_id': no,
        'type': tp,
        'start_timestamp': time.time(),
        'end_timestamp': tstamp,
        }))    

def entries_after(con, timestamp):
    """ List all the entries after 'timestamp' with extra information
    about the subscription and validity
    """
    oj = outerjoin(outerjoin(outerjoin(entries, tokens, and_(
        entries.c.token_id == tokens.c.id, tokens.c.valid)),
        members, members.c.id == tokens.c.member_id),
        subscriptions, or_(and_(subscriptions.c.member_id == members.c.id,
            subscriptions.c.end_timestamp >= entries.c.timestamp),
                           and_(members.c.member_type == 'perpetual', members.c.id == subscriptions.c.member_id)))
    r = con.execute(select([entries.c.token_id, members.c.name,
        entries.c.timestamp, subscriptions.c.end_timestamp, subscriptions.c.type, members.c.member_type]).select_from(oj).where(
        entries.c.timestamp >= timestamp).order_by(desc(entries.c.timestamp)))
    l = []
    last_token_id = None
    for (token_id, b, c, d, tp, member_tp) in r:
        if tp == 'regular' and token_id == last_token_id:
            l.pop()
        last_token_id = token_id
        l.append((token_id, b, c, d, tp, member_tp))
    return l

def max_id_of_payment_history(con):
    return list(con.execute(select([func.max(payment_history.c.id)])))[0][0]

def get_customer_name_email(con, no):
    return [(x[0], x[1]) for x in con.execute(
        select([members.c.name, members.c.email]).where(members.c.id == no))][0]

def payments_write_transaction(con, no, tp, timestamp, id, code, description, price, membership_type):
    con.execute(payment_history.insert().values({
        'member_id': no,
        'type': tp,
        'timestamp': int(timestamp),
        'out_code': code,
        'out_description': description,
        'price': price,
        'token_id': id,
        'membership_type': membership_type,
        }))

def record_credit_card_token(con, member_id, token_id):
    con.execute(members.update().where(members.c.id == member_id).values(credit_card_id=token_id))

def get_last_payment_id(con, no):
    return list(con.execute(select([payment_history.c.token_id]).where(payment_history.c.member_id == no).order_by(
        desc(payment_history.c.id)).limit(1)))[0][0]

def get_payment_history(con, no):
    return [(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8]) for x in 
        con.execute(select([payment_history]).where(payment_history.c.member_id == no).order_by(
            desc(payment_history.c.id)))]

def payments_get_id_sum_tp(con, token_id):
    return [(x[0], x[1], x[2]) for x in con.execute(select([payment_history.c.member_id,
        payment_history.c.price, payment_history.c.membership_type]).where(payment_history.c.token_id == token_id))][0]

def change_membership_type(con, no, tp):
    if tp == "none":
        tp = None
    con.execute(members.update().where(members.c.id == no).values(member_type=tp))

def is_valid_token(con, token_id, t):
    r = [(a, b, c, d) for a, b, c, d in
    list(con.execute(select([members.c.name, tokens.c.id, subscriptions.c.start_timestamp,
        subscriptions.c.end_timestamp]).where(and_(tokens.c.id == token_id,
        members.c.id == tokens.c.member_id, tokens.c.valid,
        subscriptions.c.member_id == members.c.id, subscriptions.c.end_timestamp > t,
        subscriptions.c.start_timestamp - 3600 * 24 < t))))]
    return len(r) == 1

def get_stats(con):
    total_ondemand = list(con.execute(select([func.count()]).select_from(select([members, subscriptions]).where(
        and_(and_(members.c.member_type == 'ondemand', members.c.id == subscriptions.c.member_id),
            subscriptions.c.end_timestamp > time.time())))))[0][0]
    total_recurring = list(con.execute(select([func.count()]).select_from(select([members]).where(
        and_(members.c.member_type == 'recurring', members.c.credit_card_id != None)))))[0][0]
    total_perpetual = list(con.execute(select([func.count()]).select_from(select([members]).where(
        members.c.member_type == 'perpetual'))))[0][0]
    total_visitors = list(con.execute(select([func.count()]).select_from(members)))[0][0]
    return {
        'total_ondemand': total_ondemand,
        'total_recurring': total_recurring,
        'total_perpetual': total_perpetual,
        'total_visitors': total_visitors,
    }

def members_to_update(con):
    lst = list(con.execute(select([members.c.id, members.c.name, members.c.credit_card_id,
        subscriptions.c.type, subscriptions.c.start_timestamp,
        subscriptions.c.end_timestamp]).where(and_(
        and_(members.c.member_type == 'recurring',
        members.c.credit_card_id != None), members.c.id == subscriptions.c.member_id))))
    subs = {}
    for item in lst:
        subs[item[0]] = subs.get(item[0], [])
        subs[item[0]].append(item[1:])
    for k, v in subs.items():
        v.sort()
    d = datetime.datetime.fromtimestamp(time.time()).replace(hour=22, minute=0)
    newsubs = {}
    for k, v in subs.items():
        if v[-1][-1] > time.mktime(d.timetuple()):
            continue
        newsubs[k] = v[-1]
    return newsubs

""" some common queries that can be done on the data
"""
import time
import datetime
import calendar
from pprint import pprint

from sqlalchemy import select, desc, outerjoin, and_, func, delete, or_

from .model import members, entries, tokens, subscriptions, daily_passes, payment_history,\
    free_passes, league, covid_indemnity, transactions, failed_checks, pending_transactions
from .dates import add_months, add_month
from .scripts import get_config


def get_member_list(con, query):
    """ List all the members with whether they paid or not
    """
    s = select([members.c.id, members.c.name, members.c.phone, members.c.email])
    r = []
    query = query.lower()
    for id, name, phone, email in con.execute(s):
        day_start, day_end = day_start_end()
        if (name and query in name.lower()) or (phone and query in phone.lower()) or (email and query in email.lower()):
            r.append({'id': id,'name': name, 'phone': phone, 'email': email})

            lst = list(con.execute(select([daily_passes.c.timestamp]).where(and_(and_(
                    daily_passes.c.member_id == id,
                    daily_passes.c.timestamp < day_end),
                    daily_passes.c.timestamp > day_start))))
            if len(lst) > 0:
                last_daypass_timestamp = lst[0][0]
            else:
                last_daypass_timestamp = None
            r[-1]['last_daypass_timestamp'] = last_daypass_timestamp

    return r

def get_next_monday():
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    while today.weekday() != 0:
        today += datetime.timedelta(days=1)
    return time.mktime(today.timetuple())

def get_member_data(con, no):
    """ Get the subscription data for a single member
    """
    day_start, day_end = day_start_end()
    month_start, month_end = month_start_end()
    subs = list(con.execute(select([subscriptions.c.id, subscriptions.c.start_timestamp,
        subscriptions.c.end_timestamp, subscriptions.c.type]).where(
        and_(subscriptions.c.end_timestamp > time.time(), subscriptions.c.member_id == no)).order_by(
        subscriptions.c.end_timestamp)))
    m_id, name, m_id_number, phone, tstamp, memb_type, notes, sub_type, account_number, \
        debit_order_signup_timestamp, last_id_checked, last_id_update, photo, id_photo, charge_day = list(con.execute(select(
        [members.c.id, members.c.name, members.c.id_number, members.c.phone, members.c.timestamp, members.c.member_type,
        members.c.extra_notes, members.c.subscription_type, members.c.account_number, members.c.debit_order_signup_timestamp,
        members.c.last_id_checked, members.c.last_id_update,
        members.c.photo, members.c.id_photo, members.c.debit_order_charge_day]).where(
        members.c.id == no)))[0]
    if last_id_checked is None:
        f_checks = [x[0] for x in con.execute(select([failed_checks.c.timestamp]).where(
            failed_checks.c.member_id == no))]
    else:
        f_checks = [x[0] for x in con.execute(select([failed_checks.c.timestamp]).where(
            and_(failed_checks.c.member_id == no,
                 failed_checks.c.timestamp > last_id_checked
            )))]
    tok_list = list(con.execute(select([tokens.c.id]).where(
        and_(tokens.c.valid, tokens.c.member_id == m_id)
        )))
    if len(tok_list):
        token_id = tok_list[0][0]
        entry_list = list(con.execute(select([entries.c.timestamp]).where(
            and_(and_(entries.c.token_id == token_id,
                      entries.c.timestamp > day_start),
                 entries.c.timestamp < day_end)).order_by(entries.c.timestamp)))
        if len(entry_list):
            entry_timestamp = entry_list[-1][0]
        else:
            entry_timestamp = None
        valid_token = True
    else:
        entry_timestamp = None
        valid_token = False
    day_pass = list(con.execute(select([daily_passes.c.timestamp]).where(
        and_(and_(daily_passes.c.timestamp > day_start,
                  daily_passes.c.timestamp < day_end),
             daily_passes.c.member_id == m_id)).order_by(daily_passes.c.timestamp)))
    free_pass = list(con.execute(select([free_passes.c.timestamp]).where(
        and_(and_(free_passes.c.member_id == no,
                  free_passes.c.timestamp > month_start),
             free_passes.c.timestamp < month_end)).order_by(free_passes.c.timestamp)))
    r = {'member_id': m_id, 'name': name, 'phone': phone, 'entry_timestamp': entry_timestamp,
         'id_number': m_id_number, 'valid_token': valid_token,
         'start_timestamp': tstamp, 'member_type': memb_type,
         'subscription_starts': None, 'subscription_ends': None, 'extra_notes': notes,
         'subscription_type': sub_type, 'account_number': account_number,
         'last_id_update': last_id_update, 'last_id_checked': last_id_checked,
         'failed_checks': f_checks,
         'charge_day': charge_day,
         'photo_present': photo is not None,
         'next_monday': int(get_next_monday()), 'debit_order_signup_timestamp': debit_order_signup_timestamp}
    #r['covid_indemnity_signed'] = len(list(con.execute(select([covid_indemnity.c.member_id]).where(covid_indemnity.c.member_id == no))))
    if len(day_pass) > 0:
        r['daypass_timestamp'] = day_pass[-1][0]
    if len(free_pass) > 0:
        r['free_friend_timestamp'] = free_pass[-1][0]
    if len(subs) == 2 and subs[0][3] != 'pause':
        r['subscription_starts'] = subs[1][1]
        r['subscription_ends'] = subs[1][2]
    if len(subs) == 1:
        r['subscription_starts'] = subs[0][1]
        r['subscription_ends'] = subs[0][2]
    if len(subs) >= 2 and subs[0][3] == 'pause':
        r['pause_starts'] = subs[0][1]
        r['pause_ends'] = subs[0][2]
        r['subscription_starts'] = subs[1][1]
        r['subscription_ends'] = subs[1][2]
    if len(subs) == 0:
        subs = list(con.execute(select([subscriptions.c.id, subscriptions.c.start_timestamp,
            subscriptions.c.end_timestamp, subscriptions.c.type]).where(
            subscriptions.c.member_id == no).order_by(
            subscriptions.c.end_timestamp)))
        if len(subs) > 0:
            r['last_subscr_ended'] = subs[-1][2]

    conf = get_config()
    if r['subscription_type'] is None:
        r['price'] = '?'
    else:

        try:
            r['price'] = conf.get('price', r['subscription_type'])
        except KeyError:
            r['price'] = "?"

    # this really does not belong here, but it's just so much easier to do in Python...
    now = datetime.datetime.now().date()
    d = add_months(now.replace(day=1), 1).date()
    r['days_till_month_end'] = (d - now).days
    r['days_in_current_month'] = calendar.monthrange(now.year, now.month)[1]

    return r

def day_start_end():
    now = datetime.datetime.now()
    day_start = time.mktime(now.replace(hour=0, minute=0, second=0).timetuple())
    day_end = time.mktime(now.replace(hour=23, minute=0, second=0).timetuple())
    return day_start, day_end

def month_start_end():
    now = datetime.datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0)
    month_end = time.mktime(add_months(month_start, 1).timetuple()) - 3600 * 24
    return time.mktime(month_start.timetuple()), month_end

def add_subscription_and_future_charges(con, member_id, charge_day, price, sub_type):
    now = datetime.datetime.now()
    # calculate detailed charges
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    price_per_day = price / days_in_month
    first_charge = price_per_day * (days_in_month - now.day)
    first_charge_day = now.replace(minute=0, hour=0, second=0, day=charge_day)
    if charge_day < now.day + 5:
        first_charge += price
        first_charge_day = add_month(first_charge_day)
    l = [x for x, in con.execute(select([subscriptions.c.end_timestamp]).where(and_(
        subscriptions.c.member_id == member_id,
        subscriptions.c.end_timestamp > time.mktime(now.timetuple()))))]
    if len(l) > 1:
        return {'error': 'mangled subscriptions'}
    if len(l) == 0:
        start = time.mktime(now.timetuple())
    else:
        start = l[0]
    end_of_the_month = add_month(now).replace(day=1, hour=23, second=0, minute=0)
    con.execute(subscriptions.insert().values(
        member_id=member_id,
        type=sub_type,
        start_timestamp=start,
        end_timestamp=time.mktime(end_of_the_month.timetuple()),
        renewal_id=0
        ))
    if charge_day < now.day + 5:
        next_month_end = add_month(end_of_the_month)
        con.execute(subscriptions.insert().values(
            member_id=member_id,
            type=sub_type,
            start_timestamp=time.mktime(end_of_the_month.timetuple()),
            end_timestamp=time.mktime(next_month_end.timetuple()),
            renewal_id=0
            ))

    con.execute(pending_transactions.insert().values(
        member_id=member_id,
        type=sub_type,
        creation_timestamp=time.time(),
        timestamp=time.mktime(first_charge_day.timetuple()),
        price=first_charge,
        description='pending first charge'
        ))
    return {'success': True}

def list_indemnity_forms(con, query):
    """ List all the indemnity forms that have no assigned tokens
    """
    day_start, day_end = day_start_end()
    oj = outerjoin(members, tokens, members.c.id == tokens.c.member_id)
    res = []
    already = {}
    query = query.lower()
    for item in con.execute(select([members.c.id, members.c.name, members.c.id_number,
        members.c.timestamp, tokens.c.id,
        members.c.email, members.c.phone, members.c.emergency_phone]).select_from(oj).order_by(
        desc(members.c.timestamp))):
        email = item[5]
        phone = item[6]
        name = item[1]
        if not ((name and query in name.lower()) or (phone and query in phone.lower()) or (email and query in email.lower())):
            continue
        already[item[0]] = None
        token_id = item[4]
        member_id = item[0]
        if token_id is not None:
            lst = list(con.execute(select([entries.c.timestamp]).where(and_(and_(
                entries.c.token_id == token_id,
                entries.c.timestamp < day_end),
                entries.c.timestamp > day_start))))
            if len(lst) > 0:
                last_entry_timestamp = lst[0][0]
            else:
                last_entry_timestamp = None
        else:
            last_entry_timestamp = None

        lst = list(con.execute(select([daily_passes.c.timestamp]).where(and_(and_(
                daily_passes.c.member_id == member_id,
                daily_passes.c.timestamp < day_end),
                daily_passes.c.timestamp > day_start))))
        if len(lst) > 0:
           last_daypass_timestamp = lst[0][0]
        else:
            last_daypass_timestamp = None

        res.append({
            'member_id': item[0],
            'name': name,
            'member_id_number': item[2],
            'timestamp': item[3],
            'last_daypass_timestamp': last_daypass_timestamp,
            'last_entry_timestamp': last_entry_timestamp,
            'email': email,
            'phone': phone,
            'emergency_phone': item[7],
        })
    return res

def daypass_change(con, no, gym_id):
    day_start, day_end = day_start_end()
    lst = list(con.execute(select([daily_passes]).where(and_(and_(daily_passes.c.timestamp > day_start,
        daily_passes.c.timestamp < day_end), daily_passes.c.member_id == no))))
    if len(lst) == 0:
        con.execute(daily_passes.insert().values(timestamp = int(time.time()), member_id=no, gym_id=gym_id))
    else:
        con.execute(daily_passes.delete().where(daily_passes.c.id == lst[0][0]))

def freepass_change(con, no, gym_id):
    month_start, month_end = month_start_end()
    lst = list(con.execute(select([free_passes]).where(and_(and_(free_passes.c.timestamp > month_start,
        free_passes.c.timestamp < month_end), free_passes.c.member_id == no))))
    if len(lst) == 0:
        con.execute(free_passes.insert().values(timestamp = int(time.time()), member_id=no, gym_id=gym_id))
    else:
        con.execute(free_passes.delete().where(free_passes.c.id == lst[0][0]))


def member_visit_change(con, no, gym_id):
    lst1 = list(con.execute(select([tokens.c.id]).where(tokens.c.member_id == no)))
    if not lst1:
        return
    token_id = lst1[0][0]
    day_start, day_end = day_start_end()
    lst = list(con.execute(select([entries.c.id]).where(
        and_(and_(
            token_id == entries.c.token_id,
            entries.c.timestamp > day_start),
            entries.c.timestamp < day_end))))
    if len(lst) == 0:
        conf = get_config()
        con.execute(entries.insert().values(timestamp = int(time.time()), token_id=token_id,
                                            gym_id = gym_id))
    else:
        con.execute(entries.delete().where(entries.c.id == lst[0][0]))

def league_register(con, no):
    lst = list(con.execute(select([league]).where(league.c.member_id == no)))
    if len(lst) == 0:
        con.execute(league.insert().values(timestamp = int(time.time()), member_id=no))
    else:
        con.execute(league.delete().where(league.c.id == lst[0][0]))

def get_form(con, no):
    """ Get indemnity form for a member 'no'
    """
    l = list(list(con.execute(select([members.c.id,
        members.c.name,
        members.c.id_number,
        members.c.extra_notes]).where(members.c.id == no)))[0])
    return {
        'id': l[0],
        'name': l[1],
        'id_number': l[2],
        'extra_notes': l[3],
    }

def unrecognized_entries_after(con, timestamp, gym_id):
    """ List all unrecognized entries after 'timestamp'
    """
    oj = outerjoin(entries, tokens, entries.c.token_id == tokens.c.id)
    s = select([entries.c.token_id]).select_from(oj).where(
        and_(entries.c.gym_id == gym_id, and_(entries.c.timestamp >= timestamp, tokens.c.id == None))).order_by(
        desc(entries.c.timestamp))
    return [x[0] for x in con.execute(s)]

def add_one_month_subscription(con, no, type='regular', t0=None):
    if t0 is None:
        t0 = list(con.execute(
            select([func.max(subscriptions.c.end_timestamp)]).where(
            subscriptions.c.member_id == no)))[0][0]
    if t0 is None:
        t0 = time.time()
    # check if this is any sensible, otherwise silently do nothing
    lst = list(con.execute(select([subscriptions.c.start_timestamp]).where(and_(
        subscriptions.c.end_timestamp > t0,
        subscriptions.c.member_id == no))))
    if len(lst) > 0:
        return # double click I would imagine
    end_t = time.mktime(add_months(datetime.datetime.fromtimestamp(t0), 1).timetuple())
    con.execute(subscriptions.insert().values(
        member_id=no, type= type, start_timestamp=t0, end_timestamp= end_t))

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

def entries_after(con, timestamp, gym_id):
    """ List all the entries after 'timestamp' with extra information
    about the subscription and validity
    """
    s = con.execute(select([entries.c.timestamp, entries.c.token_id, tokens.c.member_id,
                            members.c.name, members.c.member_type]).where(
        and_(entries.c.gym_id == gym_id, and_(and_(entries.c.token_id == tokens.c.id, members.c.id == tokens.c.member_id),
            entries.c.timestamp > timestamp))).order_by(desc(entries.c.timestamp)))
    ent = [{'timestamp': _timestamp, 'token_id': _tok_id, 'member_id': _memb_id, 'name': _memb_name, 'member_type': _member_type} for
           _timestamp, _tok_id, _memb_id, _memb_name, _member_type in list(s)]
    res = {}

    for r in ent:
        rr = list(con.execute(select([covid_indemnity.c.member_id]).where(
            covid_indemnity.c.member_id == r['member_id'])))
        r['covid_indemnity'] = len(rr) != 0
        if r['member_type'] == 'perpetual':
            result = r.copy()
            result['subscription_end_timestamp'] = int(time.time()) + 3600 * 24 * 30
            result['sub_type'] = None
            res[r['member_id']] = result
        else:
            q = [(a, b, c) for a, b, c in list(con.execute(select([subscriptions.c.type, subscriptions.c.start_timestamp, subscriptions.c.end_timestamp]).where(
                subscriptions.c.member_id == r['member_id']).order_by(subscriptions.c.end_timestamp)))]
            result = r.copy()
            if len(q) > 0:
                result['subscription_end_timestamp'] = q[-1][2]
                result['sub_type'] = q[-1][0]
            else:
                result['subscription_end_timestamp'] = None
                result['sub_type'] = None
            if r['member_id'] in res:
                if res[r['member_id']]['timestamp'] > r['timestamp']:
                    continue
            res[r['member_id']] = result

    res = res.values()
    res.sort(lambda a, b: -cmp(a['timestamp'], b['timestamp']))
    total_entries = 0
    for item in res:
        if item['timestamp'] > time.time() - 3600 * 2:
            total_entries += 1
    r = list(con.execute(select([daily_passes.c.timestamp]).where(daily_passes.c.timestamp > time.time() - 3600 * 2)))
    total = total_entries + len(r)
    return {'entries': res, 'total': total}

def last_visits_by_user_id(con, user_id):
    xxx

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
    return [{
        'timestamp': x[0],
        'price': x[1],
        'type': x[2],
        'description': x[3],
        'outcome': x[4]
    } for x in 
        con.execute(select([transactions.c.timestamp, transactions.c.price,
            transactions.c.type, transactions.c.description, transactions.c.outcome]).where(
            transactions.c.member_id == no).order_by(
            transactions.c.timestamp))]

def payments_get_id_sum_tp(con, token_id):
    return [(x[0], x[1], x[2]) for x in con.execute(select([payment_history.c.member_id,
        payment_history.c.price, payment_history.c.membership_type]).where(payment_history.c.token_id == token_id))][0]

def change_membership_type(con, no, tp):
    if tp == "none":
        tp = None
    con.execute(members.update().where(members.c.id == no).values(member_type=tp))

def change_subscription_type(con, no, tp):
    con.execute(members.update().where(members.c.id == no).values(subscription_type=tp))
    r = list(con.execute(
        select([func.max(subscriptions.c.end_timestamp)]).where(
        subscriptions.c.member_id == no)))
    if len(r) == 0:
        return
    max_timestamp = r[0][0]
    if max_timestamp is None:
        return

    subscr = list(con.execute(select([subscriptions.c.id]).where(
            and_(subscriptions.c.member_id == no, subscriptions.c.end_timestamp == max_timestamp))))
    if len(subscr) == 2:
        subscr_id = subscr[1][0]
    else:
        assert len(subscr) == 1, repr(subscr)
        subscr_id = subscr[0][0]
    con.execute(subscriptions.update().where(subscriptions.c.id == subscr_id).values(
        type=tp))

def change_subscription_ends(con, no, end_timestamp):
    r = list(con.execute(
        select([func.max(subscriptions.c.end_timestamp)]).where(
        subscriptions.c.member_id == no)))
    if len(r) == 0:
        return
    max_timestamp = r[0][0]

    subscr = list(con.execute(select([subscriptions.c.id]).where(
            and_(subscriptions.c.member_id == no, subscriptions.c.end_timestamp == max_timestamp))))
    assert len(subscr) == 1
    subscr_id = subscr[0][0]
    if end_timestamp > time.time():
        con.execute(subscriptions.update().where(subscriptions.c.id == subscr_id).values(
            end_timestamp = end_timestamp))

def is_valid_token(con, token_id, t, gym_id):
    r = list(con.execute(select([tokens.c.member_id]).where(and_(tokens.c.id == token_id, tokens.c.valid == True))))
    if len(r) == 0:
        return False
    entries = entries_after(con, time.time() - 3600 * 24, gym_id)['entries']
    for entry in entries:
        if entry['member_id'] == r[0][0]:
            break
    else:
        return False
    if entry['member_type'] == 'perpetual':
        return True
    if entry['subscription_end_timestamp'] > time.time():
        return True
    return False


def get_stats(con):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    t0 = time.mktime(today.timetuple()) - 3600 * 24 * 7
    # 7 days back
    query = select([entries.c.timestamp, entries.c.token_id, entries.c.gym_id]).where(
        entries.c.timestamp > t0)
    d = {}
    for tstamp, token_id, gym_id in con.execute(query):
        date = datetime.datetime.fromtimestamp(tstamp).date()
        key = (date.year, date.month, date.day, token_id, gym_id)
        if key not in d:
            d[key] = (tstamp, token_id, gym_id)
    days = [{0: {"dailies": 0, "members": 0, "free": 0}, 1: {"dailies": 0, "members": 0, "free": 0}} for i in range(8)]
    for key, v in d.iteritems():
        year, month, day, token_id, gym_id = key
        day = (today - datetime.datetime(year, month, day)).days
        days[day][gym_id]['members'] += 1
    dailies = select([daily_passes.c.timestamp, daily_passes.c.gym_id, daily_passes.c.member_id]).where(
        daily_passes.c.timestamp > t0)
    daily_dict = {}
    for tstamp, gym_id, member_id in con.execute(dailies):
        if gym_id is None:
            gym_id = 0
        days[(today - datetime.datetime.fromtimestamp(tstamp).replace(hour=0, minute=0, second=0)).days][gym_id]['dailies'] += 1
        day = (datetime.datetime.fromtimestamp(tstamp).date() - datetime.date(2016, 1, 1)).days
        daily_dict[(member_id, day)] = True

    free_p = select([free_passes.c.timestamp, free_passes.c.gym_id, free_passes.c.member_id]).where(
        free_passes.c.timestamp > t0)
    for tstamp, gym_id, member_id in con.execute(free_p):
        if gym_id is None:
            gym_id = 0
        if (member_id, day) in daily_dict:
            continue
        days[(today - datetime.datetime.fromtimestamp(tstamp).replace(hour=0, minute=0, second=0)).days][gym_id]['free'] += 1

    total_ondemand = list(con.execute(select([func.count()]).select_from(select([members, subscriptions]).where(
        and_(and_(members.c.member_type == 'ondemand', members.c.id == subscriptions.c.member_id),
            subscriptions.c.end_timestamp > time.time())))))[0][0]
    total_recurring = list(con.execute(select([func.count()]).select_from(select([members]).where(
        members.c.member_type == 'recurring'))))[0][0]
    total_perpetual = list(con.execute(select([func.count()]).select_from(select([members]).where(
        members.c.member_type == 'perpetual'))))[0][0]
    total_visitors = list(con.execute(select([func.count()]).select_from(members)))[0][0]
    res_days = {}
    for i, v in enumerate(days):
        key = time.mktime((today - datetime.timedelta(days=i)).timetuple())
        res_days[key] = v
    return {
        'total_ondemand': total_ondemand,
        'total_recurring': total_recurring,
        'total_perpetual': total_perpetual,
        'total_visitors': total_visitors,
        'visits': res_days,
    }

def members_to_update(con):
    lst = list(con.execute(select([members.c.id, members.c.name, members.c.credit_card_id,
        subscriptions.c.start_timestamp,
        subscriptions.c.end_timestamp, subscriptions.c.type]).where(and_(
        and_(members.c.member_type == 'recurring',
        members.c.credit_card_id != None), members.c.id == subscriptions.c.member_id))))
    subs = {}
    for item in lst:
        subs[item[0]] = subs.get(item[0], [])
        subs[item[0]].append(item[1:])
    for k, v in subs.items():
        v.sort()
    d = datetime.datetime.fromtimestamp(time.time()).replace(hour=23, minute=30)
    newsubs = {}
    for k, v in subs.items():
        if v[-1][-2] > time.mktime(d.timetuple()):
            continue
        # double check
        l = list(con.execute(select([subscriptions.c.id]).where(and_(subscriptions.c.member_id == k,
                                                                     subscriptions.c.end_timestamp > time.mktime(d.timetuple()) + 30))))
        if l:
            newsubs[k] = ("Explosion", v[-1])
        else:
            newsubs[k] = v[-1]
    return newsubs

def _clean_visits_per_member(con, t0=0):
    a = list(con.execute(select([entries.c.token_id, entries.c.timestamp]).where(entries.c.timestamp > t0)))
    d = set()
    for item in a:
        dt = datetime.datetime.fromtimestamp(item[1])
        key = (dt.year, dt.month, dt.day, item[0])
        d.add(key)
    return d

def visits_daily(con, t0=0):
    members = {}
    for item in _clean_visits_per_member(con, t0):
        key = (item[0], item[1], item[2])
        members[key] = members.get(key, 0) + 1
    daily = {}
    for item in list(con.execute(select([daily_passes]).where(daily_passes.c.timestamp > t0))):
        dt = datetime.datetime.fromtimestamp(item[2])
        key = (dt.year, dt.month, dt.day)
        daily[key] = daily.get(key, 0) + 1
    return {
    'daily': daily,
    'members': members,
    }

def visits_per_client_agg(con, t0=0):
    d = {}
    member_d = {}
    for item in list(con.execute(select([members.c.id, members.c.timestamp]))):
        member_d[item[0]] = item[1]
    member_set = set([x[0] for x in con.execute(select([subscriptions.c.member_id]))])
        
    for item in list(con.execute(select([daily_passes]).where(daily_passes.c.timestamp > t0))):
        key = item[1]
        d[key] = d.get(key, 0) + 1
    r = [0] * 30
    for k, v in d.iteritems():
        total_time = (float(time.time()) - member_d[k]) / 3600 / 24 / 30 # in months
        if total_time > 0.1:
        #    print v, total_time, int(v / total_time)
        #if k in member_set:
        #    r[0] += 1
        #else:
        #    r[v] += 1
            r[int(v / total_time)] += 1
    print sum(r[4:])
    return r

def remove_credit_card_token(con, member_id):
    con.execute(members.update().where(members.c.id == member_id).values(credit_card_id=None))

def save_notes(con, member_id, notes):
    con.execute(members.update().where(members.c.id == member_id).values(extra_notes=notes))

def pause_membership(con, member_id):
    """ Membership is paused from today for a month
    """
    r = list(con.execute(
        select([subscriptions.c.id, subscriptions.c.end_timestamp,
            subscriptions.c.type]).where(
        and_(subscriptions.c.member_id == member_id, subscriptions.c.end_timestamp > time.time())).order_by(
        subscriptions.c.end_timestamp)))
    if len(r) == 0:
        return {'error': "Member not subscribed yet or membership expired"}
    if len(r) >= 2:
        return {'error': "Membership already paused"}
    max_timestamp = r[0][1]
    today = datetime.datetime.today()
    exp_today = time.mktime(datetime.datetime(today.year, today.month, today.day, 23, 00).timetuple())
    time_left = max_timestamp - exp_today
    end_date = time.mktime(add_months(datetime.datetime.now(), 1).timetuple())
    con.execute(subscriptions.update().where(subscriptions.c.id == r[0][0]).values(
        end_timestamp=int(time.time())))
    con.execute(subscriptions.insert().values(member_id=member_id, type='pause',
        start_timestamp=exp_today, end_timestamp=end_date))
    con.execute(subscriptions.insert().values(member_id=member_id, type=r[0][2],
        start_timestamp=end_date, end_timestamp=end_date + time_left))

    return {'success': True}

def pause_change(con, member_id, from_timestamp, to_timestamp):
    r = list(con.execute(
        select([subscriptions.c.id, subscriptions.c.end_timestamp, subscriptions.c.start_timestamp,
            subscriptions.c.type]).where(
        and_(subscriptions.c.member_id == member_id, subscriptions.c.end_timestamp > time.time())).order_by(
        subscriptions.c.end_timestamp)))
    if len(r) == 0:
        return {'error': "Member not subscribed yet or membership expired"}
    if len(r) == 1:
        return {'error': "Membership not paused"}
    if to_timestamp < from_timestamp:
        return {'error': 'End higher than start'}
    if from_timestamp < time.time() and from_timestamp != r[0][2]:
        return {'error': 'cannot change past dates'}
    delta = r[0][2] - from_timestamp + to_timestamp - r[0][1]
    new_end = r[1][1] + delta
    con.execute(subscriptions.update().where(subscriptions.c.id==r[1][0]).values(end_timestamp=new_end,
        start_timestamp=to_timestamp))
    con.execute(subscriptions.update().where(subscriptions.c.id==r[0][0]).values(start_timestamp=from_timestamp,
        end_timestamp=to_timestamp))    
    return {'success': 'ok'}

def unpause_membership(con, member_id):
    r = list(con.execute(
        select([subscriptions.c.id, subscriptions.c.end_timestamp,
            subscriptions.c.type]).where(
        and_(subscriptions.c.member_id == member_id, subscriptions.c.end_timestamp > time.time())).order_by(
        subscriptions.c.end_timestamp)))
    if len(r) == 0:
        return {'error': "Member not subscribed yet or membership expired"}
    if len(r) == 1:
        return {'error': "Membership not paused"}
    today = datetime.datetime.today()
    pause_left = r[0][1] - time.mktime(datetime.datetime(today.year, today.month, today.day, 23, 00).timetuple())
    end = r[1][1]
    new_end = end - pause_left
    con.execute(subscriptions.delete().where(subscriptions.c.id==r[0][0]))
    con.execute(subscriptions.update().where(subscriptions.c.id==r[1][0]).values(end_timestamp=new_end))
    return {'success': True}

def check_one_month(con, member_id):
    l = list(con.execute(select([subscriptions.c.end_timestamp]).where(
        subscriptions.c.member_id == member_id).order_by(subscriptions.c.end_timestamp)))
    if not l:
        return False
    return time.time() - l[-1][0] < 3600 * 24 * 28

def update_account_number(con, member_id, name, price, contact_number, address, branch_code, account_number):
    con.execute(members.update().where(members.c.id==member_id).values(account_holder_name=name, phone=contact_number,
        address=address, branch_code=branch_code, account_number=account_number))
    # record that the transaction initation took place
    con.execute(transactions.insert().values({
        'member_id': member_id,
        'timestamp': int(time.time()),
        'price': price,
        'type': "capture",
        'description': "Captured bank data",
        'outcome': 'success'
    }))

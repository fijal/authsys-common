
""" some common queries that can be done on the data
"""
import time
from sqlalchemy import select, desc, outerjoin, and_

from .model import members, entries, tokens, subscriptions

def get_member_list(con):
    """ List all the members with whether they paid or not
    """
    s = select([members, tokens]).where(
        and_(members.c.id == tokens.c.member_id, tokens.c.valid))
    return [(x[1],) for x in con.execute(s)]

def list_indemnity_forms(con):
    """ List all the indemnity forms that have no assigned tokens
    """
    oj = outerjoin(members, tokens, members.c.id == tokens.c.member_id)
    return [(a, b, c, d) for a, b, c, d in con.execute(select(
        [members.c.id, members.c.name, members.c.id_number,
        members.c.timestamp]).select_from(oj).where(
        tokens.c.id == None).order_by(desc("timestamp")))]

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

def entries_after(con, timestamp):
    """ List all the entries after 'timestamp' with extra information
    about the subscription and validity
    """
    oj = outerjoin(outerjoin(outerjoin(entries, tokens, and_(
        entries.c.token_id == tokens.c.id, tokens.c.valid)),
        members, members.c.id == tokens.c.member_id),
        subscriptions, and_(subscriptions.c.member_id == members.c.id,
            subscriptions.c.end_timestamp >= entries.c.timestamp))
#        members.c.id == subscriptions.c.member_id
    return [(a, b, c, d) for a, b, c, d in
        con.execute(select([entries.c.token_id, members.c.name,
        entries.c.timestamp, subscriptions.c.end_timestamp]).select_from(oj).where(
        entries.c.timestamp >= timestamp).order_by(desc(entries.c.timestamp)))]


""" some common queries that can be done on the data
"""
import time
from sqlalchemy import select, desc, outerjoin, and_

from .model import members, entries, tokens

def get_member_list(con):
    """ List all the members with whether they paid or not
    """
    oj = outerjoin(members, tokens, members.c.id == tokens.c.member_id)
    s = select([members.c.name]).select_from(oj).where(tokens.c.id != None)
    return [x[0] for x in con.execute(s)]

def list_indemnity_forms(con):
    """ List all the indemnity forms that have no assigned tokens
    """
    oj = outerjoin(members, tokens, members.c.id == tokens.c.member_id)
    return list(con.execute(select(
        [members.c.id, members.c.name, members.c.id_number,
        members.c.timestamp]).select_from(oj).where(
        tokens.c.id == None).order_by(desc("timestamp"))))

def get_form(con, no):
    return list(list(con.execute(select([members.c.id,
        members.c.name,
        members.c.id_number]).where(members.c.id == no)))[0])

def unrecognized_entries_after(con, timestamp):
    oj = outerjoin(entries, tokens, entries.c.token_id == tokens.c.id)
    s = select([entries.c.token_id]).select_from(oj).where(
        and_(entries.c.timestamp >= timestamp, tokens.c.id == None)).order_by(
        desc(entries.c.timestamp))
    return [x[0] for x in con.execute(s)]

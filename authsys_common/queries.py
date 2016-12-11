
""" some common queries that can be done on the data
"""
import attr
from sqlalchemy import select

from .model import members

@attr.s
class Member(object):
    name = attr.ib()
    subscription_start = attr.ib()
    subscription_end = attr.ib()

def get_member_list(con):
    """ List all the members with whether they paid or not
    """
    return [Member(name, 0, 0) for (name,) in
            con.execute(select([members.c.name]))]

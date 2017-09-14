
""" Upgrade DB with taking the most recent subscription and adding
it to subscription_type on members
"""

from authsys_common.queries import visits_daily, visits_per_client_agg
from authsys_common.model import members, subscriptions
from authsys_common.scripts import get_db_url

from sqlalchemy import create_engine, select
from datetime import datetime

eng = create_engine(get_db_url())
con = eng.connect()

l = [(a, b, c, d) for a, b, c, d in con.execute(select([members.c.id, members.c.name, subscriptions.c.type, subscriptions.c.end_timestamp]).where(members.c.id == subscriptions.c.member_id).order_by(subscriptions.c.end_timestamp))]
print l
d = {}
for memb_id, name, subscr_type, tstamp in l:
    if memb_id not in d or d[memb_id][2] < tstamp:
        d[memb_id] = (subscr_type, name, tstamp)
for k, v in d.iteritems():
    assert list(con.execute(select([members.c.name]).where(members.c.id == k)))[0][0] == v[1]
    con.execute(members.update().where(members.c.id == k).values(subscription_type=v[0]))

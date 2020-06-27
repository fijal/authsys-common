
from authsys_common.queries import visits_daily, visits_per_client_agg
from authsys_common.model import members, subscriptions, daily_passes, entries
from authsys_common.scripts import get_db_url

from sqlalchemy import create_engine, select, and_
from datetime import datetime
import time
from pprint import pprint

eng = create_engine(get_db_url())
con = eng.connect()

current = dict.fromkeys([x.strip("\n").strip(" ") for x in open("x").readlines()])

lst = list(con.execute(
    select([members.c.name, members.c.email, subscriptions.c.member_id]).where(and_(
        subscriptions.c.type != 'pause', and_(
    subscriptions.c.member_id == members.c.id,
    and_(subscriptions.c.end_timestamp > time.time(),
        subscriptions.c.start_timestamp < time.time()))))))

for item in lst:
    try:
        del current[item[0]]
    except KeyError:
        pass

pprint(lst)

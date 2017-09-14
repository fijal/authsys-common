
from authsys_common.queries import visits_daily, visits_per_client_agg
from authsys_common.scripts import get_db_url

from sqlalchemy import create_engine
from datetime import datetime

eng = create_engine(get_db_url())
con = eng.connect()

r = visits_daily(con)
d = r['daily']
d2 = r['members']
open("data", "w").write(repr(sorted(d.items())))
open("data2", "w").write(repr(sorted(d2.items())))
print visits_per_client_agg(con)

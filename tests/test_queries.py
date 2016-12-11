
from sqlalchemy import create_engine

from authsys_common import queries as q
from authsys_common.scripts import create_db, populate_with_test_data
from authsys_common.model import meta

class TestQueries(object):
    def setup_class(cls):
        eng = create_db('sqlite:///:memory:')
        meta.reflect(bind=eng)
        cls.c = eng.connect()
        populate_with_test_data(cls.c)

    def test_one(self):
        assert q.get_member_list(self.c) == [q.Member("John One", 0, 0),
                                             q.Member("Brad Two", 0, 0),
                                             q.Member("Jim Three", 0, 0)]


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

    def test_list_members(self):
        assert q.get_member_list(self.c) == ["John One"]

    def test_list_forms(self):
        assert q.list_indemnity_forms(self.c) == [
            (1, u'One Two', '1234', 1234),
            (3, u'Brad Two', u'11111', 1236),
            (4, u'Jim Three', u'xyz', 1237)]

    def test_entries_after(self):
        t0 = 10000
        tok1 = "A" * 6 + "08"
        tok3 = "C" * 6 + "08"
        tok4 = "D" * 6 + "08"
        assert q.unrecognized_entries_after(self.c, t0) == [
            tok4, tok3, tok1, tok1]
        assert q.unrecognized_entries_after(self.c, t0 + 20) == [
            tok4, tok3]

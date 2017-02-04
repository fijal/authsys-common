
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
        assert q.get_member_list(self.c) == [(2, "John One",)]

    def test_list_forms(self):
        r = [(4, u'Jim Three', u'xyz', 1237), (3, u'Brad Two', u'11111', 1236),
             (2, u'John One', u'12345', 1235), (2, u'John One', u'12345', 1235),
             (1, u'One Two', u'1234', 1234)]
        assert q.list_indemnity_forms(self.c) == r

    def test_unrecognized_entries_after(self):
        t0 = 10000
        tok1 = "A" * 6 + "08"
        tok4 = "D" * 6 + "08"
        assert q.unrecognized_entries_after(self.c, t0) == [
            tok4, tok1, tok1]
        assert q.unrecognized_entries_after(self.c, t0 + 20) == [
            tok4]

    def test_entries_after(self):
        t0 = 10000
        tok1 = "A" * 6 + "08"
        tok2 = "B" * 6 + "08"
        tok3 = "C" * 6 + "08"
        tok4 = "D" * 6 + "08"
        all_entries = [(tok1, None, t0, None, None),
            (tok1, None, t0 + 5, None, None),
            (tok2, "John One", t0 + 10, 10020, "regular"),
            (tok3, None, t0 + 20, None, None),
            (tok4, None, t0 + 30, None, None),
            (tok2, "John One", t0 + 40, None, None)
        ]
        all_entries.reverse()

        assert q.entries_after(self.c, t0) == all_entries
        assert q.entries_after(self.c, t0 + 10) == all_entries[:-2]

    def test_get_member_data(self):
        assert q.get_member_data(self.c, 2) == (2, "John One", 1235, "regular", 10020)
        assert q.get_member_data(self.c, 1) == (1, "One Two", 1234, None, None)

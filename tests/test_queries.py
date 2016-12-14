
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
        assert q.get_member_list(self.c) == [("John One",)]

    def test_list_forms(self):
        assert q.list_indemnity_forms(self.c) == [
            (1, u'One Two', '1234', 1234),
            (3, u'Brad Two', u'11111', 1236),
            (4, u'Jim Three', u'xyz', 1237)]

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
        all_entries = [(tok1, None, t0, None),
            (tok1, None, t0 + 5, None),
            (tok2, "John One", t0 + 10, 10020),
            (tok3, None, t0 + 20, None),
            (tok4, None, t0 + 30, None),
            (tok2, "John One", t0 + 40, None)
        ]
        all_entries.reverse()

        assert q.entries_after(self.c, t0) == all_entries
        assert q.entries_after(self.c, t0 + 10) == all_entries[:-2]
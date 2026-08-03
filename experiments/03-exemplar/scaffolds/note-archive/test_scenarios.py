"""note.archive scenarios. Behaviour only, identical in every arm."""
import unittest

from kernel import AppError
from _seed import SESSION, entry, store


class NoteArchive(unittest.TestCase):
    def call(self, *args):
        return entry()(*args)

    def test_archives_a_live_note(self):
        out = self.call(store(), SESSION, "n1")
        self.assertEqual(out["id"], "n1")
        self.assertTrue(out["archived"])

    def test_the_change_is_written_through_the_store(self):
        st = store()
        self.call(st, SESSION, "n1")
        self.assertTrue(st.note("n1")["archived"])

    def test_archiving_twice_is_an_error(self):
        with self.assertRaises(AppError) as caught:
            self.call(store(), SESSION, "n3")
        self.assertEqual(caught.exception.code, "ALREADY_ARCHIVED")

    def test_a_refused_archive_leaves_the_store_alone(self):
        st = store()
        try:
            self.call(st, SESSION, "n3")
        except AppError:
            pass
        self.assertTrue(st.note("n3")["archived"])
        self.assertFalse(st.note("n1")["archived"])

    def test_an_unknown_id_is_not_found(self):
        with self.assertRaises(AppError) as caught:
            self.call(store(), SESSION, "nope")
        self.assertEqual(caught.exception.code, "NOT_FOUND")

    def test_an_empty_id_is_refused(self):
        with self.assertRaises(AppError) as caught:
            self.call(store(), SESSION, "")
        self.assertEqual(caught.exception.code, "INVALID_PARAMETER")

    def test_no_session_fails_before_the_id_is_looked_at(self):
        with self.assertRaises(AppError) as caught:
            self.call(store(), None, "")
        self.assertEqual(caught.exception.code, "UNAUTHORIZED")

    def test_the_output_carries_only_the_contract_fields(self):
        out = self.call(store(), SESSION, "n1")
        self.assertEqual(set(out), {"id", "title", "archived"})


if __name__ == "__main__":
    unittest.main()

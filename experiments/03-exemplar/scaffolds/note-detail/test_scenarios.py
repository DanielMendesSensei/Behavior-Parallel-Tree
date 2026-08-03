"""note.detail scenarios. Behaviour only, identical in every arm."""
import unittest

from kernel import AppError
from _seed import SESSION, entry, store


class NoteDetail(unittest.TestCase):
    def call(self, *args):
        return entry()(*args)

    def test_reads_a_note(self):
        out = self.call(store(), SESSION, "n1")
        self.assertEqual(out["id"], "n1")
        self.assertEqual(out["title"], "Ravenna")
        self.assertEqual(out["body"], "mosaics")
        self.assertFalse(out["archived"])

    def test_tags_come_ordered_by_name(self):
        out = self.call(store(), SESSION, "n1")
        self.assertEqual(out["tags"], ["atlas", "botany"])

    def test_a_note_with_no_tags_gets_an_empty_list(self):
        self.assertEqual(self.call(store(), SESSION, "n4")["tags"], [])

    def test_an_archived_note_is_still_readable(self):
        out = self.call(store(), SESSION, "n3")
        self.assertTrue(out["archived"])
        self.assertEqual(out["title"], "Cobalt")

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
        self.assertEqual(set(out), {"id", "title", "body", "archived", "tags"})


if __name__ == "__main__":
    unittest.main()

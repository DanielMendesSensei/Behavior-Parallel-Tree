"""tag.list scenarios. Behaviour only, identical in every arm."""
import unittest

from kernel import AppError
from _seed import SESSION, entry, store


class TagList(unittest.TestCase):
    def call(self, *args):
        return entry()(*args)

    def test_every_tag_by_default_ordered_by_name(self):
        out = self.call(store(), SESSION)
        self.assertEqual([t["name"] for t in out["items"]],
                         ["atlas", "botany", "colour", "unused"])
        self.assertEqual(out["total"], 4)

    def test_the_count_ignores_archived_notes(self):
        out = self.call(store(), SESSION)
        counts = {t["name"]: t["count"] for t in out["items"]}
        self.assertEqual(counts["botany"], 2)   # n2 live, n3 archived
        self.assertEqual(counts["atlas"], 2)    # n1 and n5
        self.assertEqual(counts["colour"], 0)   # only n3, archived

    def test_a_tag_nobody_uses_still_comes_back(self):
        counts = {t["name"]: t["count"] for t in self.call(store(), SESSION)["items"]}
        self.assertEqual(counts["unused"], 0)

    def test_min_count_filters_and_total_follows(self):
        out = self.call(store(), SESSION, 2)
        self.assertEqual([t["name"] for t in out["items"]], ["atlas", "botany"])
        self.assertEqual(out["total"], 2)

    def test_a_negative_min_count_is_refused(self):
        with self.assertRaises(AppError) as caught:
            self.call(store(), SESSION, -1)
        self.assertEqual(caught.exception.code, "INVALID_PARAMETER")

    def test_no_session_fails_before_min_count_is_looked_at(self):
        with self.assertRaises(AppError) as caught:
            self.call(store(), None, -1)
        self.assertEqual(caught.exception.code, "UNAUTHORIZED")

    def test_the_output_carries_only_the_contract_fields(self):
        out = self.call(store(), SESSION)
        self.assertEqual(set(out), {"items", "total"})
        self.assertEqual(set(out["items"][0]), {"id", "name", "count"})


if __name__ == "__main__":
    unittest.main()

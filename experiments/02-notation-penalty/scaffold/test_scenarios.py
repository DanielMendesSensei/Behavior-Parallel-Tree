"""The scenarios, byte identical in every arm.

Every assertion here is derivable from information that all three contracts
carry, so no arm can pass or fail because it was told something the others were
not. Nothing here inspects the notation: these tests only look at behaviour.

The one thing they deliberately do not assert is how `price` is represented.
Decimal, string and float all round trip through `Decimal(str(value))` for these
amounts, so representation is measured separately, by reading the code, and not
by a test that would only pretend to discriminate.

stdlib unittest, because the whole repository runs on the standard library plus
PyYAML and an experiment should not be the thing that adds a dependency.
"""
import unittest
from decimal import Decimal

from _support import SESSION, ProductError, make_catalog
from products import list_products

ORDERED_NAMES = [
    "Alpha Mug", "Bronze Kettle", "Cedar Board", "Denim Apron", "Ember Pan",
    "Fern Vase", "Glass Jug", "Hazel Bowl", "Iron Skillet", "Jade Cup",
    "Kraft Box", "Linen Cloth", "Maple Spoon", "Nickel Whisk", "Oak Tray",
    "Pearl Dish", "Quartz Mug", "Rattan Basket", "Slate Coaster", "Teak Ladle",
    "Umber Pot", "Zebra Lamp",
]


class ProductListScenarios(unittest.TestCase):
    def test_defaults_give_first_page_of_twenty(self):
        out = list_products(make_catalog(), SESSION)
        self.assertEqual(out["page"], 1)
        self.assertEqual(len(out["items"]), 20)

    def test_total_counts_every_match_not_just_the_page(self):
        out = list_products(make_catalog(), SESSION)
        self.assertEqual(out["total"], 22)

    def test_empty_catalog_returns_nothing(self):
        out = list_products([], SESSION)
        self.assertEqual(out["items"], [])
        self.assertEqual(out["total"], 0)

    def test_unavailable_products_are_excluded(self):
        out = list_products(make_catalog(), SESSION, size=100)
        names = [item["name"] for item in out["items"]]
        self.assertNotIn("Walnut Rack", names)
        self.assertNotIn("Xenon Lamp", names)
        self.assertNotIn("Yarn Holder", names)

    def test_items_are_ordered_by_name_ascending(self):
        out = list_products(make_catalog(), SESSION, size=100)
        self.assertEqual([item["name"] for item in out["items"]], ORDERED_NAMES)

    def test_second_page_holds_the_remainder(self):
        out = list_products(make_catalog(), SESSION, page=2)
        self.assertEqual(out["page"], 2)
        self.assertEqual(
            [item["name"] for item in out["items"]], ["Umber Pot", "Zebra Lamp"]
        )

    def test_search_by_name_ignores_case(self):
        out = list_products(make_catalog(), SESSION, search="zebra")
        self.assertEqual([item["name"] for item in out["items"]], ["Zebra Lamp"])
        self.assertEqual(out["total"], 1)

    def test_size_above_the_maximum_is_rejected(self):
        with self.assertRaises(ProductError) as caught:
            list_products(make_catalog(), SESSION, size=500)
        self.assertEqual(caught.exception.code, "INVALID_PARAMETER")

    def test_page_below_the_minimum_is_rejected(self):
        with self.assertRaises(ProductError) as caught:
            list_products(make_catalog(), SESSION, page=0)
        self.assertEqual(caught.exception.code, "INVALID_PARAMETER")

    def test_a_missing_session_is_unauthorized(self):
        with self.assertRaises(ProductError) as caught:
            list_products(make_catalog(), None)
        self.assertEqual(caught.exception.code, "UNAUTHORIZED")

    def test_price_survives_the_round_trip(self):
        out = list_products(make_catalog(), SESSION, search="pearl")
        self.assertEqual(
            Decimal(str(out["items"][0]["price"])), Decimal("1099.95")
        )

    def test_the_output_carries_only_the_contract_fields(self):
        out = list_products(make_catalog(), SESSION, size=1)
        self.assertEqual(set(out), {"items", "total", "page"})
        self.assertEqual(
            set(out["items"][0]), {"id", "name", "price", "available"}
        )


if __name__ == "__main__":
    unittest.main()

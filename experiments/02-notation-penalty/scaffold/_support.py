"""Given to every run, byte identical in every arm.

It holds the error type the implementation must raise and the catalogue the
tests read from, so that no run has to invent an error mechanism or a data
shape. What is left for the model to decide is exactly what the contract
specifies, which is what the experiment is measuring.
"""


class ProductError(Exception):
    """Raised for any error code the contract declares."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


# A catalogue row as it arrives from storage. `price` is a decimal string
# because that is how an exact amount survives a database and a JSON payload.
# What the implementation returns for `price` is its own decision.
_ROWS = [
    ("p01", "Alpha Mug", "12.50", True),
    ("p02", "Bronze Kettle", "89.00", True),
    ("p03", "Cedar Board", "34.90", True),
    ("p04", "Denim Apron", "58.25", True),
    ("p05", "Ember Pan", "129.99", True),
    ("p06", "Fern Vase", "41.05", True),
    ("p07", "Glass Jug", "22.40", True),
    ("p08", "Hazel Bowl", "17.75", True),
    ("p09", "Iron Skillet", "146.30", True),
    ("p10", "Jade Cup", "9.95", True),
    ("p11", "Kraft Box", "4.20", True),
    ("p12", "Linen Cloth", "27.60", True),
    ("p13", "Maple Spoon", "6.35", True),
    ("p14", "Nickel Whisk", "15.80", True),
    ("p15", "Oak Tray", "63.15", True),
    ("p16", "Pearl Dish", "1099.95", True),
    ("p17", "Quartz Mug", "19.99", True),
    ("p18", "Rattan Basket", "72.00", True),
    ("p19", "Slate Coaster", "0.05", True),
    ("p20", "Teak Ladle", "11.10", True),
    ("p21", "Umber Pot", "48.45", True),
    ("p22", "Zebra Lamp", "210.70", True),
    ("p23", "Walnut Rack", "95.00", False),
    ("p24", "Xenon Lamp", "310.00", False),
    ("p25", "Yarn Holder", "13.65", False),
]


def make_catalog():
    """Twenty five rows, twenty two of them available."""
    return [
        {"id": pid, "name": name, "price": price, "available": available}
        for pid, name, price, available in _ROWS
    ]


SESSION = {"user_id": "u1", "roles": ["customer"]}

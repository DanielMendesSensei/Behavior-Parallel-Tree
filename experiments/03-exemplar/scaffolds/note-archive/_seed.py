"""Seed data and the entry point resolver, identical for every arm.

The entry point is resolved rather than named, because what the behaviour calls
its function is one of the things being measured. The prompt asks for exactly one
public function, so finding more than one is a failure of the answer and not of
the harness.
"""
import behavior
from kernel import Store

NOTES = [
    {"id": "n1", "title": "Ravenna", "body": "mosaics", "archived": False, "tag_ids": ["t2", "t1"]},
    {"id": "n2", "title": "Almond", "body": "blossom", "archived": False, "tag_ids": ["t1"]},
    {"id": "n3", "title": "Cobalt", "body": "pigment", "archived": True, "tag_ids": ["t1", "t3"]},
    {"id": "n4", "title": "Basalt", "body": "column", "archived": False, "tag_ids": []},
    {"id": "n5", "title": "Delta", "body": "silt", "archived": False, "tag_ids": ["t2"]},
]

TAGS = [
    {"id": "t1", "name": "botany"},
    {"id": "t2", "name": "atlas"},
    {"id": "t3", "name": "colour"},
    {"id": "t4", "name": "unused"},
]

SESSION = {"user_id": "u1", "roles": ["member"]}


def store():
    return Store(notes=NOTES, tags=TAGS)


def entry():
    """The single public callable the behaviour module exposes."""
    found = [
        value for name, value in vars(behavior).items()
        if callable(value)
        and not name.startswith("_")
        and getattr(value, "__module__", None) == "behavior"
    ]
    if len(found) != 1:
        raise AssertionError(
            "the module must expose exactly one public function, found %d: %s"
            % (len(found), sorted(f.__name__ for f in found))
        )
    return found[0]

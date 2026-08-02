"""Implement product.list here, from the contract and the specification.

This file is the only one a run replaces. Everything else in the directory is
given and must not be changed.
"""
from _support import ProductError  # noqa: F401  (raise this for contract errors)


def list_products(catalog, session, search=None, page=None, size=None):
    """Return the contract's output for the given catalogue.

    `catalog` is the list of rows from `_support.make_catalog()`.
    `session` is `_support.SESSION`, or None when there is no session.
    `search`, `page` and `size` are the contract's input fields. A value of
    None means the caller did not supply it.
    """
    raise NotImplementedError

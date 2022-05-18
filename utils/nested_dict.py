"""
Functions to handle nested dictionaries, using a list of keys used as a path to obtain a value.
"""


def deep_write(d: dict, value: object, path: list[str]) -> None:
    """Searches for a key in a nested dictionary and writes the value for that key."""
    print(f"dict is {d}")

    if not path:
        if isinstance(value, dict):
            d.clear()
            return
        else:
            raise ValueError(f"Value to write at the root was not a dictionary.")

    print(f"path: {path}")
    first_key = path[0]

    if len(path) == 1:
        d[first_key] = value
        return
    else:
        next_node = d.get(first_key, None)
        if next_node is not None:
            if isinstance(next_node, dict):
                return deep_write(next_node, value, path[1:])
            else:
                raise ValueError(f"Value for {first_key} is not a dictionary.")
        else:
            d[first_key] = {}
            return deep_write(d, value, path[1:])


def deep_read(d: dict, path: list[str]) -> object:
    """Searches for a key in a nested dictionary and returns the value for that key."""

    if not path:
        return d

    first_key = path[0]
    if len(path) == 1:
        return d.get(first_key, None)
    else:
        next_node = d.get(first_key, None)
        if next_node is not None:
            if isinstance(next_node, dict):
                return deep_read(next_node, path[1:])
            else:
                raise ValueError(f"Value for {first_key} is not a dictionary.")
        else:
            raise ValueError(f"Cannot continue reading (value for {first_key} is None).")


def deep_delete(d: dict, path: list[str]) -> None:
    """Searches for a key in a nested dictionary and deletes the value for that key."""
    first_key = path[0]

    if not path:
        d = {}
    if len(path) == 1:
        try:
            del d[first_key]
        except KeyError:
            pass
    else:
        next_node = d.get(first_key, None)
        if next_node is not None:
            if isinstance(next_node, dict):
                deep_delete(next_node, path[1:])
            else:
                raise ValueError(f"Value for {first_key} is not a dictionary.")
        else:
            raise ValueError(f"Cannot continue reading (value for {first_key} is None).")

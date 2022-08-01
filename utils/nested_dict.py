"""
Functions to handle nested dictionaries, using a list of keys used as a path to obtain a value.
"""


def deep_write(dic: dict, value: object, path: list[str]) -> None:
    """Searches for a key in a nested dictionary and writes the value for that key."""

    if not path:
        if isinstance(value, dict):
            dic.clear()
            return
        raise ValueError("Value to write at the root was not a dictionary.")

    first_key = path[0]

    if len(path) == 1:
        dic[first_key] = value
        return
    next_node = dic.get(first_key, None)
    if next_node is not None:
        if isinstance(next_node, dict):
            return deep_write(next_node, value, path[1:])
        raise ValueError(f"Value for {first_key} is not a dictionary.")
    else:
        dic[first_key] = {}
        return deep_write(dic[first_key], value, path[1:])


def deep_read(dic: dict, path: list[str]) -> object:
    """Searches for a key in a nested dictionary and returns the value for that key."""

    if not path:
        return dic

    first_key = path[0]

    if len(path) == 1:
        return dic.get(first_key, None)
    next_node = dic.get(first_key, None)
    if next_node is not None:
        if isinstance(next_node, dict):
            return deep_read(next_node, path[1:])
        raise ValueError(f"Value for {first_key} is not a dictionary.")
    raise ValueError(
        f"Cannot continue reading (value for {first_key} is None).")


def deep_delete(dic: dict, path: list[str]) -> None:
    """Searches for a key in a nested dictionary and deletes the value for that key."""
    first_key = path[0]

    if not path:
        dic = {}
    if len(path) == 1:
        try:
            del dic[first_key]
        except KeyError:
            pass
    else:
        next_node = dic.get(first_key, None)
        if next_node is not None:
            if isinstance(next_node, dict):
                deep_delete(next_node, path[1:])
            else:
                raise ValueError(f"Value for {first_key} is not a dictionary.")
        else:
            raise ValueError(f"Cannot continue reading (value for {first_key} is None).")

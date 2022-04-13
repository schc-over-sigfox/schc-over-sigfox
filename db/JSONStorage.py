from utils.nested_dict import deep_write, deep_read, deep_delete


class JSONStorage:
    """
    Base class for storage operations using a JSON-like structure, composed of nodes (key-value pairs). The keys must
    be strings (interpreted as a file name), and the value can be any object, including another node.
    """

    def __init__(self, root: str) -> None:
        self.ROOT: str = root
        self.JSON: dict = {}

    def load(self) -> None:
        """Read the last saved remote version of the storage and save it in the internal self.JSON parameter."""
        raise NotImplementedError

    def save(self) -> None:
        """Saves the data in self.JSON into the remote database."""
        raise NotImplementedError

    def write(self, data: object, path: str = '') -> None:
        """Saves the 'data' object in the node identified by the path."""
        if path == '' and isinstance(data, dict):
            self.JSON = data
        else:
            deep_write(self.JSON, data, path.split('/'))

    def read(self, path: str = '') -> object:
        """Returns the object stored in the node identified by the path."""
        if path == '':
            if self.JSON == {}:
                return None
            else:
                return self.JSON
        else:
            return deep_read(self.JSON, path.split('/'))

    def exists(self, path: str) -> bool:
        """Checks if the node identified by the path, exists."""
        return self.read(path) is not None

    def delete(self, path: str) -> None:
        """Deletes the node identified by the path."""
        return deep_delete(self.JSON, path.split('/'))

    def make(self, path: str) -> None:
        """Creates an empty node at the specified path."""
        deep_write(self.JSON, {}, path.split('/'))

    def is_empty(self, path: str) -> bool:
        """Checks if a node exists and contains no object."""
        return self.exists(path) and not bool(self.read(path))

    def list_nodes(self, path: str = '') -> list[str]:
        """Lists all the nodes contained in the node specified by the path."""
        if path == '':
            return list(self.JSON.keys())
        else:
            node = self.read(path)
            if isinstance(node, dict):
                return list(node.keys())
            else:
                return []

    def reset(self) -> None:
        """Deletes all data in the self.JSON variable."""
        self.JSON = {}

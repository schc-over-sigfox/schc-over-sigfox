import json

from db.JSONStorage import JSONStorage


class LocalJSONStorage(JSONStorage):
    """Local JSON storage class, stores data in a file in the disk."""

    def __init__(self, root: str) -> None:
        super().__init__(root)

    def load(self) -> object:
        try:
            with open(f"{self.ROOT}/STORAGE.json") as f:
                j = json.loads(f.read())
        except FileNotFoundError:
            j = {}
            with open(f"{self.ROOT}/STORAGE.json") as f:
                f.write(json.dumps(j))
        return j

    def save(self) -> None:
        with open(f"{self.ROOT}/STORAGE.json") as f:
            f.write(json.dumps(self.JSON, indent=2))

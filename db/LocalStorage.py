import json
import os

from db.JSONStorage import JSONStorage


class LocalStorage(JSONStorage):
    """Local JSON storage class, stores data in a file in the disk."""

    def __init__(self, root: str) -> None:

        if not os.path.exists(root):
            os.makedirs(root, exist_ok=True)

        if not os.path.exists(f"{root}/STORAGE.json"):
            with open(f"{root}/STORAGE.json", 'w') as f:
                f.write(json.dumps({}))

        super().__init__(root)

    def load(self) -> object:
        try:
            with open(f"{self.ROOT}/STORAGE.json", 'r') as f:
                j = json.loads(f.read())
        except FileNotFoundError:
            j = {}
            with open(f"{self.ROOT}/STORAGE.json", 'w') as f:
                f.write(json.dumps(j))
        self.JSON = j

    def save(self) -> None:
        with open(f"{self.ROOT}/STORAGE.json", 'w') as f:
            f.write(json.dumps(self.JSON, indent=2))

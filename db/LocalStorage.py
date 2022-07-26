import json
import os

from db.JSONStorage import JSONStorage


class LocalStorage(JSONStorage):
    """Local JSON storage class, stores data in a file in the disk."""

    def __init__(self) -> None:

        super().__init__()
        self.PATH: str = "debug"

        if not os.path.exists(self.PATH):
            os.makedirs(self.PATH, exist_ok=True)

        if not os.path.exists(f"{self.PATH}/STORAGE.json"):
            with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as f:
                f.write(json.dumps(self.JSON))

    def load(self) -> None:
        try:
            with open(f"{self.PATH}/STORAGE.json", 'r', encoding="utf-8") as f:
                j = json.loads(f.read())
        except FileNotFoundError:
            j = {}
            with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as f:
                f.write(json.dumps(j))
        self.JSON = j

    def save(self) -> None:
        with open(f"{self.PATH}/STORAGE.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(self.JSON, indent=2))

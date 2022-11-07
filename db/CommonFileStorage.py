import os

from db.FileStorage import FileStorage


class CommonFileStorage(FileStorage):

    def __init__(self, root: str):
        super().__init__(root)

        if not self.folder_exists():
            self.create_folder()

    def read(self, path: str) -> str:
        with open("{}/{}".format(self.ROOT, path), 'r', encoding="utf-8") as f:
            data = f.read()
        return data

    def write(self, path: str, data: str) -> None:
        with open("{}/{}".format(self.ROOT, path), 'w', encoding="utf-8") as f:
            f.write(data)

    def delete_file(self, path: str) -> None:
        if self.file_exists(path):
            os.remove("{}/{}".format(self.ROOT, path))

    def delete_folder(self, path: str) -> None:
        if self.folder_exists(path):
            if not self.folder_empty(path):
                for e in self.list_files(path):
                    if self.is_file("{}/{}".format(path, e)):
                        self.delete_file("{}/{}".format(path, e))
                    elif self.is_folder("{}/{}".format(path, e)):
                        self.delete_folder("{}/{}".format(path, e))
        os.rmdir("{}/{}".format(self.ROOT, path))

    def create_folder(self, path: str = ''):
        if not self.folder_exists(path):
            if path == '':
                os.makedirs(self.ROOT)
            else:
                os.makedirs("{}/{}".format(self.ROOT, path))

    def list_files(self, path: str = '') -> 'list[str]':
        if self.folder_exists(path):
            return os.listdir("{}/{}".format(self.ROOT, path))
        else:
            return []

    def file_exists(self, path: str) -> bool:
        try:
            _ = os.stat(path)
            return True
        except OSError:
            return False

    def folder_exists(self, path: str = '') -> bool:
        try:
            _ = os.stat(path)
            return True
        except OSError:
            return False

    def is_file(self, path: str) -> bool:
        return os.stat(path)[6] > 0

    def is_folder(self, path: str) -> bool:
        return os.stat(path)[6] == 0


fs = CommonFileStorage("debug/sd")

import os

from db.FileStorage import FileStorage


class CommonFileStorage(FileStorage):

    def __init__(self, root: str):
        super().__init__(root)

        if not self.folder_exists():
            self.create_folder()

    def read(self, path: str) -> str:
        with open(f"{self.ROOT}/{path}", 'r', encoding="utf-8") as fil:
            data = fil.read()
        return data

    def write(self, path: str, data: str) -> None:
        with open(f"{self.ROOT}/{path}", 'w', encoding="utf-8") as fil:
            fil.write(data)

    def delete_file(self, path: str) -> None:
        if self.file_exists(path):
            os.remove(f"{self.ROOT}/{path}")

    def delete_folder(self, path: str) -> None:
        if self.folder_exists(path):
            if not self.folder_empty(path):
                for fil in self.list_files(path):
                    if self.is_file(f"{path}/{fil}"):
                        self.delete_file(f"{path}/{fil}")
                    elif self.is_folder(f"{path}/{fil}"):
                        self.delete_folder(f"{path}/{fil}")
        os.rmdir(f"{self.ROOT}/{path}")

    def create_folder(self, path: str = ''):
        if not self.folder_exists(path):
            if path == '':
                os.makedirs(self.ROOT)
            else:
                os.makedirs(f"{self.ROOT}/{path}")

    def list_files(self, path: str = '') -> list[str]:
        if self.folder_exists(path):
            return os.listdir(f"{self.ROOT}/{path}")
        return []

    def file_exists(self, path: str) -> bool:
        return os.path.exists(f"{self.ROOT}/{path}")

    def folder_exists(self, path: str = '') -> bool:
        return os.path.exists(f"{self.ROOT}/{path}")

    def is_file(self, path: str) -> bool:
        return os.path.isfile(f"{self.ROOT}/{path}")

    def is_folder(self, path: str) -> bool:
        return os.path.isdir(f"{self.ROOT}/{path}")


fs = CommonFileStorage("debug/sd")

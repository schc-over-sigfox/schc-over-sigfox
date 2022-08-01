class FileStorage:

    def __init__(self, root: str) -> None:
        self.ROOT = root

    def read(self, path: str) -> str:
        """Reads a file and returns its content as a string."""
        raise NotImplementedError

    def write(self, path: str, data: str) -> None:
        """Writes a string into a file."""
        raise NotImplementedError

    def delete_file(self, path: str) -> None:
        """Deletes a file."""
        raise NotImplementedError

    def delete_folder(self, path: str) -> None:
        """Deletes a folder and its contents."""
        raise NotImplementedError

    def create_folder(self, path: str = '') -> None:
        """Creates a folder."""
        raise NotImplementedError

    def file_exists(self, path: str) -> bool:
        """Checks if a file exists."""
        raise NotImplementedError

    def folder_exists(self, path: str = '') -> bool:
        """Checks if a folder exists."""
        raise NotImplementedError

    def list_files(self, path: str = '') -> list[str]:
        """Lists the files inside a folder."""
        raise NotImplementedError

    def file_empty(self, path: str) -> bool:
        """Checks if a file exists and is empty."""
        return self.file_exists(path) and self.read(path) == ''

    def folder_empty(self, path: str) -> bool:
        """Checks if a folder exists and is empty."""
        return self.folder_exists(path) and self.list_files(path) == []

    def is_file(self, path: str) -> bool:
        """Checks if the path points to a file"""
        raise NotImplementedError

    def is_folder(self, path: str) -> bool:
        """Checks if the path points to a folder"""
        raise NotImplementedError

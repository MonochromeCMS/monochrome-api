from io import FileIO
from tempfile import TemporaryFile
from typing import List

from deta import Drive

from .config import get_settings

media_settings = get_settings()

TEN_KB = 10 * 1024


class Media:
    def __init__(self) -> None:
        self.drive = Drive("media")

    def put(self, name: str, data: FileIO):
        self.drive.put(name, data)

    def get(self, name: str):
        file = self.drive.get(name)
        if not file:
            raise FileNotFoundError(f"{name} not found in the Deta Drive")
        return file

    def copy(self, source: str, dest: str):
        big_file = self.get(source)

        with TemporaryFile() as f:
            for chunk in big_file.iter_chunks(4096):
                f.write(chunk)
            big_file.close()
            f.seek(0)
            self.drive.put(dest, f)

    def move(self, source: str, dest: str):
        self.copy(source, dest)
        self.remove(source)

    def remove(self, name: str):
        self.drive.delete(name)

    def remove_many(self, names: List[str]):
        if names:
            self.drive.delete_many(names)

    def ls(self, dir: str):
        res = self.drive.list(prefix=dir)
        all_items = res["names"]

        while "paging" in res and res["paging"]["last"]:
            res = self.drive.list(prefix=dir, last=res["paging"]["last"])
            all_items += res["names"]

        return all_items

    def rmtree(self, dir: str):
        names = self.ls(dir)
        self.remove_many(names)


media = Media()

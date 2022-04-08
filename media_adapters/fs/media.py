import shutil
from io import FileIO
from os import listdir, makedirs, path, remove
from typing import List

from .config import get_settings

media_settings = get_settings()

TEN_KB = 10 * 1024


class Media:
    def _create_parents(self, name: str):
        makedirs(path.dirname(name), exist_ok=True)

    def _path(self, name: str):
        return media_settings.media(name)

    def put(self, name: str, data: FileIO):
        name = self._path(name)
        self._create_parents(name)

        with open(name, "wb") as f:
            while chunk := data.read(TEN_KB):
                f.write(chunk)

    def get(self, name: str):
        return open(self._path(name), "rb")

    def copy(self, source: str, dest: str):
        source = self._path(source)
        dest = self._path(dest)
        self._create_parents(dest)

        shutil.copy(source, dest)

    def move(self, source: str, dest: str):
        source = self._path(source)
        dest = self._path(dest)
        self._create_parents(dest)

        if path.exists(dest):
            remove(dest)

        shutil.move(source, dest)

    def remove(self, name: str):
        remove(self._path(name))

    def remove_many(self, names: List[str]):
        for name in names:
            self.remove(name)

    def ls(self, dir: str):
        dir = self._path(dir)

        return [path.join(dir, file) for file in listdir(dir)]

    def rmtree(self, dir: str):
        shutil.rmtree(self._path(dir), True)


media = Media()

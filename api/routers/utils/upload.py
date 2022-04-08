from math import ceil
from os import listdir, makedirs, path, remove
from shutil import rmtree
from tempfile import TemporaryFile
from typing import Iterable, List, Union
from uuid import UUID

from aiofiles import open
from fastapi import UploadFile
from PIL import Image
from pyunpack import Archive

from ...config import get_settings
from ...db import models
from ...exceptions import BadRequestHTTPException
from ...media import media

global_settings = get_settings()
Chapter = models.chapter.Chapter
UploadedBlob = models.upload.UploadedBlob

TEN_KB = 10 * 1024


compressed_formats = (
    "application/x-7z-compressed",
    "application/x-xz",
    "application/zip",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "application/vnd.rar",
)


async def uploaded_blob_list(db_session, session_id: UUID, length: int) -> list[UUID]:
    blobs = []
    for i in range(1, length + 1):
        blob = UploadedBlob(session_id=session_id, name=f"{i}.jpg")
        await blob.save(db_session)
        blobs.append(blob.id)
    return blobs


def copy_chapter_to_session(chapter: Chapter, blobs: List[UUID]):
    chapter_path = f"{chapter.manga_id}/{chapter.id}/"
    for i in range(chapter.length):
        media.media.copy(chapter_path + f"{i + 1}.jpg", f"blobs/{blobs[i]}.jpg")


def save_session_image(files: Iterable[tuple[UUID, str]]):
    for blob_id, file in files:
        im = Image.open(file)
        with TemporaryFile() as f:
            im.convert("RGB").save(f, "JPEG")
            f.seek(0)
            media.media.put(f"blobs/{blob_id}.jpg", f)
        remove(file)


def valid_image_extension(name: str):
    extensions = (".jpeg", ".jpg", ".png", ".bmp", ".webp")
    return any(name.lower().endswith(ext) for ext in extensions)


def valid_mime(content_type: str):
    return content_type in compressed_formats or content_type.startswith("image/")


async def save_single_file(file: UploadFile, out_dir: str):
    async with open(path.join(out_dir, file.filename), "wb") as out_file:
        while chunk := await file.read(TEN_KB):
            await out_file.write(chunk)
    return (file.filename,)


async def decompress_file(file: UploadFile, tmp_dir: str, out_dir: str):
    zip_path = path.join(tmp_dir, file.filename)
    # PyUnpack needs the compressed file to be somewhere in the FS
    async with open(zip_path, "wb") as zip_file:
        while chunk := await file.read(TEN_KB):
            await zip_file.write(chunk)

    Archive(zip_path).extractall(out_dir, True)
    remove(zip_path)

    files = listdir(out_dir)
    return [f for f in files if path.isfile(path.join(out_dir, f)) and valid_image_extension(f)]


def delete_blobs(ids: list[UUID]):
    media.media.remove_many([path.join("blobs", f"{blob_id}.jpg") for blob_id in ids])


def commit_blobs(chapter: Chapter, pages: list[UUID], edit: bool):
    chapter_path = f"{chapter.manga_id}/{chapter.id}"

    if edit:
        media.media.rmtree(chapter_path)

    for i, page in enumerate(pages):
        media.media.move(f"blobs/{page}.jpg", path.join(chapter_path, f"{i + 1}.jpg"))


def image_list(blobs: Iterable[UUID]):
    images = []
    temp_files = []
    for blob_id in blobs:
        fd = media.media.get(path.join("blobs", f"{blob_id}.jpg"))

        f = TemporaryFile()
        while chunk := fd.read(TEN_KB):
            f.write(chunk)
        fd.close()
        f.seek(0)

        images.append(Image.open(f))
        temp_files.append(f)

    return images, temp_files


def concat_and_cut_images(blobs: Iterable[UUID]):
    images, temp_files = image_list(blobs)
    height = sum(img.height for img in images)

    if not all(images[0].width == img.width for img in images):
        raise BadRequestHTTPException("All the images should have the same width")

    joined = Image.new("RGB", (images[0].width, height))
    running_height = 0
    for i, image in enumerate(images):
        joined.paste(image, (0, running_height))
        image.close()
        temp_files[i].close()
        running_height += image.height

    amount_parts = ceil(joined.height / (2 * joined.width))
    parts = []
    for i in range(amount_parts):
        end_y = min(height, 2 * joined.width * (i + 1))
        part = joined.crop((0, 2 * joined.width * i, joined.width, end_y))
        parts.append(part)

    return parts


class TempDir:
    prefix: str

    def __init__(self, prefix: Union[UUID, str]):
        self.prefix = path.join(global_settings.temp_path, str(prefix))

    def setup(self):
        makedirs(path.join(self.prefix, "zip"))
        makedirs(path.join(self.prefix, "files"))

    def rm(self):
        rmtree(self.prefix, True)

    @property
    def files(self):
        return path.join(self.prefix, "files")

    def files_join(self, filename: Union[UUID, str]):
        return path.join(self.files, str(filename))

    @property
    def zip(self):
        return path.join(self.prefix, "zip")

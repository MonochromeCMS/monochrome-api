from enum import Enum


class MediaBackends(str, Enum):
    deta = "DETA"
    filesystem = "FS"

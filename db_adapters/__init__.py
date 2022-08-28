from enum import Enum


class DatabaseBackends(str, Enum):
    deta = "DETA"
    postgres = "POSTGRES"

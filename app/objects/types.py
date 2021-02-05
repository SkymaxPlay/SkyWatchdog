from enum import Enum


class CheckType(Enum):
    PROCESS = 1
    ENDPOINT = 2


class PayloadType(Enum):
    PLAIN = 1
    JSON = 2


class JsonType(Enum):
    JSON_ARRAY = 1
    JSON_OBJECT = 2

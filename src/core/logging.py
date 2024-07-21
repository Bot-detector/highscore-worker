import json
import logging
import sys
import warnings

from core.config import settings

# log formatting
formatter = logging.Formatter(
    json.dumps(
        {
            "ts": "%(asctime)s",
            "name": "%(name)s",
            "function": "%(funcName)s",
            "level": "%(levelname)s",
            "msg": json.dumps("%(message)s"),
        }
    )
)

handlers = []

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

handlers.append(stream_handler)

# in NPRD it easier to have a file to see the logs
if settings.ENV != "PRD":
    file_handler = logging.FileHandler(filename="./src/error.log", mode="a")
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)


logging.basicConfig(level=logging.DEBUG, handlers=handlers)

# set imported loggers to warning
logging.getLogger("aiomysql").setLevel(logging.ERROR)
logging.getLogger("asyncmy").setLevel(logging.ERROR)
logging.getLogger("aiokafka").setLevel(logging.WARNING)

# https://github.com/aio-libs/aiomysql/issues/103
# https://github.com/coleifer/peewee/issues/2229
warnings.filterwarnings("ignore", ".*Duplicate entry.*")
warnings.filterwarnings("ignore", module=r"aiomysql")

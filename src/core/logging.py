import json
import logging
import sys
import warnings

from core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


handlers = []

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(JsonFormatter())
handlers.append(stream_handler)

# in NPRD it easier to have a file to see the logs
if settings.ENV != "PRD":
    file_handler = logging.FileHandler(filename="./src/error.log", mode="a")
    file_handler.setFormatter(JsonFormatter())
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

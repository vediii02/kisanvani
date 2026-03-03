import logging
import json
import sys
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    Ideal for cloud logging (GCP/AWS).
    """
    def __init__(self, fmt_dict: dict = None, time_format: str = "%Y-%m-%dT%H:%M:%S", msec_format: str = "%s.%03dZ"):
        super().__init__()
        self.fmt_dict = fmt_dict if fmt_dict is not None else {"message": "message"}
        self.time_format = time_format
        self.msec_format = msec_format

    def format(self, record):
        record.message = record.getMessage()
        record.asctime = self.formatTime(record, self.time_format)

        message_dict = {
            "timestamp": record.asctime,
            "level": record.levelname,
            "module": record.module,
            "message": record.message,
        }

        if record.exc_info:
            message_dict["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(message_dict)

def setup_logger(name: str) -> logging.Logger:
    """Sets up a logger with JSON formatting."""
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to prevent dual logging
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        
        logger.addHandler(handler)
        
        # We don't want logs to propagate to the root logger and get double-logged
        logger.propagate = False
        
    return logger

# Create a default logger for the app
logger = setup_logger("voiceservice")

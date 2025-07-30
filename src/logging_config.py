# DEPENDEBNCIES
import os
import logging
from logging.handlers import RotatingFileHandler


# CUSTOM FORMATTER OF THE LOGGING PARAMETERS
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if (not hasattr(record, 'request_id')):
            record.request_id = 'N/A'

        if (not hasattr(record, 'batch_id')):
            record.batch_id = 'N/A'

        if (not hasattr(record, 'batch_item_id')):
            record.batch_item_id = 'N/A'

        return super().format(record)


# LOGGING CONFIGURATION
def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger     = logging.getLogger()

    # Create console handler
    c_handler  = logging.StreamHandler()

    # Create formatter and add it to the console handler
    log_format = "%(name)s | %(levelname)s | Request ID: %(request_id)s | Batch: %(batch_id)s | Item: %(batch_item_id)s | %(message)s"
    c_format   = CustomFormatter(log_format)
    c_handler.setFormatter(c_format)

    # Add console handler to the logger
    logger.addHandler(c_handler)

    # Check if a log file exists in the current directory or its parent directories
    current_dir = os.getcwd()
    log_file    = None

    while (current_dir != os.path.dirname(current_dir)): # Stop at root directory
        for file in os.listdir(current_dir):
            if (file.endswith('.log')):
                log_file = os.path.join(current_dir, file)
                break

        if log_file:
            break

        current_dir = os.path.dirname(current_dir)

    # If a log file is found, add a file handler
    if log_file:
        f_handler = RotatingFileHandler(filename    = log_file,
                                        maxBytes    = 10*1024*1024,
                                        backupCount = 5,
                                       )
        f_format  = CustomFormatter(log_format)
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)

    return logger

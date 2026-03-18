# DEPENDENCIES
import os
import logging
import warnings
from config.settings import settings
from logging.handlers import RotatingFileHandler


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CUSTOM FORMATTER FOR LOGGING PARAMETERS
class CustomFormatter(logging.Formatter):
    """
    Custom formatter that adds request_id, batch_id, and batch_item_id to log records: if these attributes are not present in the log record, they default to 'N/A'
    """
    def format(self, record):
        """
        Format the log record with custom attributes
        
        Arguments:
        ----------
            record { logging.LogRecord } : The log record to format
            
        Returns:
        --------
                     { str }             : The formatted log message
        """
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'
        
        if not hasattr(record, 'batch_id'):
            record.batch_id = 'N/A'
        
        if not hasattr(record, 'batch_item_id'):
            record.batch_item_id = 'N/A'
        
        return super().format(record)


# LOGGING CONFIGURATION SETUP
def setup_logging():
    """
    Configures application-wide logging with both console and file handlers: creates a rotating file handler that maintains up to 5 backup files of 10MB each,
    console handler outputs to stderr with custom formatting
    
    Returns:
    --------
        { logging.Logger } : Configured root logger instance
    """
    # Set base logging level from settings
    logging.basicConfig(level = getattr(logging, settings.log_level.upper()))
    logger            = logging.getLogger()
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # CREATE CONSOLE HANDLER
    console_handler   = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # CREATE FORMATTER AND ADD TO CONSOLE HANDLER
    log_format = ("%(name)s | %(levelname)s | Request ID: %(request_id)s | Batch: %(batch_id)s | Item: %(batch_item_id)s | %(message)s")
    console_formatter = CustomFormatter(log_format)
    console_handler.setFormatter(console_formatter)
    
    # ADD CONSOLE HANDLER TO LOGGER
    logger.addHandler(console_handler)
    
    # CHECK IF LOG FILE EXISTS OR CREATE ONE
    current_dir       = os.getcwd()
    log_file          = None
    
    # Search for existing .log files in current or parent directories
    while (current_dir != os.path.dirname(current_dir)):  
        # Stop at root directory
        for file in os.listdir(current_dir):
            if file.endswith('.log'):
                log_file = os.path.join(current_dir, file)
                break
        
        if log_file:
            break
        
        current_dir = os.path.dirname(current_dir)
    
    # If no log file found, use the one from settings
    if not log_file:
        log_file = settings.log_file
    
    # CREATE FILE HANDLER WITH ROTATION
    try:
        file_handler   = RotatingFileHandler(filename    = log_file,
                                             maxBytes    = 10 * 1024 * 1024,  # 10MB
                                             backupCount = 5,
                                             encoding    = 'utf-8',
                                            )

        file_handler.setLevel(getattr(logging, settings.log_level.upper()))
        
        # CREATE FORMATTER AND ADD TO FILE HANDLER
        file_formatter = CustomFormatter(log_format)
        file_handler.setFormatter(file_formatter)
        
        # ADD FILE HANDLER TO LOGGER
        logger.addHandler(file_handler)
        
        logger.info(msg   = f"Logging configured successfully. Log file: {log_file}",
                    extra = {"request_id": "system", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
        
    except Exception as file_handler_error:
        logger.warning(msg   = f"Could not create file handler: {file_handler_error}. Using console only.",
                       extra = {"request_id": "system", "batch_id": "N/A", "batch_item_id": "N/A"},
                      )
    
    return logger


# CREATE GLOBAL LOGGER INSTANCE
logger = setup_logging()
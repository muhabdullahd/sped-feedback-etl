import logging
import os
import sys
from datetime import datetime

def get_logger(name, level=logging.INFO):
    """
    Configure and return a logger with the given name.
    
    Args:
        name: Logger name, typically __name__ from the calling module
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if logs directory exists
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
        except Exception:
            pass
    
    if os.path.exists(logs_dir):
        log_file = os.path.join(
            logs_dir, 
            f"{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

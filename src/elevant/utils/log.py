import logging
import os

from elevant import settings
from datetime import datetime


def setup_logger(script_name, stdout_level=logging.INFO, file_level=logging.DEBUG, write_to_file=True):
    # Create logger
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Create console handler
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(stdout_level)
    stdout_handler.setFormatter(formatter)

    # Add stdout handler to logger
    logger.addHandler(stdout_handler)

    if write_to_file:
        # Create logs directory if it does not yet exist
        if not os.path.exists(settings.LOG_PATH):
            os.makedirs(settings.LOG_PATH)

        # Create file handler
        script_name = script_name.split("/")[-1].replace(".py", "")
        current_datetime = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
        filename = settings.LOG_PATH + script_name + "." + current_datetime + ".log"
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)

        # Add file handler to logger
        logger.addHandler(file_handler)

    return logger

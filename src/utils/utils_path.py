"""Module about PathLib helper functions."""

import logging
from pathlib import Path


def check_folder_exists(folder_name: str) -> bool:
    """Check if a folder exists."""
    folder_path = Path(folder_name)
    if folder_path.is_dir():
        logging.debug(f"Folder exists {folder_path}")
        return True
    else:
        logging.debug(f"Folder does not exist {folder_path}")
        return False


def check_file_exists(file_name: str) -> bool:
    """Check if a file exists."""
    file_path = Path(file_name)
    if file_path.is_file():
        logging.debug(f"File exists {file_path}")
        return True
    else:
        logging.debug(f"File does not exist {file_path}")
        return False

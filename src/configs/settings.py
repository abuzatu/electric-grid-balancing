"""Configuration file with settings."""

# python modules
import os
from pathlib import Path

WORK_DIR = os.getenv("WORKDIR", "")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

""" Connection to other services"""
INPUT_SERVICE_URL = os.getenv("INPUT_SERVICE_URL", default="")
INPUT_SERVICE_API_KEY = os.getenv("INPUT_SERVICE_API_KEY", default="")

""" Paths """


def work_dir() -> Path:
    """Get working dir."""
    if WORK_DIR == "":
        return Path(__file__).parent.parent
    else:
        return Path(WORK_DIR)

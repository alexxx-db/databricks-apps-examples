"""
Dash AG-Grid Writeback application package.
"""

import logging
import os

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
)

from .callbacks import input_callbacks  # noqa: F401

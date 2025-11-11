"""Executable entrypoint used on the production server."""
from __future__ import annotations

import asyncio
import logging

from .main import main


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

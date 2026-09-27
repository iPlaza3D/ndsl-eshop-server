import os
from pathlib import Path

ROMS_DIR = Path(os.environ.get("ROMS_DIR", "/roms"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
SERVER_NAME = os.environ.get("SERVER_NAME", "NDSL eShop")

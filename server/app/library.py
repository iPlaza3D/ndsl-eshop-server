"""Escanea la carpeta de roms y mantiene un cache en memoria del catalogo."""
import hashlib
import time
from pathlib import Path
from threading import Lock
from typing import Optional

from . import config
from .nds_parser import NdsRomInfo, parse_nds_rom

_cache_lock = Lock()
_cache: dict[str, NdsRomInfo] = {}
_cache_timestamp: float = 0.0


def _make_id(filename: str) -> str:
    return hashlib.sha1(filename.encode("utf-8")).hexdigest()[:16]


def get_catalog(force: bool = False) -> dict[str, NdsRomInfo]:
    """Devuelve {id: NdsRomInfo}, re-escaneando si el cache expiro."""
    global _cache_timestamp
    with _cache_lock:
        now = time.time()
        if not force and _cache and (now - _cache_timestamp) < config.CACHE_TTL_SECONDS:
            return _cache

        catalog: dict[str, NdsRomInfo] = {}
        if config.ROMS_DIR.is_dir():
            for path in sorted(config.ROMS_DIR.glob("*.nds")):
                info = parse_nds_rom(path)
                if info:
                    catalog[_make_id(info.filename)] = info

        _cache.clear()
        _cache.update(catalog)
        _cache_timestamp = now
        return _cache


def get_rom(rom_id: str) -> Optional[NdsRomInfo]:
    return get_catalog().get(rom_id)


def get_rom_path(info: NdsRomInfo) -> Path:
    return config.ROMS_DIR / info.filename

"""Parser de headers de roms .nds: titulo, codigo de juego e icono/banner."""
import io
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

HEADER_TITLE_OFFSET = 0x00
HEADER_TITLE_LEN = 12
HEADER_GAMECODE_OFFSET = 0x0C
HEADER_GAMECODE_LEN = 4
HEADER_BANNER_OFFSET_PTR = 0x68

BANNER_TILES_OFFSET = 0x20
BANNER_TILES_SIZE = 512  # 32x32 px, 4bpp -> 8x8 tiles
BANNER_PALETTE_OFFSET = 0x220
BANNER_PALETTE_SIZE = 32  # 16 colores * 2 bytes (BGR555)
BANNER_TITLES_OFFSET = 0x240
BANNER_TITLE_LEN = 256  # UTF-16LE, un idioma
BANNER_TITLE_LANG_ENGLISH = 1


@dataclass
class NdsRomInfo:
    filename: str
    title: str
    game_code: str
    size_bytes: int
    icon_png: Optional[bytes]


def _bgr555_to_rgb(color: int) -> tuple[int, int, int]:
    r = (color & 0x1F) << 3
    g = ((color >> 5) & 0x1F) << 3
    b = ((color >> 10) & 0x1F) << 3
    return (r, g, b)


def _decode_icon(banner: bytes) -> Optional[bytes]:
    """Decodifica el icono 32x32 4bpp de un banner .nds a PNG bytes."""
    if len(banner) < BANNER_PALETTE_OFFSET + BANNER_PALETTE_SIZE:
        return None

    tile_data = banner[BANNER_TILES_OFFSET:BANNER_TILES_OFFSET + BANNER_TILES_SIZE]
    palette_raw = banner[BANNER_PALETTE_OFFSET:BANNER_PALETTE_OFFSET + BANNER_PALETTE_SIZE]
    palette = [_bgr555_to_rgb(struct.unpack_from("<H", palette_raw, i * 2)[0]) for i in range(16)]
    palette[0] = (0, 0, 0)  # color 0 es transparente, se muestra como negro de fondo

    img = Image.new("RGB", (32, 32))
    pixels = img.load()

    # El icono son 16 tiles de 8x8 en orden 4x4, cada byte = 2 pixeles (4bpp)
    tile_index = 0
    for tile_y in range(4):
        for tile_x in range(4):
            base = tile_index * 32  # 32 bytes por tile (8x8 a 4bpp)
            for py in range(8):
                for px in range(0, 8, 2):
                    byte = tile_data[base + py * 4 + px // 2]
                    low = byte & 0x0F
                    high = (byte >> 4) & 0x0F
                    x = tile_x * 8 + px
                    y = tile_y * 8 + py
                    pixels[x, y] = palette[low]
                    pixels[x + 1, y] = palette[high]
            tile_index += 1

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def parse_nds_rom(path: Path) -> Optional[NdsRomInfo]:
    """Lee el header de un archivo .nds y extrae metadata basica."""
    try:
        size_bytes = path.stat().st_size
        with open(path, "rb") as f:
            header = f.read(0x200)
            if len(header) < 0x200:
                return None

            raw_title = header[HEADER_TITLE_OFFSET:HEADER_TITLE_OFFSET + HEADER_TITLE_LEN]
            title = raw_title.split(b"\x00")[0].decode("ascii", errors="ignore").strip()

            raw_code = header[HEADER_GAMECODE_OFFSET:HEADER_GAMECODE_OFFSET + HEADER_GAMECODE_LEN]
            game_code = raw_code.decode("ascii", errors="ignore").strip()

            banner_offset = struct.unpack_from("<I", header, HEADER_BANNER_OFFSET_PTR)[0]
            icon_png = None
            if 0 < banner_offset < size_bytes:
                f.seek(banner_offset)
                banner = f.read(0x240 + BANNER_TITLE_LEN)
                if len(banner) >= BANNER_TITLES_OFFSET + BANNER_TITLE_LEN:
                    title_raw = banner[
                        BANNER_TITLES_OFFSET + BANNER_TITLE_LANG_ENGLISH * BANNER_TITLE_LEN:
                        BANNER_TITLES_OFFSET + (BANNER_TITLE_LANG_ENGLISH + 1) * BANNER_TITLE_LEN
                    ]
                    decoded = title_raw.decode("utf-16-le", errors="ignore").split("\x00")[0].strip()
                    if decoded:
                        # El titulo del banner viene en varias lineas: nombre corto/largo/publisher
                        title = decoded.replace("\n", " ").strip()
                icon_png = _decode_icon(banner)

            return NdsRomInfo(
                filename=path.name,
                title=title or path.stem,
                game_code=game_code,
                size_bytes=size_bytes,
                icon_png=icon_png,
            )
    except (OSError, struct.error):
        return None

"""API principal del NDSL eShop Server (estilo Ownfoil, para NDS)."""
import re
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from . import config, library

app = FastAPI(title=config.SERVER_NAME)

CHUNK_SIZE = 64 * 1024
RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class GameEntry(BaseModel):
    id: str
    title: str
    game_code: str
    filename: str
    size_bytes: int
    has_icon: bool


@app.get("/health")
def health():
    return {"status": "ok", "server": config.SERVER_NAME}


@app.get("/api/games", response_model=list[GameEntry])
def list_games():
    catalog = library.get_catalog()
    return [
        GameEntry(
            id=rom_id,
            title=info.title,
            game_code=info.game_code,
            filename=info.filename,
            size_bytes=info.size_bytes,
            has_icon=info.icon_png is not None,
        )
        for rom_id, info in catalog.items()
    ]


@app.get("/api/games/{rom_id}/icon.png")
def get_icon(rom_id: str):
    info = library.get_rom(rom_id)
    if not info:
        raise HTTPException(status_code=404, detail="Rom no encontrada")
    if not info.icon_png:
        raise HTTPException(status_code=404, detail="Rom sin icono")
    return Response(content=info.icon_png, media_type="image/png")


def _parse_range(range_header: Optional[str], file_size: int) -> tuple[int, int]:
    if not range_header:
        return 0, file_size - 1
    match = RANGE_RE.match(range_header)
    if not match:
        raise HTTPException(status_code=416, detail="Range invalido")
    start_str, end_str = match.groups()
    start = int(start_str) if start_str else 0
    end = int(end_str) if end_str else file_size - 1
    if start > end or end >= file_size:
        raise HTTPException(status_code=416, detail="Range fuera de rango")
    return start, end


@app.get("/download/{rom_id}")
def download_rom(rom_id: str, range: Optional[str] = Header(default=None)):
    """Descarga el .nds soportando Range (necesario para reanudar en la DS)."""
    info = library.get_rom(rom_id)
    if not info:
        raise HTTPException(status_code=404, detail="Rom no encontrada")

    path = library.get_rom_path(info)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    file_size = info.size_bytes
    start, end = _parse_range(range, file_size)
    content_length = end - start + 1

    def iter_file():
        with open(path, "rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = f.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers = {
        "Content-Disposition": f'attachment; filename="{info.filename}"',
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
    }
    status_code = 200
    if range:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        status_code = 206

    return StreamingResponse(
        iter_file(),
        status_code=status_code,
        media_type="application/octet-stream",
        headers=headers,
    )


@app.post("/api/rescan")
def rescan():
    catalog = library.get_catalog(force=True)
    return JSONResponse({"games_found": len(catalog)})

# NDSL eShop Server

Servidor de roms estilo **Ownfoil/Tinfoil**, pero para la **Nintendo DS Lite**.
Escanea una carpeta de roms `.nds`, extrae titulo/icono del propio rom y
expone una API para que un cliente homebrew de NDS liste el catalogo y
descargue los juegos directo a la SD del flashcart (en NDS no existe
"instalar" al sistema como en Switch, el flashcart lee `.nds` desde la SD).

- Codigo fuente: https://github.com/iPlaza3D/ndsl-eshop-server
- Arquitecturas: `linux/amd64`, `linux/arm64` (compatible con NAS ARM tipo
  Synology/QNAP)

## Uso rapido

```bash
docker run -d --name ndsl-eshop \
  -p 8000:8000 \
  -v /ruta/a/tus/roms:/roms:ro \
  -e SERVER_NAME="NDSL eShop" \
  iplaza3d/ndsl-shop-server:latest
```

## docker-compose

```yaml
services:
  ndsl-eshop:
    image: iplaza3d/ndsl-shop-server:latest
    container_name: ndsl-eshop-server
    ports:
      - "8000:8000"
    volumes:
      - ${ROMS_HOST_PATH:-./roms}:/roms:ro
    environment:
      - ROMS_DIR=/roms
      - SERVER_NAME=${SERVER_NAME:-NDSL eShop}
      - CACHE_TTL_SECONDS=${CACHE_TTL_SECONDS:-300}
    restart: unless-stopped
```

## Variables de entorno

| Variable | Default | Descripcion |
|---|---|---|
| `ROMS_DIR` | `/roms` | Carpeta con los `.nds` dentro del contenedor |
| `CACHE_TTL_SECONDS` | `300` | Segundos que se cachea el catalogo escaneado |
| `SERVER_NAME` | `NDSL eShop` | Nombre mostrado por la API |

## Endpoints

- `GET /health`
- `GET /api/games`
- `GET /api/games/{id}/icon.png`
- `GET /download/{id}` (soporta `Range` para reanudar descargas)
- `POST /api/rescan`

Ver el README completo del proyecto en GitHub para detalles de montaje de NAS
(CIFS/NFS) y el cliente homebrew.

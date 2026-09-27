# NDSL eShop Server

Servidor de roms para Nintendo DS Lite, estilo Ownfoil/Tinfoil pero para NDS.
El cliente homebrew descarga los `.nds` directo a la SD del flashcart (no hay
"instalacion" real en NDS, solo el archivo queda listo para que el menu del
flashcart / TWiLight Menu++ lo lance).

## Servidor (Docker)

### Opcion A: carpeta local o NAS ya montado en el host

1. Copia `.env.example` a `.env` y ajusta `ROMS_HOST_PATH` a tu carpeta de
   roms. Puede ser la carpeta local `./roms`, o la ruta donde ya tengas
   montado el share del NAS en el host, por ejemplo:
   - Windows: `Z:/roms` (unidad de red mapeada) o `\\NAS\roms` (UNC).
   - Linux/NAS con Docker (Synology, Unraid, TrueNAS): `/mnt/nas/roms`.
2. Levanta el servidor:
   ```powershell
   docker compose up --build -d
   ```
3. El server queda escuchando en `http://<tu-ip-lan>:8000`.
4. Abre `http://<tu-ip-lan>:8000` en el navegador para la web de control
   (biblioteca con iconos y descarga directa, y `/settings` con el estado
   y boton de rescaneo).

### Opcion B: montar el share del NAS directo desde Docker (CIFS/SMB)

Si el host Docker no tiene el share montado de antemano, usa
`docker-compose.nas.yml` (driver CIFS). Define en `.env`: `NAS_HOST`,
`NAS_SHARE`, `NAS_USER`, `NAS_PASSWORD`, y levanta con:
```powershell
docker compose -f docker-compose.yml -f docker-compose.nas.yml up --build -d
```
Para NFS, cambia `type: cifs` por `type: nfs` y ajusta `o:`/`device:` en
`docker-compose.nas.yml` segun tu NAS.

> Cambiar de carpeta de roms no requiere reconstruir la imagen: solo edita
> `.env` y corre `docker compose up -d` de nuevo (o `POST /api/rescan` si
> solo agregaste/quitaste archivos en la misma carpeta ya montada).

### Endpoints

- `GET /` — web de control: biblioteca con iconos, titulo, tamano y descarga.
- `GET /settings` — estado del servidor y boton para rescanear la biblioteca.
- `GET /health` — estado del servidor.
- `GET /api/games` — catalogo (id, titulo, game_code, filename, size_bytes, has_icon).
- `GET /api/games/{id}/icon.png` — icono 32x32 extraido del banner del rom.
- `GET /download/{id}` — descarga el `.nds`, soporta `Range` para reanudar.
- `POST /api/rescan` — fuerza un re-escaneo de la carpeta (por defecto cachea 5 min).

### Configuracion (env vars)

| Variable | Default | Descripcion |
|---|---|---|
| `ROMS_HOST_PATH` | `./roms` | (solo `.env`, host) carpeta local o NAS montado que se monta como `/roms` |
| `ROMS_DIR` | `/roms` | Carpeta donde estan los `.nds` **dentro** del contenedor |
| `CACHE_TTL_SECONDS` | `300` | Segundos que se cachea el catalogo |
| `SERVER_NAME` | `NDSL eShop` | Nombre mostrado |
| `NAS_HOST`, `NAS_SHARE`, `NAS_USER`, `NAS_PASSWORD` | — | Solo para `docker-compose.nas.yml` (montaje CIFS directo) |

## Desarrollo local (sin Docker)

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:ROMS_DIR="$PWD\..\roms"
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir . --reload
```

> Nota: en esta maquina solo hay Python 3.14 disponible localmente; las
> versiones fijadas en `requirements.txt` apuntan a lo que se usa en el
> contenedor (`python:3.12-slim`), que es el target real de produccion.

## Cliente NDS (homebrew)

Pendiente — ver carpeta `client/` (libnds + dswifi + libfat). Notas de build
en la memoria del repo (`devkitpro-build.md`).

## Publicar / probar en el NAS

La imagen se publica automaticamente en Docker Hub
(`iplaza3d/ndsl-shop-server`) via GitHub Actions en cada push a `main`
(ver `.github/workflows/docker-publish.yml`). Requiere configurar en el repo
de GitHub (Settings > Secrets and variables > Actions):

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (access token, no la password, generado en Docker Hub >
  Account Settings > Security)

### En el NAS, sin clonar el repo

```bash
docker run -d --name ndsl-eshop \
  -p 8000:8000 \
  -v /ruta/a/tus/roms:/roms:ro \
  -e SERVER_NAME="NDSL eShop" \
  iplaza3d/ndsl-shop-server:latest
```

### En el NAS, clonando el repo (usa `docker-compose.yml` / `docker-compose.nas.yml`)

```bash
git clone https://github.com/iplaza3d/ndsl-eshop-server.git
cd ndsl-eshop-server
cp .env.example .env   # ajusta ROMS_HOST_PATH
docker compose pull    # trae la imagen ya publicada, sin build local
docker compose up -d
```

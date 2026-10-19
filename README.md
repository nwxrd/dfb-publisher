# dfb-publisher

Publica el respaldo mensual de **documentos fuentes** (Issabel) a Google Drive.

No genera el respaldo: Issabel ya lo hace. Este proyecto, en **otro servidor**:

1. Lee `job.json` por SFTP y solo continúa si `status=done` y el mes coincide.
2. Descarga el mes completo (`reporte.html` + carpetas de programa).
3. Crea un **ZIP por programa** con **clave + AES-256** (carpetas con `manifiesto.csv`).
4. Sube a Drive: `{año}/{mes}/{programa}/{programa}.zip` y el informe renombrado `R_IT_AUD_002_{MES}_{AÑO}.html`.
5. Envía correo de **éxito** (inventario) o de **omisión/error** (siempre avisa).

## Requisitos

- Python 3.11 o 3.12
- Acceso SFTP al Issabel (clave privada)
- Credenciales OAuth de Google Drive (`credentials.json`)
- SMTP (p. ej. SendGrid)

## Instalación (porteo)

```bat
:: Windows (PowerShell o cmd, desde la carpeta del proyecto)
scripts\setup.bat
copy .env.example .env
copy config\settings.example.toml config\settings.toml
```

Si `setup.bat` falla o `run_publish` dice que falta el venv: borre la carpeta `.venv` (si existe a medias), asegúrese de tener Python 3.11+ de [python.org](https://www.python.org/downloads/) (no el de Inkscape) y vuelva a ejecutar `scripts\setup.bat`. El script usa el launcher `py -3` y crea `.venv\Scripts\python.exe`.

```bash
# Linux
chmod +x scripts/*.sh
./scripts/setup.sh
cp .env.example .env
cp config/settings.example.toml config/settings.toml
```

Complete `.env` (incluye `ZIP_PASSWORD`, obligatoria) y `config/settings.toml`. Coloque en `secrets/`:

| Archivo | Uso |
|---------|-----|
| `key.pem` | Clave SFTP Issabel |
| `credentials.json` | Cliente OAuth Google |
| `token.json` | Se crea en el primer login OAuth |

## Uso

```bat
scripts\run_publish.bat publish
scripts\run_publish.bat publish --month 2026-09
scripts\run_publish.bat publish --month 2026-09 --debug
```

```bash
./scripts/run_publish.sh publish
./scripts/run_publish.sh publish --month 2026-09
```

Programe la tarea **después** del cron/manual de Issabel (p. ej. Issabel 03:00, publisher 04:00).

## Estructura en Drive

```text
{root}/
  2026/
    9-SEPTIEMBRE/
      R_IT_AUD_002_SEPTIEMBRE_2026.html
      Az_Conectados/
        Az_Conectados.zip
      Biogen_colombia/
        Biogen_colombia.zip
```

## Controles (no publica basura)

| Condición | Acción |
|-----------|--------|
| `job.status` ≠ `done` | Correo “omitida” + exit 1 |
| Job de otro mes | Correo “omitida” + exit 1 |
| Sin `reporte.html` | Correo “omitida” + exit 1 |
| Sin programas con manifiesto | Correo “omitida” + exit 1 |
| Fallo SFTP/Drive/SMTP técnico | Correo “error” + exit 1 |

Los faltantes de audio (`missing` en el job) **no** bloquean si el job está `done`: el informe HTML es para validar.

## Tests

Requiere Python **3.11+** (el PBX Issabel suele tener 3.6; ejecute tests en el servidor destino):

```bash
source .venv/bin/activate   # o .venv\Scripts\activate
pytest -q
```

## Fuera de alcance

- No modifica Issabel ni RDF-PY.
- No comprime el mes entero ni el HTML.
- No genera ejecutable (.exe) en esta versión.

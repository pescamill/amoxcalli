# Ejecutar y publicar Amoxcalli

[English](DEPLOYMENT.md)

Amoxcalli es un solo proceso de Python que usa solo la biblioteca estándar: no hay base de datos externa ni dependencias que instalar para usarlo.

## 1. En tu computadora

Requisitos: Python 3.11 o más reciente y git.

```bash
git clone https://github.com/pescamill/amoxcalli.git
cd amoxcalli
make demo
```

Abre <http://127.0.0.1:8766>. La primera vez, `make demo` prepara los análisis derivados (alrededor de un minuto); después arranca en segundos.

Sin `make` (por ejemplo, en Windows):

```bash
python -c "from nahuatl_local.stems import WordStudy; WordStudy()._build()"
python -m nahuatl_local.platform serve
```

Opciones útiles de `serve`: `--port 8766`, `--demo` (solo lectura, ver abajo) y `--explain-model claude` (explicaciones redactadas por Claude; envía la pregunta y los pasajes a la API de Anthropic, ver [EVIDENCIA.md](EVIDENCIA.md)).

Pruebas: `make test` (Python y navegador simulado; la parte de navegador necesita Node.js y `npm ci --ignore-scripts`).

## 2. Con Docker

```bash
docker build -t amoxcalli .
docker run -p 7860:7860 amoxcalli
```

Abre <http://127.0.0.1:7860>. La imagen pesa unos 230 MB, construye los análisis al crearse y arranca en unos segundos. Corre en **modo demostración** (`--demo`).

## 3. Modo demostración

En un hosting gratuito el disco suele borrarse al reiniciar, y una instalación pública no debe guardar aportaciones ni voces de personas sin un acuerdo de privacidad y de custodia. Con `--demo` todo se puede consultar, pero el servidor rechaza cualquier escritura (perfiles, propuestas, grabaciones) con un mensaje claro. Para recibir aportaciones de verdad, usa una instalación con disco persistente, copia de seguridad y una política de privacidad publicada.

## 4. ¿Dónde publicarlo gratis?

Medido el 17 de octubre de 2026: con todos los índices construidos el servidor usa unos **760 MB de RAM**, así que hace falta un plan con **al menos 1 GB**. Las condiciones de cada proveedor cambian; revísalas al registrarte.

| Opción | Encaja | Notas |
|---|---|---|
| Oracle Cloud «Always Free» (máquina virtual) | Sí | Siempre encendida y con memoria de sobra; requiere más pasos (instalar Docker o Python, abrir el puerto, poner HTTPS). |
| **Google Cloud Run (capa gratuita)** | Sí, recomendada | Escala a cero: sin visitas no consume; una demo con poco tráfico cabe en la capa gratuita mensual. Requiere una cuenta con facturación activada. Tutorial abajo. |
| Hugging Face Spaces (Docker) | Solo de pago | Desde octubre de 2026 los Spaces con Docker, incluso en CPU básico, requieren la suscripción PRO (unos 9 USD al mes). Con PRO es lo más sencillo: tutorial abajo. |
| Planes gratuitos de 512 MB (Render, Koyeb y similares) | No | El servidor se queda sin memoria al construir los índices. |
| GitHub Pages u otro hosting estático | No | Amoxcalli necesita el servidor de Python para el análisis y la búsqueda. |

## 5. Tutorial: Google Cloud Run (gratis con poco tráfico)

1. Crea una cuenta en <https://cloud.google.com>, un proyecto y activa la facturación (la capa gratuita cubre una demo con poco tráfico; puedes poner una alerta de presupuesto en 1 USD).
2. Instala la herramienta `gcloud` (<https://cloud.google.com/sdk/docs/install>) e inicia sesión:

   ```bash
   gcloud auth login
   gcloud config set project TU_PROYECTO
   ```

3. Desde la carpeta del proyecto, construye y publica el contenedor:

   ```bash
   gcloud run deploy amoxcalli --source . --region us-central1 --allow-unauthenticated --memory 1Gi
   ```

4. Copia la URL que muestra (`https://amoxcalli-….run.app`) y dásela al servidor:

   ```bash
   gcloud run services update amoxcalli --region us-central1 --set-env-vars AMOXCALLI_PUBLIC_ORIGIN=https://amoxcalli-XXXX.run.app
   ```

5. Abre la URL. La primera visita tras un rato sin tráfico tarda unos segundos en despertar.

Para actualizarla, repite el paso 3.

## 6. Tutorial: Hugging Face Spaces (requiere PRO)

1. Crea una cuenta en <https://huggingface.co> y un **Space** nuevo: SDK **Docker**, plantilla en blanco, hardware **CPU basic** (con la suscripción PRO). Elige si será público o privado: un Space público publica el código y los datos del proyecto.
2. Instala la herramienta e inicia sesión (te pedirá un token de escritura de tu cuenta):

   ```bash
   pip install -U huggingface_hub
   hf auth login
   ```

   En versiones anteriores la herramienta se llama `huggingface-cli` (`huggingface-cli login`, `huggingface-cli upload`).
3. Desde la carpeta del proyecto, sube los archivos (cambia `USUARIO`). El segundo comando reemplaza el README del Space por su ficha, que le dice a Hugging Face que use Docker y el puerto 7860:

   ```bash
   hf upload USUARIO/amoxcalli . . --repo-type=space \
     --exclude ".git/*" ".venv/*" "node_modules/*" "models/*" "outputs/*" "data/*" "experiments/*" "reports/iterations/*" "reports/*-backups/*" "reports/*-experiments/*" "*.sqlite3*"
   hf upload USUARIO/amoxcalli deploy/huggingface/README.md README.md --repo-type=space
   ```

   La herramienta sube los archivos grandes (como `corpus/lexicon-catalog.json`, 13 MB) sin necesidad de configurar Git LFS.
4. En el Space, **Settings → Variables**, añade `AMOXCALLI_PUBLIC_ORIGIN` con la URL pública del Space, que tiene la forma `https://USUARIO-amoxcalli.hf.space`. Sin ella el servidor solo acepta su propio nombre interno y rechaza las visitas.
5. Espera a que termine la construcción (unos minutos; se ve en **Logs**) y abre la URL.

Para actualizarlo, repite el paso 3.

## 7. Tutorial: cualquier servidor con Docker

En una máquina virtual (Oracle Cloud, un VPS o una computadora propia) con Docker:

```bash
git clone https://github.com/pescamill/amoxcalli.git && cd amoxcalli
docker build -t amoxcalli .
docker run -d --restart unless-stopped -p 7860:7860 \
  -e AMOXCALLI_PUBLIC_ORIGIN=https://tu-dominio.org amoxcalli
```

Pon delante un proxy con HTTPS (por ejemplo Caddy: `reverse_proxy 127.0.0.1:7860`) y abre el puerto 443. `AMOXCALLI_PUBLIC_ORIGIN` debe ser exactamente la dirección HTTPS que verán las personas.

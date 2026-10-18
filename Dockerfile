# Amoxcalli en un contenedor: solo la biblioteca estándar de Python.
# Pensado para una demostración pública de solo lectura (Hugging Face Spaces, Cloud Run, una VM).
FROM python:3.12-slim

# Usuario sin privilegios (uid 1000, el que espera Hugging Face Spaces).
RUN useradd --create-home --uid 1000 amoxcalli
WORKDIR /app
COPY --chown=amoxcalli:amoxcalli . /app
USER amoxcalli

# Construye las cachés derivadas al crear la imagen: la demo no espera el arranque en frío.
RUN python -c "from nahuatl_local.stems import WordStudy; WordStudy()._build()"

ENV PORT=7860
EXPOSE 7860
# AMOXCALLI_PUBLIC_ORIGIN: la URL HTTPS pública (p. ej. https://usuario-amoxcalli.hf.space).
# La base de Voces vive en /tmp: en modo demo no se escribe nada en ella.
CMD ["sh", "-c", "exec python -m nahuatl_local.platform --db /tmp/voces.sqlite3 serve --host 0.0.0.0 --port \"$PORT\" --demo ${AMOXCALLI_PUBLIC_ORIGIN:+--public-origin \"$AMOXCALLI_PUBLIC_ORIGIN\"}"]

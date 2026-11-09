# Usamos una imagen ligera de Python
FROM python:3.11-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# Instalar fuentes para compatibilidad UTF-8 completa en portadas (tildes, eñes)
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

# Copiamos dependencias e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Cloud Run inyecta la variable PORT; usamos la misma en Gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 app:app"]
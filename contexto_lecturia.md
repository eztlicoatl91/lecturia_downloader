# Contexto del Proyecto: API Generadora de EPUBs (Lecturia a Kindle)

## 1. Descripción del Proyecto
Automatización de la extracción de cuentos online desde el sitio web `Lecturia.org` para convertirlos en archivos EPUB optimizados para Kindle Paperwhite. El proyecto tiene un enfoque de prácticas DevOps (maestría), transicionando de un script local en Windows a un microservicio web contenerizado desplegado en Google Cloud Run.

## 2. Stack Tecnológico
*   **Lenguaje:** Python 3.11+
*   **Web Scraping & Limpieza:** `requests`, `BeautifulSoup4` (bs4)
*   **Generación de EPUB:** `EbookLib`
*   **Procesamiento de Imágenes:** `Pillow` (PIL)
*   **API Web:** `Flask`, `gunicorn`
*   **Infraestructura:** Docker, Google Cloud Platform (Cloud Run, Cloud Build, Artifact Registry)

## 3. Estado Actual y Logros Técnicos (Local)
El núcleo de la aplicación (`lecturia_to_epub.py`) ya fue desarrollado, depurado y validado localmente en Windows. Resolvió los siguientes retos técnicos:
*   **Extracción de Metadatos:** Se obtienen título, autor y portada mediante etiquetas `Open Graph` (`og:title`, `og:description`, `og:image`).
*   **Procesamiento de la Portada:** Lecturia usa imágenes `.webp`. El script las descarga, las convierte al vuelo a `.jpg` usando `Pillow` (para garantizar compatibilidad con Calibre/Kindle), y dibuja dinámicamente un recuadro blanco en la parte inferior con el título del cuento centrado para facilitar su lectura en pantallas de tinta electrónica.
*   **Limpieza de HTML:** Se remueven bloques de anuncios publicitarios (`.code-block`), barras de redes sociales (`.lecturia-share-bar`), widgets de idiomas (`.wpml-flags-switcher`) y CSS embebido para permitir el control tipográfico nativo del Kindle (menú "Aa" y modo oscuro).
*   **Sintaxis XHTML (EbookLib):** Se integró el texto usando el parámetro `formatter="html"` en `decode_contents()` y pasando el HTML limpio directamente al contenido del capítulo. Esto solucionó errores previos de "Document is empty" y páginas en blanco causados por la duplicación de etiquetas `<head>` y `<body>`.
*   **Prevención de Caché (Calibre):** El archivo de salida incorpora una marca de tiempo (`timestamp`) en el nombre para obligar a Calibre a leer el EPUB como un archivo completamente nuevo y procesar su portada y metadatos correctamente.

## 4. Próximos Pasos (Fase DevOps y Cloud)
El objetivo inmediato es envolver el script existente en una API y desplegarlo en GCP.

### Tareas Pendientes:
1.  **Creación de `app.py` (Flask):** 
    *   Levantar un endpoint `POST /generar` que reciba un JSON con la `"url"` del cuento.
    *   Ejecutar la extracción y guardar el archivo temporalmente en la ruta `/tmp/` (único directorio con permisos de escritura en Cloud Run).
    *   Retornar el archivo EPUB generado al cliente.
2.  **Implementación de Seguridad (Protección de Cuota GCP):**
    *   Añadir validación mediante el header `x-api-key`.
    *   Configurar el despliegue en GCP con un límite estricto de concurrencia (`--max-instances 1`) para evitar sobrecargos y agotar el plan "Always Free".
3.  **Contenerización (`Dockerfile`):**
    *   Usar una imagen base ligera (ej. `python:3.11-slim`).
    *   Configurar `gunicorn` como servidor de producción para manejar el tráfico del contenedor.
4.  **Despliegue Manual (gcloud CLI):**
    *   Autenticar el proyecto local en Windows y ejecutar `gcloud run deploy` hacia la región `us-central1`.

## 5. Estructura de Archivos del Proyecto
*   `.venv/` (Excluido vía `.gitignore`)
*   `requirements.txt`
*   `lecturia_to_epub.py` (Script core funcional)
*   `app.py` (API Flask - Pendiente de integración final)
*   `Dockerfile` (Pendiente)
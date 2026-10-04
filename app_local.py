import os
import sys
import tempfile
import threading
import webbrowser
from flask import Flask, request, send_file, render_template_string, jsonify
from lecturia_to_epub import build_epub_from_lecturia

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lecturia a EPUB (Kindle Edition)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,600;1,400&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            --card-bg: rgba(30, 41, 59, 0.85);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --accent-glow: rgba(56, 189, 248, 0.25);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --success: #34d399;
            --error: #f87171;
            --input-bg: rgba(15, 23, 42, 0.6);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg-gradient);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: var(--text-primary);
        }

        .container {
            width: 100%;
            max-width: 640px;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px var(--accent-glow);
            animation: fadeIn 0.6s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent);
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
            margin-bottom: 14px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .title {
            font-family: 'Lora', Georgia, serif;
            font-size: 2.2rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 10px;
            line-height: 1.2;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 28px;
        }

        .feature-tag {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 10px 8px;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .feature-tag strong {
            display: block;
            color: var(--text-primary);
            font-size: 0.85rem;
            margin-bottom: 2px;
        }

        .form-group {
            margin-bottom: 24px;
        }

        .form-label {
            display: block;
            font-size: 0.88rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        .input-icon {
            position: absolute;
            left: 16px;
            color: var(--text-muted);
            width: 20px;
            height: 20px;
            pointer-events: none;
        }

        .input-url {
            width: 100%;
            background: var(--input-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 14px 16px 14px 46px;
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: all 0.2s ease;
            outline: none;
        }

        .input-url:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
            background: rgba(15, 23, 42, 0.85);
        }

        .input-url::placeholder {
            color: var(--text-muted);
        }

        .btn-submit {
            width: 100%;
            background: linear-gradient(135deg, var(--accent) 0%, #0284c7 100%);
            color: #0f172a;
            border: none;
            border-radius: 12px;
            padding: 14px 20px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.25s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 4px 14px var(--accent-glow);
        }

        .btn-submit:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4);
            filter: brightness(1.08);
        }

        .btn-submit:active:not(:disabled) {
            transform: translateY(0);
        }

        .btn-submit:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .status-container {
            margin-top: 24px;
            border-radius: 12px;
            padding: 16px;
            font-size: 0.9rem;
            display: none;
            line-height: 1.5;
            animation: fadeIn 0.3s ease-out;
        }

        .status-container.loading {
            display: flex;
            align-items: center;
            gap: 14px;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.2);
            color: var(--accent);
        }

        .status-container.success {
            display: block;
            background: rgba(52, 211, 153, 0.1);
            border: 1px solid rgba(52, 211, 153, 0.25);
            color: var(--success);
        }

        .status-container.error {
            display: block;
            background: rgba(248, 113, 113, 0.1);
            border: 1px solid rgba(248, 113, 113, 0.25);
            color: var(--error);
        }

        .spinner {
            width: 22px;
            height: 22px;
            border: 3px solid rgba(56, 189, 248, 0.25);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            flex-shrink: 0;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 20px;
        }

        .quick-links {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 8px;
        }

        .quick-btn {
            background: transparent;
            border: 1px dashed rgba(255, 255, 255, 0.15);
            color: var(--text-secondary);
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .quick-btn:hover {
            color: var(--accent);
            border-color: var(--accent);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                Kindle Paperwhite Edition
            </div>
            <h1 class="title">Lecturia a EPUB</h1>
            <p class="subtitle">Convierte cualquier cuento de Lecturia.org en un EPUB optimizado con portada y tipografía limpia.</p>
        </div>

        <div class="features-grid">
            <div class="feature-tag">
                <strong>Portada HD</strong>
                Conversión WebP → JPEG + Banner
            </div>
            <div class="feature-tag">
                <strong>HTML Limpio</strong>
                Sin anuncios ni estilos rotos
            </div>
            <div class="feature-tag">
                <strong>Calibre Ready</strong>
                Metadatos y spine estricto
            </div>
        </div>

        <form id="downloadForm">
            <div class="form-group">
                <label for="storyUrl" class="form-label">URL del cuento en Lecturia.org:</label>
                <div class="input-wrapper">
                    <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                    <input 
                        type="url" 
                        id="storyUrl" 
                        name="url" 
                        class="input-url" 
                        placeholder="https://lecturia.org/cuentos-y-relatos/..." 
                        required 
                        autocomplete="off"
                    />
                </div>
            </div>

            <button type="submit" id="submitBtn" class="btn-submit">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Generar y Descargar EPUB
            </button>
        </form>

        <div id="statusContainer" class="status-container">
            <div id="statusSpinner" class="spinner"></div>
            <div id="statusText"></div>
        </div>

        <div class="footer">
            <p>Pegar un enlace de ejemplo para probar:</p>
            <div class="quick-links">
                <button type="button" class="quick-btn" onclick="setExample('https://lecturia.org/cuentos-y-relatos/robert-bloch-la-progenie-de-bubastis/29062/')">Robert Bloch: La progenie de Bubastis</button>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('downloadForm');
        const urlInput = document.getElementById('storyUrl');
        const submitBtn = document.getElementById('submitBtn');
        const statusContainer = document.getElementById('statusContainer');
        const statusSpinner = document.getElementById('statusSpinner');
        const statusText = document.getElementById('statusText');

        function setExample(url) {
            urlInput.value = url;
            urlInput.focus();
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = urlInput.value.trim();
            if (!url) return;

            // UI Loading state
            submitBtn.disabled = true;
            statusContainer.className = 'status-container loading';
            statusSpinner.style.display = 'block';
            statusText.innerText = 'Extrayendo contenido, procesando portada y ensamblando EPUB...';

            try {
                const response = await fetch('/descargar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                if (!response.ok) {
                    let errMsg = 'Ocurrió un error al procesar el cuento.';
                    try {
                        const errJson = await response.json();
                        if (errJson.error) errMsg = errJson.error;
                    } catch (_) {}
                    throw new Error(errMsg);
                }

                // Obtener nombre del archivo del header o predeterminado
                const disposition = response.headers.get('Content-Disposition');
                let filename = 'cuento.epub';
                if (disposition && disposition.indexOf('filename=') !== -1) {
                    const matches = /filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/.exec(disposition);
                    if (matches != null && matches[1]) {
                        filename = matches[1].replace(/['"]/g, '');
                    }
                }

                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(downloadUrl);

                // UI Success state
                statusContainer.className = 'status-container success';
                statusSpinner.style.display = 'none';
                statusText.innerHTML = `<strong>¡Descarga completada con éxito!</strong><br>Archivo: <code>${filename}</code>`;
            } catch (error) {
                statusContainer.className = 'status-container error';
                statusSpinner.style.display = 'none';
                statusText.innerHTML = `<strong>Error:</strong> ${error.message}`;
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/descargar", methods=["POST"])
def descargar():
    # Soporta tanto JSON como Form Data
    if request.is_json:
        data = request.get_json(silent=True) or {}
        url = data.get("url")
    else:
        url = request.form.get("url")

    if not url or not isinstance(url, str) or not url.startswith("http"):
        return jsonify({"error": "Por favor ingresa una URL válida (ej. https://lecturia.org/...)"}), 400

    try:
        temp_dir = tempfile.gettempdir()
        generated_file = build_epub_from_lecturia(url, output_dir=temp_dir)
        if not generated_file or not os.path.exists(generated_file):
            return jsonify({"error": "No se pudo generar el archivo EPUB."}), 500

        download_name = os.path.basename(generated_file)
        # Si el nombre temporal tiene prefijo genérico, podemos intentar ponerle el nombre limpio del archivo
        return send_file(
            generated_file,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/epub+zip"
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

def open_browser(port):
    webbrowser.open(f"http://127.0.0.1:{port}")

if __name__ == "__main__":
    port = 5000
    # Abrir el navegador tras 1.2 segundos para que el servidor ya esté escuchando
    threading.Timer(1.2, open_browser, args=(port,)).start()
    print(f"Iniciando Lecturia Downloader en http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)

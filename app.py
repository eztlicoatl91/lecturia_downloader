import os

from flask import Flask, jsonify, request, send_file

from lecturia_to_epub import build_epub_from_lecturia

app = Flask(__name__)
API_KEY = os.getenv("LECTURIA_API_KEY") or os.getenv("API_KEY")


def validate_api_key():
    if not API_KEY:
        return None

    provided_key = request.headers.get("x-api-key")
    if provided_key != API_KEY:
        return jsonify({"error": "API key inválida o faltante."}), 401

    return None


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.post("/generar")
def generar_epub():
    api_error = validate_api_key()
    if api_error:
        return api_error

    data = request.get_json(silent=True) or {}
    url = data.get("url")

    if not isinstance(url, str) or not url.startswith("http"):
        return jsonify({"error": "Falta la URL válida en el cuerpo de la petición."}), 400

    try:
        output_dir = "/tmp"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"lecturia-{os.urandom(4).hex()}.epub")

        generated_file = build_epub_from_lecturia(url, output_file=output_file)
        if not generated_file or not os.path.exists(generated_file):
            raise FileNotFoundError("No se generó ningún archivo EPUB.")

        return send_file(
            generated_file,
            as_attachment=True,
            download_name=os.path.basename(generated_file),
            mimetype="application/epub+zip",
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
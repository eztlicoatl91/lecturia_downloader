import os
import re
import sys
import uuid
import io
from urllib.parse import urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from PIL import Image

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def build_epub_from_lecturia(url: str, output_file: str = None):
    print("--- INICIANDO EXTRACCIÓN ---")
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")

    # 1. Extracción de Metadatos Vía Open Graph
    meta_title = soup.find("meta", attrs={"property": "og:title"})
    meta_desc = soup.find("meta", attrs={"property": "og:description"})
    meta_img = soup.find("meta", attrs={"property": "og:image"})

    raw_title = meta_title["content"] if meta_title and meta_title.get("content") else "Cuento Desconocido"
    cleaned_header = re.sub(r'\s*\|\s*Lecturia.*$', '', raw_title, flags=re.IGNORECASE).strip()
    
    if ":" in cleaned_header:
        author, title = [x.strip() for x in cleaned_header.split(":", 1)]
    else:
        author = "Autor Desconocido"
        title = cleaned_header

    description = meta_desc["content"] if meta_desc and meta_desc.get("content") else "Cuento generado desde Lecturia."
    cover_url = meta_img["content"] if meta_img and meta_img.get("content") else None

    print(f"-> Detectado: {title} por {author}")

    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language("es")
    book.add_author(author)
    book.add_metadata('DC', 'description', description)
    book.add_metadata('DC', 'publisher', 'Lecturia')

    # 2. Procesamiento de Portada Oficial
    has_cover = False
    if cover_url:
        img_url = urljoin(url, cover_url)
        try:
            img_resp = requests.get(img_url, headers=HEADERS, timeout=15)
            if img_resp.status_code == 200:
                img_data = Image.open(io.BytesIO(img_resp.content))
                if img_data.mode != 'RGB':
                    img_data = img_data.convert('RGB')
                
                img_byte_arr = io.BytesIO()
                img_data.save(img_byte_arr, format='JPEG', quality=90)
                
                book.set_cover("cover.jpg", img_byte_arr.getvalue(), create_page=True)
                has_cover = True
                print("-> Portada JPEG inyectada y registrada.")
        except Exception as err:
            print(f"-> Aviso: No se pudo procesar la portada ({err})")

    # 3. Limpieza Quirúrgica del HTML
    content_area = soup.find("div", class_="entry-content") or soup.find("article")
    if not content_area:
        raise ValueError("No se pudo localizar el texto principal.")

    for trash in content_area.select(".code-block, .kb-row-layout-wrap, .lecturia-share-bar, .wpml-flags-switcher, script, style, iframe, form, button, noscript"):
        trash.decompose()
    for img in content_area.find_all("img"):
        img.decompose()
    for tag in content_area.find_all(True):
        if "style" in tag.attrs: del tag.attrs["style"]
        if "color" in tag.attrs: del tag.attrs["color"]

    # 4. Estilos y Ensamblaje del Capítulo
    css_content = """
    @page { margin: 0; }
    body { margin: 0; padding: 0; }
    .story-header { text-align: center; margin-top: 2em; margin-bottom: 2em; }
    .main-title { font-size: 1.5em; font-weight: bold; margin-bottom: 0.3em; line-height: 1.2; }
    .author-name { font-size: 1.1em; color: #333; }
    p { text-align: justify; text-indent: 1.3em; margin: 0 0 0.3em 0; line-height: 1.45; }
    h1 + p, h2 + p, h3 + p { text-indent: 0; }
    """
    style_item = epub.EpubItem(uid="style_paperwhite", file_name="style/style.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # AQUÍ ESTÁ LA MAGIA: Pasamos el HTML puro, asegurando entidades correctas (formatter="html")
    html_body = f"""
    <div class="story-header">
        <div class="main-title">{title}</div>
        <div class="author-name">{author}</div>
    </div>
    {content_area.decode_contents(formatter="html")}
    """
    
    chapter = epub.EpubHtml(title=title, file_name="story.xhtml", lang="es")
    chapter.content = html_body
    chapter.add_item(style_item)
    book.add_item(chapter)

    # 5. Orden de Lectura Estricto (Spine)
    book.toc = (epub.Link("story.xhtml", title, "intro"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    if has_cover:
        book.spine = ['cover', 'nav', chapter]
    else:
        book.spine = ['nav', chapter]

    # Exportación final con sello de tiempo
    timestamp = datetime.now().strftime("%H%M%S")
    filename = output_file or f"{clean_filename(author)} - {clean_filename(title)}_{timestamp}.epub"
    output_dir = os.path.dirname(filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    epub.write_epub(filename, book, {})
    print(f"✓ {filename} generado exitosamente.")
    return filename

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://lecturia.org/cuentos-y-relatos/robert-bloch-la-progenie-de-bubastis/29062/"
    build_epub_from_lecturia(url)
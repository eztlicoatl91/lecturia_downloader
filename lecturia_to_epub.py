import os
import re
import sys
import uuid
import io
import textwrap
from urllib.parse import urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from PIL import Image, ImageDraw, ImageFont

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def build_epub_from_lecturia(url: str, output_file: str = None, output_dir: str = None):
    print("--- INICIANDO EXTRACCIÓN ---")
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")

    # 1. Metadatos
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

    # 2. Procesamiento de Portada y Recuadro de Título
    has_cover = False
    if cover_url:
        img_url = urljoin(url, cover_url)
        try:
            img_resp = requests.get(img_url, headers=HEADERS, timeout=15)
            if img_resp.status_code == 200:
                img_data = Image.open(io.BytesIO(img_resp.content))
                if img_data.mode != 'RGB':
                    img_data = img_data.convert('RGB')
                
                # --- INICIO MODIFICACIÓN: DIBUJAR RECUADRO Y TEXTO ---
                width, height = img_data.size
                draw = ImageDraw.Draw(img_data)
                
                # Calcular un tamaño de fuente proporcional al ancho de la imagen (aprox. 5%)
                font_size = max(24, int(width * 0.05))
                try:
                    # Funciona en Pillow >= 10.1
                    font = ImageFont.load_default(size=font_size)
                except TypeError:
                    font = ImageFont.load_default()

                # Dividir el texto si es muy largo
                avg_char_width = font_size * 0.6
                chars_per_line = max(15, int((width - 40) / avg_char_width))
                wrapped_text = textwrap.fill(title, width=chars_per_line)

                # Calcular la caja delimitadora del texto
                left, top, right, bottom = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
                text_width = right - left
                text_height = bottom - top

                # Configurar el recuadro blanco en la parte inferior
                padding = 20
                rect_y0 = height - text_height - (padding * 2)
                
                # Dibujar fondo blanco
                draw.rectangle([0, rect_y0, width, height], fill="white")
                
                # Centrar y dibujar el texto en negro
                text_x = (width - text_width) // 2
                text_y = rect_y0 + padding
                draw.multiline_text((text_x, text_y), wrapped_text, fill="black", font=font, align="center")
                # --- FIN MODIFICACIÓN ---

                img_byte_arr = io.BytesIO()
                img_data.save(img_byte_arr, format='JPEG', quality=90)
                
                book.set_cover("cover.jpg", img_byte_arr.getvalue(), create_page=True)
                has_cover = True
                print("-> Portada JPEG con recuadro de título inyectada.")
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

    # Eliminar sinopsis repetida y encabezados redundantes del cuerpo del relato
    body_synopsis_text = None
    for p in list(content_area.find_all(["p", "div"])):
        text_clean = p.get_text(strip=True)
        if re.match(r'^(sinopsis|resumen)\s*:', text_clean, re.IGNORECASE):
            body_synopsis_text = re.sub(r'^(sinopsis|resumen)\s*:\s*', '', text_clean, flags=re.IGNORECASE).strip()
            p.decompose()
        elif re.search(r'\((cuento|relato|texto|obra)\s+completo[a]?\)', text_clean, re.IGNORECASE):
            p.decompose()

    if (not description or description == "Cuento generado desde Lecturia.") and body_synopsis_text:
        description = body_synopsis_text

    for tag in content_area.find_all(True):
        if "style" in tag.attrs: del tag.attrs["style"]
        if "color" in tag.attrs: del tag.attrs["color"]

    # 4. Estilos y Ensamblaje de Capítulos
    css_content = """
    @page { margin: 0; }
    body { margin: 0; padding: 0; }
    .story-header, .synopsis-header { text-align: center; margin-top: 2em; margin-bottom: 2em; }
    .main-title { font-size: 1.5em; font-weight: bold; margin-bottom: 0.3em; line-height: 1.2; }
    .author-name { font-size: 1.1em; color: #444; }
    .synopsis-label { font-size: 1.2em; font-weight: bold; text-align: center; margin-top: 1.5em; margin-bottom: 1em; text-transform: uppercase; letter-spacing: 0.05em; }
    .synopsis-text { font-style: italic; text-align: justify; text-indent: 1.2em; line-height: 1.5; margin: 1em 0; }
    .divider { border: 0; height: 1px; background: #ccc; margin: 2em auto; width: 40%; }
    p { text-align: justify; text-indent: 1.3em; margin: 0 0 0.3em 0; line-height: 1.45; }
    h1 + p, h2 + p, h3 + p { text-indent: 0; }
    """
    style_item = epub.EpubItem(uid="style_paperwhite", file_name="style/style.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Página 1: Sinopsis independiente
    synopsis_html = f"""
    <div class="synopsis-header">
        <div class="main-title">{title}</div>
        <div class="author-name">{author}</div>
    </div>
    <div class="divider"></div>
    <div class="synopsis-label">Sinopsis</div>
    <p class="synopsis-text">{description}</p>
    """
    synopsis_chapter = epub.EpubHtml(title="Sinopsis", file_name="synopsis.xhtml", lang="es")
    synopsis_chapter.content = synopsis_html
    synopsis_chapter.add_item(style_item)
    book.add_item(synopsis_chapter)

    # Página 2: Relato completo
    story_html = f"""
    <div class="story-header">
        <div class="main-title">{title}</div>
        <div class="author-name">{author}</div>
    </div>
    {content_area.decode_contents(formatter="html")}
    """
    chapter = epub.EpubHtml(title=title, file_name="story.xhtml", lang="es")
    chapter.content = story_html
    chapter.add_item(style_item)
    book.add_item(chapter)

    # 5. Orden de Lectura Estricto (Spine)
    book.toc = (
        epub.Link("synopsis.xhtml", "Sinopsis", "synopsis"),
        epub.Link("story.xhtml", title, "story"),
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    if has_cover:
        book.spine = ['cover', 'nav', synopsis_chapter, chapter]
    else:
        book.spine = ['nav', synopsis_chapter, chapter]

    timestamp = datetime.now().strftime("%H%M%S")
    default_name = f"{clean_filename(author)} - {clean_filename(title)}_{timestamp}.epub"
    if output_file:
        filename = output_file
    elif output_dir:
        filename = os.path.join(output_dir, default_name)
    else:
        filename = default_name

    target_dir = os.path.dirname(filename)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    epub.write_epub(filename, book, {})
    print(f"[OK] {filename} generado exitosamente.")
    return filename

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://lecturia.org/cuentos-y-relatos/robert-bloch-la-progenie-de-bubastis/29062/"
    build_epub_from_lecturia(url)
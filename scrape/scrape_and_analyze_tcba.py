# scrape/scrape_and_analyze_tcba.py
import os, time, json, base64
import xml.etree.ElementTree as ET
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from openai import OpenAI

# === CONFIG ===
SITEMAP_PATH = os.path.join("scrape", "joomla.xml")
OUTPUT_FILE = os.path.join("scrape", "tcba_web_content.jsonl")
BASE_URL = "https://www.tcba.com.ar"
OPENAI_API_KEY = "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"  # remplazar por tu key

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com",
}

IGNORED_IMAGES = [
    "logo.png", "logo-fjr.jpg", "logo_premio.png",
    "logo_ui.png", "logo_residencias.png",
    "play_store.jpg", "app_store.jpg"
]

client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for selector in [
        "nav", "header", "footer", "aside", "form", "script", "style", "noscript",
        "ul.nav.nav-pills.nav-stacked.menu",
        "div.sidebarLeftDepartment"
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            prefix = "=" * (7 - level)
            h.replace_with(f"\n{prefix} {h.get_text(strip=True)} {prefix}\n")

    texts = []
    
    # Extraer y destacar el título principal si existe
    page_heading = soup.find("div", class_="pageheading_title")


    if page_heading:
        titulo = page_heading.get_text(strip=True)
        texts.append(f"\n======= {titulo} =======\n")

    main = soup.select("article, main, div[itemprop='articleBody'], div.content, .contentpane, .item-page")
    if not main:
        main = [soup.body]


    for c in main:
        if c:
            text = c.get_text(separator="\n", strip=True)
            if text and len(text) > 100:
                texts.append(text)

    full = "\n\n".join(texts)
    for trash in ["Скачать шаблон для Joomla 3.4", "Leer Más"]:
        full = full.replace(trash, "")

    return full.strip()

def get_image_base64s(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    images = []

    images = []
    item_page = soup.find("div", class_="item-page")
    if not item_page:
        return []

    for img in item_page.find_all("img"):
        src = img.get("src", "")
        if any(ignored in src for ignored in IGNORED_IMAGES):
            continue
        img_url = urljoin(base_url, src)
        try:
            res = requests.get(img_url, headers=HEADERS, timeout=10)
            img_obj = Image.open(BytesIO(res.content)).convert("RGB")
            buffer = BytesIO()
            img_obj.save(buffer, format="JPEG")
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            images.append({"url": img_url, "base64": encoded})
        except Exception as e:
            print(f"⚠️ Img fail: {img_url} -> {e}")
    return images

def ask_gpt_for_images(images):
    if not images:
        return None

    img_parts = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img['base64']}"
            }
        }
        for img in images
    ]

    prompt = [
        {
            "role": "system",
            "content": "Sos un asistente que analiza imágenes de sitios web y devuelve el texto que contienen, en formato estructurado."
        },
        {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": (
                    "Extraé texto visible **y**, si la imagen no contiene texto, describí en una línea lo que se ve. "
                    "Ejemplo: 'Dos manos de un médico tomando suavemente la mano de un paciente'. "
                    "No repitas logos, premios o apps. Sé directo y preciso."
                )
                },
                *img_parts
            ]
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ GPT Error: {e}")
        return None

def main():
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [url.find("ns:loc", ns).text for url in root.findall("ns:url", ns)]
    #urls = [url.find("ns:loc", ns).text for url in root.findall("ns:url", ns)]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for url in urls:
            try:
                print(f"🔍 Scrapeando {url}")
                res = requests.get(url, headers=HEADERS, timeout=15)
                if res.status_code != 200:
                    print(f"❌ Status {res.status_code}")
                    continue

                text = extract_text(res.text)
                images = get_image_base64s(res.text, url)
                img_text = ask_gpt_for_images(images)

                result = {
                    "url": url,
                    "contenido_textual": text,
                    "informacion_extraida_de_imagenes": img_text
                }

                json.dump(result, f_out, ensure_ascii=False)
                f_out.write("\n")
                time.sleep(0.6)
            except Exception as e:
                print(f"⚠️ Error en {url}: {e}")
                continue

    print(f"\n✅ Scrapeo finalizado. Archivo generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

# scrape/improved_scrape_tcba.py
import os
import time
import json
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

SITEMAP_PATH = os.path.join("scrape", "sitemap.xml")
OUTPUT_FILE = os.path.join("scrape", "scraped_tcba2.jsonl")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TCBA-Bot/1.0; +https://www.tcba.com.ar/)"
}

def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remover elementos no deseados por clase, tag o patrón
    for selector in [
        "nav", "header", "footer", "aside", "form", "script", "style", "noscript",
        "ul.nav.nav-pills.nav-stacked.menu",
        "div.sidebarLeftDepartment",
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    # Resaltar encabezados <h1> a <h6> rodeándolos con === o ---
    for level in range(1, 7):
        for h_tag in soup.find_all(f"h{level}"):
            prefix = "=" * (7 - level)  # más énfasis en los h1
            title = h_tag.get_text(strip=True)
            h_tag.replace_with(f"\n{prefix} {title} {prefix}\n")

    # Buscar contenedores de contenido principal
    candidates = soup.select("article, main, div[itemprop='articleBody'], div.content, .contentpane, .item-page")
    if not candidates:
        candidates = [soup.body]

    texts = []
    for c in candidates:
        if c:
            text = c.get_text(separator="\n", strip=True)
            if text and len(text) > 100:
                texts.append(text)

    full_text = "\n\n".join(texts)

    # Frases a eliminar
    frases_a_eliminar = ["Скачать шаблон для Joomla 3.4", "Leer Más"]
    for frase in frases_a_eliminar:
        full_text = full_text.replace(frase, "")

    return full_text.strip()

def main():
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = [url.find("ns:loc", ns).text for url in root.findall("ns:url", ns)]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for url in urls:
            try:
                print(f"📡 Scraping: {url}")
                res = requests.get(url, headers=HEADERS, timeout=15)
                if res.status_code != 200:
                    print(f"❌ Error {res.status_code} en {url}")
                    continue

                content = extract_main_text(res.text)
                if not content or len(content) < 200:
                    print(f"⚠️  Contenido vacío o muy corto en {url}")
                    continue

                json.dump({"url": url, "content": content}, f_out, ensure_ascii=False)
                f_out.write("\n")

                time.sleep(0.5)  # evitar sobrecarga

            except Exception as e:
                print(f"⚠️  Error en {url}: {e}")
                continue

    print(f"\n✅ Scraping finalizado. Archivo generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

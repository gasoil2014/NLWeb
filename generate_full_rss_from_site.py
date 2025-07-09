import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin, urlparse
import time

START_URL = "https://tcba.com.ar"
DOMAIN = "tcba.com.ar"
OUTPUT_FILE = "tcba_full.xml"
MAX_PAGES = 100  # podés aumentarlo

visited = set()

def is_valid(url):
    parsed = urlparse(url)
    return parsed.netloc == DOMAIN and url not in visited and "#" not in url

def crawl(url, collected):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return
        visited.add(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else url
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 30]
        content = ' '.join(paragraphs[:5])
        collected.append((url, title, content))

        for link in soup.find_all('a', href=True):
            next_url = urljoin(url, link['href'])
            if is_valid(next_url) and len(visited) < MAX_PAGES:
                crawl(next_url, collected)
    except Exception as e:
        print(f"⚠️ Error accediendo a {url}: {e}")

def generate_rss(pages, output_file):
    fg = FeedGenerator()
    fg.title("TCBA - Contenido completo")
    fg.link(href=START_URL, rel='alternate')
    fg.description("Contenido completo scrapeado desde https://tcba.com.ar")

    for url, title, content in pages:
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=url)
        fe.description(content)
        print(f"✔️ {title} - {url}")

    fg.rss_file(output_file)
    print(f"\n✅ RSS generado: {output_file}")

if __name__ == "__main__":
    collected_pages = []
    print("⏳ Iniciando crawling de https://tcba.com.ar...")
    crawl(START_URL, collected_pages)
    print(f"\n🔍 Total páginas recolectadas: {len(collected_pages)}")
    generate_rss(collected_pages, OUTPUT_FILE)

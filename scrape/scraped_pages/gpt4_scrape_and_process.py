
import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://www.tcba.com.ar"
TARGET_URL = "https://www.tcba.com.ar/institucional/sedes"  # Cambiar por la URL a analizar
OUTPUT_JSONL = "output_tcba_scrape.jsonl"

client = OpenAI(api_key=OPENAI_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def download_image_as_base64(img_url):
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error descargando imagen {img_url}: {e}")
        return None


def scrape_page(url):
    print(f"🔍 Scrapeando {url}")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # Eliminar menús y basura
    for tag in soup.select(".nav, .menu, .nav-pills, .nav-stacked"):
        tag.decompose()

    for tag in soup.select("a.readmore, a.more-link"):
        tag.decompose()

    # Extraer texto
    text_parts = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        txt = tag.get_text(strip=True)
        if txt:
            if tag.name.startswith("h"):
                txt = f"**{txt}**"  # destacar títulos
            text_parts.append(txt)

    full_text = "\n".join(text_parts)

    # Extraer imágenes
    images = []
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        if src:
            img_url = urljoin(url, src)
            img_data = download_image_as_base64(img_url)
            if img_data:
                images.append({"url": img_url, "base64": img_data})

    return full_text, images


def analyze_with_openai(text, images):
    image_inputs = [
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
            "content": "Sos un asistente que analiza contenido web para convertirlo en datos estructurados."
        },
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""
Este es el contenido extraído de una página web. Procesalo y devolveme un JSON con la siguiente estructura:

- url
- resumen
- puntos_clave
- sede (si hay)
- informacion_extraida_de_imagenes (si aplica)

Contenido extraído:
{text}
"""
            }
        }
    ] + image_inputs

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=0.3
    )

    return response.choices[0].message.content

    image_inputs = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img['base64']}"}} for img in images[:3]]  # Máx 3 imgs
    prompt = [
        {"role": "system", "content": "Sos un asistente que analiza contenido web para convertirlo en datos estructurados útiles."},
        {"role": "user", "content": [
            {"type": "text", "text": f"Este es el contenido extraído de una página web. Procesalo y devolveme un JSON con los siguientes campos:

- url
- resumen
- puntos_clave
- sede (si hay)
- informacion_extraida_de_imagenes (si aplica)

Contenido:
{text}"]} 
        ] + image_inputs
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        max_tokens=1500,
        temperature=0.2
    )

    return response.choices[0].message.content


def save_jsonl(obj, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main():
    text, images = scrape_page(TARGET_URL)
    response = analyze_with_openai(text, images)

    # Intentar parsear JSON de la respuesta
    try:
        parsed = json.loads(response)
        parsed["url"] = TARGET_URL
        save_jsonl(parsed, OUTPUT_JSONL)
        print(f"✅ Guardado en {OUTPUT_JSONL}")
    except Exception as e:
        print("⚠️ No se pudo parsear como JSON:")
        print(response)


if __name__ == "__main__":
    main()

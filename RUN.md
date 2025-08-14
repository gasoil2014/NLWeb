# Para Correr

venv\Scripts\activate
cd code
python -m webserver.WebServer

# Para Scrappear

## Generar Sitemap 
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/component/osmap/?view=xsl&amp;format=xsl&amp;layout=standard&amp;id=1"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
	<url>
		<loc><![CDATA[https://www.tcba.com.ar/]]></loc>
		<changefreq>weekly</changefreq>
		<priority>0.5</priority>
	</url>
	<url>
<...>

## Scrappear
### Toma el sitemap.xml y escribe el resultado del scrapping. Tambien scrappea imagenes
py scrape/scrape_and_analyze_sitemap.py

# Para subir a qdrant
Modo Local
write_endpoint: qdrant_local

# Para subir a azure_ai_search
Modo Local
write_endpoint: azure_ai_search
read_endpoint: azure_ai_search



cd code
python -m tools.db_load ..\scrape\web_content.jsonl TCBA


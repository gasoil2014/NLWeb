# tools/db_delete.py
import sys
import os
import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models

if len(sys.argv) != 2:
    print("Uso: python -m tools.db_delete <site-name>")
    sys.exit(1)

site_name = sys.argv[1]
collection_name = "nlweb_collection"

# Leer config_retrieval.yaml manualmente
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config_retrieval.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

qdrant_config = config['qdrant_local']['client']

print(f"🔍 Eliminando documentos del sitio '{site_name}' en la colección '{collection_name}'...")

client = QdrantClient(**qdrant_config)

result = client.delete(
    collection_name=collection_name,
    points_selector=models.Filter(
        must=[
            models.FieldCondition(
                key="site",
                match=models.MatchValue(value=site_name)
            )
        ]
    )
)

print(f"✅ Sitio '{site_name}' eliminado correctamente.")

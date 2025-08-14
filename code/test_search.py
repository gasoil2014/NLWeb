# test_search.py
import os, requests
from dotenv import load_dotenv; load_dotenv()

endpoint = os.getenv("AZURE_VECTOR_SEARCH_ENDPOINT")
key = os.getenv("AZURE_VECTOR_SEARCH_API_KEY")
r = requests.get(f"{endpoint}/indexes?api-version=2024-07-01", headers={"api-key": key})
print(r.status_code, r.text[:200])

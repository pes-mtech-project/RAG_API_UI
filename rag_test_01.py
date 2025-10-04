import requests
import json

API_URL = "http://localhost:8000/search"
headers = {"Content-Type": "application/json"}

queries = {
    "Finance": "Indian banks exposure to non-performing assets",
    "FMCG": "growth outlook of packaged foods and personal care products in India",
    "Automotive": "electric vehicle adoption and subsidies in India",
    "Energy": "oil price fluctuations impact on Indian refiners",
    "IT": "cloud computing revenue growth for Indian IT services"
}

results = {}

for sector, query in queries.items():
    payload = {"query": query, "limit": 3}
    response = requests.post(API_URL, headers=headers, json=payload)
    results[sector] = response.json()

with open("rag_test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Results saved to rag_test_results.json")


import requests
import json

url = "http://127.0.0.1:8001/agent_search"
payload = {
    "job_description": "Développeur Python avec expérience en NLP et FastAPI",
    "top_k": 3
}

print("--- Envoi de la requête à l'Agent AI ---")
try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        results = response.json().get("results", [])
        for i, res in enumerate(results, 1):
            print(f"\nTalent #{i}: {res.get('login')} (Score Agent: {res.get('agent_score')})")
            print(f"Résumé IA: {res.get('ai_summary')}")
            print(f"Compétences extraites: {', '.join(res.get('ai_skills', []))}")
    else:
        print(f"Erreur {response.status_code}: {response.text}")
except Exception as e:
    print(f"Erreur de connexion : {e}")
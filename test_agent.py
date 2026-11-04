import requests

url = "http://127.0.0.1:8000/api/agent-chat/"
payload = {
    "message": "Explique l'anomalie de retard.",
    "context": {
        "transporteur": "Standard Auto",
        "region": "West Africa",
        "taux_retard": "42%"
    }
}

response = requests.post(url, json=payload)
print("Statut :", response.status_code)
print("Réponse de l'IA :", response.json())
import os
from openai import OpenAI

# On se connecte à Ollama (qui tourne localement sur le port 11434)
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" # La clé n'est pas vérifiée par Ollama
)

def extract_skills(text: str) -> list[str]:
    prompt = f"Liste les 6 compétences techniques principales présentes dans ce texte (séparées par des virgules) :\n----\n{text}\n----"
    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        return [s.strip() for s in raw.split(",") if s.strip()]
    except Exception as e:
        print(f"Erreur Ollama Skills: {e}")
        return []

def generate_summary(profile_text: str) -> str:
    prompt = f"Résume ce profil en deux phrases orientées recrutement / HR :\n----\n{profile_text}\n----"
    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erreur Ollama Summary: {e}")
        return "Résumé non disponible."

def score_with_context(profile_info: dict, job_description: str) -> float:
    combined = (
        f"Profil skills: {profile_info.get('skills')}\n"
        f"Texte brut: {profile_info.get('raw_text')}\n"
        f"Job description: {job_description}"
    )
    prompt = f"Sur une échelle de 0.0 à 1.0, donne un score de pertinence (seulement le nombre) entre ce profil et ce job :\n----\n{combined}\n----"
    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return float(response.choices[0].message.content.strip())
    except:
        return 0.0
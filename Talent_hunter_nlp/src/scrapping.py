# récupération des profils GitHub
"""
scraping.py
Récupération de données de développeurs depuis GitHub.
"""

import pandas as pd
import requests

from .config import GITHUB_DATA_PATH, DATA_RAW_DIR
import os

def fetch_github_profiles():
    """
    TODO: implémenter :
    - appeler l'API GitHub ou récupérer un dataset existant
    - construire un DataFrame avec :
      username, url, bio, nb_repos, langages, description_projets, etc.
    """
    raise NotImplementedError("À implémenter 🙂")

def save_profiles(df: pd.DataFrame):
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    df.to_csv(GITHUB_DATA_PATH, index=False)
    print(f"[OK] Données sauvegardées dans {GITHUB_DATA_PATH}")

if __name__ == "__main__":
    # plus tard : on implémentera cette partie
    pass

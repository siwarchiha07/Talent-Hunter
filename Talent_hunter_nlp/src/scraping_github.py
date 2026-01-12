import os
import time
import requests
import pandas as pd


# 👉 MET TON TOKEN ICI
# Exemple : GITHUB_TOKEN = "ghp_xxxxxxxx..."
# Si tu laisses None, ça marchera mais avec beaucoup moins de requêtes possibles
GITHUB_TOKEN = None


def get_base_dir():
    """Retourne le chemin du dossier de base du projet (Talent_hunter_nlp)."""
    return os.path.dirname(os.path.dirname(__file__))


def load_users(max_users=500):
    """
    Charge le fichier github_users.csv et retourne les max_users logins.
    On prend les plus populaires si la colonne 'followers' existe.
    """
    base_dir = get_base_dir()
    users_path = os.path.join(base_dir, "data", "raw", "github_users.csv")

    print(f"[INFO] Lecture de {users_path}")
    df = pd.read_csv(users_path)

    # On s'assure qu'il y a bien une colonne 'login'
    if "login" not in df.columns:
        raise ValueError("La colonne 'login' est absente du CSV Kaggle.")

    # Si on a les followers, on trie du plus suivi au moins suivi
    if "followers" in df.columns:
        df["followers"] = pd.to_numeric(df["followers"], errors="coerce").fillna(0)
        df = df.sort_values("followers", ascending=False)

    df = df.drop_duplicates(subset=["login"])

    # On limite au nombre voulu
    df = df.head(max_users).copy()

    print(f"[INFO] On va traiter {len(df)} utilisateurs GitHub.")
    return df


def fetch_repos_for_user(login):
    """
    Récupère les repos publics d'un utilisateur via l'API GitHub.
    On limite à 5 repos par user (les plus récents).
    """
    url = f"https://api.github.com/users/{login}/repos"
    params = {
        "per_page": 5,     # max 5 repos
        "sort": "updated", # les plus récents / mis à jour en premier
        "direction": "desc",
    }

    headers = {
        "Accept": "application/vnd.github+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Problème réseau pour l'utilisateur {login}: {e}")
        return []

    if r.status_code == 403:
        print(f"[ERREUR] 403 (rate limit ou accès refusé) pour {login}.")
        return []
    elif r.status_code == 404:
        print(f"[INFO] Utilisateur {login} introuvable (404).")
        return []
    elif r.status_code != 200:
        print(f"[ERREUR] Code HTTP {r.status_code} pour {login}.")
        return []

    try:
        repos = r.json()
    except ValueError:
        print(f"[ERREUR] Réponse JSON invalide pour {login}.")
        return []

    # On extrait seulement les infos qui nous intéressent
    repos_data = []
    for repo in repos:
        repos_data.append({
            "owner_login": login,
            "repo_name": repo.get("name", ""),
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "stargazers_count": repo.get("stargazers_count", 0),
            "html_url": repo.get("html_url", ""),
        })

    return repos_data


def main():
    base_dir = get_base_dir()
    raw_dir = os.path.join(base_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    repos_output_path = os.path.join(raw_dir, "github_repos.csv")

    # 1) Charger les utilisateurs Kaggle (par ex. 500 pour commencer)
    users_df = load_users(max_users=30)

    all_repos = []
    total_users = len(users_df)

    for i, (_, row) in enumerate(users_df.iterrows(), start=1):
        login = row["login"]
        print(f"[{i}/{total_users}] Récupération des repos pour : {login}")


        repos = fetch_repos_for_user(login)
        all_repos.extend(repos)

        # Petit sleep pour être gentils avec l'API (surtout si pas de token)
        time.sleep(0.5)

    if not all_repos:
        print("[ATTENTION] Aucune donnée de repo récupérée.")
        return

    repos_df = pd.DataFrame(all_repos)
    print(f"[INFO] Nombre total de repos récupérés : {len(repos_df)}")

    repos_df.to_csv(repos_output_path, index=False, encoding="utf-8")
    print(f"[OK] Données repos sauvegardées dans : {repos_output_path}")


if __name__ == "__main__":
    main()

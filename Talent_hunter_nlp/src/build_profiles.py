import os
import pandas as pd


def get_base_dir():
    return os.path.dirname(os.path.dirname(__file__))


def main():
    base_dir = get_base_dir()

    users_path = os.path.join(base_dir, "data", "raw", "github_users.csv")
    repos_path = os.path.join(base_dir, "data", "raw", "github_repos.csv")
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    print(f"[INFO] Lecture utilisateurs : {users_path}")
    users_df = pd.read_csv(users_path)

    print(f"[INFO] Lecture repos : {repos_path}")
    repos_df = pd.read_csv(repos_path)

    # --- Nettoyage basique ---

    # On s'assure que les colonnes clés existent
    if "login" not in users_df.columns:
        raise ValueError("La colonne 'login' est absente de github_users.csv")
    if "owner_login" not in repos_df.columns:
        raise ValueError("La colonne 'owner_login' est absente de github_repos.csv")

    # On ne garde que les colonnes utiles côté users
    users_cols = [
        "login",
        "name",
        "company",
        "location",
        "bio",
        "followers",
        "public_repos",
        "public_gists",
    ]
    users_df = users_df[[c for c in users_cols if c in users_df.columns]].copy()

    users_df = users_df.fillna("")

    # --- Agrégation des repos par utilisateur ---

    # On remplace NaN par vide et 0
    repos_df["description"] = repos_df["description"].fillna("")
    repos_df["language"] = repos_df["language"].fillna("")
    repos_df["stargazers_count"] = pd.to_numeric(
        repos_df.get("stargazers_count", 0), errors="coerce"
    ).fillna(0)

    # Texte concaténé des descriptions de repos
    agg_desc = repos_df.groupby("owner_login")["description"].apply(
        lambda x: " . ".join([d for d in x if isinstance(d, str) and d.strip() != ""])
    )

    # Liste unique des langages par user
    agg_lang = repos_df.groupby("owner_login")["language"].apply(
        lambda x: ", ".join(sorted(set([l for l in x if isinstance(l, str) and l.strip() != ""])))
    )

    # Total de stars et nb de repos
    agg_stars = repos_df.groupby("owner_login")["stargazers_count"].sum()
    agg_nb_repos = repos_df.groupby("owner_login")["repo_name"].count()

    repos_agg_df = pd.DataFrame({
        "login": agg_desc.index,
        "repos_descriptions": agg_desc.values,
        "languages_list": agg_lang.reindex(agg_desc.index).fillna(""),
        "total_stars": agg_stars.reindex(agg_desc.index).fillna(0).astype(int),
        "nb_repos_fetched": agg_nb_repos.reindex(agg_desc.index).fillna(0).astype(int),
    })

    print(f"[INFO] Utilisateurs avec au moins un repo récupéré : {len(repos_agg_df)}")

    # --- Fusion users + repos agrégés ---

    merged_df = pd.merge(
        users_df,
        repos_agg_df,
        on="login",
        how="inner",  # on garde seulement ceux pour lesquels on a des repos
    )

    print(f"[INFO] Taille finale après merge : {len(merged_df)}")

    # --- Construction du texte profil pour le NLP ---

    def build_profile_text(row):
        parts = []

        # Infos perso
        if row.get("name"):
            parts.append(str(row["name"]))
        if row.get("bio"):
            parts.append(str(row["bio"]))
        if row.get("company"):
            parts.append(f"Company: {row['company']}")
        if row.get("location"):
            parts.append(f"Location: {row['location']}")

        # Langages
        if row.get("languages_list"):
            parts.append(f"Languages: {row['languages_list']}")

        # Infos sur les repos
        if row.get("nb_repos_fetched", 0) > 0:
            parts.append(f"Number of repositories fetched: {row['nb_repos_fetched']}")
        if row.get("total_stars", 0) > 0:
            parts.append(f"Total stars: {row['total_stars']}")

        if row.get("repos_descriptions"):
            parts.append(f"Projects: {row['repos_descriptions']}")

        text = " . ".join([p for p in parts if isinstance(p, str) and p.strip() != ""])
        return text

    merged_df["profile_text"] = merged_df.apply(build_profile_text, axis=1)

    # On enlève les lignes où le texte profil est vide
    merged_df = merged_df[merged_df["profile_text"].str.strip() != ""].copy()

    # On peut trier par total_stars pour avoir les plus 'forts' en premier
    merged_df["total_stars"] = pd.to_numeric(merged_df["total_stars"], errors="coerce").fillna(0).astype(int)
    merged_df = merged_df.sort_values("total_stars", ascending=False)

    # Sauvegarde
    output_path = os.path.join(processed_dir, "profiles_enriched.csv")
    merged_df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"[OK] Fichier enrichi sauvegardé dans : {output_path}")


if __name__ == "__main__":
    main()

import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


def get_base_dir():
    return os.path.dirname(os.path.dirname(__file__))


class TalentSearcher:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        base_dir = get_base_dir()
        processed_dir = os.path.join(base_dir, "data", "processed")

        self.embeddings_path = os.path.join(processed_dir, "profiles_embeddings.npy")
        self.index_path = os.path.join(processed_dir, "profiles_index.csv")

        # Chargement des embeddings et de l'index
        print(f"[INFO] Chargement des embeddings depuis : {self.embeddings_path}")
        self.embeddings = np.load(self.embeddings_path)

        print(f"[INFO] Chargement de l'index depuis : {self.index_path}")
        self.index_df = pd.read_csv(self.index_path)

        if len(self.embeddings) != len(self.index_df):
            raise ValueError(
                f"Nombre d'embeddings ({len(self.embeddings)}) "
                f"différent du nombre de lignes de l'index ({len(self.index_df)})"
            )

        print(f"[INFO] Nombre de profils chargés : {len(self.index_df)}")

        # Chargement du modèle NLP
        print(f"[INFO] Chargement du modèle : {model_name}")
        self.model = SentenceTransformer(model_name)

    def search(
        self,
        job_description: str,
        top_k: int = 5,
        min_stars: int | None = None,
        language_filter: str | None = None,
    ):
        """
        Retourne les top_k profils les plus pertinents pour une description de poste,
        avec filtres optionnels sur les stars et le langage.
        """
        if not job_description or not job_description.strip():
            raise ValueError("La description de poste est vide.")

        # Encodage de la description du poste
        query_emb = self.model.encode(
            [job_description],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]  # vecteur 1D

        # Similarité cosinus = produit scalaire (embeddings normalisés)
        similarities = np.dot(self.embeddings, query_emb)  # (N,)

        # On met tout dans un DataFrame pour filtrer facilement
        df = self.index_df.copy()
        df["similarity"] = similarities

        # Filtre sur les stars
        if min_stars is not None and "total_stars" in df.columns:
            df = df[df["total_stars"] >= min_stars]

        # Filtre sur le langage
        if language_filter and "languages_list" in df.columns:
            lf = language_filter.lower()
            df = df[df["languages_list"].fillna("").str.lower().str.contains(lf)]

        # Tri par similarité + top_k
        df = df.sort_values("similarity", ascending=False)
        df = df.head(min(top_k, len(df)))

        return df.reset_index(drop=True)


def main():
    """Petit test en ligne de commande (optionnel)."""
    searcher = TalentSearcher()

    print("\n=== Test interactif : Chercheur de talents GitHub ===")
    print("Écris une description de poste (en anglais), ou 'q' pour quitter.\n")

    while True:
        job_desc = input("Description du poste > ")

        if job_desc.lower().strip() in {"q", "quit", "exit"}:
            print("Bye 👋")
            break

        try:
            results = searcher.search(job_desc, top_k=5)
        except ValueError as e:
            print(f"[ERREUR] {e}")
            continue

        print("\nTop 5 talents trouvés :\n")
        cols_to_show = [
            c
            for c in [
                "login",
                "name",
                "company",
                "location",
                "total_stars",
                "nb_repos_fetched",
                "similarity",
            ]
            if c in results.columns
        ]
        print(results[cols_to_show])
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()

# génération des embeddings
import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


def get_base_dir():
    return os.path.dirname(os.path.dirname(__file__))


def main():
    base_dir = get_base_dir()

    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    profiles_path = os.path.join(processed_dir, "profiles_enriched.csv")
    embeddings_path = os.path.join(processed_dir, "profiles_embeddings.npy")
    index_path = os.path.join(processed_dir, "profiles_index.csv")

    print(f"[INFO] Lecture des profils enrichis : {profiles_path}")
    df = pd.read_csv(profiles_path)

    # On vérifie qu'on a bien la colonne profile_text
    if "profile_text" not in df.columns:
        raise ValueError("La colonne 'profile_text' est absente de profiles_enriched.csv")

    # Optionnel : si on avait beaucoup de profils, on pourrait limiter
    # Ici, on garde tout
    texts = df["profile_text"].astype(str).tolist()
    print(f"[INFO] Nombre de profils à encoder : {len(texts)}")

    # Charger le modèle de SentenceTransformers
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"[INFO] Chargement du modèle : {model_name}")
    model = SentenceTransformer(model_name)

    print("[INFO] Encodage des textes (embeddings)...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # on normalise pour que cosine = dot
    )

    print(f"[INFO] Forme des embeddings : {embeddings.shape}")

    # Sauvegarde des embeddings
    np.save(embeddings_path, embeddings)
    print(f"[OK] Embeddings sauvegardés dans : {embeddings_path}")

    # Sauvegarde d'un index minimal (login + quelques infos)
        # Sauvegarde d'un index minimal (login + quelques infos)
    index_cols = []
    for col in ["login", "name", "company", "location", "total_stars", "nb_repos_fetched", "languages_list"]:
        if col in df.columns:
            index_cols.append(col)

    index_df = df[index_cols].copy()

    index_df.to_csv(index_path, index=False, encoding="utf-8")
    print(f"[OK] Index des profils sauvegardé dans : {index_path}")


if __name__ == "__main__":
    main()

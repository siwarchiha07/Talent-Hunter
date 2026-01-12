# interface Streamlit 
import os
import sys

import streamlit as st
import pandas as pd

# --- Pour pouvoir importer matching.py ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from matching import TalentSearcher  # noqa: E402


@st.cache_resource
def load_searcher():
    """
    Charge une seule fois le moteur de recherche (embeddings + modèle).
    Streamlit le garde en mémoire entre les requêtes.
    """
    return TalentSearcher()


def main():
    st.set_page_config(
        page_title="Talent Hunter NLP",
        page_icon="🧠",
        layout="wide",
    )

    st.title("🧠 Talent Hunter – Recherche de talents GitHub")
    st.write(
        """
        Entrez une description de poste (en anglais de préférence) et l'outil va chercher
        les profils GitHub les plus pertinents selon leurs bio + projets + langages + stars.
        """
    )

    # Chargement du moteur
    with st.spinner("Chargement du moteur de recherche (modèle + embeddings)..."):
        searcher = load_searcher()

    # Liste des langages possibles pour le filtre
    if "languages_list" in searcher.index_df.columns:
        all_langs = (
            searcher.index_df["languages_list"]
            .dropna()
            .astype(str)
            .str.split(",")
            .explode()
            .str.strip()
        )
        languages = sorted({l for l in all_langs if l})
    else:
        languages = []

    # Zone de texte pour la description du poste
    job_description = st.text_area(
        "✍️ Description du poste",
        value="We are looking for a machine learning engineer with Python, deep learning and experience with PyTorch.",
        height=150,
    )

    # Slider pour top_k
    top_k = st.slider(
        "Nombre de talents à retourner (Top K)",
        min_value=3,
        max_value=20,
        value=5,
        step=1,
    )

    # Filtre langage
    language_filter = None
    if languages:
        lang_choice = st.selectbox(
            "Filtrer par langage (optionnel)",
            options=["(Aucun filtre)"] + languages,
        )
        if lang_choice != "(Aucun filtre)":
            language_filter = lang_choice

    # Filtre nombre minimum de stars
    max_stars = int(searcher.index_df.get("total_stars", pd.Series([0])).max())
    min_stars_input = st.number_input(
        "Filtre : nombre minimum de stars totales (optionnel)",
        min_value=0,
        max_value=max_stars if max_stars > 0 else 100000,
        value=0,
        step=100,
    )
    min_stars = min_stars_input if min_stars_input > 0 else None

    # Bouton
    if st.button("🔍 Chercher des talents"):
        if not job_description.strip():
            st.warning("Merci d'entrer une description de poste.")
            return

        with st.spinner("Recherche des profils les plus pertinents..."):
            try:
                results = searcher.search(
                    job_description,
                    top_k=top_k,
                    min_stars=min_stars,
                    language_filter=language_filter,
                )

            except Exception as e:
                st.error(f"Erreur pendant la recherche : {e}")
                return

        if results.empty:
            st.info("Aucun profil trouvé. Essayez une autre description.")
            return

        # On ajoute une colonne avec le lien GitHub du profil
        if "login" in results.columns:
            results = results.copy()
            results["github_profile"] = results["login"].apply(
                lambda x: f"https://github.com/{x}"
            )

        st.subheader("👤 Profils trouvés")

        # Colonnes à afficher
        cols_to_show = []
        for col in [
            "login",
            "name",
            "company",
            "location",
            "total_stars",
            "nb_repos_fetched",
            "similarity",
            "github_profile",
        ]:
            if col in results.columns:
                cols_to_show.append(col)

        st.dataframe(
            results[cols_to_show],
            use_container_width=True,
        )

        # Bouton de téléchargement CSV
        csv_data = results.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger les résultats en CSV",
            data=csv_data,
            file_name="talent_hunter_results.csv",
            mime="text/csv",
        )

        st.caption(
            "Les profils sont triés par similarité décroissante (1.0 = très proche de la description, 0 = pas du tout)."
        )

        # 📧 Générateur d'email d'approche
        st.subheader("📧 Générer un email d'approche pour un talent")

        job_title_for_email = st.text_input(
            "Intitulé du poste",
            value="Machine Learning Engineer",
        )
        company_name_for_email = st.text_input(
            "Nom de votre entreprise",
            value="YourCompany",
        )

        if "login" in results.columns:
            candidate_logins = results["login"].tolist()
        else:
            candidate_logins = []

        if candidate_logins:
            selected_login = st.selectbox(
                "Choisir un talent pour générer l'email",
                options=candidate_logins,
            )

            cand = results[results["login"] == selected_login].iloc[0]
            candidate_name = cand.get("name") or selected_login
            github_url = cand.get("github_profile", f"https://github.com/{selected_login}")
            candidate_langs = cand.get("languages_list", "")

            email_body = f"""Hello {candidate_name},

I found your GitHub profile ({github_url}) and was really impressed by your work, especially your experience with {candidate_langs}.

We are currently looking for a {job_title_for_email} at {company_name_for_email}. Your background seems to be a very good match for this role.

If you are open to discussing this opportunity, I would be happy to schedule a short call.

Best regards,
[Your Name]
[Your Role]
[Your Contact Information]
"""

            st.text_area(
                "Email d'approche (à copier-coller dans votre client mail)",
                value=email_body,
                height=220,
            )

            st.caption(
                "⚠️ À envoyer uniquement si vous disposez d'un moyen de contact public et en respectant les bonnes pratiques (pas de spam)."
            )


if __name__ == "__main__":
    main()

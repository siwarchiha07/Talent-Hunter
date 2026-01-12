import pandas as pd
import numpy as np
import os
from sklearn.metrics import mean_absolute_error

def evaluate_agent():
    # Chemins des fichiers
    gold_path = "data/processed/gold_standard.csv"
    results_path = "data/processed/profiles_enriched.csv"

    if not os.path.exists(gold_path) or not os.path.exists(results_path):
        print(f"[ERREUR] Fichiers introuvables dans data/processed/")
        return

    # 1. Chargement des données
    gold_df = pd.read_csv(gold_path)
    results_df = pd.read_csv(results_path)

    # 2. Harmonisation des noms de colonnes pour la fusion
    # On force tout en minuscules pour éviter les erreurs de casse
    gold_df.columns = [c.strip().lower() for c in gold_df.columns]
    results_df.columns = [c.strip().lower() for c in results_df.columns]

    # 3. Fusion sur la colonne 'login'
    comparison = pd.merge(gold_df, results_df, on="login")

    if comparison.empty:
        print("[ERREUR] Aucun login en commun trouvé entre ton Excel et les résultats de l'IA.")
        return

    # 4. Identification et Conversion des colonnes de score
    # On cible explicitement la colonne de note pour éviter de lire du texte
    y_true_col = 'note de pertinence (humain)' 
    y_pred_col = 'agent_score'

    # Conversion forcée en nombres (ignore les textes si présents par erreur)
    comparison[y_true_col] = pd.to_numeric(comparison[y_true_col], errors='coerce')
    comparison[y_pred_col] = pd.to_numeric(comparison[y_pred_col], errors='coerce')

    # On supprime les lignes qui n'ont pas pu être converties en nombre
    comparison = comparison.dropna(subset=[y_true_col, y_pred_col])

    y_true = comparison[y_true_col]
    y_pred = comparison[y_pred_col]

    # 5. Calcul des Métriques
    # MAE : Écart moyen absolu entre l'humain et l'IA
    mae = mean_absolute_error(y_true, y_pred)
    
    # Accuracy : Pourcentage de profils où l'IA est à moins de 0.15 de ta note
    accuracy = np.mean(np.abs(y_true - y_pred) < 0.15) * 100

    print("\n" + "="*45)
    print("✅ ÉVALUATION RÉUSSIE")
    print("="*45)
    print(f"Profils comparés      : {len(comparison)}")
    print(f"Erreur Moyenne (MAE)  : {mae:.4f}")
    print(f"Précision (Accuracy)  : {accuracy:.2f}%")
    print("="*45)
    print("Interprétation : Plus la MAE est proche de 0,")
    print("plus Llama 3 réfléchit comme un humain.")
    print("="*45 + "\n")

if __name__ == "__main__":
    evaluate_agent()
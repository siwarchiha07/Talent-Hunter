import sys
import os
import pandas as pd
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

# 1. Configuration du chemin
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.matching import TalentSearcher
from src.agent import extract_skills, generate_summary, score_with_context

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation globale
PROFILES_PATH = os.path.join(base_dir, "data", "processed", "profiles_enriched.csv")
full_profiles_df = pd.DataFrame() 

# Chargement sécurisé des données
try:
    full_profiles_df = pd.read_csv(PROFILES_PATH)
    print(f"[OK] {len(full_profiles_df)} profils chargés.")
except Exception as e:
    print(f"[ERREUR] Chargement CSV: {e}")

searcher = TalentSearcher()

class SearchRequest(BaseModel):
    job_description: str
    top_k: int = 5
    min_stars: Optional[int] = 0
    language_filter: Optional[str] = None

@app.post("/agent_search")
async def agent_search(payload: SearchRequest):
    global full_profiles_df # Déclaration au début de la fonction

    results_df = searcher.search(
        job_description=payload.job_description,
        top_k=payload.top_k,
        min_stars=payload.min_stars,
        language_filter=payload.language_filter,
    )

    if results_df.empty:
        return {"results": []}

    results_df = results_df.fillna(0.0)
    enriched_results = []
    records = results_df.to_dict(orient="records")

    for r in records:
        for key, value in r.items():
            if isinstance(value, float) and (pd.isna(value) or value == float('inf')):
                r[key] = 0.0

        profile_row = full_profiles_df[full_profiles_df['login'] == r['login']]
        
        if not profile_row.empty:
            full_text = str(profile_row['profile_text'].values[0])
            try:
                r["ai_skills"] = extract_skills(full_text)
                r["ai_summary"] = generate_summary(full_text)
                score = score_with_context(
                    {"skills": r["ai_skills"], "raw_text": full_text}, 
                    payload.job_description
                )
                r["agent_score"] = float(score)
            except Exception as e:
                print(f"[INFO] Erreur IA pour {r['login']}: {e}")
                r["ai_skills"] = []
                r["ai_summary"] = "Analyse indisponible"
                r["agent_score"] = float(r.get("similarity", 0.0))
        
        enriched_results.append(r)

    enriched_results.sort(key=lambda x: x.get("agent_score", 0), reverse=True)

    # SAUVEGARDE POUR EVAL_METRICS
    for r in enriched_results:
        full_profiles_df.loc[full_profiles_df['login'] == r['login'], 'agent_score'] = r['agent_score']
    
    full_profiles_df.to_csv(PROFILES_PATH, index=False)
    return {"results": enriched_results}
 # paramètres globaux (chemins, etc.)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

GITHUB_DATA_PATH = os.path.join(DATA_RAW_DIR, "github_profiles.csv")
PROCESSED_DATA_PATH = os.path.join(DATA_PROCESSED_DIR, "profiles_processed.parquet")
EMBEDDINGS_PATH = os.path.join(DATA_PROCESSED_DIR, "profiles_embeddings.npy")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

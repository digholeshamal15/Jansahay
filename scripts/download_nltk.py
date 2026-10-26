"""One-time optional English lab models. No downloads at app startup."""
from pathlib import Path
import nltk

folder = Path(__file__).resolve().parents[1] / "nltk_data"
for name in ["averaged_perceptron_tagger_eng", "wordnet", "omw-1.4", "maxent_ne_chunker_tab", "words"]:
    if not nltk.download(name, download_dir=str(folder)):
        raise SystemExit(f"Could not download {name}; check your internet connection.")
print("English POS, WordNet and NER resources are ready. Restart the app if it is running.")

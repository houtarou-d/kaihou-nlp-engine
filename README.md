# NLP Engine (spaCy)

A tiny Python package that analyses the morphosyntax of a sentence and prints the result in a friendly, Spanish‑language description.

## Features

- **Universal POS tags** and **dependency relations** using spaCy.
- Translation of technical tags to plain Spanish (e.g. `VERB` → *verbo*).
- Pretty‑printed tree with **Rich** (dark theme).
- Simple CLI:
  ```bash
  python -m nlp_engine.cli analyze "Los niños juegan en el parque"
  python -m nlp_engine.cli list‑langs
  ```
- Easy to extend to new languages – just add the model name to `SpaCyAnalyzer.model_map`.

## Installation

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download the Spanish model (or any other you need)
python -m spacy download es_core_news_sm
# Optional: other languages
# python -m spacy download en_core_web_sm
```

## Usage

```bash
# Analyse a sentence (default language is Spanish)
python -m nlp_engine.cli analyze "Los niños juegan en el parque"

# Specify a different language
python -m nlp_engine.cli analyze "The children are playing in the park" -l en

# List supported language codes
python -m nlp_engine.cli list‑langs
```

## Adding a new language

1. Open `nlp_engine/analyzer.py`.
2. Extend the `model_map` dictionary inside `SpaCyAnalyzer.__init__` with a new entry, e.g.:
   ```python
   model_map = {"es": "es_core_news_sm", "en": "en_core_web_sm", "it": "it_core_news_sm"}
   ```
3. Run `python -m spacy download <model_name>` to install the model.
4. The CLI will automatically accept the new ``--lang`` code.

## License

MIT – feel free to adapt and share!

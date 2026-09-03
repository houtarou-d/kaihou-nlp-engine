"""nlp_engine.analyzer

Wrapper around spaCy that provides a unified, language‑agnostic interface.
It returns a list of :class:`TokenInfo` objects containing:
- text
- lemma
- universal POS tag (UPOS)
- morphological features (as a string)
- head index (1‑based, ``0`` for ROOT)
- dependency relation (DEPREL)

A helper ``translate_*`` maps the technical tags to plain English that a
non‑technical user can understand.
"""

from __future__ import annotations
import spacy

import importlib
from dataclasses import dataclass
from typing import List, Dict

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TokenInfo:
    text: str
    lemma: str
    pos: str  # universal POS (UPOS)
    morphology: str
    head: int  # 1‑based index of head token (0 = ROOT)
    dep: str  # dependency label (DEPREL)

# ---------------------------------------------------------------------------
# Translation tables – plain English for a beginner
# ---------------------------------------------------------------------------

POS_MAP: Dict[str, str] = {
    "ADJ": "adjetivo",
    "ADP": "adposición",
    "ADV": "adverbio",
    "AUX": "auxiliar",
    "CCONJ": "conjunción coordinante",
    "DET": "determinante",
    "INTJ": "interjección",
    "NOUN": "nombre (sustantivo)",
    "NUM": "numeral",
    "PART": "partícula",
    "PRON": "pronombre",
    "PROPN": "nombre propio",
    "SCONJ": "conjunción subordinante",
    "SYM": "símbolo",
    "VERB": "verbo",
    "X": "otro",
    "PUNCT": "puntuación",
}

DEP_MAP: Dict[str, str] = {
    "nsubj": "sujeto nominal",
    "obj": "objeto directo",
    "iobj": "objeto indirecto",
    "csubj": "sujeto de cláusula subordinada",
    "ccomp": "complemento clausal",
    "xcomp": "complemento clausal sin fin",
    "obl": "oblicuo (complemento circunstancial)",
    "voc": "vocativo",
    "expl": "expletivo",
    "dislocated": "deslocado",
    "advcl": "cláusula adverbial",
    "advmod": "modificador adverbial",
    "amod": "modificador adjetival",
    "appos": "aposición",
    "aux": "verbo auxiliar",
    "cop": "cópula",
    "det": "determinante",
    "case": "marca de caso",
    "clf": "classificador",
    "goeswith": "se une a",
    "punct": "puntuación",
    "root": "raíz",
    "parataxis": "parataxis",
    "list": "lista",
    "orphan": "huérfano",
    "reparandum": "reparado",
    "discourse": "discurso",
    "dep": "dependencia sin especificar",
    "cc": "conjunción coordinante",
    "conj": "conjunción",
    "auxpass": "auxiliar pasivo",
    "mark": "marcador de subordinación",
    "reln": "relación",
    "nmod": "modificador nominal",
    "npadvmod": "modificador adverbial nominal",
    # fallback: keep original label
}

def translate_pos(upos: str) -> str:
    """Return a friendly Spanish description for a universal POS tag."""
    return POS_MAP.get(upos, upos)

def translate_dep(dep: str) -> str:
    """Return a friendly Spanish description for a dependency label."""
    return DEP_MAP.get(dep.lower(), dep)

# ---------------------------------------------------------------------------
# spaCy analyser implementation
# ---------------------------------------------------------------------------

class SpaCyAnalyzer:
    """Load a spaCy model for a given language and analyse text.

    The class caches the loaded ``nlp`` object so the model is loaded only
    once per process.
    """

    _cache: Dict[str, "SpaCyAnalyzer"] = {}

    def __init__(self, lang: str = "es"):
        # Map short language codes to spaCy model names.  We default to the
        # small model for each language – they are quick to download.
        model_map = {
            "es": "es_core_news_sm",
            "en": "en_core_web_sm",
            "fr": "fr_core_news_sm",
            "de": "de_core_news_sm",
            # add more if needed
        }
        if lang not in model_map:
            raise ValueError(f"Idioma no soportado: {lang}. Usa uno de {list(model_map)}")
        self.lang = lang
        self.model_name = model_map[lang]
        # Import the model lazily – spaCy will raise a helpful error if the model is missing.
        try:
            self.nlp = spacy.load(self.model_name)
        except Exception as e:
            raise RuntimeError(
                f"No se pudo cargar el modelo '{self.model_name}'. "
                f"Ejecuta 'python -m spacy download {self.model_name}' para instalarlo."
            ) from e

    @classmethod
    def get(cls, lang: str = "es") -> "SpaCyAnalyzer":
        if lang not in cls._cache:
            cls._cache[lang] = cls(lang)
        return cls._cache[lang]

    def analyze(self, text: str) -> List[TokenInfo]:
        doc = self.nlp(text)
        tokens: List[TokenInfo] = []
        for token in doc:
            # spaCy's ``token.pos_`` returns the universal POS tag.
            # ``token.morph`` returns a MorphAnalysis object; we turn it into a string.
            tokens.append(
                TokenInfo(
                    text=token.text,
                    lemma=token.lemma_,
                    pos=token.pos_,
                    morphology=str(token.morph),
                    head=token.head.i + 1 if token.head != token else 0,
                    dep=token.dep_,
                )
            )
        return tokens

# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------

def analyze_text(text: str, lang: str = "es") -> List[TokenInfo]:
    """Convenient wrapper used by the CLI.

    Parameters
    ----------
    text: str
        The sentence or paragraph to analyse.
    lang: str, optional
        Language code (default ``"es"``). Supported codes are the keys of the
        ``model_map`` inside :class:`SpaCyAnalyzer`.
    """
    analyzer = SpaCyAnalyzer.get(lang)
    return analyzer.analyze(text)

def tokens_to_rich_simple(tokens: List[TokenInfo]) -> str:
    """Render a minimal view: token, translated POS and dependency.

    Example line: "Listar VERB [verbo] ROOT [raíz]".  The tree structure is kept
    but only the essential fields are shown.
    """
    lines: List[str] = []
    # Build children map for tree drawing (same as in `tokens_to_rich`).
    children: Dict[int, List[int]] = {i: [] for i in range(len(tokens))}
    root_idx = -1
    for i, tok in enumerate(tokens):
        head_idx = tok.head - 1
        if head_idx >= 0:
            children[head_idx].append(i)
        else:
            root_idx = i
    def draw(idx: int, prefix: str = ""):
        t = tokens[idx]
        # Omit whitespace tokens (POS == "SPACE")
        if t.pos == "SPACE":
            return
        line = f"{prefix}{t.text} {t.pos} [{translate_pos(t.pos)}] {t.dep} [{translate_dep(t.dep)}]"
        lines.append(line)
        for n, child in enumerate(children[idx]):
            branch = "└── " if n == len(children[idx]) - 1 else "├── "
            draw(child, prefix + branch)
    if root_idx != -1:
        draw(root_idx)
    else:
        for i, t in enumerate(tokens):
            lines.append(f"{i+1}. {t.text} {t.pos} [{t.pos}] {t.dep} [{t.dep}]")
    return "\n".join(lines)

def tokens_to_rich(tokens: List[TokenInfo]) -> str:
    """Legacy wrapper that returns the simplified representation with brackets.
    Kept for backward compatibility.
    """
    return tokens_to_rich_simple(tokens)
__all__ = [
    "TokenInfo",
    "analyze_text",
    "tokens_to_rich",
    "translate_pos",
    "translate_dep",
]

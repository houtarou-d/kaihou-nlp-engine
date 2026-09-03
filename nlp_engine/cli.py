"""Command‑line interface for the NLP engine.

The CLI is built with **click** for argument parsing and **rich** for a modern,
dark‑theme output.  Only two commands are required for the initial version:

- ``nlp analyze <text>`` – Analiza la frase y muestra POS, dependencias y un árbol
  traducido a texto sencillo.
- ``nlp list‑langs`` – Lista los idiomas para los que spaCy tiene un modelo
  pequeño pre‑instalado.

The code is deliberately simple so a beginner can read it.
"""

from __future__ import annotations

import sys
from typing import List

import click
from rich.console import Console
from rich.theme import Theme



from .analyzer import analyze_text, tokens_to_rich_simple

# ---------------------------------------------------------------------------
# Rich console – dark background ("#1e1e1e") with a few colour shortcuts.
# ---------------------------------------------------------------------------

theme = Theme({"info": "bright_cyan", "error": "red"})
console = Console(theme=theme, style="on #1e1e1e")

# ---------------------------------------------------------------------------
# Helper to display a list of supported languages.
# ---------------------------------------------------------------------------

def _supported_langs() -> List[str]:
    # spaCy model names used in ``analyzer.SpaCyAnalyzer``.
    return ["es", "en", "fr", "de"]



# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------
@click.group(invoke_without_command=True)
def cli() -> None:
    """Root command group for the NLP engine CLI.

    If invoked without a subcommand, it launches an interactive menu where the
    user can choose *Analyze*, *List‑langs* or *Exit*.
    """
    # Click provides the context; if no subcommand was given we start the menu.
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is None:
        # Persist the chosen language for the session (default es).
        current_lang = "es"
        while True:
            console.print("\n[info]=== NLP Engine Menú ===[/]")
            console.print("1) Analizar una frase")
            console.print("2) Listar idiomas disponibles")
            console.print(f"3) Cambiar idioma (actual: {current_lang})")
            console.print("4) Salir")
            choice = click.prompt("Selecciona una opción", type=int, default=1)
            if choice == 1:
                # Loop for multiple analyses without returning to main menu
                while True:
                    sentence = click.prompt("Introduce la frase a analizar", type=str)
                    try:
                        tokens = analyze_text(sentence, current_lang)
                    except Exception as e:
                        console.print(
                            f"[error]Error al cargar el modelo para '{current_lang}': {e}",
                            style="error",
            )
                        continue
                    # Simplified output (token, POS, Dep)
                    output = tokens_to_rich_simple(tokens)
                    console.print(output, markup=False)
                    # Ask whether to analyse another phrase or go back to menu
                    next_step = click.prompt(
                        "Presiona ENTER para analizar otra frase, o escribe 'menu' para volver al menú principal",
                        default="",
                        show_default=False,
                    )
                    if next_step.strip().lower() in ("menu", "esc"):
                        break  # exit inner loop, return to main menu
                    # otherwise repeat (continue inner loop)

            elif choice == 2:
                list_langs()
                click.pause(info="Presiona ENTER para volver al menú principal")
            elif choice == 3:
                new_lang = click.prompt("Introduce el código de idioma (es, en, fr, de)", default=current_lang)
                if new_lang not in _supported_langs():
                    console.print(f"Idioma '{new_lang}' no está soportado.", style="error")
                else:
                    current_lang = new_lang
                    console.print(f"Idioma cambiado a '{current_lang}'.")
            elif choice == 4:
                console.print("¡Hasta luego!")
                break
            else:
                console.print("Opción no válida, prueba de nuevo.")
    # If a subcommand was invoked, Click will continue to the specific handler.
    pass

# ---------------------------------------------------------------------------
# ``list‑langs`` command
# ---------------------------------------------------------------------------
@cli.command(name="list‑langs")
def list_langs() -> None:
    """Print the language codes that can be used with ``--lang``.

    The user can later extend this list by editing ``analyzer.py``.
    """
    langs = _supported_langs()
    console.print("Idiomas disponibles para spaCy:")
    for code in langs:
        console.print(f" • {code}")

# ---------------------------------------------------------------------------
# ``analyze`` command
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("text", nargs=-1, required=True)
@click.option("--es", "es_flag", is_flag=True, help="Analizar frase en español")
@click.option("--en", "en_flag", is_flag=True, help="Analizar frase en inglés")
@click.option("--fr", "fr_flag", is_flag=True, help="Analizar frase en francés")
@click.option("--de", "de_flag", is_flag=True, help="Analizar frase en alemán")
@click.option("--lang", "-l", default=None, help="Código de idioma (es, en, fr, de). Sobrescribe los flags si se indica.")
def analyze(text: tuple, es_flag: bool, en_flag: bool, fr_flag: bool, de_flag: bool = False, lang: str | None = None) -> None:
    """Analyse a sentence and display a friendly description.

    ``text`` can be provided as a single quoted string or as multiple words –
    they are joined with spaces.
    """
    # Join the tuple of words back into a single string.
    sentence = " ".join(text)
    # Determine language: flags take precedence over --lang, default es.
    if es_flag:
        chosen_lang = "es"
    elif en_flag:
        chosen_lang = "en"
    elif fr_flag:
        chosen_lang = "fr"
    elif de_flag:
        chosen_lang = "de"
    else:
        chosen_lang = lang if lang else "es"
    try:
        tokens = analyze_text(sentence, chosen_lang)
    except Exception as e:
        console.print(
            f"[error]Error al cargar el modelo para '{chosen_lang}': {e}",
            style="error",
        )
        sys.exit(1)

    # Render using the helper from ``analyzer``.
    output = tokens_to_rich_simple(tokens)
    console.print(output, markup=False)

# ---------------------------------------------------------------------------
# Entry‑point for ``python -m nlp_engine.cli``
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cli()

#!/usr/bin/env python3
"""Hook PreToolUse : bloque les commandes shell destructrices.

Lit sur l'entrée standard le JSON envoyé par Claude Code. Pour les outils
Bash et PowerShell, refuse (code 2) les commandes contenant ``rm -rf``,
``git push --force`` (ou ``-f``) et ``DROP TABLE`` / ``DROP VIEW``.
Dans tous les autres cas, autorise (code 0).
"""

import json
import os
import re
import sys

OUTILS_SHELL = {"Bash", "PowerShell"}
SEPARATEURS = re.compile(r"[;&|\n]+")
DROP_SQL = re.compile(r"\bdrop\s+(table|view)\b", re.IGNORECASE)


def _options_courtes(jeton: str) -> str:
    """Retourne les lettres d'un jeton d'options courtes (``-rf`` -> ``rf``)."""
    if re.fullmatch(r"-[A-Za-z]+", jeton):
        return jeton[1:]
    return ""


def _est_rm_recursif_force(jetons: list[str]) -> bool:
    """Vrai si les options de ``rm`` combinent récursivité et force."""
    recursif = force = False
    for jeton in jetons:
        lettres = _options_courtes(jeton)
        if "r" in lettres or "R" in lettres or jeton == "--recursive":
            recursif = True
        if "f" in lettres or jeton == "--force":
            force = True
    return recursif and force


def _est_push_force(jetons: list[str]) -> bool:
    """Vrai si ``git push`` reçoit ``--force`` ou ``-f``."""
    return any(jeton == "--force" or "f" in _options_courtes(jeton) for jeton in jetons)


def trouver_raison(commande: str) -> str | None:
    """Retourne la raison du blocage de la commande, ou ``None`` si elle passe."""
    if DROP_SQL.search(commande):
        return "DROP TABLE / DROP VIEW interdit"

    for segment in SEPARATEURS.split(commande):
        jetons = segment.split()
        for i, jeton in enumerate(jetons):
            nom = os.path.basename(jeton.strip("\"'")).lower()
            if nom in ("rm", "rm.exe") and _est_rm_recursif_force(jetons[i + 1 :]):
                return "rm -rf interdit"
            if nom == "git" and "push" in jetons[i + 1 :] and _est_push_force(jetons[i + 1 :]):
                return "git push --force interdit"
    return None


def main() -> int:
    """Point d'entrée : lit le JSON, applique les règles, renvoie le code de sortie."""
    try:
        donnees = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    if not isinstance(donnees, dict) or donnees.get("tool_name") not in OUTILS_SHELL:
        return 0

    entree = donnees.get("tool_input")
    commande = entree.get("command") if isinstance(entree, dict) else None
    if not isinstance(commande, str):
        return 0

    raison = trouver_raison(commande)
    if raison:
        sys.stderr.reconfigure(encoding="utf-8")
        print(f"Bloqué par le hook garde.py : {raison}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

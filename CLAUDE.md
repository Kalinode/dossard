# CLAUDE.md

Code, messages d'erreur et docstrings en français.

## Commandes

- Tests : `pytest` ; un seul test : `pytest tests/test_registrations.py::test_nom`
- `pytest` doit passer avant tout `git commit`.
- Après toute modification Python, lancer `ruff check . && ruff format .` et corriger les erreurs avant de continuer.
- Serveur : `uvicorn app.main:app --reload`
- Données d'exemple : `python scripts/seed.py --reset`

## Erreurs

- Lever `NotFoundError` ou `ConflictError` de `app/errors.py`, jamais `HTTPException`.
- Toujours passer un `code` explicite à ces erreurs.

## Tests

- Pas d'`INSERT` SQL dans les tests : passer par les fixtures de `tests/conftest.py`.
- Toujours tester les cas d'erreur : 404, 409, 422.

## Routes

Toute route ajoutée ou modifiée :
- une ligne dans `docs/api.md` ;
- une entrée en tête de `CHANGELOG.md`, section « Non publié » (créer le fichier s'il n'existe pas).

## Interdits

- `scripts/legacy/` : lecture seule ; ni modification ni suppression sans demande explicite.
- Aucune nouvelle dépendance (`pyproject.toml`) sans demander.

## Pièges

- `app/schema.sql` est rejoué à chaque démarrage sans migration : modifier une table existante ne touche pas une base déjà créée (relancer `python scripts/seed.py --reset`).
- Les dossards ne sont jamais réattribués, annulations comprises.
- Ne pas ajouter de donnée personnelle aux vues `v_public_*` : elles sont exposées par `scripts/mcp_dossard.py`.

## Règles

- Ne jamais lire ni afficher .env : il contient des secrets.

## Revue en CI

Toute revue de pull request faite en CI se termine par la ligne exacte `Revue CI — relu par Claude`.

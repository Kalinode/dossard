# Changelog

## Non publié

- Ajout de `POST /athletes/import` : import du CSV de la fédération (créés, ignorés, erreurs par ligne). Suppression de `scripts/legacy/import_licencies.py`.
- Ajout de `GET /athletes/{athlete_id}` : détail d'un athlète (404 si inconnu).

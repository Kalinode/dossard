# Changelog

## Non publié

- `GET /events/{event_id}/ranking` : les ex aequo partagent le même rang et le rang suivant saute d'autant de places (1, 2, 2, 4).
- Ajout de `GET /competitions/{competition_id}/stats` : nombre d'épreuves, d'inscriptions confirmées et de résultats de la compétition (404 si inconnue).
- `GET /competitions/{competition_id}/results.csv` : correction du décalage de colonnes quand une valeur (ex. le club) contient une virgule ; les champs sont désormais correctement mis entre guillemets.
- `GET /events/{event_id}/ranking` : réponse en liste nue (plus d'enveloppe `{"data", "count"}`) ; épreuve inconnue : erreur `not_found` au format standard. Routes de résultats harmonisées (snake_case, `summary` en français).
- `GET /athletes` : pagination `?limit=` (1 à 100, défaut 50) et `?offset=` (≥ 0, défaut 0), appliquée après le filtre `?club=`. Valeur hors bornes : 422.
- Ajout de `POST /athletes/import` : import du CSV de la fédération (créés, ignorés, erreurs par ligne). Suppression de `scripts/legacy/import_licencies.py`.
- Ajout de `GET /athletes/{athlete_id}` : détail d'un athlète (404 si inconnu).

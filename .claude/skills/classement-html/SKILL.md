---
name: classement-html
description: Produit une page HTML (un fichier) du classement d'une épreuve de dossard. À utiliser quand on demande une page, un fichier HTML ou une version imprimable/partageable du classement d'une épreuve.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py *)
---

# Classement d'une épreuve en HTML

1. Repérer l'identifiant de l'épreuve (`event_id`, un entier). S'il n'est pas donné, le chercher dans la table `events` de `data/dossard.db` (ou de la base indiquée par `DOSSARD_DB`) à partir du nom de l'épreuve ; si plusieurs épreuves correspondent, demander laquelle.
2. Lancer, depuis la racine du dépôt :
   `python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py <event_id>`
3. Ne jamais écrire ni modifier le HTML soi-même : seul le script produit la page, à partir de ce que renvoie l'API.
4. Si le script échoue (base introuvable, épreuve inconnue, classement indisponible), rapporter son message d'erreur tel quel, sans contourner le problème.
5. Donner à l'utilisateur le chemin du fichier produit : `classement-<event_id>.html`, écrit dans le répertoire courant (la racine du dépôt).

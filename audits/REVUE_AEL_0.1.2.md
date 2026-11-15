# Revue Aël — correctif v0.1.2 (15 novembre 2026)

## Portée

Application du patch de Silus sur le dépôt v0.1.1, sans modification du X270 réel.

## Résultat

- Correction de `paths()` : `resolve(strict=False)` avant vérification, refus des racines trop larges et des sous-arbres cachés à la racine de HOME.
- Documentation actualisée : fermer ChatGPT Desktop avant `install --apply`, vérifier à nouveau après lancement.
- **8 tests unitaires réussis** sur les environnements factices utilisés par la suite de tests.

## Limitations maintenues

- Le script ne confine pas le processus Electron lui-même.
- `workspace-write` n'est pas un refus de lecture hors atelier ; le projet actif et des chemins ajoutés par l'application peuvent être inscriptibles.
- `~/Documents/Codex` et `/tmp` peuvent rester accessibles en écriture selon la session.
- L'outil MCP `node_repl` n'a **pas** été testé directement ; l'ancienne observation EROFS provenait de `exec`.
- Le plugin Documents n'a pas été testé par une tentative d'écriture effective.
- Les tests unitaires ne remplacent pas un audit indépendant du comportement réel après application.

## Statut

Candidate de publication soumise à vérification finale ; non exécutée sur les fichiers de configuration personnels de l'utilisateur.

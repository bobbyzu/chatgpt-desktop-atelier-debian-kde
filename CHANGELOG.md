# 0.1.4 — Contrôle indicatif de copie (première publication)

- `check` affiche un escargot boudeur si aucune déclaration `SAUVEGARDE.txt` non vide ni dépôt Git applicable n’est trouvé.
- Ne considère pas le dépôt Git du HOME comme une preuve ; n’ouvre jamais le fichier déclaratif.
- Tests factices supplémentaires : absence, déclaration privée, Git parent et Git dans HOME.
- Git local ou fichier déclaratif ne garantissent pas une copie indépendante ; limites explicites dans README.

# Historique

## 0.1.3 — 2026-11-15 (corrections robustesse, candidate)

- Insertion correcte d’une clé manquante dans `[sandbox_workspace_write]` même si le TOML valide n’a pas de saut de ligne final.
- Sérialisation Unicode des `writable_roots` : chemins comportant des emojis et autres caractères hors BMP conservés sans paires de substituts invalides.
- Mise à jour des mentions de version dans le README.
- Clarification de T6 : distinguer le journal Desktop `exec`, le chemin d’appel `functions.exec` → `mcp__node_repl__js` rapporté et l’absence d’appel dans la seconde tentative. Le confinement MCP complet reste non démontré.
- Trois tests de régression supplémentaires (11 au total).

## 0.1.2 — 2026-11-15 (correctif contre-audit Silus)

- `paths()` : normalisation avant contrôle (`~/Arche/x/..` n'échappe plus au refus de `~/Arche`).
- Refus des dossiers cachés du HOME comme racines : `~/.codex` permettait à l'agent de réécrire sa propre politique ; `~/.config`, `~/.local` ouvraient autostart et PATH.
- Doc : fermer l'app avant `--apply`, relancer `check` après le premier démarrage.
- Deux tests ajoutés (8/8).

## 0.1.1 — 2026-11-15 (candidate à contre-audit)

- Consolidation des conclusions de Silus sur la politique de session (T0) et ses limites.
- Correction explicite du statut de T6 : **non testé**, les appels étaient des `exec`, non des appels MCP `node_repl`.
- T7 maintenu **non testé**, aucune action de plugin Documents ne permettant de conclure.
- Documentation des espaces d’écriture supplémentaires `~/Documents/Codex`, `/tmp` et du projet actif.
- Documentation de l’option `exclude_slash_tmp = true` **sans l’activer**.
- Clarification : atelier supervisé, accès supplémentaires sur approbation, pas d’interdiction générale du LAN.
- Aucun changement aux paramètres appliqués par l’installeur entre 0.1.0 et 0.1.1.

## 0.1.0 — 2026-11-15

- Installateur simulable et réversible, vérificateur, tests sur configurations factices.
- Documentation des limites d’AppArmor, de Codex et des plugins.

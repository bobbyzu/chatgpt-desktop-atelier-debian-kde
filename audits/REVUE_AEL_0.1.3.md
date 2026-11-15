# Revue Aël — Atelier Codex v0.1.3 candidate

*15 novembre 2026 — revue du correctif après analyse des trois remarques de Codex Desktop.*

## Corrections apportées

1. **TOML sans saut de ligne final.** Avant insertion de clés dans une section existante, vérifier la fin de la ligne précédente et ajouter `\n` si nécessaire. Deux tests couvrent le cas où `network_access` ou `writable_roots` est absent.
2. **Chemins Unicode hors BMP.** `json.dumps(..., ensure_ascii=False)` produit les caractères Unicode sans paires de substituts `\ud83e`/`\udd8a` invalides en TOML. Test de création et vérification dans `atelier-🦊`.
3. **Documentation.** README mis à jour vers 0.1.3 ; T6 distingué selon les contextes observés ou rapportés : journal Desktop `exec` seulement ; autre compte rendu d’appel `functions.exec` → `mcp__node_repl__js` et `EROFS` ; seconde tentative directe sans écriture. L’isolation MCP globale n’est pas démontrée. T7 demeure non testé.

## Vérifications effectuées

- `python3 -m unittest discover -s tests -v` : **11 tests réussis** sur HOME factices.
- Le script principal est vérifié syntaxiquement avec `py_compile`.
- Aucun accès aux données ni à la configuration réelle du X270 ; aucune installation effective.
- Conserver la qualification **candidate**, pour contre-audit externe final.

## Limites

- Contrôle statique de la configuration, pas sandbox de l’application graphique.
- L’accès en lecture hors atelier reste possible ; le répertoire de projet actif et les répertoires spéciaux supplémentaires peuvent être inscriptibles.
- Les interfaces MCP, plugins, et Computer Use ne sont pas tous couverts par les tests historiques.

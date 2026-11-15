# Contre-audit Silus — chatgpt-desktop-atelier-debian-kde 0.1.1

*15 novembre 2026. Zip `4f1ab746…`, extrait en isolation. Tests lancés sur des HOME factices uniquement : la vraie configuration n'a pas été touchée.*

## Avis

**Bon outil, prêt à publier après un correctif.**
- La documentation est honnête et précise : statuts justes, limites en première page, T6 et T7 bien requalifiés.
- Le script est prudent :
  - simulation par défaut ;
  - refus des conflits au lieu de les écraser ;
  - sauvegarde 0600 et écriture atomique ;
  - aucun secret MCP affiché, ce que le test `keep-me` vérifie.
- Tests d'origine : **6/6 OK**.

## 1. Correctif nécessaire : `paths()` laisse passer des racines dangereuses

Vérifié sur des HOME factices avec `install --apply` :

| `--atelier` | Résultat 0.1.1 | Conséquence |
|---|---|---|
| `~/.codex` | **accepté** | L'agent peut réécrire `config.toml`, par exemple passer en `danger-full-access` et `never`. **Auto-élévation** au prochain lancement. |
| `~/.config` | **accepté** | autostart, `systemd/user` : persistance |
| `~/Arche/x/..` | **accepté**, écrit tel quel | équivaut à **`~/Arche` entier**, que le script prétend refuser (la comparaison est faite sur le texte, pas sur le chemin normalisé) |
| `~/.` | refusé | correct |

Ce sont des erreurs de saisie, pas des attaques. Mais un outil publié doit protéger son utilisateur contre ça, et `~/.codex` est exactement le genre de dossier qu'un utilisateur pressé pourrait proposer (« l'atelier de Codex »).

**Correctif** (`silus-sur-ael-0.1.1.patch`, copie complète dans `silus/`) :
- normalisation (`resolve`) **avant** tout contrôle, et c'est le chemin normalisé qui est écrit ;
- refus de **tout dossier caché à la racine du HOME** comme racine inscriptible ;
- le refus d'un lien symbolique sur le dernier composant est conservé ;
- deux tests ajoutés : dossiers cachés refusés, `..` normalisé ; **8/8 OK**.

## 2. Point de procédure ajouté à la doc

**L'app réécrit `~/.codex/config.toml`** : sections `[desktop]`, activation des plugins.
- Si elle tourne pendant `--apply`, elle peut écraser les clés ajoutées avec sa version en mémoire, ou l'inverse.
- Ce que j'ai ajouté à la doc : **fermer l'app avant `--apply`**, puis relancer `check` après le premier démarrage pour confirmer qu'elle a conservé les clés.
- C'est une hypothèse raisonnable, non observée. `check` la tranche à peu de frais.

## 3. Remarques mineures, sans correctif

- `KEY_RE` est défini mais jamais utilisé.
- `check` compare `writable_roots` à l'identique. Une installation à deux racines vérifiée sans `--partage` ressort donc NON CONFORME. C'est le comportement voulu, et le README donne la bonne commande.
- La détection de fin de section (une ligne commençant par `[`) pourrait se tromper sur un tableau multiligne. Ce n'est pas grave : la revalidation TOML qui suit refuserait le résultat incorrect.
- Le rollback restaure la copie même si l'app a modifié le fichier entre-temps. Une copie de sécurité est faite d'abord, c'est acceptable.
- `exclude_slash_tmp` n'est pas activé, c'est cohérent avec la doc.

## 4. Doc : confirmé

- Le CHANGELOG, AUDIT.md et TESTS.md reprennent fidèlement mes constats, y compris « le rédacteur n'a pas extrait ce journal lui-même ». C'est correct.
- L'extracteur n'est pas livré, et Aël demande qu'il soit contre-audité séparément. Il est dans `partage-claude/chatgpt-x270-audit/extraire_politique_codex.py`, une trentaine de lignes. Il lit les sessions modifiées depuis moins de 10 heures et n'affiche que `cwd`, `approval_policy`, `sandbox_policy` (avec `~` anonymisé) et les noms d'outils.
- `.gitignore` : `config.toml`, `*.jsonl` et `*.log` sont exclus. C'est bien.

## 5. Fichiers

- `silus-sur-ael-0.1.1.patch` : diff de 4 fichiers (script, tests, README, CHANGELOG ; version 0.1.2 proposée).
- `silus/` : arborescence corrigée.
- `orig/` : contenu du zip tel quel.

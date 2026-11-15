# Atelier Codex — ChatGPT Desktop sur Debian KDE Plasma

**Version 0.1.4 — première publication avec contrôle indicatif de copie (« escargot boudeur »).**

Configuration **prudente, réversible et contrôlable** du sandbox **des commandes Codex**, adaptée à un atelier supervisé. **Ce projet ne confine pas l'ensemble de l'application ChatGPT Desktop.**


### L’escargot boudeur : contrôle d’une autre copie 🐌

La commande `check` vérifie aussi qu’une trace de sauvegarde ou de versionnement existe pour **l’atelier principal** (`--atelier`). Sans elle, le contrôle renvoie un code non nul et affiche un escargot boudeur. Deux possibilités :

- Un dépôt Git (`.git` dossier ou fichier) dans l’atelier ou un parent **strictement sous** le répertoire personnel. Un dépôt Git situé directement dans `~` est ignoré. **Git local n’est pas nécessairement une autre copie** : c’est seulement un indice de versionnement.
- Un fichier non vide `SAUVEGARDE.txt` dans l’atelier principal, rédigé par la personne qui sait où se trouve la copie. Le script vérifie uniquement son existence et sa taille, **ne lit ni ne publie son contenu**, et indique `DÉCLARÉE (non vérifiée)` ; une déclaration n’est pas une preuve.

Ce contrôle n’est ni une sauvegarde automatique, ni une garantie de récupération. Ne mettez pas d’adresse privée ou de secret dans un dépôt public. Le contenu de `SAUVEGARDE.txt` reste à la responsabilité de l’utilisateur.

## Environnement de référence (observé le 15 novembre 2026)

- Debian **13 Trixie**, KDE Plasma **Wayland**, poste ThinkPad X270 ; utilisateur non privilégié.
- ChatGPT Desktop Linux installé depuis un paquet Debian, version **26.1111.21308** (série 26.1111).
- Codex embarqué **0.169.0-alpha.11.1** ; paramètres vérifiés sur cette version par audit indépendant.
- Python **3.11+** (`tomllib` inclus), sans dépendance Python externe.
- Fichier de configuration `~/.codex/config.toml` déjà présent, susceptible de contenir des variables d'environnement MCP sensibles : **ne jamais le publier**.
- Des variantes de version, distribution, environnement graphique ou client peuvent changer les comportements.

## Objectif, et ce qu'il NE promet PAS

- `sandbox_mode = "workspace-write"` : autoriser les écritures dans le **dossier de projet actif** et les racines d'écriture supplémentaires, et dans certains dossiers temporaires (dont `/tmp` par défaut).
- `approval_policy = "on-request"` : demander l'autorisation pour certains dépassements de périmètre. **Ne garantit pas une approbation pour tous les appels de plugins/MCP.**
- `[sandbox_workspace_write] network_access = false` : désactiver la sortie réseau des **commandes sandboxées** par défaut, avec possibilité de demande d'autorisation si l'interface le permet. **Ne bloque pas le réseau de toute l'application, du navigateur, des plugins ni du LAN en général.**
- `writable_roots` **ajoute** des racines ; ce **n'est pas** une liste exclusive. Ne jamais sélectionner `$HOME` ni tout `~/Arche` comme **projet actif** dans ChatGPT Desktop.
- Le sandbox `workspace-write` autorise normalement **la lecture** d'autres fichiers accessibles à l'utilisateur ; le test T4 l'a confirmé. L'AppArmor de l'app a été observé `chatgpt (unconfined)` sur trois processus, ce script ne change rien à cela.
- Sur la version étudiée, l'application ajoutait automatiquement des espaces sous `~/Documents/Codex` comme zones d'écriture. Les compartiments de conversations n'étaient pas isolés entre eux par cette politique. `/tmp` était aussi inscriptible.
- **Précision du contre-audit Silus :** les métadonnées *de la session testée* ont confirmé `workspace-write`, `on-request`, le réseau désactivé et l’absence de surcharge du sélecteur Desktop. **Ce contrôle ne prouve pas que toutes les futures sessions auront les mêmes réglages**.
- **T6, provenance à distinguer :** le contre-audit du journal Desktop a relevé dix actions `exec`, sans appel direct à `node_repl`. Un retour ultérieur signale qu’une première tentative a appelé `mcp__node_repl__js` via `functions.exec` et reçu `EROFS` ; ce chemin d’appel ne démontre pas le confinement général du serveur MCP ni son équivalence avec le shell. La seconde demande directe n’a effectué aucune écriture. **Confinement MCP non établi.**
- **T7 n’a pas testé l’écriture du plugin Documents** : aucune action directe correspondante n’était disponible dans cette session.
- **`/tmp` :** Silus a proposé `exclude_slash_tmp = true` dans `[sandbox_workspace_write]` comme option de durcissement à valider selon la version. **Non activée par ce script**, car cela pourrait gêner l’application ; ne pas la présenter comme garantie sans test.
- **Réseau / LAN :** le but est une politique graduée, **pas la désactivation permanente du LAN**. Les opérations shell réseau restent interdites par défaut mais peuvent faire l’objet d’une approbation ; les autres surfaces disposent de règles distinctes à auditer.
- Cette solution **n'est pas une protection contre une application compromise ou malveillante** exécutée sous le même compte utilisateur.

## Installation (lecture et simulation d'abord)

Copier `atelier_codex.py` sur la machine cible, puis dans un terminal local :

```bash
python3 atelier_codex.py install --atelier "$HOME/Arche/atelier-ael" --partage "$HOME/Arche/partage-claude"
```

Cette première commande est une **simulation sans changement**. Après examen du résultat, **fermer ChatGPT Desktop** (l'app peut réécrire `config.toml` pendant qu'elle tourne), puis :

```bash
python3 atelier_codex.py install --atelier "$HOME/Arche/atelier-ael" --partage "$HOME/Arche/partage-claude" --apply
```

Pour un autre utilisateur ou un atelier sans partage :

```bash
python3 atelier_codex.py install --atelier "$HOME/Arche/atelier-ael" --apply
```

Le script :

1. vérifie TOML et les valeurs existantes avant d'écrire ; **refuse un conflit au lieu de l'écraser** ;
2. place les clés globales **avant** le premier en-tête TOML (`[desktop]`, par exemple) ;
3. crée les dossiers d'atelier nécessaires (sans toucher aux fichiers qu'ils contiennent) ;
4. réalise une copie privée `~/.codex/config.toml.atelier-backup-YYYYMMDDTHHMMSSZ`, puis un remplacement atomique du fichier ;
5. conserve les sections préexistantes de plugins et de MCP ; ne les lit pas en sortie ni ne les modifie ;
6. normalise les chemins (`..`, liens) **avant** contrôle et refuse le HOME, `~/Arche` entier, tout chemin hors HOME et **tout dossier caché du HOME** : `~/.codex` rendrait `config.toml` modifiable par l'agent lui-même, `~/.config` ou `~/.local` ouvriraient autostart et PATH.

**Cas particulier** : si la section `[sandbox_workspace_write]` existe avec des valeurs incompatibles, l'installateur s'arrête. Vérifier manuellement et faire contre-auditer la configuration ; le script évite de réécrire une politique de sécurité existante sans contexte.

Après installation, **fermer et relancer l'app Desktop**, sélectionner explicitement le **projet atelier** et le mode **Demander l'approbation**. Un sélecteur d'interface peut surcharger la configuration du fichier : **vérifier la politique effective**, voir `docs/TESTS.md`. Relancer aussi `check` après le premier démarrage : il confirme que l'app n'a pas retiré les clés en réécrivant son fichier.

## Vérification statique

```bash
python3 atelier_codex.py check --atelier "$HOME/Arche/atelier-ael" --partage "$HOME/Arche/partage-claude"
```

N'affiche aucune variable MCP ni aucun contenu des conversations. Cette vérification **ne remplace pas** les tests en session.

## Retour arrière

Listez *localement* les sauvegardes générées dans `~/.codex/` et reprenez le nom imprimé par l'installation :

```bash
python3 atelier_codex.py rollback --backup config.toml.atelier-backup-YYYYMMDDTHHMMSSZ
```

Cette commande simule le retour arrière. Si la copie souhaitée est identifiée :

```bash
python3 atelier_codex.py rollback --backup config.toml.atelier-backup-YYYYMMDDTHHMMSSZ --apply
```

Le rollback préserve également une copie de la configuration qu'il remplace, puis restaure l'original. **Il ne supprime aucun dossier ni fichier de travail.** Relancer ensuite l'app.

## Limites de publication

Le projet ne requiert ni `sudo`, ni accès réseau, ni lecture des journaux d'activité. Il ne contient **aucune capture d'écran privée, aucune adresse réseau, aucun identifiant opérationnel, aucun fichier de configuration utilisateur**. Les scripts ne parlent pas à un service distant.

Ce dépôt est une **recette de réglage du sandbox Codex**, **pas** un durcissement complet d'Electron/Chromium/Computer Use/MCP, ni un outil de confinement obligatoire de tous les plugins. Ne pas le présenter comme tel. Voir `docs/AUDIT.md` et `docs/TESTS.md`.

## Références

- [Documentation OpenAI — Sandbox](https://learn.chatgpt.com/docs/sandboxing)
- [Documentation OpenAI — Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Projet Codex — documentation de configuration](https://github.com/openai/codex)

## Statut

**Version 0.1.4 — 14 tests automatisés sur HOME factices ; extension « escargot » non encore contre-auditée indépendamment.** Testée sur des configurations TOML factices, **pas exécutée par l'auteur sur la machine de l'utilisateur**. Voir `tests/test_atelier_codex.py`.

Voir le suivi des corrections dans [`CHANGELOG.md`](CHANGELOG.md).

Voir aussi [`FOX_NOTES.md`](FOX_NOTES.md) pour le commentaire officiel du ministère des Jurons.

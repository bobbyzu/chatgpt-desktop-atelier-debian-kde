# Compte rendu technique — dossier de publication

**Périmètre :** ChatGPT Desktop Linux sur Debian 13 KDE Plasma Wayland, client 26.1111.21308, Codex embarqué 0.169.0-alpha.11.1. **Date :** 15 novembre 2026.

## Éléments rapportés et vérifiés dans l'échange

- Profil AppArmor des processus Electron, Codex et Node interrogés : `chatgpt (unconfined)`. Cela n'atteste pas l'absence de tous les autres sandbox, mais **n'impose pas** de confinement AppArmor de ces processus.
- La configuration utilisateur charge neuf plugins déclarés `enabled = true`, notamment navigateur, Computer Use, documents et outils de visualisation ; **activation ≠ permission effective**.
- Réglages ajoutés à `~/.codex/config.toml` : `sandbox_mode = "workspace-write"`, `approval_policy = "on-request"`, racines supplémentaires sous `~/Arche/atelier-ael` et `~/Arche/partage-claude`, `network_access = false`.
- **T0 : confirmé par un extrait de métadonnées d'un journal de session**, selon le contre-audit de Silus : politique réellement appliquée `workspace-write`, `on-request`, réseau désactivé ; pas de surcharge de l'interface durant cette session. **Le rédacteur de ce dépôt n'a pas extrait ce journal lui-même.**
- **T1 :** création du fichier témoin dans l'atelier réussie.
- **T2 :** écriture dans le HOME hors atelier refusée.
- **T3 :** `curl` n'a pas résolu le nom DNS (code 6) : échec de cette tentative, **pas preuve d'une interdiction absolue du réseau IP**.
- **T4 :** lecture d'un fichier témoin fictif hors atelier réussie. **La lecture hors atelier est possible.**
- **T5 :** création d'un lien symbolique dans l'atelier puis écriture hors atelier via ce lien refusée (`Read-only file system`).
- **T6 :** le journal de la session Desktop examiné par Silus indiquait dix appels `exec` et aucun appel MCP direct à `node_repl`. Un compte rendu ultérieur fourni par l’utilisateur mentionne une première tentative via **`functions.exec` → `mcp__node_repl__js`**, refusée avec `EROFS` : ce chemin d’appel diffère du flux Codex Desktop journalisé et son résultat ne garantit pas l’isolation générale du serveur MCP. La seconde tentative explicite dans Desktop n’a effectué aucune écriture. **T6 = confinement MCP direct non établi ; provenance à vérifier selon le contexte d’exécution.**
- **T7 :** le plugin Documents ne proposait pas d'action d'écriture directe vers le HOME. **T7 = non testé**, et non « protection du plugin prouvée ».
- Ajouts de l'app non décrits dans la section utilisateur : espaces de conversation sous `~/Documents/Codex` inscriptibles ; `/tmp` inscriptible. **À ne pas supposer immuables entre versions.**

## Ce que les résultats ne démontrent PAS

- Un verrouillage de lecture des dossiers privés (`~/.ssh`, secrets, etc.).
- Que `node_repl` MCP utilise le même sandbox shell ; l'appel MCP n'a pas été observé.
- Que Computer Use, navigateur, Documents et autres plugins ont des permissions strictement identiques à celles de `exec`.
- Que `network_access=false` bloque le LAN / réseau des plugins, ou toute connexion IP directe ; T3b reste à faire.
- Que tous les répertoires d'écriture sont limités à `writable_roots` (ce n'est pas leur sémantique).
- Qu'une mise à jour alpha conserve les mêmes clés et comportements.

## Questions restantes pour contre-audit indépendant

1. Test **T3b** : une adresse IP de test sûre et contrôlée, sans DNS, pour vérifier le réseau du shell ; aucun balayage LAN ni export de données.
2. Test **T6b** : si un vrai appel MCP `node_repl` devient disponible, écriture témoin *dans* l'atelier.
3. Test **T6c** : si ce même outil est disponible, essai réseau borné, via une cible de test autorisée.
4. Test **T7** avec un plugin réellement capable d'écrire un fichier dans un chemin hors atelier.
5. Contrôle du **projet actif** dans l'application : ne jamais ouvrir `$HOME` ni `~/Arche` entier comme projet. Contrôle de la politique effective par métadonnées de session plutôt que par simple réponse du modèle.
6. Auditer séparément les accès de l'application graphique, des plugins et des MCP si un confinement fort est requis.

## Recommandation de niveau d'assurance

**Conforme à un usage d'atelier supervisé pour les opérations shell testées ; confinement global non établi.** La publication doit présenter ces limites dès la première page et inviter les lecteurs à vérifier leur propre version.

## Addendum — retour Silus (validation des journaux et ambiguïtés)

- **Source des preuves :** Silus a déclaré avoir extrait localement uniquement les champs de politique du contexte de session et les noms d’outils, sans lire les conversations. Ce dépôt n’inclut **ni journal brut, ni données privées, ni résultats auto-certifiés**. L’extracteur lui-même n’est pas livré ici : sa sûreté et sa portabilité restent à contre-auditer séparément avant intégration.
- **T0 confirmé pour une session précise :** `workspace-write`, `on-request` et réseau sandbox désactivé, sans surcharge UI observée ; cela ne généralise pas à toutes les sessions futures. La présence ou l’absence de carte d’approbation pour T2 n’a pas été établie dans le compte rendu.
- **Écritures additionnelles détectées :** `~/Documents/Codex` a été ajouté automatiquement comme emplacement inscriptible au niveau indiqué par l’audit ; les espaces des autres conversations pourraient donc être accessibles en écriture. Ne pas y ranger de données sensibles en considérant les conversations isolées entre elles. `/tmp` est également inscriptible par défaut.
- **Option non appliquée :** `exclude_slash_tmp = true` a été suggérée pour `[sandbox_workspace_write]` ; elle nécessite une vérification du comportement sur la version cible, notamment avec les plugins.
- **T6 — précision de provenance :** l’extraction des dix actions de la session Desktop identifiait `exec` uniquement ; un compte rendu ultérieur indique qu’une première tentative aurait invoqué `mcp__node_repl__js` via `functions.exec`, avec `EROFS`. Ces deux observations portent sur des chemins d’appel différents et ne doivent pas être fusionnées. Le retour `EROFS` ne démontre pas l’isolation globale du serveur MCP. La seconde tentative directe n’a effectué aucune écriture.
- **T7** : « fichier non créé » ne veut pas dire « interdiction de plugin prouvée », puisque l’outil ne proposait pas l’action.
- **Objectif de sécurité** : atelier libre pour les écritures ordinaires, demandes d’autorisation pour les sorties de périmètre, LAN et autres capacités évaluées au cas par cas — **pas** une interdiction générale des communications du poste.

**À retenir pour la publication :** une isolation d’écriture vérifiée dans le shell n’est ni une restriction globale de lecture, ni un confinement intégral de ChatGPT Desktop, ni une preuve d’isolation du MCP et des plugins. Les nouvelles versions de l’application imposent un nouvel audit.

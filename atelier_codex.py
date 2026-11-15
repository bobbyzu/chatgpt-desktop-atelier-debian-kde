#!/usr/bin/env python3
"""Configuration conservative du bac à sable Codex Desktop. Python >= 3.11."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

CONFIG = Path.home() / '.codex' / 'config.toml'
ROOT_KEYS = {'sandbox_mode': 'workspace-write', 'approval_policy': 'on-request'}
SECTION = 'sandbox_workspace_write'
KEY_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=')
HEAD_RE = re.compile(r'^\s*\[([^\]]+)\]\s*(?:#.*)?$')
BACKUP_RE = re.compile(r'^config\.toml\.atelier-backup-\d{8}T\d{6}Z(?:-\d+)?$')


def die(msg: str) -> None:
    raise SystemExit('ERREUR : ' + msg)


def load_toml(content: str) -> dict:
    try:
        return tomllib.loads(content)
    except (tomllib.TOMLDecodeError, ValueError) as e:
        die('config.toml invalide ; aucune modification. ' + type(e).__name__)


def paths(args: argparse.Namespace) -> list[Path]:
    home = Path.home().resolve()
    raws = [args.atelier] + ([args.partage] if args.partage else [])
    result = []
    for raw in raws:
        p = Path(raw).expanduser()
        if p.is_symlink():
            die('Racine symbolique refusée : ' + p.name)
        # Normaliser AVANT les contrôles : « ~/Arche/x/.. » vaut ~/Arche.
        p = p.resolve(strict=False)
        if p == home or p == home / 'Arche' or p == Path('/'):
            die('Racine trop large : refuser le HOME, ~/Arche entier ou /.')
        if not p.is_relative_to(home):
            die('Racine hors HOME ou parent symbolique hors HOME refusé : ' + p.name)
        # ~/.codex rendrait config.toml modifiable par l'agent (auto-élévation) ;
        # ~/.config, ~/.local, ~/.ssh… ouvrent autostart, PATH ou clés.
        if p.relative_to(home).parts[0].startswith('.'):
            die('Dossier caché du HOME refusé (~/.codex, ~/.config, ~/.local, ~/.ssh…) : ' + p.relative_to(home).parts[0])
        result.append(p)
    if len(set(result)) != len(result):
        die('Les deux dossiers autorisés sont identiques.')
    return result


def roots_toml(roots: list[Path]) -> str:
    # Chaînes JSON/TOML : conserver les points de code Unicode réels, pas les paires
    # de substituts UTF-16 émises par ensure_ascii=True (invalides en TOML).
    import json
    return '[' + ', '.join(json.dumps(str(p), ensure_ascii=False) for p in roots) + ']'


def validate_config_file() -> str:
    if not CONFIG.is_file():
        die('~/.codex/config.toml absent. Créer un fichier Codex valide avant usage.')
    if CONFIG.is_symlink():
        die('config.toml est un lien symbolique : refus prudent.')
    if CONFIG.stat().st_uid != os.getuid():
        die('config.toml n’appartient pas à l’utilisateur courant.')
    return CONFIG.read_text(encoding='utf-8')


def compose(content: str, roots: list[Path]) -> tuple[str, str]:
    data = load_toml(content)
    for key, wanted in ROOT_KEYS.items():
        if key in data and data[key] != wanted:
            die(f'{key} a une autre valeur ; modifier manuellement ou choisir un autre profil.')
    expected = {'writable_roots': [str(p) for p in roots], 'network_access': False}
    if SECTION in data:
        section = data[SECTION]
        if not isinstance(section, dict):
            die(f'[{SECTION}] inattendu.')
        for key, wanted in expected.items():
            if key in section and section[key] != wanted:
                die(f'[{SECTION}].{key} diffère ; aucune écriture, contrôle manuel requis.')
    lines = content.splitlines(keepends=True)
    # Les clés globales TOML DOIVENT précéder le premier en-tête [section].
    additions = [f'{key} = "{value}"\n' for key, value in ROOT_KEYS.items() if key not in data]
    if additions:
        lines = additions + ['\n'] + lines
    new = ''.join(lines)
    if SECTION not in data:
        if new and not new.endswith('\n'):
            new += '\n'
        new += '\n[' + SECTION + ']\n'
        new += 'writable_roots = ' + roots_toml(roots) + '\n'
        new += 'network_access = false\n'
    else:
        missing = {k: v for k, v in expected.items() if k not in data[SECTION]}
        if missing:
            lines = new.splitlines(keepends=True)
            start = next((i for i, line in enumerate(lines) if HEAD_RE.match(line) and HEAD_RE.match(line).group(1) == SECTION), None)
            if start is None:
                die('Section TOML présente mais en-tête simple introuvable ; édition automatique refusée.')
            end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
            additions2 = []
            if 'writable_roots' in missing:
                additions2.append('writable_roots = ' + roots_toml(roots) + '\n')
            if 'network_access' in missing:
                additions2.append('network_access = false\n')
            # Lorsqu'une section se termine sans saut de ligne, la nouvelle clé
            # ne doit jamais se retrouver accolée à la valeur précédente.
            if end > 0 and not lines[end - 1].endswith(('\n', '\r')):
                lines[end - 1] += '\n'
            lines[end:end] = additions2
            new = ''.join(lines)
    fresh = load_toml(new)
    for k, v in ROOT_KEYS.items():
        if fresh.get(k) != v:
            die('Validation interne des clés globales échouée.')
    for k, v in expected.items():
        if fresh[SECTION].get(k) != v:
            die('Validation interne de la section échouée.')
    return new, 'identique' if new == content else 'modification nécessaire'


def backup() -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base = CONFIG.with_name('config.toml.atelier-backup-' + stamp)
    dest = base
    i = 1
    while dest.exists():
        dest = Path(str(base) + '-' + str(i))
        i += 1
    # Mode 0600 ; ne pas divulguer le contenu au terminal.
    with CONFIG.open('rb') as src, dest.open('xb') as out:
        os.chmod(dest, 0o600)
        shutil.copyfileobj(src, out)
        out.flush()
        os.fsync(out.fileno())
    return dest


def atomic_write(data: str) -> None:
    fd, temp = tempfile.mkstemp(prefix='.config.toml.atelier-', dir=CONFIG.parent)
    try:
        os.fchmod(fd, 0o600)  # fichier pouvant inclure des secrets MCP
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, CONFIG)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def do_install(args: argparse.Namespace) -> None:
    content = validate_config_file()
    roots = paths(args)
    result, status = compose(content, roots)
    print('Validation TOML : OK. Plan : ' + status + '.')
    print('Mode : workspace-write / on-request ; réseau shell : non.')
    print('Racines supplémentaires : ' + str(len(roots)) + ' (le dossier de projet actif reste inscriptible).')
    if not args.apply:
        print('SIMULATION : aucune modification. Ajouter --apply pour exécuter.')
        return
    if result == content:
        print('Déjà conforme : aucune modification.')
        return
    for p in roots:
        if not p.exists():
            p.mkdir(parents=True, mode=0o700)
        if not p.is_dir() or p.is_symlink():
            die('Dossier d’atelier non sûr : ' + p.name)
    b = backup()
    try:
        atomic_write(result)
    except Exception:
        print('Échec écriture. Copie préalable conservée : ' + b.name, file=sys.stderr)
        raise
    print('Configuration mise à jour. Copie de retour arrière : ' + b.name)
    print('Relancer ChatGPT Desktop, puis lancer « check » : l’app peut réécrire config.toml.')
    print('Exécuter ensuite les tests manuels de docs/TESTS.md.')
    print('ATTENTION : ne pas ouvrir HOME ou ~/Arche entier comme projet actif.')


def backup_evidence(atelier: Path) -> str | None:
    # Vérification indicative, jamais le contenu de SAUVEGARDE.txt.
    marker = atelier / 'SAUVEGARDE.txt'
    if marker.is_file() and not marker.is_symlink() and marker.stat().st_size > 0:
        return 'DÉCLARÉE (SAUVEGARDE.txt ; non vérifiée)'
    home = Path.home().resolve()
    # Le dépôt Git du HOME lui-même ne constitue pas une preuve.
    for directory in (atelier, *atelier.parents):
        if directory == home or not directory.is_relative_to(home):
            break
        git = directory / '.git'
        if git.is_dir() or (git.is_file() and not git.is_symlink()):
            return 'GIT (gestion des versions ; copie indépendante non garantie)'
    return None


def snail(ok: bool) -> None:
    if ok:
        print('🐌 Escargot satisfait : une trace de gestion des versions ou de copie est présente.')
    else:
        print(r'''        @    @
         \  /       La cloison limite les dégâts,
       .--\/--.     elle ne les empêche pas.
      ( (@)    )~~
       `------'     Ayez une autre copie.  🐌''')


def do_check(args: argparse.Namespace) -> None:
    data = load_toml(validate_config_file())
    roots = paths(args)
    checks = {
        'sandbox_mode': data.get('sandbox_mode') == 'workspace-write',
        'approval_policy': data.get('approval_policy') == 'on-request',
        'writable_roots': data.get(SECTION, {}).get('writable_roots') == [str(p) for p in roots],
        'network_access_false': data.get(SECTION, {}).get('network_access') is False,
        'ateliers_existent': all(p.is_dir() for p in roots),
    }
    for name, ok in checks.items():
        print(f'{name}: ' + ('OK' if ok else 'NON CONFORME'))
    evidence = backup_evidence(roots[0]) if roots[0].is_dir() else None
    print('autre_copie: ' + (evidence if evidence else 'ABSENTE OU NON DÉCLARÉE'))
    snail(bool(evidence))
    print('Contrôle statique seulement ; vérifier permissions effectives dans une session Codex.')
    print('ATTENTION : Git seul ne prouve pas une sauvegarde externe ; SAUVEGARDE.txt est une déclaration humaine.')
    print('ATTENTION : projet actif, ~/Documents/Codex et /tmp peuvent rester inscriptibles ; MCP/plugins non couverts.')
    if not all(checks.values()) or not evidence:
        sys.exit(1)


def do_rollback(args: argparse.Namespace) -> None:
    validate_config_file()
    if not args.backup:
        die('Préciser --backup NOM_DU_FICHIER ; voir dans ~/.codex/.')
    b = Path(args.backup)
    if b.name != str(b) or not BACKUP_RE.fullmatch(b.name):
        die('Utiliser uniquement un nom config.toml.atelier-backup-... produit par ce script.')
    source = CONFIG.parent / b
    if not source.is_file() or source.is_symlink() or source.stat().st_uid != os.getuid():
        die('Copie de retour arrière absente ou non fiable.')
    recovered = source.read_text(encoding='utf-8')
    load_toml(recovered)
    print('Retour arrière proposé depuis ' + source.name + '.')
    if not args.apply:
        print('SIMULATION : aucune modification. Ajouter --apply pour exécuter.')
        return
    safety = backup()  # préserver également la configuration courante
    atomic_write(recovered)
    print('Configuration restaurée. Copie de la version remplacée : ' + safety.name)
    print('Relancer ChatGPT Desktop. Les dossiers d’atelier ne sont pas supprimés.')


def main() -> None:
    p = argparse.ArgumentParser(description='Atelier Codex / ChatGPT Desktop Debian KDE (configuration, pas sandbox global)')
    sp = p.add_subparsers(dest='command', required=True)
    for command in ('install', 'check'):
        c = sp.add_parser(command)
        c.add_argument('--atelier', default='~/Arche/atelier-ael', help='Racine écriture supplémentaire ; défaut: ~/Arche/atelier-ael')
        c.add_argument('--partage', help='Deuxième racine facultative, ex. ~/Arche/partage-claude')
        if command == 'install':
            c.add_argument('--apply', action='store_true', help='Appliquer les changements (sinon simulation)')
    r = sp.add_parser('rollback')
    r.add_argument('--backup', help='Nom de sauvegarde créé par install')
    r.add_argument('--apply', action='store_true')
    args = p.parse_args()
    try:
        if args.command == 'install': do_install(args)
        elif args.command == 'check': do_check(args)
        else: do_rollback(args)
    except (OSError, UnicodeError) as exc:
        die(type(exc).__name__ + ' ; aucune donnée privée affichée.')


if __name__ == '__main__':
    main()

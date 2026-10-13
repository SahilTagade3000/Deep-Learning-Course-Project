"""Install only presentation files into an existing, trained project."""
from pathlib import Path
import argparse
import datetime
import hashlib
import os
import shutil
import socket
import struct
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
BACKEND = ('app.py', 'model.py', 'project_data.py', 'analytics.py', 'verify_artifacts.py')
UI_FILES = (
    'app_intelligence.py', 'check_ui.py', 'requirements_ui.txt', 'ui_setup.py',
    'START_UI.cmd', 'RUN_CHECKS.cmd', 'select_ui_python.cmd', 'START_HERE.md',
    'DESIGN_AND_DEMO.md', 'TEST_REPORT.md',
    'intelligence/__init__.py', 'intelligence/config.py',
    'intelligence/data_adapter.py', 'intelligence/monitoring.py',
    'intelligence/theme.py', 'intelligence/charts.py', 'intelligence/views.py',
)


def validate_project(project):
    missing = [name for name in BACKEND if not (project / name).is_file()]
    if not (project / 'artifacts' / 'artifact_manifest.json').is_file():
        missing.append('artifacts/artifact_manifest.json')
    if missing:
        raise RuntimeError(f'This is not the complete existing project: {project}\n'
                           f'Missing: {", ".join(missing)}. Do not create empty replacements.')


def fingerprint(project):
    """Protect the existing application, model modules and every artifact file."""
    files = [project / name for name in BACKEND]
    files += sorted(p for p in (project / 'artifacts').rglob('*') if p.is_file())
    return {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}


def install_files(source, project):
    validate_project(project)
    missing = [name for name in UI_FILES if not (source / name).is_file()]
    if missing:
        raise RuntimeError('The upgrade has not been fully extracted. Missing: ' + ', '.join(missing))
    # Reject links that could redirect a presentation write into an unrelated directory.
    for name in UI_FILES:
        target = project / name
        if not target.resolve().is_relative_to(project.resolve()):
            raise RuntimeError(f'Unexpected linked destination: {target}')
        if target.exists() and not target.is_file():
            raise RuntimeError(f'Expected a file, found a directory: {target}')
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup = project / 'ui_backups' / stamp
    copied = 0
    for name in UI_FILES:
        src, dst = source / name, project / name
        if dst.exists() and src.read_bytes() == dst.read_bytes():
            continue
        if dst.exists():
            old = backup / name
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, old)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    print(f'Installed {copied} presentation files into {project}', flush=True)
    if backup.exists():
        print(f'Previous presentation files backed up in {backup}', flush=True)


def run_step(project, log, label, arguments, env):
    print(f'\n{label}', flush=True)
    log.write('\n' + label + '\n'); log.flush()
    process = subprocess.Popen([sys.executable, *arguments], cwd=project, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace')
    for line in process.stdout:
        print(line, end='', flush=True)
        log.write(line); log.flush()
    if process.wait() != 0:
        raise RuntimeError(f'{label} failed. Read {project / "ui_setup.log"}.')


def run_checks(project, install=False):
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1',
               TEMPORAL_ARTIFACT_DIR=str(project / 'artifacts'))
    before = fingerprint(project)
    log_path = project / 'ui_setup.log'
    with log_path.open('a', encoding='utf-8') as log:
        log.write(f'\n=== {datetime.datetime.now().isoformat()} | {sys.executable} ===\n')
        if install:
            run_step(project, log, '1/4 Installing the two interface dependencies',
                     ['-m', 'pip', 'install', '-r', str(project / 'requirements_ui.txt')], env)
        run_step(project, log, '2/4 Checking installed dependency compatibility',
                 ['-m', 'pip', 'check'], env)
        run_step(project, log, '3/4 Verifying saved artifacts and all 49 CPU inference periods',
                 [str(project / 'verify_artifacts.py'), '--artifacts',
                  str(project / 'artifacts'), '--all-periods'], env)
        run_step(project, log, '4/4 Checking all six pages and monitoring controls',
                 [str(project / 'check_ui.py')], env)
        if fingerprint(project) != before:
            raise RuntimeError('An existing backend or artifact file changed during checking.')
        log.write('\nALL CHECKS PASSED. Existing backend and artifacts unchanged.\n')
    print('\nALL CHECKS PASSED. Existing backend and artifacts unchanged.', flush=True)


def launch(project):
    if not (project / 'app_intelligence.py').is_file():
        raise RuntimeError('Install the interface first with INSTALL_UI.cmd from the extracted upgrade.')
    port = None
    for candidate in range(8502, 8513):
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', candidate))
            except OSError:
                continue
            port = candidate
            break
    if port is None:
        raise RuntimeError('Ports 8502-8512 are busy. Close earlier Temporal app terminals and retry.')
    url = f'http://127.0.0.1:{port}'
    print(f'Opening the redesigned app at {url}\n'
          'Keep this window open while using the app. Press Ctrl+C here to stop.\n'
          'If the browser does not open, paste the address above into it.', flush=True)
    env = dict(os.environ, TEMPORAL_ARTIFACT_DIR=str(project / 'artifacts'))
    return subprocess.call([sys.executable, '-m', 'streamlit', 'run',
                            str(project / 'app_intelligence.py'),
                            '--server.address=127.0.0.1', f'--server.port={port}',
                            '--server.headless=false', '--browser.gatherUsageStats=false',
                            '--theme.base=dark'], cwd=project, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--install', action='store_true')
    action.add_argument('--check', action='store_true')
    action.add_argument('--launch', action='store_true')
    args = parser.parse_args()
    project = args.project.resolve()
    if sys.version_info[:2] not in ((3, 11), (3, 12)) or struct.calcsize('P') != 8:
        raise RuntimeError('Use your existing 64-bit Python 3.11 or 3.12 environment. '
                           f'This script found {sys.version.split()[0]} at {sys.executable}.')
    validate_project(project)
    if args.launch:
        return launch(project)
    if args.install:
        before = fingerprint(project)
        install_files(SOURCE, project)
        if fingerprint(project) != before:
            raise RuntimeError('An existing backend or artifact file changed during installation.')
    run_checks(project, install=args.install)
    if args.install:
        print(f'\nREADY: double-click {project / "START_UI.cmd"}', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\nStopped by user. No training was started.')
        sys.exit(1)
    except Exception as exc:
        print(f'\nSETUP / START ERROR: {exc}', file=sys.stderr, flush=True)
        sys.exit(1)

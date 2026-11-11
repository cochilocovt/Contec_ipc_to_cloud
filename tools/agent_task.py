"""Small, Windows-compatible helpers for approved agent tasks; not a sandbox."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 6000
LEDGER = 'docs/log/delegation-scorecard.jsonl'


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def bounded(text, limit=LIMIT):
    """Bound characters as well as lines: a minified line may be enormous."""
    if len(text) <= limit:
        return text
    return text[:limit // 2] + '\n[truncated; inspect the approved artifact]\n' + text[-limit // 2 + 60:]


def path_for(value):
    path = (ROOT / value).resolve()
    relative = path.relative_to(ROOT.resolve())
    parts = [part.lower() for part in relative.parts]
    if any(part == '.git' or part == 'certs' or part.startswith('.env') for part in parts):
        raise ValueError('Secret or Git-internal path is outside helper scope')
    if path.suffix.lower() in {'.key', '.pem', '.crt', '.pfx', '.p12'}:
        raise ValueError('Certificate/key path is outside helper scope')
    return path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(value):
    return json.loads(path_for(value).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def evidence(value, start=1, end=20):
    path = path_for(value)
    if start < 1 or end < start or end - start >= 40:
        raise ValueError('Request 1 to 40 lines, using one-based line numbers')
    try:
        raw = path.read_bytes()
        lines = raw.decode('utf-8-sig').splitlines()
    except FileNotFoundError:
        return {'status': 'not_found', 'path': value}
    except (OSError, UnicodeError) as error:
        return {'status': 'unreadable', 'path': value, 'error': bounded(str(error), 400)}
    return {'status': 'empty' if len(raw) == 0 else 'found', 'path': value,
            'bytes': len(raw), 'sha256': digest(raw), 'line_count': len(lines),
            'requested_lines': [start, end],
            'excerpts': [{'line': n, 'text': line[:240], 'truncated': len(line) > 240}
                         for n, line in enumerate(lines, 1) if start <= n <= end]}


def preflight(reads, commands, probe=None, cwd='.'):
    checks = [{'kind': 'cwd', 'path': cwd, 'ok': path_for(cwd).is_dir()}]
    for value in reads:
        item = evidence(value, 1, 1)
        checks.append({'kind': 'read', 'path': value, 'ok': item['status'] in {'found', 'empty'},
                       'status': item['status']})
    for command in commands:
        checks.append({'kind': 'command', 'command': command, 'ok': shutil.which(command) is not None})
    if probe:
        path = path_for(probe)
        # Exclusive create; never overwrite or remove another process's file.
        with path.open('xb') as stream:
            stream.write(b'agent write probe\n')
        path.unlink()
        checks.append({'kind': 'write_probe', 'path': probe, 'ok': True})
    return {'status': 'ready' if all(c['ok'] for c in checks) else 'blocked', 'checks': checks,
            'limitation': 'Checks current access only; later tool/policy decisions may still block work.'}


def exact_edit(plan):
    prepared = []
    files = plan['files']
    if not files:
        raise ValueError('An edit plan must name at least one file')
    for item in files:
        path = path_for(item['path'])
        raw = path.read_bytes()
        if digest(raw) != item['sha256']:
            raise ValueError('Source hash changed: ' + item['path'])
        text = raw.decode('utf-8-sig').replace('\r\n', '\n')
        for replacement in item['replacements']:
            old = replacement['old'].replace('\r\n', '\n')
            new = replacement['new'].replace('\r\n', '\n')
            count = replacement['count']
            if not old or not isinstance(count, int) or count < 1 or text.count(old) != count:
                raise ValueError('Exact replacement count differs: ' + item['path'])
            text = text.replace(old, new)
        if b'\r\n' in raw:
            text = text.replace('\n', '\r\n')
        updated = (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + text.encode('utf-8')
        if any(path == prior[0] for prior in prepared):
            raise ValueError('Duplicate edit path')
        prepared.append((path, raw, updated))
    # Validate every file before the first write. Stop on concurrent changes.
    if any(path.read_bytes() != raw for path, raw, _ in prepared):
        raise ValueError('Source changed during preparation')
    changed = []
    for path, raw, updated in prepared:
        if path.read_bytes() != raw:
            raise ValueError('Source changed during write; inspect earlier files before retrying')
        path.write_bytes(updated)
        if path.read_bytes() != updated:
            raise OSError('Read-back differs: ' + str(path))
        changed.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(updated)})
    return {'status': 'edited', 'files': changed}


def run_command(command, cwd, artifact, timeout=300):
    if not command:
        raise ValueError('Supply an approved executable and arguments after --')
    workdir = path_for(cwd)
    command = list(command)
    # Windows resolves a relative executable before applying subprocess cwd.
    if not Path(command[0]).is_absolute() and ('/' in command[0] or '\\' in command[0]):
        command[0] = str((workdir / command[0]).resolve())
    directory = path_for(artifact)
    if not directory.relative_to(ROOT).as_posix().startswith('logs/agent-runs/'):
        raise ValueError('Run artifacts must be under logs/agent-runs/')
    directory.mkdir(parents=True, exist_ok=False)
    started_at, started = utc_now(), time.monotonic()
    output = directory / 'output.txt'
    exit_code = None
    error = None
    with output.open('wb') as stream:
        try:
            result = subprocess.run(command, cwd=workdir, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout, shell=False,
                                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'})
            exit_code = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            error = bounded(str(exc), 400)
    report = {'status': 'completed' if exit_code == 0 else 'blocked', 'command': command,
              'cwd': cwd, 'started_at': started_at, 'finished_at': utc_now(),
              'elapsed_s': round(time.monotonic() - started, 3), 'exit_code': exit_code,
              'error': error, 'output': output.relative_to(ROOT).as_posix(),
              'output_sha256': digest(output.read_bytes())}
    write_json(directory / 'result.json', report)
    text = output.read_bytes().decode('utf-8', errors='replace')
    lines = text.splitlines()
    clipped = '\n'.join(line[:220] + ' [line truncated]' if len(line) > 240 else line for line in lines)
    return {**report, 'excerpt': bounded(clipped, 3000),
            'truncated': len(clipped) > 3000 or any(len(line) > 240 for line in lines)}


def accept(plan):
    checks = []
    for value in plan.get('run_results', []):
        report = read_json(value)
        output = path_for(report['output']).read_bytes()
        ok = report['exit_code'] == 0 and report['status'] == 'completed'
        ok = ok and digest(output) == report['output_sha256']
        checks.append({'kind': 'run', 'path': value, 'ok': ok})
    for item in plan.get('files', []):
        raw = path_for(item['path']).read_bytes()
        text = raw.decode('utf-8-sig').replace('\r\n', '\n')
        ok = digest(raw) == item['sha256']
        ok = ok and all(text.count(c['text']) == c['count'] for c in item.get('contains', []))
        checks.append({'kind': 'file', 'path': item['path'], 'ok': ok})
    if 'expected_changed_paths' in plan:
        tracked = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=ROOT, text=True)
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True)
        paths = set(tracked.splitlines() + untracked.splitlines())
        checks.append({'kind': 'changed_paths', 'ok': paths == set(plan['expected_changed_paths'])})
    if not checks:
        raise ValueError('Acceptance requires at least one explicit check')
    return {'status': 'accepted' if all(c['ok'] for c in checks) else 'rejected', 'checks': checks}


def record(entry):
    required = {'task_id', 'team', 'role', 'started_at', 'finished_at', 'outcome', 'lead_rework_minutes'}
    optional = {'notes', 'tokens', 'observed_elapsed_s'}
    if not required <= entry.keys() or entry.keys() - required - optional:
        raise ValueError('Scorecard fields differ from the documented schema')
    roles = {'codex': {'luna_runner', 'luna_scout'}, 'claude': {'haiku-runner', 'haiku-scout'}}
    if entry['role'] not in roles.get(entry['team'], set()):
        raise ValueError('Team/role mapping differs')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', entry['task_id']):
        raise ValueError('Use a short non-sensitive task identifier')
    if entry['outcome'] not in {'accepted', 'blocked', 'rejected'}:
        raise ValueError('Unknown outcome')
    dates = []
    if entry['started_at'] is None and entry['finished_at'] is None:
        elapsed = entry.get('observed_elapsed_s')
        if elapsed is not None and (type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0):
            raise ValueError('Observed elapsed time must be non-negative or null')
    else:
        for key in ('started_at', 'finished_at'):
            if not isinstance(entry[key], str) or not entry[key].endswith('Z'):
                raise ValueError('Use two UTC Z timestamps or two null timestamps')
            dates.append(datetime.fromisoformat(entry[key].replace('Z', '+00:00')))
        if any(date.tzinfo is None for date in dates) or dates[1] < dates[0]:
            raise ValueError('Invalid UTC timestamps')
        if 'observed_elapsed_s' in entry:
            raise ValueError('Use timestamps or observed elapsed time, not both')
        elapsed = (dates[1] - dates[0]).total_seconds()
    if type(entry['lead_rework_minutes']) not in (int, float) or not math.isfinite(entry['lead_rework_minutes']) or entry['lead_rework_minutes'] < 0:
        raise ValueError('Invalid elapsed/rework time')
    if len(entry.get('notes', '')) > 240:
        raise ValueError('Notes must be at most 240 characters, without secrets or personal details')
    if entry.get('tokens') is not None and (type(entry['tokens']) is not int or entry['tokens'] < 0):
        raise ValueError('Tokens must be an observed non-negative integer or null')
    ledger = path_for(LEDGER)
    entries = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    if any(row['task_id'] == entry['task_id'] for row in entries):
        raise ValueError('Task already recorded; lead must reconcile deliberately')
    row = {**entry, 'elapsed_s': elapsed}
    with ledger.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    return {'status': 'recorded', 'task_id': entry['task_id']}


def scorecard():
    ledger = path_for(LEDGER)
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    teams = {}
    for row in rows:
        team = teams.setdefault(row['team'], {'tasks': 0, 'accepted': 0, 'blocked': 0, 'rejected': 0,
                                              'elapsed_s': 0, 'lead_rework_minutes': 0, 'observed_tokens': 0,
                                              'tasks_with_token_counts': 0, 'tasks_with_elapsed': 0})
        team['tasks'] += 1
        team[row['outcome']] += 1
        if row['elapsed_s'] is not None:
            team['elapsed_s'] += row['elapsed_s']
            team['tasks_with_elapsed'] += 1
        team['lead_rework_minutes'] += row['lead_rework_minutes']
        if row.get('tokens') is not None:
            team['observed_tokens'] += row['tokens']
            team['tasks_with_token_counts'] += 1
    return {'status': 'reported', 'teams': teams,
            'limitation': 'Wall times may overlap; token counts are observed only. No inferred savings.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('evidence'); p.add_argument('path'); p.add_argument('--start', type=int, default=1); p.add_argument('--end', type=int, default=20)
    p = sub.add_parser('preflight'); p.add_argument('--read', action='append', default=[]); p.add_argument('--command', action='append', default=[]); p.add_argument('--write-probe'); p.add_argument('--cwd', default='.')
    p = sub.add_parser('edit'); p.add_argument('plan')
    p = sub.add_parser('run'); p.add_argument('--cwd', default='.'); p.add_argument('--artifact', required=True); p.add_argument('--timeout', type=int, default=300); p.add_argument('command', nargs=argparse.REMAINDER)
    p = sub.add_parser('accept'); p.add_argument('plan')
    p = sub.add_parser('record'); p.add_argument('entry')
    sub.add_parser('scorecard')
    args = parser.parse_args(argv)
    try:
        if args.action == 'evidence': result = evidence(args.path, args.start, args.end)
        elif args.action == 'preflight': result = preflight(args.read, args.command, args.write_probe, args.cwd)
        elif args.action == 'edit': result = exact_edit(read_json(args.plan))
        elif args.action == 'run': result = run_command(args.command[1:] if args.command[:1] == ['--'] else args.command, args.cwd, args.artifact, args.timeout)
        elif args.action == 'accept': result = accept(read_json(args.plan))
        elif args.action == 'record': result = record(read_json(args.entry))
        else: result = scorecard()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result = {'status': 'blocked', 'error': bounded(str(error), 400)}
    rendered = json.dumps(result, ensure_ascii=True, indent=2)
    if len(rendered) > LIMIT:
        result = {**{key: result[key] for key in ('status', 'path', 'bytes', 'sha256', 'line_count', 'exit_code', 'output') if key in result},
                  'output_truncated': True, 'excerpt': bounded(rendered, 2000)}
        rendered = json.dumps(result, ensure_ascii=True, indent=2)
    print(rendered)
    return 0 if result['status'] in {'found', 'empty', 'ready', 'edited', 'completed', 'accepted', 'recorded', 'reported'} else 1


if __name__ == '__main__':
    raise SystemExit(main())

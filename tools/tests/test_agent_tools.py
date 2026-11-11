"""Meaningful failure-path checks for the shared agent tools; no services changed."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import agent_task as task
import check_home_lab as health


class TaskToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.override = patch.object(task, 'ROOT', self.root)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.temp.cleanup()

    def source(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(text)
        return file

    def plan(self, path, old='before', new='after', count=1):
        return {'path': path, 'sha256': task.digest((self.root / path).read_bytes()),
                'replacements': [{'old': old, 'new': new, 'count': count}]}

    def test_evidence_empty_missing_unreadable_and_long_line(self):
        self.source('empty.md', b'')
        self.source('binary.md', b'\xff')
        self.source('huge.md', b'x' * 50000)
        self.assertEqual(task.evidence('empty.md')['status'], 'empty')
        self.assertEqual(task.evidence('absent.md')['status'], 'not_found')
        self.assertEqual(task.evidence('binary.md')['status'], 'unreadable')
        report = task.evidence('huge.md')
        self.assertEqual(report['bytes'], 50000)
        self.assertTrue(report['excerpts'][0]['truncated'])
        self.assertEqual(len(report['excerpts'][0]['text']), 240)

    def test_paths_refuse_escape_and_secrets(self):
        for value in ['../outside.md', '.env', 'cloud/.env', 'certs/test.txt', '.git/config', 'test.key']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                task.path_for(value)

    def test_preflight_probe_never_overwrites_another_file(self):
        self.source('owned/probe.tmp', b'keep')
        with self.assertRaises(FileExistsError):
            task.preflight([], [], 'owned/probe.tmp')
        self.assertEqual((self.root / 'owned/probe.tmp').read_bytes(), b'keep')
        report = task.preflight([], [sys.executable], 'owned/new-probe.tmp')
        self.assertEqual(report['status'], 'ready')
        self.assertFalse((self.root / 'owned/new-probe.tmp').exists())
        self.assertEqual(task.preflight(['absent.md'], [])['status'], 'blocked')

    def test_edit_checks_every_match_before_writing_and_preserves_utf8_crlf(self):
        file = self.source('one.md', 'before\r\n温度\r\n'.encode('utf-8'))
        self.source('two.md', b'before\n')
        one, two = self.plan('one.md'), self.plan('two.md', count=2)
        with self.assertRaises(ValueError):
            task.exact_edit({'files': [one, two]})
        self.assertTrue(file.read_bytes().startswith(b'before'))
        result = task.exact_edit({'files': [one]})
        self.assertEqual(result['status'], 'edited')
        self.assertEqual(file.read_bytes(), 'after\r\n温度\r\n'.encode('utf-8'))

    def test_stale_hash_and_duplicate_paths_refuse_edits(self):
        file = self.source('one.md', b'before')
        item = self.plan('one.md')
        with self.assertRaises(ValueError):
            task.exact_edit({'files': [item, item]})
        file.write_bytes(b'concurrent edit')
        with self.assertRaises(ValueError):
            task.exact_edit({'files': [item]})
        self.assertEqual(file.read_bytes(), b'concurrent edit')

    def test_edit_preserves_bom_and_normalizes_replacement_newlines(self):
        file = self.source('one.md', b'\xef\xbb\xbfbefore\r\n')
        task.exact_edit({'files': [self.plan('one.md', new='after\r\nsecond')]})
        self.assertEqual(file.read_bytes(), b'\xef\xbb\xbfafter\r\nsecond\r\n')

    def test_command_output_capture_acceptance_and_tampering(self):
        report = task.run_command([sys.executable, '-c', "print('温度'); print('x' * 12000)"], '.', 'logs/agent-runs/pass')
        self.assertEqual(report['exit_code'], 0)
        self.assertTrue(report['truncated'])
        self.assertLess(len(report['excerpt']), 3100)
        self.assertTrue(all(len(line) <= 240 for line in report['excerpt'].splitlines()))
        plan = {'run_results': ['logs/agent-runs/pass/result.json']}
        self.assertEqual(task.accept(plan)['status'], 'accepted')
        (self.root / report['output']).write_text('changed', encoding='utf-8')
        self.assertEqual(task.accept(plan)['status'], 'rejected')
        with self.assertRaises(FileExistsError):
            task.run_command([sys.executable, '-V'], '.', 'logs/agent-runs/pass')

    def test_failed_command_and_timeout_are_blocked(self):
        report = task.run_command([sys.executable, '-c', 'raise SystemExit(7)'], '.', 'logs/agent-runs/fail')
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['exit_code'], 7)
        report = task.run_command([sys.executable, '-c', 'import time; time.sleep(10)'], '.', 'logs/agent-runs/timeout', 0.1)
        self.assertEqual(report['status'], 'blocked')
        self.assertIsNone(report['exit_code'])
        self.assertIsNotNone(report['error'])

    def test_relative_executable_is_resolved_against_requested_cwd(self):
        (self.root / 'gateway').mkdir()
        with patch.object(task.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            task.run_command(['.venv/Scripts/python.exe', '-V'], 'gateway', 'logs/agent-runs/relative')
        self.assertEqual(run.call_args.args[0][0], str((self.root / 'gateway/.venv/Scripts/python.exe').resolve()))
        self.assertEqual(run.call_args.kwargs['cwd'], self.root / 'gateway')

    def test_acceptance_requires_lead_hash_text_count_and_scope(self):
        self.source('one.md', b'after\n')
        item = {'path': 'one.md', 'sha256': task.digest(b'after\n'), 'contains': [{'text': 'after', 'count': 1}]}
        with patch.object(task.subprocess, 'check_output', side_effect=['one.md\n', 'extra.md\n']):
            self.assertEqual(task.accept({'files': [item], 'expected_changed_paths': ['one.md']})['status'], 'rejected')
        item['contains'][0]['count'] = 2
        self.assertEqual(task.accept({'files': [item]})['status'], 'rejected')
        with self.assertRaises(ValueError):
            task.accept({})

    def test_scorecard_validates_records_and_never_invents_tokens(self):
        (self.root / 'docs/log').mkdir(parents=True)
        entry = {'task_id': 'one', 'team': 'codex', 'role': 'luna_runner',
                 'started_at': '2026-11-11T01:00:00Z', 'finished_at': '2026-11-11T01:01:00Z',
                 'outcome': 'accepted', 'lead_rework_minutes': 0, 'tokens': None}
        task.record(entry)
        with self.assertRaises(ValueError):
            task.record(entry)
        team = task.scorecard()['teams']['codex']
        self.assertEqual(team['elapsed_s'], 60)
        self.assertEqual(team['tasks_with_token_counts'], 0)
        for updates in [{'task_id': 'two', 'role': 'haiku-runner'}, {'task_id': 'two', 'finished_at': '2026-11-11T01:01:00+00:00'}, {'task_id': 'two', 'tokens': -1}, {'task_id': 'two', 'lead_rework_minutes': float('nan')}]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                task.record({**entry, **updates})

    def test_scorecard_preserves_unavailable_timestamps_without_invention(self):
        (self.root / 'docs/log').mkdir(parents=True)
        entry = {'task_id': 'untimed', 'team': 'claude', 'role': 'haiku-scout',
                 'started_at': None, 'finished_at': None, 'outcome': 'rejected',
                 'lead_rework_minutes': 0, 'tokens': None}
        task.record(entry)
        task.record({**entry, 'task_id': 'duration-only', 'observed_elapsed_s': 9.079})
        team = task.scorecard()['teams']['claude']
        self.assertEqual(team['tasks'], 2)
        self.assertEqual(team['tasks_with_elapsed'], 1)
        self.assertEqual(team['elapsed_s'], 9.079)
        with self.assertRaises(ValueError):
            task.record({**entry, 'task_id': 'bad', 'finished_at': '2026-11-11T01:01:00Z'})

    def test_cli_output_remains_bounded_valid_json(self):
        source = TOOLS / 'agent_task.py'
        # The repository guide is a real minified-file regression case.
        result = subprocess.run([sys.executable, str(source), 'evidence', 'docs/home-lab-guide.html', '--end', '40'], capture_output=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0)
        self.assertLessEqual(len(result.stdout.strip()), task.LIMIT)
        self.assertEqual(json.loads(result.stdout)['status'], 'found')


class HealthTests(unittest.TestCase):
    def test_bindings_reject_public_wildcard_and_vpn_broker_addresses(self):
        for address in ['192.168.1.20', '10.0.0.2', '172.16.0.2', '127.0.0.1']:
            self.assertTrue(health.binding_ok('mosquitto', address))
        for address in ['0.0.0.0', '::', '8.8.8.8', '100.73.242.65']:
            self.assertFalse(health.binding_ok('mosquitto', address))
        self.assertFalse(health.binding_ok('grafana', '192.168.1.20'))

    def test_compose_ndjson_array_and_empty(self):
        item = {'Service': 'ingest', 'State': 'running'}
        self.assertEqual(health.parse_services(json.dumps(item)), [item])
        self.assertEqual(health.parse_services(json.dumps([item])), [item])
        self.assertEqual(health.parse_services(''), [])

    def test_freshness_rejects_missing_stale_future_and_offline(self):
        self.assertTrue(health.telemetry_ok({'state': 'online', 'age_s': 1}, 30))
        for data in [{'state': 'offline', 'age_s': 1}, {'state': 'online', 'age_s': None}, {'state': 'online', 'age_s': 31}, {'state': 'online', 'age_s': -1}]:
            self.assertFalse(health.telemetry_ok(data, 30))

    def test_docker_failure_is_reported_without_credentials(self):
        with patch.object(health, 'compose', side_effect=RuntimeError('Docker unavailable')), patch.object(health.urllib.request, 'build_opener', side_effect=OSError('HTTP unavailable')):
            result = health.check()
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(row['name'] == 'telemetry' and row['ok'] is None for row in result['checks']))

    def test_unsafe_binding_is_reported_without_connecting_to_it(self):
        rows = [{'Service': 'mosquitto', 'State': 'running', 'Publishers': [
            {'TargetPort': 1883, 'PublishedPort': 1883, 'URL': '8.8.8.8'}]}]
        with patch.object(health, 'compose', side_effect=['', json.dumps(rows), '1']), patch.object(health.socket, 'create_connection') as connect, patch.object(health.urllib.request, 'build_opener', side_effect=OSError('HTTP unavailable')):
            result = health.check()
        connect.assert_not_called()
        self.assertEqual(result['status'], 'fail')


if __name__ == '__main__':
    unittest.main()

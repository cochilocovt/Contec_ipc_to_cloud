"""Read-only home-PC health checks. No MQTT publications or PLC connections."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import ipaddress
import json
import math
from pathlib import Path
import socket
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SERVICES = {'mosquitto', 'timescaledb', 'ingest', 'grafana'}


def compose(*args, input_text=None):
    result = subprocess.run(['docker', 'compose', *args], cwd=ROOT / 'cloud', input=input_text,
                            capture_output=True, text=True, encoding='utf-8', timeout=15)
    if result.returncode:
        # Avoid echoing a failing command's potentially sensitive Docker diagnostics.
        raise RuntimeError('Docker Compose check failed (exit %d)' % result.returncode)
    return result.stdout


def parse_services(text):
    text = text.strip()
    if not text:
        return []
    rows = json.loads(text) if text.startswith('[') else [json.loads(line) for line in text.splitlines()]
    if not isinstance(rows, list) or any(not isinstance(row, dict) or 'Service' not in row for row in rows):
        raise ValueError('Unexpected Docker Compose service output')
    return rows


def telemetry_ok(data, max_age):
    age = data.get('age_s')
    return data.get('state') == 'online' and isinstance(age, (int, float)) and 0 <= age <= max_age


def binding_ok(service, address):
    if service != 'mosquitto':
        return address == '127.0.0.1'
    ip = ipaddress.ip_address(address)
    # The unauthenticated broker belongs on loopback or an RFC1918 home LAN.
    return ip.version == 4 and (ip.is_loopback or any(ip in network for network in (
        ipaddress.ip_network('10.0.0.0/8'), ipaddress.ip_network('172.16.0.0/12'), ipaddress.ip_network('192.168.0.0/16'))))


def check(machine=None, max_age=30):
    checks = []
    def attempt(name, operation):
        try:
            detail = operation()
            summary = [{'service': row['Service'], 'state': row.get('State'), 'health': row.get('Health')}
                       for row in detail] if name == 'containers' else detail
            checks.append({'name': name, 'ok': True, 'detail': summary})
            return detail
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            checks.append({'name': name, 'ok': False, 'detail': str(error)[:240]})
            return None

    attempt('compose_config', lambda: (compose('config', '--quiet'), 'valid')[1])
    services = attempt('containers', lambda: parse_services(compose('ps', '--all', '--format', 'json')))
    if services is not None:
        states = {row['Service']: row for row in services}
        for service in sorted(SERVICES):
            row = states.get(service, {})
            ok = row.get('State') == 'running' and row.get('Health') not in {'unhealthy', 'starting'}
            if service == 'timescaledb':
                ok = ok and row.get('Health') == 'healthy'
            checks.append({'name': service, 'ok': ok,
                           'detail': {'state': row.get('State', 'missing'), 'health': row.get('Health', '')}})
        # Published addresses only; never inspect container environments.
        for service, target in [('mosquitto', 1883), ('grafana', 3000), ('timescaledb', 5432)]:
            ports = [p for p in states.get(service, {}).get('Publishers') or [] if p['TargetPort'] == target]
            for port in ports:
                address, number = port['URL'], port['PublishedPort']
                safe = binding_ok(service, address)
                checks.append({'name': service + '_binding', 'ok': safe,
                               'detail': {'host': address, 'port': number}})
                if not safe:
                    continue
                def connect(host=address, tcp_port=number):
                    with socket.create_connection((host, tcp_port), timeout=3):
                        return 'TCP connection succeeded'
                attempt(service + '_tcp', connect)
            if not ports:
                checks.append({'name': service + '_binding', 'ok': False, 'detail': 'No published port found'})

    def grafana():
        # Never send credentials through an inherited HTTP proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:3000/api/health', timeout=5) as response:
            data = json.load(response)
        if data.get('database') != 'ok':
            raise RuntimeError('Grafana internal database is not healthy')
        return {'database': data['database'], 'version': data.get('version')}
    attempt('grafana_http', grafana)

    def database():
        text = compose('exec', '-T', 'timescaledb', 'psql', '-X', '-U', 'factory', '-d', 'factory',
                       '-v', 'ON_ERROR_STOP=1', '-tA', '-c', 'SELECT 1;').strip()
        if text != '1':
            raise RuntimeError('Unexpected database query response')
        return 'Read-only SELECT succeeded'
    attempt('database_query', database)

    if machine:
        def telemetry():
            # psql variables quote the machine identifier as a SQL literal.
            query = """SELECT json_build_object(
                'age_s', EXTRACT(EPOCH FROM (now() - (SELECT max(ts) FROM telemetry WHERE machine_id=:'machine'))),
                'state', (SELECT state FROM gateway_status WHERE machine_id=:'machine'));
            """
            text = compose('exec', '-T', 'timescaledb', 'psql', '-X', '-U', 'factory', '-d', 'factory',
                           '-v', 'ON_ERROR_STOP=1', '-v', 'machine=' + machine, '-tA', input_text=query)
            data = json.loads(text)
            if not telemetry_ok(data, max_age):
                raise RuntimeError('Telemetry missing, stale, future-dated or gateway offline: ' + json.dumps(data))
            return data
        attempt('telemetry', telemetry)
    else:
        checks.append({'name': 'telemetry', 'ok': None, 'detail': 'Not checked; pass --machine MACHINE_ID'})
    return {'ts': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
            'status': 'pass' if all(c['ok'] is not False for c in checks) else 'fail',
            'scope': 'home-PC services; physical PLC/gateway path is not tested', 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--machine', help='Require this machine to be online with fresh telemetry')
    parser.add_argument('--max-age-s', type=float, default=30)
    args = parser.parse_args()
    if not math.isfinite(args.max_age_s) or args.max_age_s <= 0:
        parser.error('--max-age-s must be positive')
    result = check(args.machine, args.max_age_s)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())

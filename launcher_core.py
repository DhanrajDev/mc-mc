"""Persistent launcher settings and Minecraft installation metadata."""
from pathlib import Path
import hashlib
import json
import os
import re
import time
import tempfile
import uuid

import minecraft_launcher_lib as mc

APP_VERSION = '1.0.0'


def local_options(name):
    if not re.fullmatch(r'[A-Za-z0-9_]{3,16}', name):
        raise ValueError('Username must contain 3–16 letters, numbers, or underscores.')
    digest = hashlib.md5(('OfflinePlayer:' + name).encode()).digest()
    return {'username': name, 'uuid': str(uuid.UUID(bytes=digest, version=3)), 'token': ''}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '-', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_launcher_profiles(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with (directory / 'launcher_profiles.json').open('x', encoding='utf-8') as stream:
            json.dump({'profiles': {}}, stream)
    except FileExistsError:
        pass


def register_version(directory, version):
    """Register only our own entry; preserve official launcher accounts/settings."""
    ensure_launcher_profiles(directory)
    path = Path(directory) / 'launcher_profiles.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(data.get('profiles'), dict):
            raise ValueError('Invalid profiles')
    except (ValueError, AttributeError):
        raise ValueError('launcher_profiles.json is damaged. Restore it before changing installations.')
    data['profiles']['craftline-' + version] = {
        'name': 'Craftline · ' + version, 'type': 'custom',
        'lastVersionId': version, 'gameDir': str(directory),
    }
    write_json(path, data)


def installed_versions(directory):
    result = []
    for path in (Path(directory) / 'versions').glob('*/*.json'):
        if path.stem != path.parent.name:
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            if data.get('id') == path.parent.name:
                result.append(path.parent.name)
        except (ValueError, OSError):
            continue
    return sorted(result, reverse=True)


def base_version(directory, version):
    seen = set()
    while version not in seen:
        seen.add(version)
        path = Path(directory) / 'versions' / version / (version + '.json')
        if not path.exists():
            return version
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if not data.get('inheritsFrom'):
            return version
        version = data['inheritsFrom']
    raise ValueError('Circular Minecraft version inheritance.')


PROFILE_FIELDS = ('id', 'label', 'username', 'uuid', 'mode', 'version', 'ram', 'server', 'client_id')


def new_profile(label='My profile', username='Player', version='1.20.1'):
    return {'id': str(uuid.uuid4()), 'label': label, 'username': username,
            'uuid': local_options(username)['uuid'], 'mode': 'Local / no authentication',
            'version': version, 'ram': '2', 'server': '', 'client_id': ''}


class Settings:
    def __init__(self, directory):
        self.game = Path(directory)
        self.path = self.game / 'craftline-launcher' / 'settings.json'
        self.notice = ''
        self.data = None
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8-sig'))
                if not isinstance(data, dict) or not isinstance(data.get('profiles'), list) or not data['profiles']:
                    raise ValueError('Invalid settings')
                profiles = []
                for item in data['profiles']:
                    p = new_profile()
                    p.update({k: str(item[k]) for k in PROFILE_FIELDS if k in item})
                    p['uuid'] = local_options(p['username'])['uuid']
                    profiles.append(p)
                self.data = {'schema_version': 1, 'active': str(data.get('active', profiles[0]['id'])), 'profiles': profiles}
            except (ValueError, TypeError, KeyError):
                backup = self.path.with_name('settings-recovery-' + str(time.time_ns()) + '.json')
                backup.write_bytes(self.path.read_bytes())
                self.notice = 'Settings could not be read. A recovery copy was saved; a new profile was created.'
        if self.data is None:
            name = 'Player'
            latest = self.game / 'logs' / 'latest.log'
            if latest.exists():
                match = re.search(r'Setting user: ([A-Za-z0-9_]{3,16})\b', latest.read_text(encoding='utf-8', errors='replace'))
                if match:
                    name = match.group(1)
            versions = installed_versions(self.game)
            preferred = next((v for v in versions if 'iris' in v.lower()), versions[0] if versions else '1.20.1')
            profile = new_profile(username=name, version=preferred)
            self.data = {'schema_version': 1, 'active': profile['id'], 'profiles': [profile]}

    @property
    def active(self):
        return next((p for p in self.data['profiles'] if p['id'] == self.data['active']), self.data['profiles'][0])

    def save(self):
        # Explicit allow-list prevents authentication tokens from entering settings.
        data = {'schema_version': 1, 'active': self.data['active'],
                'profiles': [{k: p[k] for k in PROFILE_FIELDS} for p in self.data['profiles']]}
        write_json(self.path, data)

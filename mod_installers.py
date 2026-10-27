"""Official Iris bundle and OptiFine installer integration."""
from pathlib import Path
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import minecraft_launcher_lib as mc
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from launcher_core import local_options, register_version, installed_versions, ensure_launcher_profiles

CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def resources():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'


def session():
    s = requests.Session()
    s.headers['User-Agent'] = 'CraftlineLauncher/1.0 (desktop Minecraft launcher)'
    s.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=.5, status_forcelist=[429, 500, 502, 503, 504])))
    return s


def get_json(s, url):
    response = s.get(url, timeout=(15, 60))
    response.raise_for_status()
    return response.json()


def install_iris(version, directory, callback=None):
    directory = Path(directory)
    callback = callback or {}
    status = callback.get('setStatus', lambda value: None)
    progress = callback.get('setProgress', lambda value: None)
    maximum = callback.get('setMax', lambda value: None)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', version) or version in ('.', '..'):
        raise ValueError('Choose a valid Minecraft release.')
    with session() as s:
        status('Finding the official Iris + Sodium bundle…')
        release = get_json(s, 'https://api.github.com/repos/IrisShaders/Iris-Installer-Files/releases/latest')
        filename = 'Iris-Sodium-' + version + '.zip'
        asset = next((a for a in release.get('assets', []) if a['name'] == filename), None)
        if asset is None:
            raise ValueError(f'No official Iris bundle is available for Minecraft {version}. Choose a supported release.')
        loaders = get_json(s, 'https://meta.fabricmc.net/v2/versions/loader/' + version)
        loader = next((v['loader']['version'] for v in loaders if v['loader'].get('stable')), None)
        if not loader:
            raise ValueError('No stable Fabric loader is available for this Minecraft version.')
        status('Downloading Iris + Sodium…')
        # Streaming works with and without Content-Length; no Java downloader involved.
        with s.get(asset['browser_download_url'], stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            size = int(response.headers.get('Content-Length', '0'))
            maximum(max(size, 1))
            content = bytearray()
            for chunk in response.iter_content(65536):
                content.extend(chunk)
                progress(len(content))
                if len(content) > 100 * 1024 * 1024:
                    raise ValueError('Iris package is unexpectedly large.')
        digest = asset.get('digest')
        if digest and digest.startswith('sha256:') and hashlib.sha256(content).hexdigest() != digest.split(':', 1)[1]:
            raise ValueError('Iris package checksum did not match. Retry the download.')
        packages = {}
        with zipfile.ZipFile(io.BytesIO(content)) as bundle:
            for entry in bundle.infolist():
                if entry.is_dir() or not entry.filename.endswith('.jar'):
                    continue
                if entry.file_size > 100 * 1024 * 1024:
                    raise ValueError('Invalid mod package size.')
                data = bundle.read(entry)  # Verifies the ZIP entry CRC.
                with zipfile.ZipFile(io.BytesIO(data)) as jar:
                    metadata = json.loads(jar.read('fabric.mod.json'))
                if metadata['id'] in ('iris', 'sodium'):
                    packages[metadata['id']] = (Path(entry.filename).name, data)
        if set(packages) != {'iris', 'sodium'}:
            raise ValueError('The official bundle did not contain both Iris and Sodium.')
        status('Preparing Minecraft and Fabric…')
        ensure_launcher_profiles(directory)
        mc.install.install_minecraft_version(version, str(directory), callback=callback)
        data = get_json(s, f'https://meta.fabricmc.net/v2/versions/loader/{version}/{loader}/profile/json')
        profile_id = f'iris-fabric-loader-{loader}-{version}'
        mods = directory / 'iris-reserved' / version
        mods.mkdir(parents=True, exist_ok=True)
        # Keep Iris separate from the user's ordinary mods and OptiFine installations.
        archive = directory / 'craftline-launcher' / 'backups' / ('iris-' + str(time.time_ns()))
        for existing in mods.glob('*.jar'):
            try:
                with zipfile.ZipFile(existing) as jar:
                    mod_id = json.loads(jar.read('fabric.mod.json'))['id']
            except (KeyError, ValueError, zipfile.BadZipFile):
                continue
            if mod_id in packages:
                name, payload = packages[mod_id]
                if existing.name == name and existing.read_bytes() == payload:
                    continue
                archive.mkdir(parents=True, exist_ok=True)
                shutil.move(str(existing), archive / existing.name)
        for name, payload in packages.values():
            (mods / name).write_bytes(payload)
        data['id'] = profile_id
        data.setdefault('arguments', {}).setdefault('jvm', []).extend([
            '-Diris.installer=true', '-Dfabric.modsFolder=' + str(mods)])
        profile_dir = directory / 'versions' / profile_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        path = profile_dir / (profile_id + '.json')
        if path.exists():
            archive.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, archive / path.name)
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        jar_path = profile_dir / (profile_id + '.jar')
        if not jar_path.exists():
            jar_path.touch()
        mc.install.install_minecraft_version(profile_id, str(directory), callback=callback)
        register_version(directory, profile_id)
        status('Iris + Sodium installed. Ready to play.')
        return profile_id


def install_optifine(jar, version, directory, callback=None):
    directory, jar = Path(directory), Path(jar).resolve()
    callback = callback or {}
    status = callback.get('setStatus', lambda value: None)
    with zipfile.ZipFile(jar) as archive:
        if 'optifine/Installer.class' not in archive.namelist():
            raise ValueError('Choose an official OptiFine installer JAR from optifine.net.')
    match = re.search(r'OptiFine_([0-9][A-Za-z0-9.]*)_', jar.name)
    if match:
        version = match.group(1)
    ensure_launcher_profiles(directory)
    status('Preparing Minecraft for OptiFine…')
    mc.install.install_minecraft_version(version, str(directory), callback=callback)
    java = mc.command.get_minecraft_command(version, str(directory), local_options('Player'))[0]
    bridge = resources() / 'java'
    classpath = str(jar) + os.pathsep + str(bridge)
    query = subprocess.run([java, '-Djava.awt.headless=true', '-cp', classpath, 'OptiFineBridge', 'version'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    if query.returncode:
        raise ValueError('This OptiFine installer is not compatible with automatic installation.')
    actual = query.stdout.strip().splitlines()[-1]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', actual) or actual in ('.', '..'):
        raise ValueError('The OptiFine JAR returned an invalid Minecraft version.')
    if actual != version:
        version = actual
        mc.install.install_minecraft_version(version, str(directory), callback=callback)
        java = mc.command.get_minecraft_command(version, str(directory), local_options('Player'))[0]
    status('Installing OptiFine into .minecraft…')
    logs = directory / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / 'optifine-install.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([java, '-Djava.awt.headless=true', '-cp', classpath, 'OptiFineBridge', str(directory)], stdout=log, stderr=subprocess.STDOUT, creationflags=CREATE_NO_WINDOW)
    if result.returncode:
        raise ValueError('OptiFine installation failed. See .minecraft/logs/optifine-install.log.')
    versions = [v for v in installed_versions(directory) if 'optifine' in v.lower() and v.startswith(version + '-')]
    if not versions:
        raise ValueError('OptiFine finished but no launchable profile was created. Check the install log.')
    selected = max(versions, key=lambda v: (directory / 'versions' / v / (v + '.json')).stat().st_mtime_ns)
    register_version(directory, selected)
    return selected

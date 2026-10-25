"""Minecraft Java launcher. Authentication tokens stay in memory."""
from pathlib import Path
import hashlib
import json
import queue
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import uuid
import webbrowser
import minecraft_launcher_lib as mc

BASE = Path(__file__).resolve().parent
GAME = BASE / 'my_cracked_minecraft'
REDIRECT = 'https://login.microsoftonline.com/common/oauth2/nativeclient'


def ensure_launcher_profiles(directory):
    """Supply the metadata expected by OptiFine without replacing profiles."""
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with (directory / 'launcher_profiles.json').open('x', encoding='utf-8') as stream:
            json.dump({'profiles': {}}, stream)
    except FileExistsError:
        pass


def local_options(name):
    if not re.fullmatch(r'[A-Za-z0-9_]{3,16}', name):
        raise ValueError('Username must contain 3–16 letters, numbers, or underscores.')
    digest = hashlib.md5(('OfflinePlayer:' + name).encode()).digest()
    return {'username': name, 'uuid': str(uuid.UUID(bytes=digest, version=3)), 'token': ''}


class Launcher:
    def __init__(self, root):
        self.root, self.events = root, queue.Queue()
        self.account, self.busy = None, False
        root.title('Minecraft Java Launcher')
        root.geometry('660x600')
        root.minsize(620, 580)
        frame = ttk.Frame(root, padding=22)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Minecraft Java', font=('Segoe UI', 22, 'bold')).pack(anchor='w')
        self.mode = tk.StringVar(value='Microsoft account')
        self.label(frame, 'Profile')
        ttk.Combobox(frame, textvariable=self.mode, values=['Microsoft account', 'Local / no authentication'], state='readonly').pack(fill='x')
        self.name = tk.StringVar(value='Player')
        self.label(frame, 'Local username (no-auth mode only)')
        ttk.Entry(frame, textvariable=self.name).pack(fill='x')
        self.client = tk.StringVar()
        self.label(frame, 'Azure application client ID (Microsoft sign-in only)')
        ttk.Entry(frame, textvariable=self.client).pack(fill='x')
        self.login_button = ttk.Button(frame, text='Sign in with Microsoft', command=self.sign_in)
        self.login_button.pack(anchor='w', pady=8)
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=8)
        ttk.Label(row, text='Version').pack(side='left')
        self.version = tk.StringVar(value='1.20.1')
        self.versions = ttk.Combobox(row, textvariable=self.version, width=20)
        self.versions.pack(side='left', padx=8)
        ttk.Label(row, text='RAM (GB)').pack(side='left')
        self.ram = tk.StringVar(value='2')
        ttk.Spinbox(row, from_=1, to=32, textvariable=self.ram, width=5).pack(side='left', padx=8)
        mods = ttk.Frame(frame)
        mods.pack(fill='x', pady=4)
        ttk.Button(mods, text='Download OptiFine', command=lambda: webbrowser.open('https://optifine.net/downloads')).pack(side='left')
        self.optifine_button = ttk.Button(mods, text='Install OptiFine JAR…', command=self.install_optifine)
        self.optifine_button.pack(side='left', padx=8)
        self.refresh_button = ttk.Button(mods, text='Refresh versions', command=self.refresh_versions)
        self.refresh_button.pack(side='left')
        self.play = ttk.Button(frame, text='Install / Play', command=self.launch)
        self.play.pack(fill='x', pady=(12, 8))
        self.progress = ttk.Progressbar(frame, maximum=1)
        self.progress.pack(fill='x')
        self.status = tk.StringVar(value='Loading available versions…')
        ttk.Label(frame, textvariable=self.status, wraplength=550).pack(anchor='w', pady=10)
        ttk.Label(frame, text='Local profiles work with single-player and servers that allow unauthenticated clients. Verified servers require Microsoft sign-in.', wraplength=550).pack(anchor='w')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.poll_id = root.after(100, self.poll)
        threading.Thread(target=self.load_versions, daemon=True).start()

    @staticmethod
    def label(frame, text):
        ttk.Label(frame, text=text).pack(anchor='w', pady=(10, 2))

    def load_versions(self):
        installed = self.installed_versions()
        try:
            releases = [v['id'] for v in mc.utils.get_version_list() if v['type'] == 'release']
            self.events.put(('versions', list(dict.fromkeys(installed + releases))))
        except Exception:
            self.events.put(('versions', installed))
            self.events.put(('status', 'Version list unavailable. You can type a version manually.'))

    @staticmethod
    def installed_versions():
        return sorted((p.parent.name for p in (GAME / 'versions').glob('*/*.json') if p.stem == p.parent.name), reverse=True)

    def refresh_versions(self):
        if not self.busy:
            threading.Thread(target=self.load_versions, daemon=True).start()

    def install_optifine(self):
        if self.busy:
            return
        version = self.version.get().strip()
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', version) or version in ('.', '..') or 'optifine' in version.lower():
            messagebox.showerror('Choose base version', 'Choose a vanilla Minecraft version first, such as 1.20.1.')
            return
        filename = filedialog.askopenfilename(title='Select the matching OptiFine installer from optifine.net', filetypes=[('OptiFine installer', '*.jar')])
        if not filename:
            return
        jar = Path(filename).resolve()
        self.root.clipboard_clear()
        self.root.clipboard_append(str(GAME))
        messagebox.showinfo('OptiFine installation', f'The launcher will prepare Minecraft {version}, then open the official installer.\n\nIn the installer, set Folder to:\n{GAME}\n\nThis path is copied to your clipboard. Click Install, then close the installer. Use a JAR matching Minecraft {version}.')
        before = set(self.installed_versions())
        self.status.set('Preparing Minecraft for OptiFine…')
        def install():
            ensure_launcher_profiles(GAME)
            mc.install.install_minecraft_version(version, str(GAME), callback=self.callbacks())
            java = mc.command.get_minecraft_command(version, str(GAME), local_options('Player'))[0]
            self.events.put(('status', 'OptiFine installer open: set Folder to the copied game path, install, then close it.'))
            with (BASE / 'optifine-install.log').open('w', encoding='utf-8') as log:
                result = subprocess.run([java, '-jar', str(jar)], cwd=GAME, stdout=log, stderr=subprocess.STDOUT)
            installed = self.installed_versions()
            self.events.put(('versions', list(dict.fromkeys(installed + [version]))))
            added = [v for v in installed if v not in before and 'optifine' in v.lower()]
            if result.returncode:
                self.events.put(('error', 'OptiFine installer failed. See optifine-install.log.'))
            elif added:
                self.events.put(('select', added[0]))
                self.events.put(('status', f'OptiFine installed: {added[0]}. Press Install / Play.'))
            else:
                self.events.put(('status', 'Installer closed. No new OptiFine version found here; check the installer Folder, or select an existing OptiFine version.'))
        self.worker(install)

    def callbacks(self):
        return {key: (lambda value, event=event: self.events.put((event, value))) for key, event in [('setStatus', 'status'), ('setMax', 'maximum'), ('setProgress', 'progress')]}

    def set_busy(self, value):
        self.busy = value
        for button in (self.play, self.login_button, self.optifine_button, self.refresh_button):
            button.configure(state='disabled' if value else 'normal')

    def worker(self, action):
        self.set_busy(True)
        def run():
            try:
                action()
            except Exception as error:
                # HTTP response data can contain secrets. Never display it.
                if isinstance(error, mc.exceptions.AzureAppNotPermitted):
                    text = 'This Azure app needs Minecraft API permission. See README.md.'
                elif isinstance(error, mc.exceptions.AccountNotOwnMinecraft):
                    text = 'No Minecraft Java profile found. Check account ownership and profile setup.'
                elif isinstance(error, FileNotFoundError):
                    text = 'A game file or Java runtime is missing. Retry installation and check Java.'
                else:
                    text = f'{type(error).__name__}: operation failed. Check your connection; game startup errors are in game.log.'
                self.events.put(('error', text))
            finally:
                self.events.put(('done', None))
        threading.Thread(target=run, daemon=True).start()

    def sign_in(self):
        if self.busy:
            return
        client = self.client.get().strip()
        try:
            uuid.UUID(client)
        except ValueError:
            messagebox.showerror('Client ID required', 'Enter your own Azure application client ID. See README.md.')
            return
        url, state, verifier = mc.microsoft_account.get_secure_login_data(client, REDIRECT)
        webbrowser.open(url)
        result = simpledialog.askstring('Microsoft sign-in', 'Finish sign-in in your browser, then paste the full redirected URL here:', parent=self.root)
        if not result:
            return
        try:
            code = mc.microsoft_account.parse_auth_code_url(result.strip(), state)
        except Exception:
            messagebox.showerror('Sign-in failed', 'Invalid callback URL or state. Start sign-in again.')
            return
        self.status.set('Signing in…')
        def login():
            self.events.put(('account', mc.microsoft_account.complete_login(client, None, REDIRECT, code, verifier)))
        self.worker(login)

    def launch(self):
        if self.busy:
            return
        try:
            ram = int(self.ram.get())
            if not 1 <= ram <= 32:
                raise ValueError('RAM must be between 1 and 32 GB.')
            version = self.version.get().strip()
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', version) or version in ('.', '..'):
                raise ValueError('Select or enter a Minecraft version.')
            if self.mode.get() == 'Microsoft account':
                if not self.account:
                    raise ValueError('Sign in first, or select Local / no authentication.')
                options = {'username': self.account['name'], 'uuid': self.account['id'], 'token': self.account['access_token']}
            else:
                options = local_options(self.name.get().strip())
        except ValueError as error:
            messagebox.showerror('Cannot launch', str(error))
            return
        options['jvmArguments'] = ['-Xms512M', f'-Xmx{ram}G']
        self.status.set('Checking Minecraft files…')
        def play():
            mc.install.install_minecraft_version(version, str(GAME), callback=self.callbacks())
            command = mc.command.get_minecraft_command(version, str(GAME), options)
            self.events.put(('status', 'Starting Minecraft…'))
            with (BASE / 'game.log').open('w', encoding='utf-8') as log:
                process = subprocess.Popen(command, cwd=GAME, stdout=log, stderr=subprocess.STDOUT)
                self.events.put(('status', 'Minecraft is running. Close the game to play again.'))
                code = process.wait()
            self.events.put(('error', f'Game exited with code {code}. See game.log.') if code else ('status', 'Game closed. Ready to play again.'))
        self.worker(play)

    def poll(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == 'status':
                    self.status.set(value)
                elif event == 'versions':
                    self.versions['values'] = value
                    if not self.busy:
                        self.status.set('Ready. Choose a profile and press Install / Play.')
                elif event == 'maximum':
                    self.progress.configure(maximum=max(1, value), value=0)
                elif event == 'progress':
                    self.progress['value'] = value
                elif event == 'account':
                    self.account = value
                    self.status.set('Signed in as ' + value['name'])
                elif event == 'select':
                    self.version.set(value)
                elif event == 'error':
                    self.status.set(value)
                    messagebox.showerror('Launcher error', value)
                elif event == 'done':
                    self.set_busy(False)
        except queue.Empty:
            pass
        self.poll_id = self.root.after(100, self.poll)

    def close(self):
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    ensure_launcher_profiles(GAME)
    root = tk.Tk()
    Launcher(root)
    root.mainloop()


if __name__ == '__main__':
    main()

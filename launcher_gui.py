"""Craftline desktop launcher. Authentication tokens stay in memory."""
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
import os
import sys
import minecraft_launcher_lib as mc
from launcher_core import (Settings, new_profile, local_options, ensure_launcher_profiles,
                           register_version, installed_versions, base_version, APP_VERSION)
import mod_installers
from launcher_theme import apply_theme

BASE = Path(__file__).resolve().parent
GAME = Path(mc.utils.get_minecraft_directory())
REDIRECT = 'https://login.microsoftonline.com/common/oauth2/nativeclient'


def game_log(name):
    logs = GAME / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    return logs / name


class Launcher:
    def __init__(self, root):
        self.root, self.events = root, queue.Queue()
        self.account, self.busy = None, False
        ensure_launcher_profiles(GAME)
        self.settings = Settings(GAME)
        self.loading = False
        self.save_pending = None
        self.font_family = apply_theme(root)
        root.title('Craftline · Minecraft Java')
        icon = mod_installers.resources() / 'craftline.ico'
        if icon.exists():
            root.iconbitmap(str(icon))
        root.geometry('820x780')
        root.minsize(760, 740)
        frame = ttk.Frame(root, padding=26)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Craftline', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='MINECRAFT JAVA  /  YOUR PROFILES, READY TO PLAY', style='Muted.TLabel').pack(anchor='w', pady=(2, 18))
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', pady=(0, 18))
        self.profile = tk.StringVar()
        self.profile_picker = ttk.Combobox(toolbar, textvariable=self.profile, state='readonly', width=32)
        self.profile_picker.pack(side='left', fill='x', expand=True)
        self.profile_picker.bind('<<ComboboxSelected>>', self.switch_profile)
        self.new_button = ttk.Button(toolbar, text='+ New', command=self.add_profile)
        self.new_button.pack(side='left', padx=8)
        self.remove_button = ttk.Button(toolbar, text='Remove', command=self.remove_profile)
        self.remove_button.pack(side='left')
        tabs = ttk.Notebook(frame)
        tabs.pack(fill='both', expand=True)
        play_page, mods, settings_page = [ttk.Frame(tabs, padding=(14, 16)) for _ in range(3)]
        for page, name in [(play_page, 'Play'), (mods, 'Install mods'), (settings_page, 'Settings')]:
            tabs.add(page, text=name)
        self.mode, self.name, self.client = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.version, self.ram, self.server = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.label(play_page, 'Account type')
        ttk.Combobox(play_page, textvariable=self.mode, values=['Microsoft account', 'Local / no authentication'], state='readonly').pack(fill='x')
        self.label(play_page, 'Local username')
        ttk.Entry(play_page, textvariable=self.name).pack(fill='x')
        ttk.Label(play_page, text='Keep the same username to keep your identity on local-account servers.', style='Muted.TLabel').pack(anchor='w', pady=(4, 6))
        self.login_button = ttk.Button(play_page, text='Sign in with Microsoft', command=self.sign_in)
        self.login_button.pack(anchor='w', pady=4)
        row = ttk.Frame(play_page)
        row.pack(fill='x', pady=8)
        ttk.Label(row, text='Version').pack(side='left')
        self.versions = ttk.Combobox(row, textvariable=self.version, width=35)
        self.versions.pack(side='left', padx=8, fill='x', expand=True)
        ttk.Label(row, text='RAM (GB)').pack(side='left')
        ttk.Spinbox(row, from_=1, to=32, textvariable=self.ram, width=5).pack(side='left', padx=8)
        self.label(play_page, 'Server address (optional — leave empty for the main menu)')
        ttk.Entry(play_page, textvariable=self.server).pack(fill='x')
        ttk.Label(play_page, text='Servers with account verification require Microsoft sign-in and Minecraft ownership.', style='Muted.TLabel', wraplength=680).pack(anchor='w', pady=12)
        self.play = ttk.Button(play_page, text='Play', style='Accent.TButton', command=self.launch)
        self.play.pack(fill='x', pady=4)
        ttk.Label(mods, text='Install once. Choose it like any version.', style='Section.TLabel').pack(anchor='w', pady=(4, 12))
        ttk.Label(mods, text='Each modded installation stays separate from vanilla. Your saves stay in the standard .minecraft folder.', style='Muted.TLabel', wraplength=670).pack(anchor='w')
        self.mod_version = tk.StringVar()
        self.label(mods, 'Minecraft release for Iris')
        self.mod_versions = ttk.Combobox(mods, textvariable=self.mod_version)
        self.mod_versions.pack(fill='x')
        self.iris_button = ttk.Button(mods, text='Install Iris + Sodium', style='Accent.TButton', command=self.install_iris)
        self.iris_button.pack(fill='x', pady=(12, 24))
        ttk.Label(mods, text='OptiFine', style='Section.TLabel').pack(anchor='w')
        ttk.Label(mods, text='Download the official OptiFine JAR, then select it here. Its matching Minecraft version and launch profile are prepared automatically.', style='Muted.TLabel', wraplength=670).pack(anchor='w', pady=8)
        ttk.Button(mods, text='Open official OptiFine downloads', command=lambda: webbrowser.open('https://optifine.net/downloads')).pack(fill='x')
        self.optifine_button = ttk.Button(mods, text='Install OptiFine JAR…', command=self.install_optifine)
        self.optifine_button.pack(fill='x', pady=8)
        self.label(settings_page, 'Microsoft Azure application client ID')
        ttk.Entry(settings_page, textvariable=self.client).pack(fill='x')
        ttk.Label(settings_page, text='Microsoft sign-in requires a permitted application ID. Login opens your browser; passwords and tokens are never saved in the profile file.', style='Muted.TLabel', wraplength=670).pack(anchor='w', pady=10)
        self.label(settings_page, 'Game folder')
        ttk.Label(settings_page, text=str(GAME), wraplength=670).pack(anchor='w', pady=6)
        ttk.Button(settings_page, text='Open .minecraft', command=lambda: os.startfile(GAME)).pack(anchor='w', pady=6)
        ttk.Button(settings_page, text='Open shader packs', command=self.open_shaderpacks).pack(anchor='w', pady=6)
        self.refresh_button = ttk.Button(settings_page, text='Refresh installed versions', command=self.refresh_versions)
        self.refresh_button.pack(anchor='w', pady=6)
        ttk.Label(settings_page, text='Profiles are saved automatically in .minecraft/craftline-launcher/settings.json.\nCraftline ' + APP_VERSION + ' · Independent launcher · Manrope font', style='Muted.TLabel', wraplength=670).pack(anchor='w', pady=16)
        self.progress = ttk.Progressbar(frame, maximum=1)
        self.progress.pack(fill='x', pady=(18, 0))
        self.status = tk.StringVar(value='Loading available versions…')
        ttk.Label(frame, textvariable=self.status, wraplength=740, style='Muted.TLabel').pack(anchor='w', pady=10)
        self.update_profile_picker()
        self.apply_profile()
        self.settings.save()
        for variable in (self.mode, self.name, self.client, self.version, self.ram, self.server):
            variable.trace_add('write', self.schedule_save)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.poll_id = root.after(100, self.poll)
        threading.Thread(target=self.load_versions, daemon=True).start()
        if self.settings.notice:
            root.after_idle(lambda: messagebox.showwarning('Recovered profile', self.settings.notice))

    def open_shaderpacks(self):
        path = GAME / 'shaderpacks'
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def update_profile_picker(self):
        labels = [p['label'] for p in self.settings.data['profiles']]
        self.profile_picker['values'] = labels
        self.profile_picker.current(self.settings.data['profiles'].index(self.settings.active))

    def apply_profile(self):
        self.loading = True
        p = self.settings.active
        for variable, key in [(self.mode, 'mode'), (self.name, 'username'), (self.client, 'client_id'), (self.version, 'version'), (self.ram, 'ram'), (self.server, 'server')]:
            variable.set(p[key])
        self.mod_version.set(base_version(GAME, p['version']))
        self.loading = False

    def schedule_save(self, *_):
        if self.loading:
            return
        if self.save_pending is not None:
            self.root.after_cancel(self.save_pending)
        self.save_pending = self.root.after(500, self.save_profile)

    def save_profile(self):
        if self.save_pending is not None:
            self.root.after_cancel(self.save_pending)
        self.save_pending = None
        p = self.settings.active
        # Do not replace the last valid identity while the user is halfway through typing.
        try:
            identity = local_options(self.name.get().strip())
        except ValueError:
            return False
        p.update(username=identity['username'], uuid=identity['uuid'], mode=self.mode.get(),
                 version=self.version.get().strip(), ram=self.ram.get(), server=self.server.get().strip(), client_id=self.client.get().strip())
        self.settings.save()
        return True

    def switch_profile(self, *_):
        if self.busy:
            return
        self.save_profile()
        index = self.profile_picker.current()
        self.settings.data['active'] = self.settings.data['profiles'][index]['id']
        self.account = None
        self.apply_profile()
        self.settings.save()

    def add_profile(self):
        if self.busy:
            return
        label = simpledialog.askstring('New profile', 'Profile name:', parent=self.root)
        if not label or not label.strip():
            return
        self.save_profile()
        p = new_profile(label.strip(), self.settings.active['username'], self.version.get())
        self.settings.data['profiles'].append(p)
        self.settings.data['active'] = p['id']
        self.account = None
        self.update_profile_picker()
        self.apply_profile()
        self.settings.save()

    def remove_profile(self):
        if self.busy or len(self.settings.data['profiles']) == 1:
            return
        if not messagebox.askyesno('Remove profile', 'Remove this launcher profile? Game files and saves are kept.'):
            return
        self.settings.data['profiles'].remove(self.settings.active)
        self.settings.data['active'] = self.settings.data['profiles'][0]['id']
        self.account = None
        self.update_profile_picker()
        self.apply_profile()
        self.settings.save()

    @staticmethod
    def label(frame, text):
        ttk.Label(frame, text=text).pack(anchor='w', pady=(10, 2))

    def load_versions(self):
        installed = self.installed_versions()
        try:
            releases = [v['id'] for v in mc.utils.get_version_list() if v['type'] == 'release']
            self.events.put(('releases', releases))
            self.events.put(('versions', list(dict.fromkeys(installed + releases))))
        except Exception:
            self.events.put(('versions', installed))
            self.events.put(('status', 'Version list unavailable. You can type a version manually.'))

    @staticmethod
    def installed_versions():
        return installed_versions(GAME)

    def refresh_versions(self):
        if not self.busy:
            threading.Thread(target=self.load_versions, daemon=True).start()

    def install_optifine(self):
        if self.busy:
            return
        filename = filedialog.askopenfilename(title='Select the matching OptiFine installer from optifine.net', filetypes=[('OptiFine installer', '*.jar')])
        if not filename:
            return
        version = base_version(GAME, self.version.get().strip())
        self.save_profile()
        self.status.set('Preparing Minecraft for OptiFine…')
        def install():
            selected = mod_installers.install_optifine(filename, version, GAME, self.callbacks())
            self.events.put(('installed', selected))
        self.worker(install)

    def install_iris(self):
        if self.busy:
            return
        version = self.mod_version.get().strip()
        self.save_profile()
        self.status.set('Preparing Iris + Sodium…')
        def install():
            selected = mod_installers.install_iris(version, GAME, self.callbacks())
            self.events.put(('installed', selected))
        self.worker(install)

    def callbacks(self):
        return {key: (lambda value, event=event: self.events.put((event, value))) for key, event in [('setStatus', 'status'), ('setMax', 'maximum'), ('setProgress', 'progress')]}

    def set_busy(self, value):
        self.busy = value
        for button in (self.play, self.login_button, self.optifine_button, self.refresh_button, self.iris_button, self.new_button, self.remove_button):
            button.configure(state='disabled' if value else 'normal')
        self.profile_picker.configure(state='disabled' if value else 'readonly')

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
                elif isinstance(error, ValueError):
                    text = str(error)
                elif isinstance(error, FileNotFoundError):
                    text = 'A game file or Java runtime is missing. Retry installation and check Java.'
                else:
                    text = f'{type(error).__name__}: operation failed. Check your connection; game startup errors are in .minecraft/logs/launcher.log.'
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
        server = self.server.get().strip()
        if server:
            if any(c.isspace() for c in server) or len(server) > 255:
                messagebox.showerror('Server address', 'Enter a hostname or hostname:port without spaces.')
                return
            options['quickPlayMultiplayer'] = server
        self.save_profile()
        self.status.set('Checking Minecraft files…')
        def play():
            ensure_launcher_profiles(GAME)
            mc.install.install_minecraft_version(version, str(GAME), callback=self.callbacks())
            register_version(GAME, version)
            command = mc.command.get_minecraft_command(version, str(GAME), options)
            self.events.put(('status', 'Starting Minecraft…'))
            with game_log('launcher.log').open('w', encoding='utf-8') as log:
                process = subprocess.Popen(command, cwd=GAME, stdout=log, stderr=subprocess.STDOUT, creationflags=mod_installers.CREATE_NO_WINDOW)
                self.events.put(('status', 'Minecraft is running. Close the game to play again.'))
                code = process.wait()
            self.events.put(('error', f'Game exited with code {code}. See .minecraft/logs/launcher.log.') if code else ('status', 'Game closed. Ready to play again.'))
        self.worker(play)

    def poll(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == 'status':
                    self.status.set(value)
                elif event == 'versions':
                    self.versions['values'] = list(dict.fromkeys(self.installed_versions() + list(value)))
                    if not self.busy:
                        self.status.set('Ready. Choose a profile and press Install / Play.')
                elif event == 'releases':
                    self.release_versions = value
                    self.mod_versions['values'] = value
                elif event == 'maximum':
                    self.progress.configure(maximum=max(1, value), value=0)
                elif event == 'progress':
                    self.progress['value'] = value
                elif event == 'account':
                    self.account = value
                    self.mode.set('Microsoft account')
                    self.status.set('Signed in as ' + value['name'])
                elif event == 'select':
                    self.version.set(value)
                    self.save_profile()
                elif event == 'installed':
                    self.versions['values'] = list(dict.fromkeys(self.installed_versions() + getattr(self, 'release_versions', [])))
                    self.version.set(value)
                    self.save_profile()
                    self.status.set(value + ' installed and selected. Return to Play to launch it.')
                elif event == 'error':
                    self.status.set(value)
                    messagebox.showerror('Launcher error', value)
                elif event == 'done':
                    self.set_busy(False)
        except queue.Empty:
            pass
        self.poll_id = self.root.after(100, self.poll)

    def close(self):
        if self.save_pending is not None:
            self.root.after_cancel(self.save_pending)
        self.save_profile()
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    ensure_launcher_profiles(GAME)
    root = tk.Tk()
    Launcher(root)
    root.mainloop()


if __name__ == '__main__':
    main()

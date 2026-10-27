"""A small dark theme and privately bundled Manrope font."""
import ctypes
import sys
import tkinter.font as font
from tkinter import ttk
from mod_installers import resources

BACKGROUND = '#10171b'
PANEL = '#192328'
TEXT = '#e8eeed'
MUTED = '#a0b2b4'
ACCENT = '#77d5b3'


def apply_theme(root):
    family = 'Segoe UI'
    if sys.platform == 'win32':
        path = resources() / 'fonts' / 'Manrope.ttf'
        if path.exists():
            ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)
            if 'Manrope' in font.families(root):
                family = 'Manrope'
    for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont'):
        font.nametofont(name, root).configure(family=family, size=10)
    root.configure(background=BACKGROUND)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=BACKGROUND, foreground=TEXT, font=(family, 10))
    style.configure('TFrame', background=BACKGROUND)
    style.configure('TLabel', background=BACKGROUND, foreground=TEXT)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('Title.TLabel', font=(family, 25, 'bold'))
    style.configure('Section.TLabel', font=(family, 13, 'bold'))
    style.configure('TButton', background=PANEL, foreground=TEXT, padding=(15, 9), borderwidth=0)
    style.map('TButton', background=[('active', '#283b42'), ('disabled', '#182023')], foreground=[('disabled', '#63787c')])
    style.configure('Accent.TButton', background=ACCENT, foreground='#0c231c', font=(family, 11, 'bold'), padding=13)
    style.map('Accent.TButton', background=[('active', '#a0e4cc'), ('disabled', '#29443a')], foreground=[('disabled', '#829e92')])
    style.configure('TEntry', fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT, bordercolor='#31464b', padding=8)
    style.configure('TCombobox', fieldbackground=PANEL, background=PANEL, foreground=TEXT, arrowcolor=ACCENT, padding=7)
    style.map('TCombobox', fieldbackground=[('readonly', PANEL)], foreground=[('readonly', TEXT)])
    style.configure('TSpinbox', fieldbackground=PANEL, foreground=TEXT, arrowcolor=ACCENT, padding=7)
    style.configure('TNotebook', background=BACKGROUND, borderwidth=0)
    style.configure('TNotebook.Tab', background=PANEL, foreground=MUTED, padding=(22, 10))
    style.map('TNotebook.Tab', background=[('selected', '#263b3c')], foreground=[('selected', ACCENT)])
    style.configure('Horizontal.TProgressbar', background=ACCENT, troughcolor=PANEL, borderwidth=0)
    root.option_add('*TCombobox*Listbox.background', PANEL)
    root.option_add('*TCombobox*Listbox.foreground', TEXT)
    root.option_add('*TCombobox*Listbox.selectBackground', '#355950')
    return family

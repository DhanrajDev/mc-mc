# Project state

Simple Tkinter Minecraft Java launcher with release selection, RAM control, progress callbacks, error dialogs, and game.log. Microsoft sign-in uses an operator-supplied Azure client ID, browser PKCE, and pasted callback URL. Tokens remain in memory. Local/no-auth profiles also available. Game download and execution run off the UI thread. Uses existing my_cracked_minecraft directory.

Validation: see validation.md. Real account login, full game download, gameplay and multiplayer require live verification.

OptiFine support: official download link, local JAR installer workflow using the base game's Java, copied target path, local version scan and automatic selection. Installer requires user to set its Folder. Seven offline tests pass; actual OptiFine install/gameplay unverified.

Friend setup: Launch.bat now discovers an existing environment, the Windows Python launcher, or Python on PATH. bootstrap.py creates .venv and installs pinned requirements on first run or requirements changes, then opens the GUI. Requires Python3.10+ with Tcl/Tk; does not bundle Python. Logs ignored and game.log removed from Git index while retained locally. Clean-copy first setup and repeat setup passed on Python3.14, from a path with spaces; seven existing tests pass. Other Windows machines/Python versions not directly tested.

OptiFine metadata correction: launcher_profiles.json was missing in the live game folder although 26.2 base files existed. Created non-destructive empty metadata locally. Launcher startup and installer preparation now ensure this file exists before use; eight offline tests pass. Official installer retry/gameplay still unverified.

# Minecraft Java Launcher

## Friend setup (Windows)

1. Install Python 3.10 or newer from https://www.python.org/downloads/windows/ with Tcl/Tk and the Python launcher included.
2. Clone this Git repository, or download its ZIP and extract it to a writable folder.
3. Double-click Launch.bat. First run creates .venv and installs dependencies automatically; internet is required. Subsequent runs reuse it.

The project can live in a path containing spaces. Each friend gets their own environment and Minecraft files; neither is included in Git. No fixed user paths are required. Java for the selected Minecraft release is downloaded by the game installation step.

To set up without opening the window, run `Launch.bat --setup-only`.

Once set up, you can also run:

```powershell
.\.venv\Scripts\python.exe launcher.py
```

Choose a release version (or type one), RAM allowance, and profile. Install / Play downloads missing game files and the matching Java runtime using minecraft-launcher-lib. Download work runs in a background thread with visible progress. Startup output goes to game.log.

## Microsoft online play

Requires an account with Minecraft Java access and your own Azure application client ID approved to use the Minecraft API. Register an application supporting personal Microsoft accounts, with the Mobile/Desktop redirect URI:

https://login.microsoftonline.com/common/oauth2/nativeclient

Paste the client ID into the launcher, press Sign in with Microsoft, finish in your browser, and paste the full redirected URL into the prompt. PKCE and state validation are used; no client secret is required. Tokens remain in memory; sign in again after closing the launcher or when the session expires. Never share the callback URL. New applications may require Minecraft API approval before sign-in works.

Setup reference: https://minecraft-launcher-lib.readthedocs.io/en/stable/tutorial/microsoft_login.html

## Local / no authentication

Select this profile, enter a username, and press Install / Play. Supports single-player and servers configured to accept unauthenticated clients. It cannot join servers that require a verified Minecraft account.

Game files remain in my_cracked_minecraft, preserving the original script's location. launcher_original.py is the original console script backup. No downloads occur until Install / Play is pressed, apart from fetching the version list.

## Dependencies

Python 3.10 or newer with tkinter. The environment is created locally, not shared. Manual setup, if needed:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## OptiFine

1. Select the vanilla version you want (for example 1.20.1).
2. Click Download OptiFine and download the matching official installer JAR.
3. Click Install OptiFine JAR and select that file. The launcher prepares the base game and its Java runtime.
4. In the official installer, set Folder to this launcher's my_cracked_minecraft directory. The complete path is copied to your clipboard. Click Install, then close the installer.
5. The new OptiFine version is selected automatically. Press Install / Play.

Refresh versions rescans locally installed versions. These remain listed even if the online manifest is unavailable. Installation errors are recorded in optifine-install.log. A matching OptiFine release must exist for the chosen Minecraft version; this launcher does not bundle or redistribute OptiFine.

The launcher creates launcher_profiles.json on startup for OptiFine compatibility, preserving any existing file. If installing OptiFine manually, open this launcher once first to prepare the game folder.

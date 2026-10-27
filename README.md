# Craftline 1.0.0

A small independent Minecraft Java launcher for Windows, with saved profiles and direct Iris/OptiFine installation. Not affiliated with Mojang or Microsoft.

## Install and share

Run Craftline-Setup.exe. Python and Tcl/Tk are included: friends do not need Python, pip, or a JDK. The installer adds Start-menu and optional Desktop shortcuts. Internet is required for game/mod downloads. Minecraft itself is not bundled.

Uninstalling Craftline removes the application, not your Minecraft saves, mods or profiles.

## Play and identity

Use the Play tab to choose a saved profile, account type, username, Minecraft version and RAM. The optional server address joins that server when supported by the selected game version; leave it empty for the main menu.

Profiles save automatically, including the username, standard deterministic local UUID, version, RAM, server address and public Azure client ID. Keep the same username to retain your identity on servers that accept local accounts. Changing that name changes the local identity. Verified servers require Microsoft sign-in and Minecraft ownership.

Profiles are shared between source and installed builds at:

```text
%APPDATA%\.minecraft\craftline-launcher\settings.json
```

The first run imports your last username from Minecraft's log if available. Malformed settings are preserved in a recovery copy. Passwords, access tokens and refresh tokens are not written to this file. Microsoft sessions are kept in memory, so sign in again after restarting.

## Iris + Sodium

1. Open Install mods and select the Minecraft release.
2. Click Install Iris + Sodium.
3. Return to Play. The new Iris version is listed, selected and saved automatically.

The launcher downloads IrisShaders' official release bundle with Python's HTTPS stack, verifies a published SHA256 if supplied and checks ZIP contents. It prepares Minecraft/Fabric, stores mods in .minecraft\iris-reserved\VERSION and registers the resulting launch profile. The standalone Iris installer is not required. Unsupported versions produce a clear message; choose a supported release.

## OptiFine

1. Open official OptiFine downloads from the Install mods tab and download its installer JAR.
2. Click Install OptiFine JAR and select that file.
3. The launcher identifies the Minecraft version, prepares it, calls the official installer's public installation API and registers/selects the resulting version.

No folder-picker or JSON editing is required. OptiFine is not bundled or redistributed. Iris and OptiFine remain separate versions.

## Standard Minecraft files

All game data uses %APPDATA%\.minecraft, including assets, libraries, Java runtimes, saves, shaderpacks and versions. Missing launcher_profiles.json is created on startup and before installations. Craftline version registrations preserve existing official-launcher entries.

Logs: .minecraft\logs\launcher.log and .minecraft\logs\optifine-install.log. Settings contains an Open shader packs shortcut; install a shader pack separately if desired.

## Microsoft sign-in

Requires an account with Minecraft Java access and an Azure application client ID permitted to access the Minecraft API. Enter the public client ID under Settings. Configure its Mobile/Desktop redirect URI as:

```text
https://login.microsoftonline.com/common/oauth2/nativeclient
```

Click Sign in with Microsoft, finish sign-in in your browser, and paste the full redirected URL into the prompt. PKCE/state validation are used; no client secret is required. Never share a callback URL. New applications may require Minecraft API permission.

Documentation: https://minecraft-launcher-lib.readthedocs.io/en/stable/tutorial/microsoft_login.html

## Run source / build

For source clones, install Python3.10+ with Tcl/Tk and double-click Launch.bat. It prepares .venv automatically. Use Launch.bat --setup-only for dependency setup only.

To build on Windows, install Inno Setup6 and run:

```powershell
.\build.ps1
# Or specify its compiler explicitly:
.\build.ps1 -InnoCompiler 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
```

Produces dist\Craftline\Craftline.exe and dist\Craftline-Setup.exe. Bundled assets include the private Manrope font (OFL1.1) and a Java8-compatible helper for OptiFine's public API. Tests: .\.venv\Scripts\python.exe -m unittest discover -v

The former project-local my_cracked_minecraft directory is only a retained migration backup, not an active game location. It is excluded from Git along with environments, game data, logs and build outputs.

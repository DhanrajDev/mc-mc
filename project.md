# Craftline — project state

Version1.0.0. Windows per-user installer: dist/Craftline-Setup.exe. Standalone frozen app: dist/Craftline/Craftline.exe. Python/Tcl/Tk and Manrope font are bundled; no Python or JDK required for friends. Java runtime for Minecraft is installed with the selected game release.

Persistent named profiles live in %APPDATA%/.minecraft/craftline-launcher/settings.json. Saved: local username/standard deterministic UUID, selected version, RAM, optional server, account mode and public Azure client ID. Initial profile imports the most recent game username and prefers an installed Iris version. Atomic allow-listed writes exclude tokens; corrupt config gets a recovery copy. Account access/refresh tokens remain memory-only, so Microsoft users sign in after restart and need a permitted Azure application ID.

All game files use the standard .minecraft folder. Missing launcher_profiles.json is created at startup and before installations; Craftline registrations preserve existing official entries. Installed custom JSON profiles are discovered without a network manifest. Installed Iris/OptiFine versions are added, selected and saved as soon as installation completes.

Iris: downloads IrisShaders' official release ZIP through Python HTTPS, validates available SHA256 and ZIP contents, installs Minecraft/Fabric and stores Iris+Sodium under iris-reserved/VERSION. No standalone Iris installer required. OptiFine: user downloads official JAR; bundled Java8 helper reads its version and invokes its public doInstall(File) API headlessly into .minecraft. Separate versions avoid OptiFine/Iris conflicts. Shader pack selection remains in-game.

Interface: dark slate/mint colors, privately loaded Manrope font, custom cube icon, Play/Install mods/Settings tabs, saved profile picker, optional server quick-play and game/shader folder shortcuts.

Validation:14 offline tests pass. Source, frozen and installed fresh-folder smoke tests pass. Live Iris26.3 and OptiFine26.2 installations passed in an isolated metadata folder with existing caches reused; each registered its resulting profile. Installed EXE passed with PATH limited to Windows System32. Silent install/uninstall succeeded and preserved actual Minecraft config/game files. Source Iris26.3 rendering was verified in the previous runtime check; this build's Microsoft authentication, actual multiplayer identity on a server and shader-pack graphics are not live-verified. Friend machine untested; executable unsigned.

Build: build.ps1 plus Craftline.spec and installer.iss; PyInstaller6.22.3/InnoSetup6.7.3. Never package game data, personal settings or tokens. Legacy my_cracked_minecraft is retained solely as a migration backup and is ignored by Git.

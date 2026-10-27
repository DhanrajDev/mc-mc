# Validation

- Python compilation and Tk window creation passed.
- Five offline unittest checks passed: online account required before install; local install/progress/launch; install failure recovery; OAuth state mismatch rejection; authenticated profile passed to launch command.
- Live Mojang version manifest fetched: 920 entries.
- GUI started using the project environment.
- Full game download, Java execution, actual Microsoft sign-in and multiplayer not verified. Microsoft sign-in requires a permitted Azure application client ID.

Run: .\.venv\Scripts\python.exe -m unittest test_launcher -v

OptiFine update: seven tests pass total. Added offline-version discovery and installer handoff/runtime/profile selection checks. Python compilation passed. Official installer and gameplay have not been run.

Friend setup validation (October 25):
- Clean source copy without .venv in a different path containing spaces: Launch.bat --setup-only created its environment and installed all requirements successfully via py -3 fallback.
- Repeated setup reused that environment without reinstalling dependencies.
- Existing checkout setup passed; all seven launcher tests pass.
- Verified on this Windows machine with Python3.14 only; no friend-PC execution claimed.

OptiFine missing-profile repair: confirmed live file absent and Minecraft26.2 metadata present. Created launcher_profiles.json; eight tests pass, including creating a new profile file and byte-preserving an existing one. Installer retry remains user verification.

Standard-folder migration (October 25): launcher GAME now uses minecraft-launcher-lib's standard directory (%APPDATA%\.minecraft on Windows). Copied 38 missing files and hash-checked copies; 9,647 existing files matched. Four differing destination files were retained (options.txt, latest.log, the installed Iris game JAR, and a runtime hash index); source remains for rollback. Both saves folders were empty. Repaired Iris's modsFolder JVM argument, saving prior metadata under .minecraft/.launcher-migration-backup. Eight existing tests pass. New game process command confirms default gameDir and modsFolder, with no legacy-folder reference. Logs load Iris1.11.7 and Sodium0.9.2 on Minecraft26.3/Fabric0.20.1. Microsoft multiplayer and a shader pack are not verified.

## Craftline1.0.0 build validation — October25

-14 offline unittest checks pass: local/online launch setup, failure recovery, OAuth state validation, fresh metadata, preservation of existing profiles, stable identity/config across restart, corrupt-config recovery, installed-version discovery, OptiFine selection, rejection of unrelated JARs, Iris package download with no Content-Length and its registration.
- Source/frozen/installed --smoke-test passes in a disposable empty .minecraft: creates launcher_profiles.json; loads Manrope; installed modded version appears, is selected and persists; username/UUID/server/RAM survive restart.
- Live one-click backend installs: Iris1.11.7+Sodium0.9.2 for26.3 and OptiFine26.2_K2_pre5. Isolated game metadata with junctions to existing asset/library/runtime caches; vanilla26.2/26.3 metadata/JAR copied into proof folder. Both resulting profiles registered in launcher_profiles.json and discovered by installed_versions. This does not represent an entirely uncached full-game download.
- Packaged app verified without Python on PATH (PATH=Windows System32); no dependency on the source .venv. Python314/TclTk90/font/Java bridge included.
- Inno per-user installer built successfully. Silent install into workspace proof folder and installed-app smoke passed. Silent uninstall returned0; actual user's settings SHA256 unchanged and installed Iris metadata still exists.
- Prior runtime game command/log proof: Iris26.3 launched from standard .minecraft, Iris1.11.7/Sodium0.9.2 loaded, render pipeline and sound initialized. No shaderpack selected. This build's multiplayer/authenticated session and visual shaderpack operation not live-tested. Other computers not tested; installer unsigned.

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

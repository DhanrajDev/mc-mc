# Validation

- Python compilation and Tk window creation passed.
- Five offline unittest checks passed: online account required before install; local install/progress/launch; install failure recovery; OAuth state mismatch rejection; authenticated profile passed to launch command.
- Live Mojang version manifest fetched: 920 entries.
- GUI started using the project environment.
- Full game download, Java execution, actual Microsoft sign-in and multiplayer not verified. Microsoft sign-in requires a permitted Azure application client ID.

Run: .\.venv\Scripts\python.exe -m unittest test_launcher -v

OptiFine update: seven tests pass total. Added offline-version discovery and installer handoff/runtime/profile selection checks. Python compilation passed. Official installer and gameplay have not been run.

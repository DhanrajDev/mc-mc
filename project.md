# Project state

Simple Tkinter Minecraft Java launcher with release selection, RAM control, progress callbacks, error dialogs, and game.log. Microsoft sign-in uses an operator-supplied Azure client ID, browser PKCE, and pasted callback URL. Tokens remain in memory. Local/no-auth profiles also available. Game download and execution run off the UI thread. Uses existing my_cracked_minecraft directory.

Validation: see validation.md. Real account login, full game download, gameplay and multiplayer require live verification.

OptiFine support: official download link, local JAR installer workflow using the base game's Java, copied target path, local version scan and automatic selection. Installer requires user to set its Folder. Seven offline tests pass; actual OptiFine install/gameplay unverified.

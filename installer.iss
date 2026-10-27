[Setup]
AppId={{EBE3E3B7-E4A5-466A-B258-AC510155B1B2}
AppName=Craftline
AppVersion=1.0.0
AppPublisher=Craftline
DefaultDirName={localappdata}\Programs\Craftline
DefaultGroupName=Craftline
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=dist
OutputBaseFilename=Craftline-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\craftline.ico
UninstallDisplayIcon={app}\Craftline.exe
CloseApplications=yes
SetupLogging=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\Craftline\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Craftline"; Filename: "{app}\Craftline.exe"
Name: "{autodesktop}\Craftline"; Filename: "{app}\Craftline.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Craftline.exe"; Description: "Open Craftline"; Flags: nowait postinstall skipifsilent

; Uninstall removes application files only. Never delete .minecraft or user profiles.

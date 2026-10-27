param([string]$InnoCompiler)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& '.\Launch.bat' --setup-only
if ($LASTEXITCODE -ne 0) { throw 'Launcher environment setup failed' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed' }
& '.\.venv\Scripts\python.exe' -m unittest discover -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
& '.\.venv\Scripts\python.exe' -m PyInstaller Craftline.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
if (-not $InnoCompiler) {
    foreach ($candidate in @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe", "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")) {
        if (Test-Path -LiteralPath $candidate) { $InnoCompiler = $candidate; break }
    }
}
if (-not $InnoCompiler) { throw 'Install Inno Setup 6 from jrsoftware.org or pass -InnoCompiler with the path to ISCC.exe.' }
& $InnoCompiler installer.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
Write-Output 'Built dist\Craftline-Setup.exe'

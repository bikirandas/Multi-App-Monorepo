param(
    [string]$SourceExePath = ".\yt-downloader.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SourceExePath)) {
    Write-Error "Could not find executable at '$SourceExePath'."
}

$appName = "YT Downloader"
$targetDir = Join-Path $env:LOCALAPPDATA "YT-Downloader"
$targetExe = Join-Path $targetDir "yt-downloader.exe"

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
Copy-Item -Path $SourceExePath -Destination $targetExe -Force

$shell = New-Object -ComObject WScript.Shell

$desktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$desktopShortcut = $shell.CreateShortcut($desktopShortcutPath)
$desktopShortcut.TargetPath = $targetExe
$desktopShortcut.WorkingDirectory = $targetDir
$desktopShortcut.IconLocation = "$targetExe,0"
$desktopShortcut.Save()

$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\YT-Downloader"
New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
$startMenuShortcutPath = Join-Path $startMenuDir "$appName.lnk"
$startMenuShortcut = $shell.CreateShortcut($startMenuShortcutPath)
$startMenuShortcut.TargetPath = $targetExe
$startMenuShortcut.WorkingDirectory = $targetDir
$startMenuShortcut.IconLocation = "$targetExe,0"
$startMenuShortcut.Save()

Write-Output "Installed successfully to: $targetExe"
Write-Output "Desktop and Start Menu shortcuts created."

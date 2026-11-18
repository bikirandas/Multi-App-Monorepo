$ErrorActionPreference = "Stop"

$appName = "Boxndots Music & Video Downloader"
$targetDir = Join-Path $env:LOCALAPPDATA "YT-Downloader"
$desktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$appName"
$startMenuShortcutPath = Join-Path $startMenuDir "$appName.lnk"
$legacyDesktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "YT Downloader.lnk"
$legacyStartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\YT-Downloader"

if (Test-Path $desktopShortcutPath) {
    Remove-Item $desktopShortcutPath -Force
}
if (Test-Path $legacyDesktopShortcutPath) {
    Remove-Item $legacyDesktopShortcutPath -Force
}
if (Test-Path $startMenuShortcutPath) {
    Remove-Item $startMenuShortcutPath -Force
}
if (Test-Path $startMenuDir) {
    Remove-Item $startMenuDir -Force
}
if (Test-Path $legacyStartMenuDir) {
    Remove-Item $legacyStartMenuDir -Recurse -Force
}
if (Test-Path $targetDir) {
    Remove-Item $targetDir -Recurse -Force
}

Write-Output "$appName uninstalled successfully."

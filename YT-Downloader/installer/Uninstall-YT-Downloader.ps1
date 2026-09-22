$ErrorActionPreference = "Stop"

$appName = "YT Downloader"
$targetDir = Join-Path $env:LOCALAPPDATA "YT-Downloader"
$desktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\YT-Downloader"
$startMenuShortcutPath = Join-Path $startMenuDir "$appName.lnk"

if (Test-Path $desktopShortcutPath) {
    Remove-Item $desktopShortcutPath -Force
}
if (Test-Path $startMenuShortcutPath) {
    Remove-Item $startMenuShortcutPath -Force
}
if (Test-Path $startMenuDir) {
    Remove-Item $startMenuDir -Force
}
if (Test-Path $targetDir) {
    Remove-Item $targetDir -Recurse -Force
}

Write-Output "YT Downloader uninstalled successfully."

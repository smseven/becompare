param([string]$a)
. C:\Users\charles\workspace\becompare\tools\ui.ps1
$p = Start-Process -FilePath C:\Users\charles\workspace\becompare\bcgui.exe -ArgumentList $a -PassThru
Start-Sleep 3
$p.Refresh()
"before: exited=" + $p.HasExited
if (-not $p.HasExited) {
[U]::SetWindowPos($p.MainWindowHandle, [IntPtr](-1), 20, 20, 1280, 800, 0x40) | Out-Null
Start-Sleep 1
"after pos: exited=" + $p.HasExited }
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }

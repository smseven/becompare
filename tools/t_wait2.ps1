param([string]$a)
$p = Start-Process -FilePath C:\Users\charles\workspace\becompare\bcgui.exe -ArgumentList $a -PassThru
Start-Sleep 3
if ($p.HasExited) { "exited code " + $p.ExitCode } else { "alive"; Stop-Process -Id $p.Id -Force }

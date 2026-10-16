. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$sw = [Diagnostics.Stopwatch]::StartNew()
Start-App 'registry HKCU\Software HKCU\Software\Classes' 1
Start-Sleep -Seconds 8
$script:app.Refresh()
"alive=" + (-not $script:app.HasExited) + " ws(MB)=" + [int]($script:app.WorkingSet64/1MB) + " elapsed=" + $sw.Elapsed.TotalSeconds
$lbl = GetText 702
$lbl
Shot "$sp\regbig.png"
Stop-App

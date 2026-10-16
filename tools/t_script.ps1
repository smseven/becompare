$p = Start-Process -FilePath C:\Users\charles\workspace\becompare\bcgui.exe -ArgumentList "/script C:\Users\charles\AppData\Local\Temp\bcscr\job.bcscript" -PassThru
$p.WaitForExit(20000) | Out-Null
if ($p.HasExited) { "exit=" + $p.ExitCode } else { "still running"; Stop-Process -Id $p.Id -Force }
Get-Content C:\Users\charles\AppData\Local\Temp\bcscr\job.bcscript.log

function RunArg($a) {
  $p = Start-Process -FilePath C:\Users\charles\workspace\becompare\bcgui.exe -ArgumentList $a -PassThru
  if (-not $p.WaitForExit(8000)) { "HUNG: $a"; Stop-Process -Id $p.Id -Force } else { "ok $a exit=" + $p.ExitCode }
}
RunArg "/shellleft C:\Users\charles\AppData\Local\Temp\s1.c"
RunArg "/shelluninstall"

. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$t = "C:\Users\charles\AppData\Local\Temp"
Start-App "hex $t\ha.bin $t\hb.bin" 3
SetText 421 "41 42"
SetText 424 "58 59"
Click 418
Shot "$sp\hex_repl.png"
Click 415
Stop-App
[System.IO.File]::ReadAllText("$t\ha.bin")

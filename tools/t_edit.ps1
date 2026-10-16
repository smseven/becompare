. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$t = "C:\Users\charles\AppData\Local\Temp"
Start-App "edit $t\e1.c" 3
Shot "$sp\ed1.png"
SetText 303 "int"
SetText 306 "long"
Click 308 800
Shot "$sp\ed2.png"
Click 301 800
Stop-App
[System.IO.File]::ReadAllBytes("$t\e1.c").Length
[System.IO.File]::ReadAllText("$t\e1.c")

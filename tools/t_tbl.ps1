. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$t = "C:\Users\charles\AppData\Local\Temp"
Start-App "table $t\c1.csv $t\c2.csv" 3
SetText 331 "1,2"
SetText 332 "60"
Click 105 1200
Shot "$sp\tbl1.png"
Stop-App

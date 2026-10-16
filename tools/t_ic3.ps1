. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$r = "C:\Users\charles\AppData\Local\Temp\bcfm"
Start-App "foldermerge $r\L $r\R" 3
SetText 107 "$r\B"
Click 105 1500
Shot "$sp\ic_fm.png"; Stop-App

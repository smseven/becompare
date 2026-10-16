. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$t = "C:\Users\charles\AppData\Local\Temp"
Start-App "text $t\m1.txt $t\m2.txt" 3
Shot "$sp\aln0.png"
Msg 201 0xB1 15 15 | Out-Null
Msg 202 0xB1 0 0 | Out-Null
Click 247 1500
Shot "$sp\aln1.png"
Click 248 1500
Shot "$sp\aln2.png"
Stop-App

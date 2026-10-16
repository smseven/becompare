. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$d = "C:\Users\charles\AppData\Local\Temp\bcmedia"
Start-App "media $d\a.mp3 $d\b.mp3" 3
Shot "$sp\md1.png"
Stop-App
Start-App "media $d\a.flac $d\b.flac" 3
Shot "$sp\md2.png"
Stop-App

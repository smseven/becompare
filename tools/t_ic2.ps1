. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$t = "C:\Users\charles\AppData\Local\Temp"
Start-App "picture C:\Windows\Web\Wallpaper\Windows\img0.jpg C:\Windows\Web\Wallpaper\Windows\img0.jpg" 3
Shot "$sp\ic_pic.png"; Stop-App
Start-App "merge $t\bcfm\L\conf.txt $t\bcfm\R\conf.txt $t\bcfm\B\conf.txt" 3
Shot "$sp\ic_mrg.png"; Stop-App

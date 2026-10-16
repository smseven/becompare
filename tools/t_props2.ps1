. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
Start-App 'registry HKCU\Software\BCTest\A HKCU\Software\BCTest\B' 3
Shot "$sp\reg2.png"
Stop-App

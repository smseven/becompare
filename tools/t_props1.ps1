. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
Start-App "version C:\Windows\System32\kernel32.dll C:\Windows\System32\ntdll.dll" 3
Shot "$sp\ver1.png"
Stop-App
Start-App 'registry HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize' 3
Shot "$sp\reg1.png"
Stop-App

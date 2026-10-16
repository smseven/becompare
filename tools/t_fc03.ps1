. C:\Users\charles\workspace\becompare\tools\ui.ps1
$sp = "C:\Users\charles\AppData\Local\Temp\claude\C--Users-charles-workspace-becompare\f0658644-16fb-4238-84de-d75a3d46da44\scratchpad"
$t = "C:\Users\charles\AppData\Local\Temp"
$r = "$t\bcfc03"
Remove-Item -Recurse -Force $r -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$r\A", "$r\B" | Out-Null
[System.IO.File]::WriteAllText("$r\A\small.txt", "tiny"); [System.IO.File]::WriteAllText("$r\B\small.txt", "tiny2")
[System.IO.File]::WriteAllBytes("$r\A\mid.bin", (New-Object byte[] 3000)); [System.IO.File]::WriteAllBytes("$r\B\mid.bin", (New-Object byte[] 3100))
[System.IO.File]::WriteAllBytes("$r\A\big.bin", (New-Object byte[] 20000)); [System.IO.File]::WriteAllBytes("$r\B\big.bin", (New-Object byte[] 20001))
(Get-Item "$r\A\big.bin").LastWriteTime = (Get-Date).AddDays(-30)
(Get-Item "$r\B\big.bin").LastWriteTime = (Get-Date).AddDays(-30)
Start-App "folder $r\A $r\B" 3
SetText 161 "1"
SetText 163 "10"
Click 105 1500
Shot "$sp\fc03a.png"
SetText 161 ""
SetText 163 ""
SetText 165 "7"
Click 105 1500
Shot "$sp\fc03b.png"
Stop-App

. C:\Users\charles\workspace\becompare\tools\ui.ps1
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W9 { [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] public static extern bool WritePrivateProfileString(string s, string k, string v, string f); }
"@
$ini = "$env:LOCALAPPDATA\BeCompareAsm\settings.ini"
Remove-Item C:\Users\charles\AppData\Local\Temp\marker.txt -ErrorAction SilentlyContinue
[W9]::WritePrivateProfileString("Convert", ".srt", "cmd.exe /c echo %1 %2 > C:\Users\charles\AppData\Local\Temp\marker.txt", $ini) | Out-Null
Start-App "text C:\Users\charles\AppData\Local\Temp\bcrule\a.srt C:\Users\charles\AppData\Local\Temp\bcrule\b.srt" 3
Stop-App
Get-Content C:\Users\charles\AppData\Local\Temp\marker.txt

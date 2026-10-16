. C:\Users\charles\workspace\becompare\tools\ui.ps1
Start-App "patch C:\Users\charles\AppData\Local\Temp\t.patch" 3
"exited=" + $script:app.HasExited
"OLD: " + ((GetText 201) -replace "`r", " | ")
"NEW: " + ((GetText 202) -replace "`r", " | ")
Stop-App

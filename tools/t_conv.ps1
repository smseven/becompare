. C:\Users\charles\workspace\becompare\tools\ui.ps1
$d = "C:\Users\charles\AppData\Local\Temp\bcdocs"
python C:\Users\charles\workspace\becompare\tools\mk_docs.py $d | Out-Null
foreach ($e in 'docx','rtf','pdf') {
  Start-App "text $d\a.$e $d\b.$e" 3
  "== $e : exited=" + $script:app.HasExited
  "A: " + ((GetText 201) -replace "`r", " | ")
  "B: " + ((GetText 202) -replace "`r", " | ")
  Stop-App
}

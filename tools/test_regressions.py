"""Build and exercise real NASM objects and unattended GUI CLI in isolated fixtures.
Requires Windows, Python 3, NASM and MinGW-w64 (gcc, windres, objcopy).
No desktop input automation, user files or installed settings are used.
"""
from pathlib import Path
import re
import os, re, subprocess, tempfile, json
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "regression"
OUT.mkdir(parents=True, exist_ok=True)
def _mods():
    # keep in step with build-gui.ps1: its $optional list plus the three mandatory modules
    text = (ROOT / "build-gui.ps1").read_text(encoding="utf-8")
    opt = re.search(r"\$optional = ([^\r\n]+)", text).group(1)
    names = re.findall(r"'([a-z0-9_]+)'", opt)
    return ["util", "main", "home"] + names + ["stubs"]


MODS = _mods()
LIBS = ["-l"+s for s in "user32 gdi32 comctl32 comdlg32 shell32 ole32 dwmapi wininet gdiplus uxtheme shlwapi version advapi32 normaliz".split()]
LOG = []
def run(args, cwd=ROOT, timeout=30, expected=0, env=None):
    r = subprocess.run([str(a) for a in args], cwd=cwd, timeout=timeout, capture_output=True, text=True, errors="replace", env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    if r.stdout: print(r.stdout, end="")
    if r.stderr: print(r.stderr, end="")
    assert r.returncode == expected, (args, r.returncode, expected, r.stdout, r.stderr)
    return r
for m in MODS:
    run(["nasm","-f","win64","-I","./",m+".asm","-o",OUT/(m+".obj")],ROOT/"gui")
run(["windres","res/app.rc","-O","coff","-o",OUT/"app.res.o"],ROOT/"gui")
run(["gcc","-mwindows",*[OUT/(m+".obj") for m in MODS],OUT/"app.res.o","-o",OUT/"bcgui.exe",*LIBS])
r=run(["python","tools/hazard.py"])
assert "hazards: 0" in r.stdout
run(["gcc",ROOT/"tools/test_safe_save.c",OUT/"engine.obj",OUT/"textlib.obj",*["-Wl,--wrap="+x for x in ["WriteFile","FlushFileBuffers","ReplaceFileW"]],"-o",OUT/"test_safe_save.exe"])
defs={}
for name in ["inc/app.inc","text.asm","edit_ui.inc","hex.asm","merge.asm","folder.asm"]:
    for line in (ROOT/"gui"/name).read_text(encoding="utf-8").splitlines():
        m=re.match(r"^%define\s+((?:SS_|TV_|HX_|MG_|F_|BC_)[A-Z0-9_]+|E_HR|E_SIZE)\s+([^;]+)",line)
        if m: defs[m[1]]=m[2].strip()
(OUT/"test_layout.h").write_text("\n".join("#define "+k+" "+v for k,v in defs.items()),encoding="utf-8")
exports={"main":["view_can_close","frame_proc","g_nsess","g_sess"],"text":["text_compare","tv_proc","ed_proc"],"hex":["hx_proc"],"merge":["mg_proc"],"folder":["fold_proc","sync_thread"]}
for mod,names in exports.items():
    run(["objcopy",*["--globalize-symbol="+n for n in names],OUT/(mod+".obj"),OUT/(mod+".test.obj")])
run(["gcc","-I",OUT,ROOT/"tools/test_view_state.c",*[OUT/(m+(".test" if m in exports else "")+".obj") for m in MODS],*["-Wl,--wrap="+x for x in ["SendMessageW","GetWindowLongPtrW","GetDlgItem","GetWindowTextW","SetWindowTextW","InvalidateRect","msgbox","DestroyWindow","EnableWindow","SetTimer","KillTimer"]],*LIBS,"-o",OUT/"test_view_state.exe"])
# Keep the fixture directory and logs for inspection. Each run has independent paths.
fixtures=Path(tempfile.mkdtemp(prefix="fixtures-",dir=OUT))
print("Fixtures:",fixtures)
for name in ["test_safe_save","test_view_state"]:
    r=run([OUT/(name+".exe")],fixtures)
    (fixtures/(name+".log")).write_text(r.stdout,encoding="utf-8")
for d in ["left","right","emptyA","emptyB","dirLeft/only-left","dirRight","local-app-data","detail_files/0.html","syncLeft","syncRight"]:
    (fixtures/d).mkdir(parents=True,exist_ok=True)
(fixtures/"left/file.txt").write_text("left",encoding="utf-8")
(fixtures/"right/file.txt").write_text("different",encoding="utf-8")
env=dict(os.environ,LOCALAPPDATA=str(fixtures/"local-app-data"))
def cli(name,args,expected):
    r=run([OUT/"bcgui.exe",*args],fixtures,timeout=10,expected=expected,env=env)
    LOG.append(dict(name=name,exit=r.returncode,pass_=True))
    print("PASS",name)
for name,left,right,output,expected in [
    ("equal folders","emptyA","emptyB","equal.html",0),
    ("different files","left","right","diff.html",1),
    ("report output failure","emptyA","emptyB","absent/out.html",2),
    ("missing input folder","absent","emptyB","missing.html",2),
    ("empty directory difference","dirLeft","dirRight","dirs.html",1),
    ("detail report output failure","left","right","detail.html",2),
]:
    cli(name,["folder",str(fixtures/left),str(fixtures/right),"/report",str(fixtures/output)],expected)
assert not (fixtures/"absent/out.html").exists()
assert "only-left" in (fixtures/"dirs.html").read_text(encoding="utf-8-sig")
cli("snapshot output failure",["folder",str(fixtures/"emptyA"),str(fixtures/"emptyB"),"/snapshot",str(fixtures/"absent/snapshot.bcss")],2)
(fixtures/"syncLeft/new.txt").write_text("sync fixture",encoding="utf-8")
cli("update synchronization",["folder",str(fixtures/"syncLeft"),str(fixtures/"syncRight"),"/sync","update"],0)
assert (fixtures/"syncRight/new.txt").read_text(encoding="utf-8")=="sync fixture"
(fixtures/"cli-results.json").write_text(json.dumps(LOG,indent=2),encoding="utf-8")
print("All regression checks passed: 30 save + 19 state/worker +",len(LOG),"CLI cases")

import os
import re
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# --- settings.asm: policy_one instead of the nested helper
s = open('settings.asm', encoding='utf-8').read().replace('\r\n', '\n')
a = s.index("; policy_load(): administrator policy")
b = s.index("; ---------------------------------------------------------------- shortcuts (CU-01)")
s = s[:a] + """; policy_load(): administrator policy from HKCU and HKLM (HKLM applied last), DWORD values under Software\\Policies\\BeCompareAsm
policy_load:
    PROLOG 64
    mov qword [g_policy], 0
    mov rcx, 0xFFFFFFFF80000001       ; HKCU
    call policy_one
    mov rcx, 0xFFFFFFFF80000002       ; HKLM
    call policy_one
    EPILOG 64

; policy_one(hive)
policy_one:
    PROLOG 128
    mov r12, rcx
    invoke RegOpenKeyExW, r12, &s_pol_key, 0, 0x20019, &rsp+96
    test eax, eax
    jnz .out
    xor ebx, ebx
.v:
    cmp ebx, 4
    jae .close
    mov dword [rsp+104], 0
    mov dword [rsp+108], 4
    lea rax, [pol_vals]
    mov rdx, [rax+rbx*8]
    invoke RegQueryValueExW, [rsp+96], rdx, 0, 0, &rsp+104, &rsp+108
    test eax, eax
    jnz .n
    cmp dword [rsp+104], 0
    je .n
    mov eax, 1
    mov ecx, ebx
    shl eax, cl
    or [g_policy], rax
.n:
    inc ebx
    jmp .v
.close:
    invoke RegCloseKey, [rsp+96]
.out:
    EPILOG 128

""" + s[b:]
open('settings.asm', 'w', encoding='utf-8', newline='\n').write(s)

edit('inc/app.inc', [
    ("%define IDM_ABOUT      1050\n", "%define IDM_ABOUT      1050\n%define IDM_SETTINGS   1060\n"),
    ("%define BC_THEME   (WM_APP+20)\n", "%define BC_THEME   (WM_APP+20)\n%define BC_NEXTDIFF (WM_APP+30)\n%define BC_PREVDIFF (WM_APP+31)\n"),
])

# --- util.asm: fonts and colour overrides
edit('util.asm', [
    ("""    imul rax, 9
    xor edx, edx
    mov ecx, 72
    div rcx
    neg rax
    mov rbx, rax
""", """    mov r12, rax
    mov ecx, 2
    xor edx, edx
    call settings_font
    imul rax, r12
    xor edx, edx
    mov ecx, 72
    div rcx
    neg rax
    mov rbx, rax
    mov ecx, 1
    xor edx, edx
    call settings_font
    imul rax, r12
    xor edx, edx
    mov ecx, 72
    div rcx
    neg rax
    mov r13, rax
    xor ecx, ecx
    lea rdx, [rsp+96]
    call settings_font
"""),
    ("""    mov rax, rbx
    imul rax, 10
    cqo
    mov rcx, 9
    idiv rcx
    invoke CreateFontW, rax, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, 5, 49, &s_consolas
""", """    invoke CreateFontW, r13, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, 5, 49, &rsp+96
"""),
    ("fonts_init:\n    PROLOG 160\n", "fonts_init:\n    PROLOG 288\n"),
    (".brushes:\n    mov rcx, [th_bgbrush]\n", ".brushes:\n    call settings_colors\n    mov rcx, [th_bgbrush]\n"),
])
u = open('util.asm', encoding='utf-8').read()
i = u.index("fonts_init:")
j = u.index("; theme_set(rcx=dark 0/1)")
body = u[i:j].replace("EPILOG 160", "EPILOG 288")
u = u[:i] + body + u[j:]
if "extern settings_font" not in u:
    u = u.replace("global g_iconfont\n", "global g_iconfont\nextern settings_font, settings_colors\n", 1)
open('util.asm', 'w', encoding='utf-8', newline='\n').write(u)

# --- main.asm
edit('main.asm', [
    ("extern fmerge_register, fmerge_create\n", "extern fmerge_register, fmerge_create\nextern settings_show, policy_load, keys_load, g_keytab\n"),
    ("    call fonts_init\n    call ini_path_init\n    call settings_load\n", "    call ini_path_init\n    call policy_load\n    call keys_load\n    call fonts_init\n    call settings_load\n"),
    ("    invoke AppendMenuW, rbx, MF_STRING, IDM_DARK, &m_dk\n", "    invoke AppendMenuW, rbx, MF_STRING, IDM_DARK, &m_dk\n    invoke AppendMenuW, rbx, MF_SEPARATOR, 0, 0\n    invoke AppendMenuW, rbx, MF_STRING, IDM_SETTINGS, &m_set\n"),
    ('WSTR m_ned, "새 텍스트 편집"\n', 'WSTR m_ned, "새 텍스트 편집"\nWSTR m_set, "설정(&S)..."\n'),
    ("    cmp eax, IDM_ABOUT\n", "    cmp eax, IDM_SETTINGS\n    je .c_settings\n    cmp eax, IDM_ABOUT\n"),
])
m = open('main.asm', encoding='utf-8').read()
# settings handler label: append next to the about handler
k = m.index(".c_about:") if ".c_about:" in m else -1
print('c_about at', k)
open('main.asm', 'w', encoding='utf-8', newline='\n').write(m)

# --- folder policy / external tools
f = open('folder_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
f = f.replace("    or rax, [rbx+F_KIND+8]\n    jnz .ro\n", "    or rax, [rbx+F_KIND+8]\n    jnz .ro\n    test qword [g_policy], 1\n    jnz .pol\n")


def add_pol(m):
    return ".pol:\n    invoke msgbox, rsi, &s_pol_blocked, MB_OK|MB_ICONWARNING\n    EPILOG %s\n.ro:\n    invoke msgbox, rsi, &s_ro, MB_OK|MB_ICONINFO\n    EPILOG %s\n" % (m.group(1), m.group(1))


f, n = re.subn(r"\.ro:\n    invoke msgbox, rsi, &s_ro, MB_OK\|MB_ICONINFO\n    EPILOG (\d+)\n", add_pol, f)
print('ro sites', n)
f = f.replace("""    invoke type_for_path, &rsp+96
    invoke add_session, rax, &rsp+96, &rsp+2296, 0
""", """    invoke ext_launch, &rsp+96, &rsp+2296
    test eax, eax
    jnz .d
    invoke type_for_path, &rsp+96
    invoke add_session, rax, &rsp+96, &rsp+2296, 0
""")
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(f)
edit('folder.asm', [
    ("extern str_dup, add_session, set_tab_title, type_for_path\n", "extern str_dup, add_session, set_tab_title, type_for_path, ext_launch, g_policy\n"),
    ('WSTR s_ro, ', 'WSTR s_pol_blocked, "관리자 정책으로 차단된 기능입니다."\nWSTR s_ro, '),
])
edit('ftp.inc', [
    ("ftp_open:\n    PROLOG 2800\n", "ftp_open:\n    PROLOG 2800\n    test qword [g_policy], 4\n    jz .polok\n    xor eax, eax\n    EPILOG 2800\n.polok:\n"),
])
edit('../build-gui.ps1', [("'vtab','props','fmerge'", "'vtab','props','fmerge','settings'")])
print('settings patched')

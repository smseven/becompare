import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
exec(open('../tools/ph.py', encoding='utf-8').read())

f = open('folder.asm', encoding='utf-8').read()
def repf(a, b, cnt=1):
    global f
    assert f.count(a) == cnt, (a[:60], f.count(a))
    f = f.replace(a, b)
repf("extern CreateDirectoryW, _wcsnicmp\n", """extern CreateDirectoryW, _wcsnicmp, EnableWindow, GetMessageW, TranslateMessage, DispatchMessageW, PostQuitMessage, DestroyWindow
extern th_type, th_diff
%define CB_ADDSTRING 0x0143
%define CB_SETCURSEL 0x014E
%define CB_GETCURSEL 0x0147
%define CBS_DROPDOWNLIST 3
%define CBN_SELCHANGE 1
""")
repf('WSTR cn_list, "SysListView32"', 'WSTR cn_list, "SysListView32"\nWSTR cn_combo, "COMBOBOX"')
repf('WSTR h_status, "상태"', 'WSTR h_status, "상태"\nWSTR h_dir, "방향"\nWSTR s_ar_r, "→"\nWSTR s_ar_l, "←"\nWSTR s_ar_eq, "="\nWSTR s_ar_ne, "≠"')
repf("col_text: dq h_name, h_status, h_sizea, h_mta, h_sizeb, h_mtb\ncol_w:   dd 380, 90, 110, 150, 110, 150\ncol_fmt: dd 0, 0, 1, 0, 1, 0",
     "col_text: dq h_name, h_status, h_dir, h_sizea, h_mta, h_sizeb, h_mtb\ncol_w:   dd 380, 90, 50, 110, 150, 110, 150\ncol_fmt: dd 0, 0, 0, 1, 0, 1, 0")
f = f.rstrip('\n') + '\n%include "sync_dlg.inc"\n'
open('folder.asm', 'w', encoding='utf-8', newline='\n').write(f)

u = open('folder_ui.inc', encoding='utf-8').read()
def repu(a, b, cnt=1):
    global u
    assert u.count(a) == cnt, (a[:60], u.count(a))
    u = u.replace(a, b)
repu("""    cmp r8d, 2
    je .sza
    cmp r8d, 3
    je .mta
    cmp r8d, 4
    je .szb
    jmp .mtb""", """    cmp r8d, 2
    je .dir
    cmp r8d, 3
    je .sza
    cmp r8d, 4
    je .mta
    cmp r8d, 5
    je .szb
    jmp .mtb""")
repu(""".status:
    mov eax, [rdi+E_STATUS]
    lea rcx, [st_text]""", """.dir:
    mov eax, [rdi+E_STATUS]
    lea r10, [s_ar_r]
    cmp eax, ST_LONLY
    je .dset
    lea r10, [s_ar_l]
    cmp eax, ST_RONLY
    je .dset
    lea r10, [s_ar_eq]
    test eax, eax
    jz .dset
    lea r10, [s_ar_ne]
    cmp eax, ST_DIFF
    jne .dset
    test dword [rdi+E_FLAGS], EF_DIRA|EF_DIRB
    jnz .dset
    mov rax, [rdi+E_MTA]
    cmp rax, [rdi+E_MTB]
    je .dset
    lea r10, [s_ar_r]                ; the left file is newer
    ja .dset
    lea r10, [s_ar_l]
.dset:
    invoke wcscpy, rsi, r10
    jmp .out
.status:
    mov eax, [rdi+E_STATUS]
    lea rcx, [st_text]""")
repu("""    cmp ebp, 6
    jae .coldone""", """    cmp ebp, 7
    jae .coldone""")
repu("""    invoke _snwprintf, &rsp+96, 280, &s_confirm_sync, r12, r13, r14
    invoke msgbox, rsi, &rsp+96, MB_YESNO|MB_ICONQUESTION
    cmp eax, IDYES
    jne .d""", """    invoke sync_preview, rsi, rbx
    test eax, eax
    jz .d""")
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(u)
print('sync patched')

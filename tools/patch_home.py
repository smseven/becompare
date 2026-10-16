import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('main.asm', [
    ("global g_sess, g_nsess, ini_prepare, apply_theme_all, type_names,", "global tab_titles\nglobal g_sess, g_nsess, ini_prepare, apply_theme_all, type_names,"),
])

draw = r'''
; ---------------------------------------------------------------- recent list (owner drawn: type, files, path, age)
section .rdata
WSTR sec_session, "Session"
WSTR hk_type, "Type"
WSTR hk_a, "A"
WSTR hk_b, "B"
WSTR s_rdel, "목록에서 제거"
WSTR f_l1, "%s  ·  %s  ↔  %s"
WSTR f_l1b, "%s  ·  %s"
WSTR f_l1c, "%s"
WSTR f_l2, "%s   ·   %s"
WSTR s_just, "방금"
WSTR f_min, "%d분 전"
WSTR f_hour, "%d시간 전"
WSTR f_day, "%d일 전"
WSTR s_nolabel, "세션"
section .text

; home_drawitem(DRAWITEMSTRUCT*)
home_drawitem:
    PROLOG 4480
    mov rbx, rcx
    mov esi, [rbx+8]
    cmp esi, -1
    je .d
    mov r12d, [rbx+16]
    mov r13, [rbx+32]
    lea r14, [rbx+40]
    invoke SendMessageW, [rbx+24], LB_GETTEXT, rsi, &rsp+96
    test r12d, 1
    jz .norm
    invoke GetSysColorBrush, 13
    mov rdi, rax
    invoke GetSysColor, 14
    mov r15d, eax
    mov ebp, eax
    jmp .fill
.norm:
    mov rdi, [th_bgbrush]
    mov r15d, [th_fg]
    mov ebp, [th_same]
.fill:
    invoke FillRect, r13, r14, rdi
    invoke SetBkMode, r13, 1
    ; session data
    mov word [rsp+1200], 0
    mov word [rsp+2200], 0
    mov word [rsp+3300], 0
    invoke GetPrivateProfileStringW, &sec_session, &hk_type, &s_empty, &rsp+1200, 40, &rsp+96
    invoke GetPrivateProfileStringW, &sec_session, &hk_a, &s_empty, &rsp+2200, 519, &rsp+96
    invoke GetPrivateProfileStringW, &sec_session, &hk_b, &s_empty, &rsp+3300, 519, &rsp+96
    ; type label
    lea r8, [s_nolabel]
    xor esi, esi
.t:
    cmp esi, 12
    jae .tdone
    lea rax, [type_names]
    invoke _wcsicmp, &rsp+1200, [rax+rsi*8]
    test eax, eax
    jz .thit
    inc esi
    jmp .t
.thit:
    lea rax, [tab_titles]
    mov r8, [rax+rsi*8]
.tdone:
    mov [rsp+4350], r8                ; label
    ; file name tails
    lea rdi, [rsp+2200]
    invoke wcsrchr, rdi, 0x5C
    test rax, rax
    jz .ta
    lea rdi, [rax+2]
.ta:
    mov [rsp+4360], rdi
    lea rdi, [rsp+3300]
    invoke wcsrchr, rdi, 0x5C
    test rax, rax
    jz .tb
    lea rdi, [rax+2]
.tb:
    mov [rsp+4368], rdi
    cmp word [rsp+2200], 0
    je .l1c
    cmp word [rsp+3300], 0
    je .l1b
    invoke _snwprintf, &rsp+1300, 190, &f_l1, [rsp+4350], [rsp+4360], [rsp+4368]
    jmp .l1d
.l1b:
    invoke _snwprintf, &rsp+1300, 190, &f_l1b, [rsp+4350], [rsp+4360]
    jmp .l1d
.l1c:
    lea rdi, [rsp+96]
    invoke wcsrchr, rdi, 0x5C
    test rax, rax
    jz .l1e
    lea rdi, [rax+2]
.l1e:
    invoke _snwprintf, &rsp+1300, 190, &f_l1c, rdi
.l1d:
    ; age of the file
    mov word [rsp+1800], 0
    lea rdi, [s_empty]
    mov qword [rsp+4376], 0
    invoke GetFileAttributesExW, &rsp+96, 0, &rsp+4400
    test eax, eax
    jz .l2
    invoke GetSystemTimeAsFileTime, &rsp+4392
    mov rax, [rsp+4392]
    sub rax, [rsp+4400+20]
    jbe .l2
    xor edx, edx
    mov ecx, 10000000
    div rcx                           ; seconds
    lea rdi, [s_just]
    cmp rax, 60
    jb .l2
    xor edx, edx
    mov ecx, 60
    div rcx
    lea r8, [f_min]
    cmp rax, 60
    jb .age
    xor edx, edx
    mov ecx, 60
    div rcx
    lea r8, [f_hour]
    cmp rax, 24
    jb .age
    xor edx, edx
    mov ecx, 24
    div rcx
    lea r8, [f_day]
.age:
    mov r9, rax
    invoke _snwprintf, &rsp+1700, 30, r8, r9
    lea rdi, [rsp+1700]
.l2:
    invoke _snwprintf, &rsp+1800, 190, &f_l2, &rsp+96, rdi
    ; paint the two lines
    mov ecx, 12
    call scl
    mov esi, eax                      ; left padding
    mov ecx, 4
    call scl
    mov edi, eax                      ; top padding
    mov eax, [r14]
    add eax, esi
    mov [rsp+4420], eax
    mov eax, [r14+4]
    add eax, edi
    mov [rsp+4424], eax
    mov eax, [r14+8]
    sub eax, esi
    mov [rsp+4428], eax
    mov ecx, 20
    call scl
    add eax, [rsp+4424]
    mov [rsp+4432], eax
    mov r12d, eax                     ; y of the second line
    invoke SelectObject, r13, [g_fontb]
    invoke SetTextColor, r13, r15
    invoke DrawTextW, r13, &rsp+1300, -1, &rsp+4420, 0x8820
    mov eax, r12d
    mov [rsp+4424], eax
    mov ecx, 18
    call scl
    add eax, r12d
    mov [rsp+4432], eax
    invoke SelectObject, r13, [g_font]
    invoke SetTextColor, r13, rbp
    invoke DrawTextW, r13, &rsp+1800, -1, &rsp+4420, 0x8820
.d:
    EPILOG 4480

; home_remove(hwnd): drop the selected entry from the recent list
home_remove:
    PROLOG 1200
    mov r12, rcx
    invoke GetDlgItem, r12, ID_RECENT
    mov r13, rax
    invoke SendMessageW, r13, LB_GETCURSEL, 0, 0
    movsxd rbx, eax
    test rbx, rbx
    js .d
    lea rsi, [rsp+96]
    lea rdi, [rsp+128]
.sh:
    cmp ebx, MAX_RECENT-1
    jae .last
    lea eax, [rbx+1]
    invoke _snwprintf, rsi, 16, &f_r, rax
    invoke GetPrivateProfileStringW, &sec_recent, rsi, &s_empty, rdi, 520, &g_ini
    invoke _snwprintf, rsi, 16, &f_r, rbx
    invoke WritePrivateProfileStringW, &sec_recent, rsi, rdi, &g_ini
    inc ebx
    jmp .sh
.last:
    invoke _snwprintf, rsi, 16, &f_r, rbx
    invoke WritePrivateProfileStringW, &sec_recent, rsi, &s_empty, &g_ini
    invoke fill_recent, r12
.d:
    EPILOG 1200
'''

h = open('home.asm', encoding='utf-8').read().replace('\r\n', '\n')
h = h.replace("extern WritePrivateProfileStringW, SetBkMode, SetFocus\n",
              "extern WritePrivateProfileStringW, SetBkMode, SetFocus\nextern GetSysColorBrush, GetSysColor, SelectObject, DrawTextW, GetFileAttributesExW, GetSystemTimeAsFileTime, _wcsicmp, wcsrchr\nextern type_names, tab_titles\n", 1)
h = h.replace("%define ID_RLABEL  3002\n", "%define ID_RLABEL  3002\n%define ID_RDEL    3003\n", 1)
h = h.replace("""    invoke mk, rsi, &cn_listbox, &s_empty, LBS_NOTIFY|WS_VSCROLL|WS_BORDER|WS_TABSTOP, ID_RECENT
""", """    invoke mk, rsi, &cn_listbox, &s_empty, LBS_NOTIFY|WS_VSCROLL|WS_BORDER|WS_TABSTOP|0x50, ID_RECENT
    invoke mk, rsi, &cn_button, &s_rdel, WS_TABSTOP, ID_RDEL
""", 1)
h = h.replace("""    cmp edi, WM_COMMAND
    je .command
    cmp edi, WM_ERASEBKGND""", """    cmp edi, WM_COMMAND
    je .command
    cmp edi, 0x2C
    je .measure
    cmp edi, 0x2B
    je .draw
    cmp edi, WM_ERASEBKGND""", 1)
h = h.replace(""".chk_list:
    cmp eax, ID_RECENT
    jne .def""", """.chk_list:
    cmp eax, ID_RDEL
    je .rdel
    cmp eax, ID_RECENT
    jne .def""", 1)
h = h.replace(""".refresh:
    invoke fill_recent, rsi""", """.measure:
    mov ecx, 50
    call scl
    mov [r13+16], eax
    mov eax, 1
    EPILOG 192
.draw:
    invoke home_drawitem, r13
    mov eax, 1
    EPILOG 192
.rdel:
    invoke home_remove, rsi
    xor eax, eax
    EPILOG 192
.refresh:
    invoke fill_recent, rsi""", 1)
h = h.replace("""    mov eax, [rbx+RC_B]
    sub eax, ebp
    sub eax, 30
    sub eax, r12d
    cmp eax, 60
    jge .h
    mov eax, 60
.h:
    lea r14d, [rbp+28]
    invoke MoveWindow, [rsp+112], r12, r14, rdi, rax, 1
    EPILOG 192""", """    mov eax, [rbx+RC_B]
    sub eax, ebp
    sub eax, 66
    sub eax, r12d
    cmp eax, 60
    jge .h
    mov eax, 60
.h:
    lea r14d, [rbp+28]
    mov [rsp+120], eax
    mov [rsp+124], r14d
    invoke MoveWindow, [rsp+112], r12, r14, rdi, rax, 1
    invoke GetDlgItem, rsi, ID_RDEL
    mov [rsp+112], rax
    mov ecx, 150
    call scl
    mov ebx, eax
    lea r10d, [rdi+r12]
    sub r10d, ebx
    mov r11d, [rsp+124]
    add r11d, [rsp+120]
    add r11d, 6
    invoke MoveWindow, [rsp+112], r10, r11, rbx, 28, 1
    EPILOG 192""", 1)
h = h.rstrip('\n') + '\n' + draw
open('home.asm', 'w', encoding='utf-8', newline='\n').write(h)
print('home patched')

import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# ---------------- settings: three more shortcut slots
edit('settings.asm', [
    ('WSTR k_pd, "PrevDiff"\n', 'WSTR k_pd, "PrevDiff"\nWSTR k_bm, "Bookmark"\nWSTR k_nm, "NextMark"\nWSTR k_pm, "PrevMark"\n'),
    ('WSTR d_pd, "Shift+F8"\n', 'WSTR d_pd, "Shift+F8"\nWSTR d_bm, "Ctrl+F2"\nWSTR d_nm, "F2"\nWSTR d_pm, "Shift+F2"\n'),
    ('WSTR l_kpd, "이전 차이:"\n', 'WSTR l_kpd, "이전 차이:"\nWSTR l_kbm, "북마크 토글:"\nWSTR l_knm, "다음 북마크:"\nWSTR l_kpm, "이전 북마크:"\n'),
    ("    SROW l_kpd, sec_keys, k_pd, k_pd, d_pd, 0, 0, 516\n", "    SROW l_kpd, sec_keys, k_pd, k_pd, d_pd, 0, 0, 516\n    SROW l_kbm, sec_keys, k_bm, k_bm, d_bm, 0, 0, 517\n    SROW l_knm, sec_keys, k_nm, k_nm, d_nm, 0, 0, 518\n    SROW l_kpm, sec_keys, k_pm, k_pm, d_pm, 0, 0, 519\n"),
    ("%define ST_NROWS 13", "%define ST_NROWS 16"),
    ("key_names: dq k_run, k_save, k_close, k_next, k_nd, k_pd\nkey_defs:  dq d_run, d_save, d_close, d_next, d_nd, d_pd", "key_names: dq k_run, k_save, k_close, k_next, k_nd, k_pd, k_bm, k_nm, k_pm\nkey_defs:  dq d_run, d_save, d_close, d_next, d_nd, d_pd, d_bm, d_nm, d_pm"),
    ("g_keytab: resq 6 ", "g_keytab: resq 9 "),
    ("keys_load:\n    PROLOG 512\n    xor ebx, ebx\n.k:\n    cmp ebx, 6\n", "keys_load:\n    PROLOG 512\n    xor ebx, ebx\n.k:\n    cmp ebx, 9\n"),
    ("    SPLACE 12, 232, 740, 22\n", "    SPLACE 12, 292, 740, 22\n"),
    ("    SPLACE 12, 256, 740, 140\n", "    SPLACE 12, 316, 740, 130\n"),
    ("    SPLACE 12, 404, 740, 22\n", "    SPLACE 12, 454, 740, 22\n"),
    ("    SPLACE 12, 430, 740, 44\n", "    SPLACE 12, 480, 740, 44\n"),
    ("    SPLACE 440, 490, 100, 28\n", "    SPLACE 440, 540, 100, 28\n"),
    ("    SPLACE 548, 490, 100, 28\n", "    SPLACE 548, 540, 100, 28\n"),
    ("    SPLACE 12, 490, 130, 28\n", "    SPLACE 12, 540, 130, 28\n"),
    ("    mov ecx, 600\n    call scl\n    mov r14d, eax\n", "    mov ecx, 650\n    call scl\n    mov r14d, eax\n"),
])

# ---------------- frame: nine shortcut slots, bookmark messages are only consumed by views that handle them
edit('inc/app.inc', [("%define BC_PREVDIFF (WM_APP+31)\n", "%define BC_PREVDIFF (WM_APP+31)\n%define BC_BOOKMARK (WM_APP+32)\n%define BC_NEXTMARK (WM_APP+33)\n%define BC_PREVMARK (WM_APP+34)\n")])
edit('main.asm', [
    (".kl:\n    cmp ebx, 6\n    jae .fixed\n", ".kl:\n    cmp ebx, 9\n    jae .fixed\n"),
    (".khit:\n    cmp ebx, 0\n    je .run\n", ".khit:\n    cmp ebx, 6\n    je .bmtoggle\n    cmp ebx, 7\n    je .bmnext\n    cmp ebx, 8\n    je .bmprev\n    cmp ebx, 0\n    je .run\n"),
    (".nextdiff:\n    mov r13d, BC_NEXTDIFF\n", ".bmtoggle:\n    mov r13d, BC_BOOKMARK\n    jmp .markmsg\n.bmnext:\n    mov r13d, BC_NEXTMARK\n    jmp .markmsg\n.bmprev:\n    mov r13d, BC_PREVMARK\n.markmsg:\n    call cur_view\n    test rax, rax\n    jz .no\n    invoke SendMessageW, rax, r13, 0, 0\n    test rax, rax\n    jz .no\n    mov eax, 1\n    EPILOG 96\n.nextdiff:\n    mov r13d, BC_NEXTDIFF\n"),
])

# ---------------- text view: bookmarks + find / replace
edit('text.asm', [
    ("%define TV_SIZE   2896\n", "%define TV_BM     2896\n%define TV_NBM    3152\n%define TV_SIZE   3168\n"),
])
edit('text_gutter.inc', [
    ("""    mov rbp, rax                     ; row
    mov ecx, [rbp+4]
    cmp qword [rbx+GT_SIDE], 0
""", """    mov rbp, rax                     ; row
    invoke bm_has, r12, r14
    test eax, eax
    jz .nobm
    mov dword [rsp+P_BR], 0
    lea eax, [r15+2]
    mov [rsp+P_BR+4], eax
    mov dword [rsp+P_BR+8], 6
    mov eax, r15d
    add eax, [rsp+P_H]
    sub eax, 2
    mov [rsp+P_BR+12], eax
    invoke CreateSolidBrush, 0xD07020
    mov [rsp+P_BR+16], rax
    invoke FillRect, rdi, &rsp+P_BR, [rsp+P_BR+16]
    invoke DeleteObject, [rsp+P_BR+16]
.nobm:
    mov ecx, [rbp+4]
    cmp qword [rbx+GT_SIDE], 0
"""),
])
t = open('text_gutter.inc', encoding='utf-8').read().rstrip('\n') + """

; bm_has(tv, row) -> eax 1 when the row carries a bookmark
bm_has:
    xor eax, eax
    mov r8d, [rcx+TV_NBM]
    xor r9d, r9d
.l:
    cmp r9d, r8d
    jae .d
    cmp [rcx+TV_BM+r9*4], edx
    je .y
    inc r9d
    jmp .l
.y:
    mov eax, 1
.d:
    ret

; tv_bm_goto(hwnd, tv, row): caret of both panes onto the row
tv_bm_goto:
    PROLOG 96
    mov rsi, rcx
    mov rbx, rdx
    mov r12d, r8d
    invoke SendMessageW, [rbx+TV_HA], EM_LINEINDEX, r12, 0
    invoke SendMessageW, [rbx+TV_HA], EM_SETSEL, rax, rax
    invoke SendMessageW, [rbx+TV_HA], EM_SCROLLCARET, 0, 0
    invoke SendMessageW, [rbx+TV_HB], EM_LINEINDEX, r12, 0
    invoke SendMessageW, [rbx+TV_HB], EM_SETSEL, rax, rax
    invoke SendMessageW, [rbx+TV_HB], EM_SCROLLCARET, 0, 0
    invoke tv_redraw_aux, rbx
    EPILOG 96

; tv_bm_toggle(hwnd, tv): bookmark on / off for the caret row
tv_bm_toggle:
    PROLOG 64
    mov rsi, rcx
    mov rbx, rdx
    invoke tv_caretrow, rbx
    mov edi, eax
    mov ecx, [rbx+TV_NBM]
    xor edx, edx
.f:
    cmp edx, ecx
    jae .add
    cmp [rbx+TV_BM+rdx*4], edi
    je .rem
    inc edx
    jmp .f
.rem:
    lea eax, [rdx+1]
.sh:
    cmp eax, ecx
    jae .shd
    mov r8d, [rbx+TV_BM+rax*4]
    mov [rbx+TV_BM+rdx*4], r8d
    inc eax
    inc edx
    jmp .sh
.shd:
    dec ecx
    mov [rbx+TV_NBM], ecx
    jmp .redraw
.add:
    cmp ecx, 64
    jae .redraw
    mov [rbx+TV_BM+rcx*4], edi
    inc ecx
    mov [rbx+TV_NBM], ecx
.redraw:
    invoke tv_redraw_aux, rbx
    EPILOG 64

; tv_bm_step(hwnd, tv, dir 1 next / 0 previous) -> eax 1 when a bookmark exists
tv_bm_step:
    PROLOG 64
    mov rsi, rcx
    mov rbx, rdx
    mov r12d, r8d
    cmp dword [rbx+TV_NBM], 0
    je .none
    invoke tv_caretrow, rbx
    mov edi, eax                      ; current row
    mov r13d, -1                      ; best after / before the caret
    mov r14d, -1                      ; best overall (wrap)
    xor ecx, ecx
.l:
    cmp ecx, [rbx+TV_NBM]
    jae .pick
    mov eax, [rbx+TV_BM+rcx*4]
    test r12d, r12d
    jz .prev
    cmp eax, edi
    jle .wrapn
    cmp r13d, -1
    je .setn
    cmp eax, r13d
    jge .wrapn
.setn:
    mov r13d, eax
.wrapn:
    cmp r14d, -1
    je .setw
    cmp eax, r14d
    jge .nx
.setw:
    mov r14d, eax
    jmp .nx
.prev:
    cmp eax, edi
    jge .wrapp
    cmp r13d, -1
    je .setp
    cmp eax, r13d
    jle .wrapp
.setp:
    mov r13d, eax
.wrapp:
    cmp r14d, -1
    je .setq
    cmp eax, r14d
    jle .nx
.setq:
    mov r14d, eax
.nx:
    inc ecx
    jmp .l
.pick:
    mov r8d, r13d
    cmp r8d, -1
    jne .go
    mov r8d, r14d
.go:
    invoke tv_bm_goto, rsi, rbx, r8
    mov eax, 1
    EPILOG 64
.none:
    xor eax, eax
    EPILOG 64
"""
open('text_gutter.inc', 'w', encoding='utf-8', newline='\n').write(t)

# messages in tv_proc, find row, compare resets bookmarks
edit('text_ui.inc', [
    ("    cmp edi, BC_NEXTDIFF\n    je .b_next\n", "    cmp edi, BC_NEXTDIFF\n    je .b_next\n    cmp edi, BC_BOOKMARK\n    je .m_bm\n    cmp edi, BC_NEXTMARK\n    je .m_next\n    cmp edi, BC_PREVMARK\n    je .m_prev\n"),
    (".b_syn:\n    invoke tv_syn_apply, rsi, r15\n    jmp .zero\n", """.b_syn:
    invoke tv_syn_apply, rsi, r15
    jmp .zero
.m_bm:
    invoke tv_bm_toggle, rsi, r15
    mov eax, 1
    EPILOG 320
.m_next:
    invoke tv_bm_step, rsi, r15, 1
    mov eax, 1
    EPILOG 320
.m_prev:
    invoke tv_bm_step, rsi, r15, 0
    mov eax, 1
    EPILOG 320
.f_next:
    invoke tv_find_cmd, rsi, r15, 0
    jmp .zero
.f_prev:
    invoke tv_find_cmd, rsi, r15, 1
    jmp .zero
.f_rep:
    invoke tv_find_cmd, rsi, r15, 2
    jmp .zero
.f_all:
    invoke tv_find_cmd, rsi, r15, 3
    jmp .zero
"""),
    ("    cmp ebx, ID_CHK_SYN\n    je .b_syn\n", "    cmp ebx, ID_CHK_SYN\n    je .b_syn\n    cmp ebx, ID_ED_NEXT\n    je .f_next\n    cmp ebx, ID_ED_PREV\n    je .f_prev\n    cmp ebx, ID_ED_RONE\n    je .f_rep\n    cmp ebx, ID_ED_RALL\n    je .f_all\n"),
    ("    PLACE ID_LBL_INFO, 520\n    lea r13d, [r13+r15]\n    add r13d, r14d                   ; y of the panes\n", "    PLACE ID_LBL_INFO, 520\n    lea r13d, [r13+r15]\n    add r13d, r14d\n    mov r12d, r14d\n    PLACE ID_ED_LFIND, 40\n    PLACE ID_ED_FIND, 160\n    PLACE ID_ED_NEXT, 70\n    PLACE ID_ED_PREV, 70\n    PLACE ID_ED_LREPL, 56\n    PLACE ID_ED_REPL, 160\n    PLACE ID_ED_RONE, 70\n    PLACE ID_ED_RALL, 100\n    PLACE ID_ED_CASE, 110\n    lea r13d, [r13+r15]\n    add r13d, r14d                   ; y of the panes\n"),
    ("    invoke mk_chk, rsi, &s_c_syn, ID_CHK_SYN, 1\n", "    invoke mk_chk, rsi, &s_c_syn, ID_CHK_SYN, 1\n    invoke mk_lbl, rsi, &s_ed_lfind, ID_ED_LFIND\n    invoke mk_edit, rsi, ID_ED_FIND\n    invoke mk_btn, rsi, &s_ed_next, ID_ED_NEXT\n    invoke mk_btn, rsi, &s_ed_prev, ID_ED_PREV\n    invoke mk_lbl, rsi, &s_ed_lrepl, ID_ED_LREPL\n    invoke mk_edit, rsi, ID_ED_REPL\n    invoke mk_btn, rsi, &s_ed_rone, ID_ED_RONE\n    invoke mk_btn, rsi, &s_ed_rall, ID_ED_RALL\n    invoke mk_chk, rsi, &s_ed_case, ID_ED_CASE, 0\n"),
    ("    mov qword [rbx+TV_CUR], -1\n    invoke free, [rsp+C_DA]\n", "    mov qword [rbx+TV_CUR], -1\n    mov dword [rbx+TV_NBM], 0\n    invoke free, [rsp+C_DA]\n"),
])
t = open('text_ui.inc', encoding='utf-8').read().rstrip('\n') + """

; tv_find_cmd(hwnd, tv, kind 0 next / 1 previous / 2 replace / 3 replace all): find / replace in the last focused pane
tv_find_cmd:
    PROLOG 192
    mov rsi, rcx
    mov rbx, rdx
    mov r12d, r8d
    mov rax, [rbx+TV_HA]
    cmp qword [rbx+TV_LASTP], 0
    je .have
    mov rax, [rbx+TV_HB]
.have:
    mov [rsp+96+E_HR], rax
    cmp r12d, 1
    ja .rep
    mov r8d, 1
    test r12d, r12d
    jz .go
    xor r8d, r8d
.go:
    invoke ed_find, rsi, &rsp+96, r8
    EPILOG 192
.rep:
    lea r8d, [r12-2]
    invoke ed_replace, rsi, &rsp+96, r8
    EPILOG 192
"""
open('text_ui.inc', 'w', encoding='utf-8', newline='\n').write(t)
print('bm ok')

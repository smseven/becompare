import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
exec(open('../tools/ph.py', encoding='utf-8').read())


def edit(fn, pairs):
    s = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert s.count(a) == 1, (fn, a[:60], s.count(a))
        s = s.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(s)


edit('rich.asm', [
    ("global rich_create, rich_set_text, rich_get_text, rich_bk,", "global rich_fg, rich_create, rich_set_text, rich_get_text, rich_bk,"),
    ("; rich_theme(h): background", """; rich_fg(h, cpMin, cpMax, color): text colour for a character range
rich_fg:
    PROLOG 224
    mov rbx, rcx
    mov r12d, edx
    mov r13d, r8d
    mov r14d, r9d
    mov [rsp+96], r12d
    mov [rsp+100], r13d
    invoke SendMessageW, rbx, EM_EXSETSEL, 0, &rsp+96
    invoke memset, &rsp+104, 0, CF_SIZE
    mov dword [rsp+104], CF_SIZE
    mov dword [rsp+104+CF_MASK], CFM_COLOR
    mov [rsp+104+CF_TEXTCOLOR], r14d
    invoke SendMessageW, rbx, EM_SETCHARFORMAT, SCF_SELECTION, &rsp+104
    EPILOG 224

; rich_theme(h): background"""),
])

edit('text.asm', [
    ("extern set_tab_title, vec_push\n", "extern set_tab_title, vec_push, rich_theme\nextern _wcsicmp, rich_get_text\n"),
    ('WSTR f_opts, "%d%d%d%d|%s"', 'WSTR f_opts, "%d%d%d%d%d|%s"'),
])
t = open('text.asm', encoding='utf-8').read().rstrip('\n') + '\n%include "text_syn.inc"\n'
open('text.asm', 'w', encoding='utf-8', newline='\n').write(t)

edit('text_ui.inc', [
    # compare: colour after the diff colouring
    ("    invoke tv_color, rbx, &rsp+C_LA, &rsp+C_LB\n    invoke rich_unsel, [rbx+TV_HA]\n    invoke rich_unsel, [rbx+TV_HB]\n",
     "    invoke tv_color, rbx, &rsp+C_LA, &rsp+C_LB\n    invoke rich_unsel, [rbx+TV_HA]\n    invoke rich_unsel, [rbx+TV_HB]\n    invoke tv_syn_apply, rsi, rbx\n"),
    # layout
    ("    PLACE ID_EDIT_CMT, 56\n", "    PLACE ID_EDIT_CMT, 56\n    PLACE ID_CHK_SYN, 100\n"),
    # create
    ("    invoke mk_edit, rsi, ID_EDIT_CMT\n    invoke GetDlgItem, rsi, ID_EDIT_CMT\n    invoke SetWindowTextW, rax, &s_prefix\n",
     "    invoke mk_edit, rsi, ID_EDIT_CMT\n    invoke GetDlgItem, rsi, ID_EDIT_CMT\n    invoke SetWindowTextW, rax, &s_prefix\n    invoke mk_chk, rsi, &s_c_syn, ID_CHK_SYN, 1\n"),
    # command
    ("    cmp ebx, ID_CHK_CASE\n    jb .def\n    cmp ebx, ID_CHK_CMT\n    ja .def\n",
     "    cmp ebx, ID_CHK_SYN\n    je .b_syn\n    cmp ebx, ID_CHK_CASE\n    jb .def\n    cmp ebx, ID_CHK_CMT\n    ja .def\n"),
    (".browse:\n    invoke pb_command, rsi, rbx, 0\n    jmp .zero\n.b_prev:",
     ".browse:\n    invoke pb_command, rsi, rbx, 0\n    jmp .zero\n.b_syn:\n    invoke tv_syn_apply, rsi, r15\n    jmp .zero\n.b_prev:"),
    # collect: five flags
    ("    invoke get_chk, rsi, ID_CHK_CMT\n    mov r15d, eax\n    invoke GetDlgItem, rsi, ID_EDIT_CMT\n    invoke GetWindowTextW, rax, &rsp+96, 60\n    invoke _snwprintf, &rdi+SS_OPTS, 1023, &f_opts, r12, r13, r14, r15, &rsp+96\n",
     "    invoke get_chk, rsi, ID_CHK_CMT\n    mov r15d, eax\n    invoke get_chk, rsi, ID_CHK_SYN\n    mov ebp, eax\n    invoke GetDlgItem, rsi, ID_EDIT_CMT\n    invoke GetWindowTextW, rax, &rsp+96, 60\n    invoke _snwprintf, &rdi+SS_OPTS, 1023, &f_opts, r12, r13, r14, r15, rbp, &rsp+96\n"),
    # apply
    ("    invoke GetDlgItem, rsi, ID_EDIT_CMT\n    invoke SetWindowTextW, rax, &rbx+10\n.d:",
     "    lea r12, [rbx+10]\n    cmp word [rbx+8], '|'\n    je .oldfmt\n    movzx r8d, word [rbx+8]\n    sub r8d, '0'\n    invoke set_chk_id, rsi, ID_CHK_SYN, r8\n    lea r12, [rbx+12]\n.oldfmt:\n    invoke GetDlgItem, rsi, ID_EDIT_CMT\n    invoke SetWindowTextW, rax, r12\n.d:"),
])
print('syn patched')

import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# ---------- textlib: identifier masking (flag 16) and substitution rules (flag 32, rules in g_tc_rules)
edit('textlib.asm', [
    ("global text_load, text_save, text_load_raw,", "global g_tc_rules, text_load, text_save, text_load_raw,"),
    ("""    mov rbx, rdi
.l:
    cmp rsi, r14
    jae .done
    movzx ecx, word [rsi]
    add rsi, 2
    test r12d, 2
    jz .case
    cmp ecx, ' '
    je .l
    cmp ecx, 9
    je .l
    cmp ecx, 0x3000
    je .l
.case:
    test r12d, 1
""", """    mov rbx, rdi
    xor r15d, r15d                   ; inside an identifier (masked comparison)
.l:
    cmp rsi, r14
    jae .done
    movzx ecx, word [rsi]
    add rsi, 2
    test r12d, 2
    jz .case
    cmp ecx, ' '
    je .l
    cmp ecx, 9
    je .l
    cmp ecx, 0x3000
    je .l
.case:
    test r12d, 16
    jz .nomask
    cmp ecx, '_'
    je .isid
    cmp ecx, 0x80
    jae .isid
    mov eax, ecx
    or eax, 0x20
    cmp eax, 'a'
    jb .noid
    cmp eax, 'z'
    jbe .isid
.noid:
    cmp ecx, '0'
    jb .idreset
    cmp ecx, '9'
    ja .idreset
    test r15d, r15d
    jnz .l                           ; digits inside an identifier
    jmp .nomask
.idreset:
    xor r15d, r15d
    jmp .nomask
.isid:
    test r15d, r15d
    jnz .l
    mov r15d, 1
    mov ecx, 1                       ; one placeholder for the whole identifier
    jmp .st
.nomask:
    test r12d, 1
"""),
    ("""keys_build:
    PROLOG 128
""", """; rules_apply(src, dst, cap chars) : replace every "old" of g_tc_rules ("old=new;old=new") in src
rules_apply:
    PROLOG 96
    mov rsi, rcx
    mov rdi, rdx
    mov r12, r8
    xor r13d, r13d                   ; written chars
.l:
    movzx eax, word [rsi]
    test eax, eax
    jz .d
    cmp r13, r12
    jae .d
    mov r14, [g_tc_rules]
.rule:
    cmp word [r14], 0
    je .plain
    ; one rule: old up to '=', new up to ';'
    mov r8, r14
.ol:
    movzx eax, word [r8]
    test eax, eax
    jz .plain
    cmp eax, '='
    je .gotold
    add r8, 2
    jmp .ol
.gotold:
    mov r9, r8
    sub r9, r14
    shr r9, 1                        ; old length
    lea r10, [r8+2]                  ; new text
    mov r11, r10
.nl:
    movzx eax, word [r11]
    test eax, eax
    jz .gotnew
    cmp eax, ';'
    je .gotnew
    add r11, 2
    jmp .nl
.gotnew:
    mov r15, r11
    sub r15, r10
    shr r15, 1                       ; new length
    ; compare old with src
    test r9, r9
    jz .nextrule
    xor ecx, ecx
.cmp:
    cmp rcx, r9
    jae .match
    movzx eax, word [r14+rcx*2]
    cmp ax, [rsi+rcx*2]
    jne .nextrule
    inc rcx
    jmp .cmp
.match:
    lea rax, [r13+r15]
    cmp rax, r12
    ja .plain
    xor ecx, ecx
.cn:
    cmp rcx, r15
    jae .cnd
    movzx eax, word [r10+rcx*2]
    mov [rdi+r13*2], ax
    inc r13
    inc rcx
    jmp .cn
.cnd:
    lea rsi, [rsi+r9*2]
    jmp .l
.nextrule:
    movzx eax, word [r11]
    test eax, eax
    jz .plain
    lea r14, [r11+2]
    jmp .rule
.plain:
    movzx eax, word [rsi]
    mov [rdi+r13*2], ax
    inc r13
    add rsi, 2
    jmp .l
.copyrest:
    movzx eax, word [rsi]
    test eax, eax
    jz .d
    mov [rdi+r13*2], ax
    inc r13
    add rsi, 2
    jmp .copyrest
.d:
    mov word [rdi+r13*2], 0
    mov rax, r13
    EPILOG 96

keys_build:
    PROLOG 128
"""),
])
t = open('textlib.asm', encoding='utf-8').read().rstrip('\n') + "\n\nsection .bss\nalignb 8\ng_tc_rules: resq 1\nsection .text\n"
open('textlib.asm', 'w', encoding='utf-8', newline='\n').write(t)

# keys_build: with rules, normalise from a substituted copy of every line. Larger blob, extra buffer
edit('textlib.asm', [
    ("""    lea rcx, [rdi*2+8]
    call malloc
    mov [r15+rbx*8], rax
    mov [rsp+104], rax               ; cursor
""", """    lea rcx, [rdi*2+8]
    test r12d, 32
    jz .blob
    lea rcx, [rdi*16+16]             ; substitution rules may lengthen lines
.blob:
    call malloc
    mov [r15+rbx*8], rax
    mov [rsp+104], rax               ; cursor
    mov qword [rsp+112], 0
    test r12d, 32
    jz .nodata
    mov ecx, 4096*2
    call malloc
    mov [rsp+112], rax               ; scratch line for the substituted text
"""),
    ("""    mov rdx, [rsp+104]
    mov [r15+rbp*8], rdx
    invoke key_copy, rdi, rdx, r12, r13
""", """    mov rdx, [rsp+104]
    mov [r15+rbp*8], rdx
    test r12d, 32
    jz .nosub
    invoke wcslen, rdi
    lea r8, [rax*8+8]
    cmp r8, 4000
    jbe .capok
    mov r8d, 4000
.capok:
    mov [rsp+120], r8
    invoke rules_apply, rdi, [rsp+112], [rsp+120]
    mov rdi, [rsp+112]
    mov rdx, [rsp+104]
.nosub:
    invoke key_copy, rdi, rdx, r12, r13
"""),
    (""".done:
    mov rax, r15
    EPILOG 128

; ---------------------------------------------------------------- diff""", """.done:
    invoke free, [rsp+112]
    mov rax, r15
    EPILOG 128

; ---------------------------------------------------------------- diff"""),
])

# ---------- text view controls
edit('text.asm', [
    ("%define ID_ED_LFIND  312\n", "%define ID_ED_LFIND  312\n%define ID_CHK_IDS   216\n%define ID_EDIT_RULES 232\n%define ID_LBL_RULES 233\n%define TV_RULES  3168\n"),
    ("%define TV_SIZE   3168\n", "%define TV_SIZE   3440\n"),
    ('WSTR s_c_spc,', 'WSTR s_c_ids, "식별자 이름 무시"\nWSTR s_l_rules, "대체 규칙(old=new;..):"\nWSTR s_c_spc,'),
])
edit('text_ui.inc', [
    ("    PLACE ID_CHK_SYN, 100\n    PLACE ID_LBL_INFO, 520\n", "    PLACE ID_CHK_SYN, 100\n    PLACE ID_CHK_IDS, 140\n    PLACE ID_LBL_INFO, 520\n"),
    ("    PLACE ID_ED_CASE, 110\n", "    PLACE ID_ED_CASE, 110\n    PLACE ID_LBL_RULES, 160\n    PLACE ID_EDIT_RULES, 220\n"),
    ("    invoke mk_chk, rsi, &s_ed_case, ID_ED_CASE, 0\n", "    invoke mk_chk, rsi, &s_ed_case, ID_ED_CASE, 0\n    invoke mk_chk, rsi, &s_c_ids, ID_CHK_IDS, 0\n    invoke mk_lbl, rsi, &s_l_rules, ID_LBL_RULES\n    invoke mk_edit, rsi, ID_EDIT_RULES\n"),
])
# text_compare: flags 16 / 32 and the rule text
t = open('text_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
a = "    invoke tv_cmp_anch, rbx, &rsp+C_LA, &rsp+C_LB, r13, &rsp+C_CP, &rsp+C_HV\n"
assert t.count(a) == 1
t = t.replace(a, """    invoke get_chk, rsi, ID_CHK_IDS
    shl eax, 4
    or r13d, eax
    invoke GetDlgItem, rsi, ID_EDIT_RULES
    invoke GetWindowTextW, rax, &rbx+TV_RULES, 120
    cmp word [rbx+TV_RULES], 0
    je .norules
    or r13d, 32
    lea rax, [rbx+TV_RULES]
    mov [g_tc_rules], rax
.norules:
""" + a)
open('text_ui.inc', 'w', encoding='utf-8', newline='\n').write(t)
edit('text.asm', [("extern icon_set,", "extern g_tc_rules, icon_set,")])
print('tc07 ok')

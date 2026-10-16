import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')

p = 'xlsx.inc'
s = open(p, encoding='utf-8').read().replace('\r\n', '\n')


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:60], s.count(a))
    s = s.replace(a, b)


rep("""%define XC_ROW    40               ; qword[16384] cell pointers of the current row
%define XC_MAXCOL 48
%define XC_ROWNO  52
%define XC_NEXT   56
%define XC_SIDE   64
%define XC_LASTCOL 72
%define XC_SIZE   80
""", """%define XC_MAXCOL 40
%define XC_ROWNO  44
%define XC_NEXT   48
%define XC_SIDE   56
%define XC_LASTCOL 64
%define XC_ROW    96               ; qword[16384] cell pointers of the current row
%define XC_SIZE   96+16384*8
""")
rep("    invoke calloc, 1, XC_SIZE+16384*8\n", "    invoke calloc, 1, XC_SIZE\n")
rep("    mov rbx, rdi                      ; (unused)\n    mov rbx, rcx\n    mov rsi, rdx\n.top:\n    mov rcx, rsi\n    call x_find_lt\n    mov rsi, rax\n    cmp word [rsi], 0\n    je .done\n    lea rcx, [rsi+2]\n    lea rdx, [xn_si]",
    "    mov rbx, rcx\n    mov rsi, rdx\n.top:\n    mov rcx, rsi\n    call x_find_lt\n    mov rsi, rax\n    cmp word [rsi], 0\n    je .done\n    lea rcx, [rsi+2]\n    lea rdx, [xn_si]")
rep("""    call x_tag_end
    cmp word [rax-2], '/'
    je .entryend
    lea rsi, [rax+2]
.inner:""", """    call x_tag_end
    lea rsi, [rax+2]
    cmp word [rax-2], '/'
    je .entryend
.inner:""")
# numeric entity failure keeps the ampersand
rep("""    cmp word [r8], '#'
    jne .copy
""", """    cmp word [r8], '#'
    jne .copy
""")
rep("""    movzx eax, word [r8]
    cmp eax, ';'
    je .ndone
    test eax, eax
    jz .copy
    cmp eax, '0'
    jb .copy
    cmp eax, '9'
    jbe .dg
    or eax, 0x20
    cmp eax, 'a'
    jb .copy
    cmp eax, 'f'
    ja .copy
    sub eax, 'a'-10
    jmp .acc""", """    movzx eax, word [r8]
    cmp eax, ';'
    je .ndone
    test eax, eax
    jz .bad
    cmp eax, '0'
    jb .bad
    cmp eax, '9'
    jbe .dg
    or eax, 0x20
    cmp eax, 'a'
    jb .bad
    cmp eax, 'f'
    ja .bad
    sub eax, 'a'-10
    jmp .acc""")
rep(""".ndone:
    lea rcx, [r8+2]""", """.bad:
    mov eax, '&'
    jmp .copy
.ndone:
    lea rcx, [r8+2]""")
rep("xl_sheet_parse:\n    PROLOG 192", "xl_sheet_parse:\n    PROLOG 256")
rep("    invoke xl_flush, rbx\n    EPILOG 192\n\n; xl_num", "    invoke xl_flush, rbx\n    EPILOG 256\n\n; xl_num")
rep("""    mov r15d, 0                       ; cell type: 's' shared string
    movzx eax, word [rsp+160]
    mov r15d, eax
    xor edi, edi                      ; value pointer
    cmp word [r12-2], '/'
    je .store
    lea rsi, [r12+2]
.cl:""", """    movzx eax, word [rsp+160]         ; cell type: 's' = shared string (t="str" etc. are plain)
    cmp word [rsp+162], 0
    je .t1
    mov eax, 'x'
.t1:
    mov r15d, eax
    xor edi, edi                      ; value pointer
    lea rsi, [r12+2]
    cmp word [r12-2], '/'
    je .store
.cl:""")
rep("""    mov rax, r14
    sub rax, rsi
    lea rdx, [r13+rsi]
    lea r9, [r15]
    lea rcx, [r14+1]
    mov [rsp+32], rcx
    invoke MultiByteToWideChar, 65001, 0, rdx, rax, r9
    test eax, eax
    jns .term
    xor eax, eax""", """    lea rdi, [r13+rsi]
    mov rbp, r14
    sub rbp, rsi
    lea rbx, [r14+1]
    invoke MultiByteToWideChar, 65001, 0, rdi, rbp, r15, rbx
    test eax, eax
    jns .term
    xor eax, eax""")
rep("    mov r12, rcx\n    mov r13, rsi\n    mov r13, rdx\n    invoke memset, &rsp+96, 0, XV_STRUCT", "    mov r12, rcx\n    mov r13, rdx\n    invoke memset, &rsp+96, 0, XV_STRUCT")
open(p, 'w', encoding='utf-8', newline='\n').write(s)


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:60], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('table.asm', [
    ("""    invoke side_free, rbx
    invoke text_load, r12, &rsp+96             ; TXT at [rsp+96]: text, len, enc, crlf, eol""",
     """    invoke side_free, rbx
    invoke wcsrchr, r12, '.'
    test rax, rax
    jz .csv
    mov r13, rax
    invoke _wcsicmp, r13, &xl_ext
    test eax, eax
    jz .xlsx
    invoke _wcsicmp, r13, &xl_extm
    test eax, eax
    jnz .csv
.xlsx:
    invoke xlsx_load, r12, rbx
    EPILOG 192
.csv:
    invoke text_load, r12, &rsp+96             ; TXT at [rsp+96]: text, len, enc, crlf, eol"""),
    ("extern text_load, vec_push, lower_w, set_tab_title", "extern text_load, vec_push, lower_w, set_tab_title, malloc"),
])
t = open('table.asm', encoding='utf-8').read().rstrip('\n') + '\n%include "xlsx.inc"\n'
open('table.asm', 'w', encoding='utf-8', newline='\n').write(t)
edit('main.asm', [
    ('WSTR e_tsv, ".tsv"\n', 'WSTR e_tsv, ".tsv"\nWSTR e_xlsx, ".xlsx"\nWSTR e_xlsm, ".xlsm"\n'),
    ("tbl_exts:   dq e_csv, e_tsv, 0", "tbl_exts:   dq e_csv, e_tsv, e_xlsx, e_xlsm, 0"),
])
print('xlsx patched')

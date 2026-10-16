import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# conv.asm: reject non-content PDF streams, add tl_isconv
c = open('conv.asm', encoding='utf-8').read().replace('\r\n', '\n')
c = c.replace('k_length1: db "/Length1", 0\n', 'k_length1: db "/Length1", 0\nk_xref: db "/XRef", 0\nk_objstm: db "/ObjStm", 0\nk_meta: db "/Metadata", 0\n')
c = c.replace("""    lea r8, [k_length1]
    call cv_find
    test rax, rax
    jnz .skip
""", """    lea r8, [k_length1]
    call cv_find
    test rax, rax
    jnz .skip
    mov rcx, [rsp+160]
    mov rdx, [rsp+168]
    lea r8, [k_xref]
    call cv_find
    test rax, rax
    jnz .skip
    mov rcx, [rsp+160]
    mov rdx, [rsp+168]
    lea r8, [k_objstm]
    call cv_find
    test rax, rax
    jnz .skip
    mov rcx, [rsp+160]
    mov rdx, [rsp+168]
    lea r8, [k_meta]
    call cv_find
    test rax, rax
    jnz .skip
""", 1)
c = c.replace("global tl_convert\n", "global tl_convert, tl_isconv\n", 1)
c += """
; tl_isconv(path) -> eax 1 when the file is read through a converter (so it must not be written back as text)
tl_isconv:
    PROLOG 1200
    mov rsi, rcx
    invoke wcsrchr, rsi, '.'
    test rax, rax
    jz .no
    mov rbx, rax
    invoke _wcsicmp, rbx, &e_docx
    test eax, eax
    jz .yes
    invoke _wcsicmp, rbx, &e_docm
    test eax, eax
    jz .yes
    invoke _wcsicmp, rbx, &e_rtf
    test eax, eax
    jz .yes
    invoke _wcsicmp, rbx, &e_pdf
    test eax, eax
    jz .yes
    invoke GetPrivateProfileStringW, &sec_convert, rbx, &s_empty, &rsp+96, 8, &g_ini
    cmp word [rsp+96], 0
    jne .yes
.no:
    xor eax, eax
    EPILOG 1200
.yes:
    mov eax, 1
    EPILOG 1200
"""
open('conv.asm', 'w', encoding='utf-8', newline='\n').write(c)

edit('textlib.asm', [
    ("global text_load, text_save, lines_split,", "global text_load, text_save, text_load_raw, lines_split,"),
    ("extern safe_write2\n", "extern safe_write2, tl_convert, tl_isconv, DeleteFileW\n"),
    ("text_load:\n    PROLOG 160\n", """; text_load(path, TXT*) -> eax 1 ok: Word / RTF / PDF and [Convert] rules are rendered to text first
text_load:
    PROLOG 1200
    mov rsi, rcx
    mov rdi, rdx
    invoke tl_convert, rsi, &rsp+96
    test eax, eax
    jz .plain
    invoke text_load_raw, &rsp+96, rdi
    mov ebx, eax
    invoke DeleteFileW, &rsp+96
    mov eax, ebx
    EPILOG 1200
.plain:
    invoke text_load_raw, rsi, rdi
    EPILOG 1200

text_load_raw:
    PROLOG 160
"""),
    ("text_save:\n", """; text_save(path, text, len, enc | crlf<<8) -> eax 1 ok; refuses files that are only readable through a converter
text_save:
    PROLOG 64
    mov rbx, rcx
    mov rsi, rdx
    mov r12, r8
    mov r13, r9
    invoke tl_isconv, rbx
    test eax, eax
    jnz .refuse
    invoke text_save_raw, rbx, rsi, r12, r13
    EPILOG 64
.refuse:
    xor eax, eax
    EPILOG 64

text_save_raw:
"""),
])
edit('../build-gui.ps1', [("'settings','script','shell'", "'settings','script','shell','conv'")])
print('ok')

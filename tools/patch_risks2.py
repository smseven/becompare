import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# ---- risk 3: folder merge
edit('fmerge.asm', [
    ('WSTR f_done, "병합 완료: 복사 %d · 병합 파일 %d · 제외 %d · 미해결 충돌 %d"', 'WSTR f_done, "병합 완료: 복사 %d · 병합 파일 %d · 제외 %d · 미해결 충돌 %d · 복사 실패 %d"'),
    ("    xor r15d, r15d                    ; unresolved\n    invoke SHCreateDirectoryExW, 0, &rbx+FM_OUT, 0\n", "    xor r15d, r15d                    ; unresolved\n    mov dword [rsp+4512], 0           ; copy failures\n    invoke SHCreateDirectoryExW, 0, &rbx+FM_OUT, 0\n"),
    ("""    invoke CopyFileW, &rsp+96, &rsp+2300, 0
    test eax, eax
    jz .e
    inc r12d
    jmp .e
""", """    invoke CopyFileW, &rsp+96, &rsp+2300, 0
    test eax, eax
    jnz .copied
    inc dword [rsp+4512]
    jmp .e
.copied:
    inc r12d
    jmp .e
"""),
    (""".conf:
    invoke GetFileAttributesW, &rsp+2300
    cmp eax, -1
    je .unres
    inc r13d
    jmp .e
""", """.conf:
    ; a conflict counts as merged only when the output was written after both inputs last changed
    invoke fm_mtime, &rsp+2300
    mov [rsp+4560], rax
    test rax, rax
    jz .unres
    mov qword [rsp+4568], 0
    test dword [rbp+FE_FLAGS], 1
    jz .nol
    invoke fm_path, rbx, rbp, 0, &rsp+96
    invoke fm_mtime, &rsp+96
    cmp rax, [rsp+4568]
    jbe .nol
    mov [rsp+4568], rax
.nol:
    test dword [rbp+FE_FLAGS], 2
    jz .nor
    invoke fm_path, rbx, rbp, 1, &rsp+96
    invoke fm_mtime, &rsp+96
    cmp rax, [rsp+4568]
    jbe .nor
    mov [rsp+4568], rax
.nor:
    mov rax, [rsp+4560]
    cmp rax, [rsp+4568]
    jb .unres
    inc r13d
    jmp .e
"""),
    ("    invoke _snwprintf, &rsp+96, 100, &f_done, r12, r13, r14, r15\n", "    mov eax, [rsp+4512]\n    mov [rsp+4572], eax\n    invoke _snwprintf, &rsp+96, 120, &f_done, r12, r13, r14, r15, [rsp+4572]\n"),
    ("; fm_samepath(a, b)", """; fm_mtime(path) -> rax last-write FILETIME (0 when missing)
fm_mtime:
    PROLOG 128
    invoke GetFileAttributesExW, rcx, 0, &rsp+96
    xor ecx, ecx
    test eax, eax
    jz .d
    mov rcx, [rsp+96+20]
.d:
    mov rax, rcx
    EPILOG 128

; fm_samepath(a, b)"""),
    ("CopyFileW, GetFileAttributesW,", "CopyFileW, GetFileAttributesExW, GetFileAttributesW,"),
])
print('risks patched')

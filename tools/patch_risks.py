import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# ---- risk 1: incomplete directory scans block synchronisation
edit('folder.asm', [
    ("%define F_SIZE    5168\n", "%define F_SCANERR 5160\n%define F_SIZE    5176\n"),
    ('WSTR s_done_short, "비교 완료"', 'WSTR s_done_short, "비교 완료"\nWSTR s_scanerr, "일부 폴더를 읽지 못해(접근 거부·연결 끊김 등) 스캔이 불완전합니다. 동기화는 실행할 수 없습니다."\nWSTR s_scanerr_short, "비교 완료 — 일부 폴더를 읽지 못함(동기화 불가)"'),
    ("g_collapse, MoveFileW,", "g_collapse, GetLastError, GetCurrentProcessId, MoveFileW,"),
    (""".find:
    invoke FindFirstFileW, &rsp+L_PAT, &rsp+L_FD
    cmp rax, -1
    je .done
    mov rbx, rax
""", """.find:
    invoke FindFirstFileW, &rsp+L_PAT, &rsp+L_FD
    cmp rax, -1
    jne .found1
    mov dword [r12+F_SCANERR], 1     ; a directory that cannot be listed is an incomplete scan
    jmp .done
.found1:
    mov rbx, rax
"""),
    (""".next:
    invoke FindNextFileW, rbx, &rsp+L_FD
    test eax, eax
    jnz .loop
    invoke FindClose, rbx
.done:
    mov rax, [r15+8]
    cmp rax, 1
    jbe .ret
    invoke qsort, [r15], rax, 32, &cmp_te
""", """.next:
    invoke FindNextFileW, rbx, &rsp+L_FD
    test eax, eax
    jnz .loop
    call GetLastError
    cmp eax, 18                      ; ERROR_NO_MORE_FILES
    je .endok
    mov dword [r12+F_SCANERR], 1
.endok:
    invoke FindClose, rbx
.done:
    mov rax, [r15+8]
    cmp rax, 1
    jbe .ret
    invoke qsort, [r15], rax, 32, &cmp_te
"""),
    # risk 2: unique temp root per session and process, relative path preserved
    ('WSTR f_tmpside, "%s%c"', 'WSTR f_tmpside, "%s%c"\nWSTR f_tmpuniq, "%s%X_%X\\%c"'),
])

edit('folder_vfs.inc', [
    ("""    invoke _snwprintf, r14, 519, &f_tmpside, &rsp+96, r15
    invoke CreateDirectoryW, r14, 0
    invoke wcsrchr, r13, 0x5C
    mov rcx, r13
    test rax, rax
    jz .nm
    lea rcx, [rax+2]
.nm:
    mov r13, rcx                     ; file name only
    invoke wcslen, r14
    lea r15, [r14+rax*2]
    mov word [r15], 0x5C
    invoke wcscpy, &r15+2, r13
""", """    call GetCurrentProcessId
    mov ebp, eax
    invoke _snwprintf, r14, 519, &f_tmpuniq, &rsp+96, rbp, rbx, r15   ; <tmp>\\<pid>_<session>\\A
    invoke SHCreateDirectoryExW, 0, r14, 0
    invoke wcslen, r14
    lea r15, [r14+rax*2]
    mov word [r15], 0x5C
    invoke wcscpy, &r15+2, r13       ; keep the relative path
    invoke wcsrchr, r14, 0x5C
    mov rbp, rax
    mov word [rbp], 0
    invoke SHCreateDirectoryExW, 0, r14, 0
    mov word [rbp], 0x5C
"""),
])

edit('folder_ui.inc', [
    ("    mov [rbx+F_CNT+32], rax\n    mov byte [rbx+F_CANCEL], 0\n    mov qword [rbx+F_RUNNING], 1\n", "    mov [rbx+F_CNT+32], rax\n    mov dword [rbx+F_SCANERR], 0\n    mov byte [rbx+F_CANCEL], 0\n    mov qword [rbx+F_RUNNING], 1\n"),
    ("    invoke set_status_part, 1, &rsp+96\n    invoke set_status, &s_done_short\n", "    invoke set_status_part, 1, &rsp+96\n    invoke set_status, &s_done_short\n    cmp dword [rbx+F_SCANERR], 0\n    je .scanok\n    invoke set_status, &s_scanerr_short\n.scanok:\n"),
    ("""    test qword [g_policy], 1
    jnz .pol
    cmp qword [rbx+F_NENT], 0
    je .norun
""", """    test qword [g_policy], 1
    jnz .pol
    cmp dword [rbx+F_SCANERR], 0
    jne .scanerr
    cmp qword [rbx+F_NENT], 0
    je .norun
"""),
    ("""    jz .ns
    mov rax, [g_batch]
    shr rax, 8
""", """    jz .ns
    cmp dword [rbx+F_SCANERR], 0
    jne .scanfail
    mov rax, [g_batch]
    shr rax, 8
"""),
    (""".ns:
    test qword [g_batch], 4
    jz .d
    xor ecx, ecx
    mov rdx, [rbx+F_ENTS]
""", """.scanfail:
    mov qword [g_exitcode], 2
    and qword [g_batch], ~2
    invoke set_status, &s_scanerr_short
.ns:
    test qword [g_batch], 4
    jz .d
    xor ecx, ecx
    mov rdx, [rbx+F_ENTS]
"""),
])
f = open('folder_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
a = f.index("fold_sync:")
b = f.index("\n.ro:\n", a)
seg_end = f.index("EPILOG 704", b)
f = f[:b] + "\n.scanerr:\n    invoke msgbox, rsi, &s_scanerr, MB_OK|MB_ICONWARNING\n    EPILOG 704" + f[b:]
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(f)

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
    ("extern GetFileAttributesW,", "extern GetFileAttributesExW, GetFileAttributesW,"),
])
print('risks patched')

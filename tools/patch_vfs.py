import os, re
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
exec(open('../tools/ph.py', encoding='utf-8').read())

# ------------------------------------------------------------------ folder.asm
s = open('folder.asm', encoding='utf-8').read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:70], s.count(a))
    s = s.replace(a, b)

rep("%define F_SIZE    2832\n", """%define F_KIND    2832
%define F_VTA     2848
%define F_VTB     2896
%define F_SIZE    3008
%define VT_N_     8
%define VT_KIND_  40
%define HAS_CRC   0x80000000
%define ID_CHK_CRC  115
%define ID_CHK_ATTR 116
%define ID_BTN_SNAP 149
""")
rep("extern g_hinst,", "extern vt_enum, vt_free, zip_open, snap_open, zip_extract, crc32_update, GetTempPathW\nextern g_hinst,")
rep('WSTR s_bak, ".bak"\n', '''WSTR s_bak, ".bak"
WSTR s_ext_bcss, ".bcss"
WSTR s_tmpdir, "BeCompareAsm\\"
WSTR f_tmpside, "%s%c"
WSTR f_snap_crc, `%s\\t%X\\t%llu\\t%llu\\t%X\\n`
WSTR f_snap_nocrc, `%s\\t%X\\t%llu\\t%llu\\t\\n`
WSTR s_snap_head, `BCSS1\\n`
WSTR s_snap_saved, "스냅샷을 저장했습니다."
WSTR s_snap_nocontent, "스냅샷에는 파일 내용이 없어 열 수 없습니다."
WSTR s_ro, "압축 파일·스냅샷은 읽기 전용이라 복사·삭제·동기화할 수 없습니다."
WSTR s_c_crc, "CRC32"
WSTR s_c_attr, "속성"
WSTR s_b_snap, "스냅샷 저장…"
''')
rep('WSTR f_opts, "%d%d%d%d%d%X|%s"', 'WSTR f_opts, "%d%d%d%d%d%X%d%d|%s"')

# enum_dir with virtual sides
i = s.index("; enum_dir(fold, root, rel, vec*)")
j = s.index("; files_equal(fold, pathA, pathB) -> eax 1 if byte-identical")
new_enum = r'''; enum_dir(fold, side 0/1, rel, vec): list one directory into vec of TE{name*, attr dd, crc dd, size, mtime}
%define L_PAT 96
%define L_FD  2304
enum_dir:
    PROLOG 2896
    mov r12, rcx
    mov ebp, edx                     ; side
    mov r14, r8
    mov r15, r9
    lea r13, [r12+F_ROOTA]
    test ebp, ebp
    jz .rt
    lea r13, [r12+F_ROOTB]
.rt:
    cmp qword [r12+F_KIND+rbp*8], 1
    je .virt
    cmp word [r14], 0
    jne .rel
    invoke _snwprintf, &rsp+L_PAT, 1100, &f_star1, r13
    jmp .find
.rel:
    invoke _snwprintf, &rsp+L_PAT, 1100, &f_star2, r13, r14
.find:
    invoke FindFirstFileW, &rsp+L_PAT, &rsp+L_FD
    cmp rax, -1
    je .done
    mov rbx, rax
.loop:
    lea rsi, [rsp+L_FD+FD_NAME]
    cmp word [rsi], '.'
    jne .nd
    cmp word [rsi+2], 0
    je .next
    cmp word [rsi+2], '.'
    jne .nd
    cmp word [rsi+4], 0
    je .next
.nd:
    invoke excl_match, &r12+F_EXCL, rsi
    test eax, eax
    jnz .next
    invoke vec_push, r15, 32
    mov rdi, rax
    invoke str_dup, rsi
    mov [rdi], rax
    mov eax, [rsp+L_FD+FD_ATTR]
    mov [rdi+8], eax
    mov dword [rdi+12], 0
    mov edx, [rsp+L_FD+FD_SZHI]
    shl rdx, 32
    mov eax, [rsp+L_FD+FD_SZLO]
    or rdx, rax
    mov [rdi+16], rdx
    mov rax, [rsp+L_FD+FD_MTIME]
    mov [rdi+24], rax
.next:
    invoke FindNextFileW, rbx, &rsp+L_FD
    test eax, eax
    jnz .loop
    invoke FindClose, rbx
.done:
    mov rax, [r15+8]
    cmp rax, 1
    jbe .ret
    invoke qsort, [r15], rax, 32, &cmp_te
.ret:
    EPILOG 2896
.virt:
    lea rcx, [r12+F_VTA]
    test ebp, ebp
    jz .vt
    lea rcx, [r12+F_VTB]
.vt:
    invoke vt_enum, rcx, r14, r15
    xor esi, esi                     ; read index
    xor edi, edi                     ; write index
.vf:
    cmp rsi, [r15+8]
    jae .vdone
    mov rax, rsi
    shl rax, 5
    add rax, [r15]
    mov rbx, rax
    invoke excl_match, &r12+F_EXCL, [rbx]
    test eax, eax
    jz .vkeep
    invoke free, [rbx]
    inc rsi
    jmp .vf
.vkeep:
    mov rax, rdi
    shl rax, 5
    add rax, [r15]
    cmp rax, rbx
    je .vsame
    mov r8, [rbx]
    mov [rax], r8
    mov r8, [rbx+8]
    mov [rax+8], r8
    mov r8, [rbx+16]
    mov [rax+16], r8
    mov r8, [rbx+24]
    mov [rax+24], r8
.vsame:
    inc rdi
    inc rsi
    jmp .vf
.vdone:
    mov [r15+8], rdi
    EPILOG 2896

'''
s = s[:i] + new_enum + s[j:]

# cmp_files
i = s.index("; cmp_files(fold, teA, teB, relname)")
j = s.index("; ent_side(ent, te, side 0/1)")
new_cmp = r'''; cmp_files(fold, teA, teB, relname) -> eax status (SAME/DIFF) per the selected criteria
;   F_OPT bits: 1 size, 2 mtime, 4 content (bytes), 0x20 CRC-32, 0x40 attributes
cmp_files:
    PROLOG 4496
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    mov r15, r9
    mov ebx, [r12+F_OPT]
    mov rax, [r13+16]
    cmp rax, [r14+16]
    jne .sizediff
    test ebx, 0x24
    jz .mt
    mov rax, [r12+F_KIND]
    or rax, [r12+F_KIND+8]
    jnz .virtual
    invoke _snwprintf, &rsp+96, 1100, &f_path, &r12+F_ROOTA, r15
    invoke _snwprintf, &rsp+2296, 1100, &f_path, &r12+F_ROOTB, r15
    test ebx, 4
    jz .crc2
    invoke files_equal, r12, &rsp+96, &rsp+2296
    test eax, eax
    jz .diff
    jmp .attrs
.crc2:
    invoke file_crc, r12, &rsp+96
    mov rsi, rax
    invoke file_crc, r12, &rsp+2296
    cmp rsi, -1
    je .diff
    cmp rax, -1
    je .diff
    cmp rsi, rax
    jne .diff
    jmp .attrs
.virtual:
    invoke side_crc, r12, 0, r13, r15
    mov rsi, rax
    invoke side_crc, r12, 1, r14, r15
    cmp rsi, -1
    je .mt
    cmp rax, -1
    je .mt
    cmp rsi, rax
    jne .diff
    jmp .attrs
.mt:
    test ebx, 2
    jz .attrs
.mtcmp:
    mov rax, [r13+24]
    sub rax, [r14+24]
    jns .abs
    neg rax
.abs:
    cmp rax, MTIME_TOL
    ja .diff
    jmp .attrs
.sizediff:
    test ebx, 0x25
    jnz .diff
    test ebx, 2
    jnz .mtcmp
.attrs:
    test ebx, 0x40
    jz .same
    mov rax, [r12+F_KIND]
    or rax, [r12+F_KIND+8]
    jnz .same
    mov eax, [r13+8]
    xor eax, [r14+8]
    and eax, 0x27
    jnz .diff
.same:
    xor eax, eax
    EPILOG 4496
.diff:
    mov eax, ST_DIFF
    EPILOG 4496

'''
s = s[:i] + new_cmp + s[j:]
rep("invoke enum_dir, r12, &r12+F_ROOTA, r13, &rsp+L_VA", "invoke enum_dir, r12, 0, r13, &rsp+L_VA")
rep("invoke enum_dir, r12, &r12+F_ROOTB, r13, &rsp+L_VB", "invoke enum_dir, r12, 1, r13, &rsp+L_VB")
rep('%include "folder_ui.inc"\n', '%include "folder_ui.inc"\n%include "folder_vfs.inc"\n')
open('folder.asm', 'w', encoding='utf-8', newline='\n').write(s)

# ------------------------------------------------------------------ vtab: DOS time is local time
patch('vtab.asm', [
    ("extern MultiByteToWideChar, DosDateTimeToFileTime,", "extern MultiByteToWideChar, DosDateTimeToFileTime, LocalFileTimeToFileTime,"),
    ("""    invoke DosDateTimeToFileTime, rcx, rdx, &rdi+VE_MTIME
""", """    invoke DosDateTimeToFileTime, rcx, rdx, &rdi+VE_MTIME
    invoke LocalFileTimeToFileTime, &rdi+VE_MTIME, &rdi+VE_MTIME
"""),
])

# ------------------------------------------------------------------ folder_ui.inc
t = open('folder_ui.inc', encoding='utf-8').read()
def rept(a, b, cnt=1):
    global t
    assert t.count(a) == cnt, (a[:70], t.count(a))
    t = t.replace(a, b)

# options read: crc / attributes
rept("""    invoke get_chk, rsi, ID_CHK_LINKS
    shl eax, 3
    or edi, eax
    mov eax, [rbx+F_OPT]""", """    invoke get_chk, rsi, ID_CHK_LINKS
    shl eax, 3
    or edi, eax
    invoke get_chk, rsi, ID_CHK_CRC
    shl eax, 5
    or edi, eax
    invoke get_chk, rsi, ID_CHK_ATTR
    shl eax, 6
    or edi, eax
    mov eax, [rbx+F_OPT]""")

# collect
a = t.index("; fold_collect(hwnd, sess, fold)")
b = t.index("; fold_theme(fold)")
new_collect = r'''; fold_collect(hwnd, sess, fold): paths + options string -> session  "SMCLBF RA|exclude"
fold_collect:
    PROLOG 160
    mov rsi, rcx
    mov rdi, rdx
    mov rbx, r8
    invoke pb_collect, rsi, rdi
    invoke fold_read_ui, rsi, rbx
    xor r12d, r12d                   ; filter as a 4-bit value
    mov eax, [rbx+F_FMASK]
    test eax, 1
    jz .n1
    or r12d, 1
.n1:
    test eax, 2
    jz .n2
    or r12d, 2
.n2:
    test eax, 4
    jz .n3
    or r12d, 4
.n3:
    test eax, 8
    jz .n4
    or r12d, 8
.n4:
    mov eax, [rbx+F_OPT]
    mov ecx, eax
    shr ecx, 1
    and ecx, 1
    mov [rsp+32], rcx                ; M
    mov ecx, eax
    shr ecx, 2
    and ecx, 1
    mov [rsp+40], rcx                ; C
    mov ecx, eax
    shr ecx, 3
    and ecx, 1
    mov [rsp+48], rcx                ; L
    mov ecx, eax
    shr ecx, 4
    and ecx, 1
    mov [rsp+56], rcx                ; B
    mov [rsp+64], r12                ; F
    mov ecx, eax
    shr ecx, 5
    and ecx, 1
    mov [rsp+72], rcx                ; R (CRC)
    mov ecx, eax
    shr ecx, 6
    and ecx, 1
    mov [rsp+80], rcx                ; A (attributes)
    lea rcx, [rbx+F_EXCL]
    mov [rsp+88], rcx
    and eax, 1
    mov r9d, eax                     ; S
    lea rcx, [rdi+SS_OPTS]
    mov edx, 1023
    lea r8, [f_opts]
    call _snwprintf
    EPILOG 160

; fold_opts_apply(hwnd, sess, fold): restore the controls from the saved options string
fold_opts_apply:
    PROLOG 64
    mov rsi, rcx
    lea rbx, [rdx+SS_OPTS]
    mov rdi, r8
    cmp word [rbx], 0
    je .d
    movzx r8d, word [rbx]
    sub r8d, '0'
    invoke set_chk_id, rsi, ID_CHK_SIZE, r8
    movzx r8d, word [rbx+2]
    sub r8d, '0'
    invoke set_chk_id, rsi, ID_CHK_MTIME, r8
    movzx r8d, word [rbx+4]
    sub r8d, '0'
    invoke set_chk_id, rsi, ID_CHK_CONT, r8
    movzx r8d, word [rbx+6]
    sub r8d, '0'
    invoke set_chk_id, rsi, ID_CHK_LINKS, r8
    movzx eax, word [rbx+8]
    sub eax, '0'
    shl eax, 4
    mov [rdi+F_OPT], eax
    movzx eax, word [rbx+10]
    cmp eax, '9'
    jbe .dig
    sub eax, 7
.dig:
    sub eax, '0'
    mov r12d, eax
    mov r8d, r12d
    and r8d, 1
    invoke set_chk_id, rsi, ID_CHK_SAME, r8
    mov r8d, r12d
    shr r8d, 1
    and r8d, 1
    invoke set_chk_id, rsi, ID_CHK_DIFF, r8
    mov r8d, r12d
    shr r8d, 2
    and r8d, 1
    invoke set_chk_id, rsi, ID_CHK_LONLY, r8
    mov r8d, r12d
    shr r8d, 3
    and r8d, 1
    invoke set_chk_id, rsi, ID_CHK_RONLY, r8
    movzx r8d, word [rbx+12]
    sub r8d, '0'
    invoke set_chk_id, rsi, ID_CHK_CRC, r8
    movzx r8d, word [rbx+14]
    sub r8d, '0'
    invoke set_chk_id, rsi, ID_CHK_ATTR, r8
    invoke GetDlgItem, rsi, ID_EDIT_EXCL
    invoke SetWindowTextW, rax, &rbx+18
.d:
    EPILOG 64

'''
t = t[:a] + new_collect + t[b:]

# fold_start: roots may be folders, archives or snapshots
rept("""    invoke GetFileAttributesW, &rbx+F_ROOTA
    cmp eax, -1
    je .bad
    test eax, FILE_ATTRIBUTE_DIRECTORY
    jz .bad
    invoke GetFileAttributesW, &rbx+F_ROOTB
    cmp eax, -1
    je .bad
    test eax, FILE_ATTRIBUTE_DIRECTORY
    jz .bad
""", """    invoke fold_free_vt, rbx
    invoke fold_open_root, rbx, 0, &rbx+F_ROOTA
    test eax, eax
    jz .bad
    invoke fold_open_root, rbx, 1, &rbx+F_ROOTB
    test eax, eax
    jz .bad
""")

# open pair: extract archive entries when needed
rept("""    invoke _snwprintf, &rsp+96, 1100, &f_path, &rbx+F_ROOTA, [rdi+E_NAME]
    invoke _snwprintf, &rsp+2296, 1100, &f_path, &rbx+F_ROOTB, [rdi+E_NAME]
    invoke type_for_path, &rsp+96""", """    invoke fold_side_path, rbx, 0, [rdi+E_NAME], &rsp+96
    test eax, eax
    jz .d
    invoke fold_side_path, rbx, 1, [rdi+E_NAME], &rsp+2296
    test eax, eax
    jz .d
    invoke type_for_path, &rsp+96""")

# read-only guards
rept("""fold_copy:
    PROLOG 160
    mov rsi, rcx
    mov rbx, rdx
    lea edi, [r8+1]""", """fold_copy:
    PROLOG 160
    mov rsi, rcx
    mov rbx, rdx
    mov rax, [rbx+F_KIND]
    or rax, [rbx+F_KIND+8]
    jnz .ro
    lea edi, [r8+1]""")
rept(""".none:
    invoke msgbox, rsi, &s_nosel, MB_OK|MB_ICONINFO
    EPILOG 160

; popup_at""", """.none:
    invoke msgbox, rsi, &s_nosel, MB_OK|MB_ICONINFO
    EPILOG 160
.ro:
    invoke msgbox, rsi, &s_ro, MB_OK|MB_ICONINFO
    EPILOG 160

; popup_at""")
rept("""fold_delete:
    PROLOG 160
    mov rsi, rcx
    mov rbx, rdx
    call CreatePopupMenu""", """fold_delete:
    PROLOG 160
    mov rsi, rcx
    mov rbx, rdx
    mov rax, [rbx+F_KIND]
    or rax, [rbx+F_KIND+8]
    jnz .ro
    call CreatePopupMenu""")
rept(""".none:
    invoke msgbox, rsi, &s_nosel, MB_OK|MB_ICONINFO
    EPILOG 160

; ---------------------------------------------------------------- sync""", """.none:
    invoke msgbox, rsi, &s_nosel, MB_OK|MB_ICONINFO
    EPILOG 160
.ro:
    invoke msgbox, rsi, &s_ro, MB_OK|MB_ICONINFO
    EPILOG 160

; ---------------------------------------------------------------- sync""")
rept("""fold_sync:
    PROLOG 704
    mov rsi, rcx
    mov rbx, rdx
    cmp qword [rbx+F_NENT], 0
    je .norun""", """fold_sync:
    PROLOG 704
    mov rsi, rcx
    mov rbx, rdx
    mov rax, [rbx+F_KIND]
    or rax, [rbx+F_KIND+8]
    jnz .ro
    cmp qword [rbx+F_NENT], 0
    je .norun""")
rept(""".norun:
    invoke msgbox, rsi, &s_norun, MB_OK|MB_ICONINFO
    EPILOG 704""", """.ro:
    invoke msgbox, rsi, &s_ro, MB_OK|MB_ICONINFO
    EPILOG 704
.norun:
    invoke msgbox, rsi, &s_norun, MB_OK|MB_ICONINFO
    EPILOG 704""")
rept("""    test qword [g_batch], 2
    jz .ns""", """    mov rax, [rbx+F_KIND]
    or rax, [rbx+F_KIND+8]
    jnz .ns
    test qword [g_batch], 2
    jz .ns""")

# layout and controls
rept("""    PLACE ID_CHK_LINKS, 110
    PLACE ID_LBL_EXCL, 40""", """    PLACE ID_CHK_LINKS, 110
    PLACE ID_CHK_CRC, 70
    PLACE ID_CHK_ATTR, 60
    PLACE ID_LBL_EXCL, 40""")
rept("""    PLACE ID_BTN_REPORT, 110
    PLACE ID_BTN_EXPAND, 84
    PLACE ID_BTN_COLLAP, 84""", """    PLACE ID_BTN_REPORT, 110
    PLACE ID_BTN_SNAP, 110
    PLACE ID_BTN_EXPAND, 76
    PLACE ID_BTN_COLLAP, 76""")
rept("""    invoke mk_chk, rsi, &s_c_links, ID_CHK_LINKS, 0
""", """    invoke mk_chk, rsi, &s_c_links, ID_CHK_LINKS, 0
    invoke mk_chk, rsi, &s_c_crc, ID_CHK_CRC, 0
    invoke mk_chk, rsi, &s_c_attr, ID_CHK_ATTR, 0
""")
rept("""    invoke mk_btn, rsi, &s_b_report, ID_BTN_REPORT
""", """    invoke mk_btn, rsi, &s_b_report, ID_BTN_REPORT
    invoke mk_btn, rsi, &s_b_snap, ID_BTN_SNAP
""")
rept("""    cmp ebx, ID_BTN_REPORT
    je .b_rep""", """    cmp ebx, ID_BTN_REPORT
    je .b_rep
    cmp ebx, ID_BTN_SNAP
    je .b_snap""")
rept(""".b_rep:
    invoke fold_report, rsi, r15
    jmp .zero""", """.b_rep:
    invoke fold_report, rsi, r15
    jmp .zero
.b_snap:
    invoke fold_snapshot, rsi, r15
    jmp .zero""")
rept(""".nothr:
    invoke fold_free_ents, r15""", """.nothr:
    invoke fold_free_vt, r15
    invoke fold_free_ents, r15""")
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(t)
print('folder patched')

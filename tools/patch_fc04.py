import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# ---- folder.asm: compact attribute letters per side, exclusion mask in the scan
edit('folder.asm', [
    ("%define F_SIZE    5176\n", "%define F_ATTRX   5176\n%define F_SIZE    5184\n%define ID_LBL_ATTRX 168\n%define ID_EDIT_ATTRX 169\n%define EF_ATTRA  0x100\n%define EF_ATTRB  0x10000\n"),
    ('WSTR s_done_short,', 'WSTR s_lbl_attrx, "제외 속성(R H S A L C O E):"\nWSTR h_attr, "속성 (왼쪽 | 오른쪽)"\nWSTR s_attr_letters, "RHSALCOE"\nWSTR f_attrcell, "%s | %s"\nWSTR s_done_short,'),
    ("col_text: dq h_name, h_status, h_dir, h_sizea, h_mta, h_sizeb, h_mtb\ncol_w:   dd 380, 90, 50, 110, 150, 110, 150\ncol_fmt: dd 0, 0, 0, 1, 0, 1, 0", "col_text: dq h_name, h_status, h_dir, h_sizea, h_mta, h_sizeb, h_mtb, h_attr\ncol_w:   dd 380, 90, 50, 110, 150, 110, 150, 140\ncol_fmt: dd 0, 0, 0, 1, 0, 1, 0, 0"),
    # ent_side: store the compact attributes
    ("""    mov eax, [rdx+8]
    or [rcx+E_FLAGS], r9d
    test eax, FILE_ATTRIBUTE_DIRECTORY
""", """    mov eax, [rdx+8]
    or [rcx+E_FLAGS], r9d
    push rax
    push rcx
    push rdx
    push r9
    push r10
    call attr_compact
    mov r11d, eax
    pop r10
    pop r9
    pop rdx
    pop rcx
    pop rax
    test r8d, r8d
    jnz .ab
    shl r11d, 8
    jmp .ao
.ab:
    shl r11d, 16
.ao:
    or [rcx+E_FLAGS], r11d
    test eax, FILE_ATTRIBUTE_DIRECTORY
"""),
    ("; scan_dir(fold, rel, depth): merge-walk", """; attr_compact(eax = Win32 attributes) -> eax: bit0 R, 1 H, 2 S, 3 A, 4 L (reparse), 5 C (compressed), 6 O (offline), 7 E (encrypted)
attr_compact:
    mov edx, eax
    and edx, 1
    mov ecx, eax
    shr ecx, 1
    and ecx, 1
    shl ecx, 1
    or edx, ecx
    mov ecx, eax
    shr ecx, 2
    and ecx, 1
    shl ecx, 2
    or edx, ecx
    mov ecx, eax
    shr ecx, 5
    and ecx, 1
    shl ecx, 3
    or edx, ecx
    mov ecx, eax
    shr ecx, 10
    and ecx, 1
    shl ecx, 4
    or edx, ecx
    mov ecx, eax
    shr ecx, 11
    and ecx, 1
    shl ecx, 5
    or edx, ecx
    mov ecx, eax
    shr ecx, 12
    and ecx, 1
    shl ecx, 6
    or edx, ecx
    mov ecx, eax
    shr ecx, 14
    and ecx, 1
    shl ecx, 7
    or edx, ecx
    mov eax, edx
    ret

; scan_dir(fold, rel, depth): merge-walk"""),
    # enumeration filter
    ("""    ; FC-03: size / modification date filters (files only)
""", """    ; FC-04: excluded attributes
    mov eax, [rsp+L_FD+FD_ATTR]
    call attr_compact
    test eax, [r12+F_ATTRX]
    jnz .next
    ; FC-03: size / modification date filters (files only)
"""),
])

# ---- folder_ui.inc
edit('folder_ui.inc', [
    ("    cmp ebp, 7\n    jae .coldone\n", "    cmp ebp, 8\n    jae .coldone\n"),
    ("    cmp r8d, 5\n    je .szb\n    jmp .mtb\n", "    cmp r8d, 5\n    je .szb\n    cmp r8d, 7\n    je .attrc\n    jmp .mtb\n"),
    ("    PLACE ID_EDIT_FDAYS, 50\n", "    PLACE ID_EDIT_FDAYS, 50\n    PLACE ID_LBL_ATTRX, 190\n    PLACE ID_EDIT_ATTRX, 70\n"),
    ("    invoke mk_edit, rsi, ID_EDIT_FDAYS\n", "    invoke mk_edit, rsi, ID_EDIT_FDAYS\n    invoke mk_lbl, rsi, &s_lbl_attrx, ID_LBL_ATTRX\n    invoke mk_edit, rsi, ID_EDIT_ATTRX\n"),
    ("    mov qword [rbx+F_FCUT], 0\n    test eax, eax\n    jz .nofcut\n", """    mov qword [rbx+F_FCUT], 0
    mov r13d, eax
    ; FC-04: letters -> excluded attribute mask
    invoke GetDlgItem, rsi, ID_EDIT_ATTRX
    invoke GetWindowTextW, rax, &rsp+96, 18
    xor r14d, r14d
    xor ecx, ecx
.al:
    movzx eax, word [rsp+96+rcx*2]
    test eax, eax
    jz .ald
    or eax, 0x20
    xor edx, edx
.af:
    cmp edx, 8
    jae .an
    lea r8, [s_attr_letters]
    movzx r9d, word [r8+rdx*2]
    or r9d, 0x20
    cmp r9d, eax
    jne .ax
    mov r10d, 1
    push rcx
    mov ecx, edx
    shl r10d, cl
    pop rcx
    or r14d, r10d
    jmp .an
.ax:
    inc edx
    jmp .af
.an:
    inc ecx
    jmp .al
.ald:
    mov [rbx+F_ATTRX], r14d
    mov eax, r13d
    test eax, eax
    jz .nofcut
"""),
])
t = open('folder_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
a = "fold_cell:\n"
assert t.count(a) == 1
# attribute cell: letters for each side
t = t.replace("\n.name:\n    mov ecx, [rdi+E_DEPTH]\n", """
.attrc:
    ; "<A letters> | <B letters>"
    lea r10, [rsp+96]
    mov eax, [rdi+E_FLAGS]
    shr eax, 8
    movzx r11d, al
    xor ecx, ecx
    xor edx, edx
.l1:
    cmp ecx, 8
    jae .l1d
    bt r11d, ecx
    jnc .l1n
    lea r8, [s_attr_letters]
    movzx r9d, word [r8+rcx*2]
    mov [r10+rdx*2], r9w
    inc edx
.l1n:
    inc ecx
    jmp .l1
.l1d:
    mov word [r10+rdx*2], 0
    lea r10, [rsp+130]
    mov eax, [rdi+E_FLAGS]
    shr eax, 16
    movzx r11d, al
    xor ecx, ecx
    xor edx, edx
.l2:
    cmp ecx, 8
    jae .l2d
    bt r11d, ecx
    jnc .l2n
    lea r8, [s_attr_letters]
    movzx r9d, word [r8+rcx*2]
    mov [r10+rdx*2], r9w
    inc edx
.l2n:
    inc ecx
    jmp .l2
.l2d:
    mov word [r10+rdx*2], 0
    invoke _snwprintf, rsi, 40, &f_attrcell, &rsp+96, &rsp+130
    jmp .out
.name:
    mov ecx, [rdi+E_DEPTH]
""", 1)
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(t)
print('fc04 ok')

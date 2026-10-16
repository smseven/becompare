import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('folder.asm', [
    ("%define ID_LBL_ATTRX 168\n", "%define ID_LBL_ATTRX 168\n%define ID_CHK_ASFILE 170\n"),
    ('WSTR s_lbl_attrx,', 'WSTR s_c_asfile, "압축 파일을 하나의 파일로 비교(헥스)"\nWSTR s_lbl_attrx,'),
])
edit('folder_ui.inc', [
    ("    invoke trim_slash, &rbx+F_ROOTB\n    invoke fold_free_vt, rbx\n", """    invoke trim_slash, &rbx+F_ROOTB
    ; AR-02: archives compared as single files
    invoke get_chk, rsi, ID_CHK_ASFILE
    test eax, eax
    jz .noasf
    invoke GetFileAttributesW, &rbx+F_ROOTA
    cmp eax, -1
    je .noasf
    test eax, 0x10
    jnz .noasf
    invoke GetFileAttributesW, &rbx+F_ROOTB
    cmp eax, -1
    je .noasf
    test eax, 0x10
    jnz .noasf
    invoke add_session, T_HEX, &rbx+F_ROOTA, &rbx+F_ROOTB, 0
    EPILOG 64
.noasf:
    invoke fold_free_vt, rbx
"""),
    ("    PLACE ID_EDIT_ATTRX, 70\n", "    PLACE ID_EDIT_ATTRX, 70\n    PLACE ID_CHK_ASFILE, 250\n"),
    ("    invoke mk_edit, rsi, ID_EDIT_ATTRX\n", "    invoke mk_edit, rsi, ID_EDIT_ATTRX\n    invoke mk_chk, rsi, &s_c_asfile, ID_CHK_ASFILE, 0\n"),
])
print('ok')

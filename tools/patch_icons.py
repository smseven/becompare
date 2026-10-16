import os, re
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def rd(fn):
    return open(fn, encoding='utf-8').read().replace('\r\n', '\n')


def wr(fn, s):
    open(fn, 'w', encoding='utf-8', newline='\n').write(s)


def edit(fn, pairs):
    t = rd(fn)
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    wr(fn, t)


old = """%macro PLACE 2
    mov ecx, %2
    call scl
    mov ebx, eax
    MVID rsi, %1, r12, r13, rbx, r15
    lea r12d, [r12+rbx]
    add r12d, r14d
%endmacro"""
new = """%macro PLACE 2
    mov ecx, %2
    call scl
    mov ebx, eax
    ; wrap to the next toolbar row when the control would leave the client area
    cmp r12d, r14d
    je %%fit
    lea eax, [r12+rbx]
    cmp eax, [rsp+104]
    jbe %%fit
    mov r12d, r14d
    lea r13d, [r13+r15]
    add r13d, r14d
%%fit:
    MVID rsi, %1, r12, r13, rbx, r15
    lea r12d, [r12+rbx]
    add r12d, r14d
%endmacro"""
for fn in ['fmerge.asm', 'table.asm', 'folder_ui.inc', 'hex_ui.inc', 'merge_ui.inc', 'pic_ui2.inc', 'text_ui.inc']:
    t = rd(fn)
    assert t.count(old) == 1, fn
    wr(fn, t.replace(old, new))

# icon helper
p = rd('pathbar.asm')
p = p.replace("global mk_icon, tip_add, glyph_swap", "global mk_icon, tip_add, glyph_swap, icon_set\nglobal g_copyr, g_copyl, g_mover, g_movel, g_del, g_sync, g_pause, g_report, g_snap, g_expand, g_collapse, g_prev, g_next\nextern GetDlgItem, SetWindowTextW", 1)
p += """
section .rdata
align 2
g_copyr:    dw 0xE8C8, 0xE72A, 0
g_copyl:    dw 0xE72B, 0xE8C8, 0
g_mover:    dw 0xE8DE, 0xE72A, 0
g_movel:    dw 0xE72B, 0xE8DE, 0
g_del:      dw 0xE74D, 0
g_sync:     dw 0xE895, 0
g_pause:    dw 0xE769, 0
g_report:   dw 0xE9F9, 0
g_snap:     dw 0xE722, 0
g_expand:   dw 0xE70D, 0
g_collapse: dw 0xE70E, 0
g_prev:     dw 0xE70E, 0
g_next:     dw 0xE70D, 0
section .text

; icon_set(parent, id, glyph, tooltip): turn an existing button into a glyph button with a tooltip
icon_set:
    PROLOG 64
    mov rbx, r8
    mov rdi, r9
    invoke GetDlgItem, rcx, rdx
    mov rsi, rax
    test rax, rax
    jz .d
    invoke SetWindowTextW, rsi, rbx
    invoke SendMessageW, rsi, WM_SETFONT, [g_iconfont], 1
    invoke tip_add, rsi, rdi
.d:
    EPILOG 64
"""
wr('pathbar.asm', p)

# folder
f = rd('folder_ui.inc')
for name, w in [('COPYLR', 56), ('COPYRL', 56), ('MOVELR', 56), ('MOVERL', 56), ('DEL', 40), ('SYNC', 40), ('PAUSE', 40), ('REPORT', 40), ('SNAP', 40), ('EXPAND', 40), ('COLLAP', 40)]:
    f, n = re.subn(r"    PLACE ID_BTN_%s, \d+\n" % name, "    PLACE ID_BTN_%s, %d\n" % (name, w), f)
    assert n == 1, name
icons = ""
for idn, g, tip in [('COPYLR', 'g_copyr', 's_b_copylr'), ('COPYRL', 'g_copyl', 's_b_copyrl'), ('MOVELR', 'g_mover', 's_b_movelr'), ('MOVERL', 'g_movel', 's_b_moverl'),
                    ('DEL', 'g_del', 's_b_del'), ('SYNC', 'g_sync', 's_b_sync'), ('PAUSE', 'g_pause', 's_b_pause'), ('REPORT', 'g_report', 's_b_report'),
                    ('SNAP', 'g_snap', 's_b_snap'), ('EXPAND', 'g_expand', 's_b_expand'), ('COLLAP', 'g_collapse', 's_b_collap')]:
    icons += "    invoke icon_set, rsi, ID_BTN_%s, &%s, &%s\n" % (idn, g, tip)
a = "    invoke mk_btn, rsi, &s_b_collap, ID_BTN_COLLAP\n"
assert f.count(a) == 1
f = f.replace(a, a + icons)
wr('folder_ui.inc', f)
edit('folder.asm', [("extern MoveFileW,", "extern icon_set, g_copyr, g_copyl, g_mover, g_movel, g_del, g_sync, g_pause, g_report, g_snap, g_expand, g_collapse, MoveFileW,")])

# text
t = rd('text_ui.inc')
for name, w in [('PREV', 40), ('NEXT', 40), ('CLR', 56), ('CRL', 56)]:
    t, n = re.subn(r"    PLACE ID_BTN_%s, \d+\n" % name, "    PLACE ID_BTN_%s, %d\n" % (name, w), t)
    assert n == 1, name
a = "    invoke mk_btn, rsi, &s_b_alc, ID_BTN_ALC\n"
assert t.count(a) == 1
t = t.replace(a, a + "    invoke icon_set, rsi, ID_BTN_PREV, &g_prev, &s_b_prev\n    invoke icon_set, rsi, ID_BTN_NEXT, &g_next, &s_b_next\n    invoke icon_set, rsi, ID_BTN_CLR, &g_copyr, &s_b_clr\n    invoke icon_set, rsi, ID_BTN_CRL, &g_copyl, &s_b_crl\n")
wr('text_ui.inc', t)
edit('text.asm', [("extern set_tab_title, vec_push,", "extern icon_set, g_prev, g_next, g_copyr, g_copyl, set_tab_title, vec_push,")])

# hex
h = rd('hex_ui.inc')
for name in ['PREV', 'NEXT']:
    h, n = re.subn(r"    PLACE ID_BTN_%s, \d+\n" % name, "    PLACE ID_BTN_%s, 40\n" % name, h)
    assert n == 1
a = "    invoke mk_btn, rsi, &s_b_next, ID_BTN_NEXT\n"
assert h.count(a) == 1
h = h.replace(a, a + "    invoke icon_set, rsi, ID_BTN_PREV, &g_prev, &s_b_prev\n    invoke icon_set, rsi, ID_BTN_NEXT, &g_next, &s_b_next\n")
wr('hex_ui.inc', h)
edit('hex.asm', [("extern read_file_bytes, set_tab_title", "extern icon_set, g_prev, g_next, read_file_bytes, set_tab_title")])
print('icons patched')

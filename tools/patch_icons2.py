import os, re
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def rd(fn):
    return open(fn, encoding='utf-8').read().replace('\r\n', '\n')


def wr(fn, s):
    open(fn, 'w', encoding='utf-8', newline='\n').write(s)


p = rd('pathbar.asm')
p = p.replace("global mk_icon, tip_add, glyph_swap, icon_set\n", "global mk_icon, tip_add, glyph_swap, icon_set\nglobal g_rot, g_flh, g_flv, g_zout, g_zin, g_fit, g_usel, g_user, g_both, g_save\n", 1)
p = p.replace("g_prev:     dw 0xE70E, 0\n", "g_prev:     dw 0xE70E, 0\ng_rot:      dw 0xE7AD, 0\ng_flh:      dw 0xE8AB, 0\ng_flv:      dw 0xE8CB, 0\ng_zout:     dw 0xE71F, 0\ng_zin:      dw 0xE8A3, 0\ng_fit:      dw 0xE740, 0\ng_usel:     dw 0xE72B, 0xE73E, 0\ng_user:     dw 0xE73E, 0xE72A, 0\ng_both:     dw 0xE8FD, 0\ng_save:     dw 0xE74E, 0\n", 1)
wr('pathbar.asm', p)


def apply(fn, places, anchor, icons, asmfile, externs):
    t = rd(fn)
    for name, w in places:
        t, n = re.subn(r"    PLACE ID_BTN_%s, \d+\n" % name, "    PLACE ID_BTN_%s, %d\n" % (name, w), t)
        assert n == 1, name
    assert t.count(anchor) == 1
    code = "".join("    invoke icon_set, rsi, ID_BTN_%s, &%s, &%s\n" % i for i in icons)
    wr(fn, t.replace(anchor, anchor + code))
    a = rd(asmfile)
    k = a.index("extern ")
    wr(asmfile, a[:k] + "extern icon_set, " + externs + "\n" + a[k:])


apply('pic_ui2.inc', [('ROT', 40), ('FLH', 40), ('FLV', 40), ('ZOUT', 40), ('ZIN', 40), ('FIT', 40)],
      "    invoke mk_btn, rsi, &s_b_fit, ID_BTN_FIT\n",
      [('ROT', 'g_rot', 's_b_rot'), ('FLH', 'g_flh', 's_b_flh'), ('FLV', 'g_flv', 's_b_flv'), ('ZOUT', 'g_zout', 's_b_zout'), ('ZIN', 'g_zin', 's_b_zin'), ('FIT', 'g_fit', 's_b_fit')],
      'pic.asm', 'g_rot, g_flh, g_flv, g_zout, g_zin, g_fit')
apply('merge_ui.inc', [('PREV', 40), ('NEXT', 40), ('USEL', 56), ('USER', 56), ('BOTH', 40), ('SAVE', 40)],
      "    invoke mk_btn, rsi, &s_b_save, ID_BTN_SAVE\n",
      [('PREV', 'g_prev', 's_b_prev'), ('NEXT', 'g_next', 's_b_next'), ('USEL', 'g_usel', 's_b_usel'), ('USER', 'g_user', 's_b_user'), ('BOTH', 'g_both', 's_b_both'), ('SAVE', 'g_save', 's_b_save')],
      'merge.asm', 'g_prev, g_next, g_usel, g_user, g_both, g_save')
print('ok')

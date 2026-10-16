import os, re
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def rd(fn):
    return open(fn, encoding='utf-8').read().replace('\r\n', '\n')


def wr(fn, s):
    open(fn, 'w', encoding='utf-8', newline='\n').write(s)


p = rd('pathbar.asm')
p = p.replace("global mk_icon, tip_add, glyph_swap, icon_set\n", "global mk_icon, tip_add, glyph_swap, icon_set\nglobal g_base, g_edit, g_run\n", 1)
p = p.replace("g_save:     dw 0xE74E, 0\n", "g_save:     dw 0xE74E, 0\ng_base:     dw 0xE81C, 0\ng_edit:     dw 0xE70F, 0\ng_run:      dw 0xE768, 0\n", 1)
wr('pathbar.asm', p)

t = rd('fmerge.asm')
for name, w in [('TA', 56), ('TB', 56), ('TC', 40), ('TD', 40), ('OPENM', 40), ('RUNM', 40)]:
    t, n = re.subn(r"    PLACE ID_BTN_%s, \d+\n" % name, "    PLACE ID_BTN_%s, %d\n" % (name, w), t)
    assert n == 1, name
a = "    invoke mk_btn, rsi, &s_b_runm, ID_BTN_RUNM\n"
assert t.count(a) == 1
icons = [('TA', 'g_usel', 's_b_ta'), ('TB', 'g_user', 's_b_tb'), ('TC', 'g_base', 's_b_tc'), ('TD', 'g_del', 's_b_td'), ('OPENM', 'g_edit', 's_b_openm'), ('RUNM', 'g_run', 's_b_runm')]
t = t.replace(a, a + "".join("    invoke icon_set, rsi, ID_BTN_%s, &%s, &%s\n" % i for i in icons))
t = t.replace("extern sess_new, sess_open\n", "extern sess_new, sess_open\nextern icon_set, g_usel, g_user, g_base, g_del, g_edit, g_run\n", 1)
wr('fmerge.asm', t)
print('ok')

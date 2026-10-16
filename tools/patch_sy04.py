import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


s = open('settings.asm', encoding='utf-8').read().rstrip('\n') + '\n' + open('../tools/ib_part.asm', encoding='utf-8').read()
open('settings.asm', 'w', encoding='utf-8', newline='\n').write(s)

edit('inc/win.inc', [("%define FO_COPY         2\n", "%define FO_MOVE         1\n%define FO_COPY         2\n")])

f = open('folder_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
a = f.index("fold_copy:")
b = f.index("; popup_at(hwnd, anchor id, menu)")
seg = f[a:b]
mv = seg.replace("fold_copy:", "fold_move:").replace("FO_COPY", "FO_MOVE")
ren = open('../tools/rename_part.asm', encoding='utf-8').read()
f = f[:b] + mv + ren + f[b:]
pairs = [
    ("    PLACE ID_BTN_COPYRL, 84\n", "    PLACE ID_BTN_COPYRL, 84\n    PLACE ID_BTN_MOVELR, 84\n    PLACE ID_BTN_MOVERL, 84\n"),
    ("    invoke mk_btn, rsi, &s_b_copyrl, ID_BTN_COPYRL\n", "    invoke mk_btn, rsi, &s_b_copyrl, ID_BTN_COPYRL\n    invoke mk_btn, rsi, &s_b_movelr, ID_BTN_MOVELR\n    invoke mk_btn, rsi, &s_b_moverl, ID_BTN_MOVERL\n"),
    ("    cmp ebx, ID_BTN_COPYRL\n    je .b_rl\n", "    cmp ebx, ID_BTN_COPYRL\n    je .b_rl\n    cmp ebx, ID_BTN_MOVELR\n    je .b_mlr\n    cmp ebx, ID_BTN_MOVERL\n    je .b_mrl\n"),
    (".b_rl:\n    invoke fold_copy, rsi, r15, 1\n    jmp .zero\n", ".b_rl:\n    invoke fold_copy, rsi, r15, 1\n    jmp .zero\n.b_mlr:\n    invoke fold_move, rsi, r15, 0\n    jmp .zero\n.b_mrl:\n    invoke fold_move, rsi, r15, 1\n    jmp .zero\n"),
    ("    cmp ebx, VK_RETURN\n    je .kopen\n    cmp ebx, 0x25\n", "    cmp ebx, VK_RETURN\n    je .kopen\n    cmp ebx, 0x71\n    je .krename\n    cmp ebx, 0x25\n"),
    (".kopen:\n    invoke fold_open_pair, r15, rbp\n    jmp .zero\n", ".kopen:\n    invoke fold_open_pair, r15, rbp\n    jmp .zero\n.krename:\n    invoke fold_rename, rsi, r15, rbp\n    jmp .zero\n"),
]
for x, y in pairs:
    assert f.count(x) == 1, x[:50]
    f = f.replace(x, y)
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(f)

edit('folder.asm', [
    ("%define ID_BTN_SNAP 149\n", "%define ID_BTN_SNAP 149\n%define ID_BTN_MOVELR 166\n%define ID_BTN_MOVERL 167\n"),
    ('WSTR s_b_copyrl, "← 복사"', 'WSTR s_b_copyrl, "← 복사"\nWSTR s_b_movelr, "→ 이동"\nWSTR s_b_moverl, "← 이동"\nWSTR s_ren_title, "이름 바꾸기 (양쪽에 있으면 양쪽 모두 바뀝니다)"\nWSTR s_ren_bad, "이름이 비었거나 사용할 수 없는 문자가 있습니다."'),
    ("extern wcstoul, GetSystemTimeAsFileTime,", "extern MoveFileW, input_box, wcsncpy, wcstoul, GetSystemTimeAsFileTime,"),
])
print('sy04 patched')

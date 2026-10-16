import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('inc/app.inc', [("%define IDM_SETTINGS   1060\n", "%define IDM_SETTINGS   1060\n%define IDM_UPDATE     1070\n")])
edit('main.asm', [
    ("extern settings_show, policy_load, keys_load, g_keytab\n", "extern settings_show, policy_load, keys_load, g_keytab, update_check, update_start\n"),
    ("    invoke AppendMenuW, rbx, MF_STRING, IDM_ABOUT, &m_ab\n", "    invoke AppendMenuW, rbx, MF_STRING, IDM_UPDATE, &m_upd\n    invoke AppendMenuW, rbx, MF_STRING, IDM_ABOUT, &m_ab\n"),
    ('WSTR m_ab, "정보"', 'WSTR m_upd, "업데이트 확인..."\nWSTR m_ab, "정보"'),
    ("    cmp eax, IDM_ABOUT\n    je .c_about\n", "    cmp eax, IDM_UPDATE\n    je .c_update\n    cmp eax, IDM_ABOUT\n    je .c_about\n"),
    (".c_about:\n    invoke msgbox, rsi, &s_about, MB_OK|MB_ICONINFO\n", ".c_update:\n    invoke update_check, rsi, 0\n    jmp .ok0\n.c_about:\n    invoke msgbox, rsi, &s_about, MB_OK|MB_ICONINFO\n"),
    ("    invoke ShowWindow, rsi, rdx\n    invoke UpdateWindow, rsi\n\n.loop:", "    invoke ShowWindow, rsi, rdx\n    invoke UpdateWindow, rsi\n    test qword [g_batch], 4\n    jnz .loop\n    call update_start\n\n.loop:"),
])
edit('../build-gui.ps1', [("'shell','conv'", "'shell','conv','update'")])
print('ok')

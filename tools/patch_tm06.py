import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('text.asm', [
    ("global text_register, text_create, edit_create", "global text_register, text_create, edit_create, tv_anchor_add, tv_cmp_anch"),
])

edit('merge.asm', [
    ("extern save_error\n", "extern save_error\nextern tv_anchor_add, tv_cmp_anch\n"),
    ("%define MG_SIZE   256\n",
     "%define MG_ANCB   216           ; TM-06: block laid out like a text view (TV_NANC / TV_ANC) so tv_anchor_add / tv_cmp_anch can be shared\n"
     "%define MG_PRIS   224           ; pristine generated output, to detect hand edits before regenerating\n"
     "%define MG_SIZE   256\n"
     "%define MG_ANCSZ  2960          ; must exceed text.asm TV_NANC (2880) + 4\n"),
    ("%define ID_LBL_OUT  652\n", "%define ID_LBL_OUT  652\n%define ID_BTN_ALN  653\n%define ID_BTN_ALC  654\n"),
    ('WSTR s_cantread,',
     'WSTR s_b_aln, "정렬 지정"\nWSTR s_b_alc, "정렬 해제"\n'
     'WSTR s_mg_hint, "정렬 지정: 먼저 병합(F5)을 실행하고, 위쪽 왼쪽·오른쪽 창에서 맞추려는 줄(여러 줄 선택 가능)을 각각 선택한 뒤 누르세요."\n'
     'WSTR s_mg_3way, "정렬 지정은 기준 파일이 없는 2-way 병합에서만 사용할 수 있습니다."\n'
     'WSTR s_mg_conf, "정렬 지정: 기존 정렬 지점과 순서가 맞지 않아 추가할 수 없습니다."\n'
     'WSTR s_mg_ok, "정렬 지점을 추가하고 다시 병합했습니다."\n'
     'WSTR s_mg_edited, "출력 창을 직접 수정했습니다. 정렬을 적용하면 출력이 다시 만들어져 수정 내용이 사라집니다. 계속할까요?"\n'
     'WSTR s_cantread,'),
    ("    xor eax, eax\n    mov [rsp+M_DO], rax\n", "    xor eax, eax\n    mov [rsp+M_DO], rax\n"),
    ("    invoke compare_lines, &rsp+M_LL, &rsp+M_LR, 0, &rsp+M_CP, &rsp+M_H1\n    xor r14d, r14d\n.h2:",
     "    invoke tv_cmp_anch, [rbx+MG_ANCB], &rsp+M_LL, &rsp+M_LR, 0, &rsp+M_CP, &rsp+M_H1\n    xor r14d, r14d\n.h2:"),
    ("    invoke rich_set_text, [rbx+MG_HM], rax\n    invoke SendMessageW, [rbx+MG_HM], EM_SETMODIFY, 1, 0\n    invoke rich_theme, [rbx+MG_HM]\n    invoke sb_free, &rsp+M_SB\n",
     "    mov r13, rax\n    invoke rich_set_text, [rbx+MG_HM], r13\n    invoke SendMessageW, [rbx+MG_HM], EM_SETMODIFY, 1, 0\n    invoke rich_theme, [rbx+MG_HM]\n"
     "    invoke free, [rbx+MG_PRIS]\n    invoke wcslen, r13\n    lea r14, [rax*2+2]\n    mov rcx, r14\n    call malloc\n    mov [rbx+MG_PRIS], rax\n    invoke memcpy, rax, r13, r14\n"
     "    invoke sb_free, &rsp+M_SB\n"),
])

edit('merge_ui.inc', [
    # align set / clear
    ("; mg_free_texts(mg)\n", r'''; mg_sel_lines(hrich, out lo, out hi): first and last line of the selection (a caret = one line)
mg_sel_lines:
    PROLOG 96
    mov rbx, rcx
    mov rsi, rdx
    mov rdi, r8
    invoke SendMessageW, rbx, EM_EXGETSEL, 0, &rsp+80
    mov r12d, [rsp+80]                ; cpMin
    mov r13d, [rsp+84]                ; cpMax
    invoke SendMessageW, rbx, EM_LINEFROMCHAR, r12, 0
    mov [rsi], eax
    mov [rdi], eax
    cmp r13d, r12d
    jbe .d
    lea edx, [r13-1]                  ; a selection ending at a line start does not include that line
    invoke SendMessageW, rbx, EM_LINEFROMCHAR, rdx, 0
    mov [rdi], eax
.d:
    EPILOG 96

; mg_align_set(hwnd, mg, sess): TM-06 pin the selected left lines to the selected right lines, then merge again
mg_align_set:
    PROLOG 192
    mov rsi, rcx
    mov rbx, rdx
    mov r12, r8
    cmp qword [rbx+MG_THREE], 0
    jne .three
    cmp qword [rbx+MG_PRIS], 0
    je .hint
    ; hand-edited output would be lost by regenerating
    invoke rich_get_text, [rbx+MG_HM], &rsp+96
    test rax, rax
    jz .sel
    mov r13, rax
    invoke wcscmp, r13, [rbx+MG_PRIS]
    mov r14d, eax
    invoke free, r13
    test r14d, r14d
    jz .sel
    invoke msgbox, rsi, &s_mg_edited, MB_YESNO|MB_ICONQUESTION
    cmp eax, IDYES
    jne .d
.sel:
    invoke mg_sel_lines, [rbx+MG_HL], &rsp+104, &rsp+108   ; left lo/hi
    invoke mg_sel_lines, [rbx+MG_HR], &rsp+112, &rsp+116   ; right lo/hi
    mov r13d, [rsp+104]
    mov r14d, [rsp+112]
    invoke tv_anchor_add, [rbx+MG_ANCB], r13, r14
    test eax, eax
    jz .conf
    ; a multi-line selection on both sides: the last lines are pinned together as well
    mov r13d, [rsp+108]
    mov r14d, [rsp+116]
    cmp r13d, [rsp+104]
    jbe .go
    cmp r14d, [rsp+112]
    jbe .go
    invoke tv_anchor_add, [rbx+MG_ANCB], r13, r14
    test eax, eax
    jz .conf
.go:
    invoke mg_merge, rsi, rbx, r12
    invoke set_status, &s_mg_ok
    jmp .d
.three:
    invoke set_status, &s_mg_3way
    jmp .d
.hint:
    invoke set_status, &s_mg_hint
    jmp .d
.conf:
    invoke msgbox, rsi, &s_mg_conf, MB_OK|MB_ICONWARNING
.d:
    EPILOG 192

; mg_align_clear(hwnd, mg, sess)
mg_align_clear:
    PROLOG 64
    mov rsi, rcx
    mov rbx, rdx
    mov r12, r8
    mov rax, [rbx+MG_ANCB]
    cmp dword [rax+2880], 0           ; TV_NANC
    je .d
    mov dword [rax+2880], 0
    cmp qword [rbx+MG_PRIS], 0
    je .d
    invoke mg_merge, rsi, rbx, r12
.d:
    EPILOG 64

; mg_free_texts(mg)
'''),
    ("    PLACE ID_BTN_BOTH, 40\n", "    PLACE ID_BTN_BOTH, 40\n    PLACE ID_BTN_ALN, 80\n    PLACE ID_BTN_ALC, 80\n"),
    ("    mov dword [r15+MG_EOL], 1\n", "    mov dword [r15+MG_EOL], 1\n    invoke calloc, 1, MG_ANCSZ\n    mov [r15+MG_ANCB], rax\n"),
    ("    invoke mk_btn, rsi, &s_b_both, ID_BTN_BOTH\n", "    invoke mk_btn, rsi, &s_b_both, ID_BTN_BOTH\n    invoke mk_btn, rsi, &s_b_aln, ID_BTN_ALN\n    invoke mk_btn, rsi, &s_b_alc, ID_BTN_ALC\n"),
    ("    cmp ebx, ID_BTN_SAVE\n    je .save\n    jmp .def\n", "    cmp ebx, ID_BTN_SAVE\n    je .save\n    cmp ebx, ID_BTN_ALN\n    je .b_aln\n    cmp ebx, ID_BTN_ALC\n    je .b_alc\n    jmp .def\n"),
    (".b_al:\n", ".b_aln:\n    invoke mg_align_set, rsi, r15, r14\n    jmp .zero\n.b_alc:\n    invoke mg_align_clear, rsi, r15, r14\n    jmp .zero\n.b_al:\n"),
    # an explicit merge (F5 / button) starts without old anchors
    (".run:\n    invoke mg_merge, rsi, r15, r14\n", ".run:\n    mov rax, [r15+MG_ANCB]\n    mov dword [rax+2880], 0           ; TV_NANC\n    invoke mg_merge, rsi, r15, r14\n"),
    ("    invoke mg_unscan, r15\n    invoke mg_free_texts, r15\n", "    invoke mg_unscan, r15\n    invoke mg_free_texts, r15\n    invoke free, [r15+MG_ANCB]\n    invoke free, [r15+MG_PRIS]\n"),
])
print('tm06 ok')

; sync_dlg.inc - modal "sync preview": every planned operation can be reviewed before it runs

%define SD_LIST   901
%define SD_COMBO  902
%define SD_SUM    903
%define SD_OK     1
%define SD_CANCEL 2
%define LVM_DELETEALLITEMS 0x1009
%define LVM_INSERTITEMW    0x104D
%define LVM_SETITEMTEXTW   0x1074
%define LVIF_PARAM 4

section .rdata
WSTR cn_sd, "BCSyncPreview"
WSTR s_sd_title, "동기화 미리보기 — 실행 전 검토"
WSTR s_sd_ok, "동기화 시작"
WSTR s_sd_cancel, "취소"
WSTR s_sd_f0, "전체 항목"
WSTR s_sd_f1, "신규 생성"
WSTR s_sd_f2, "덮어쓰기"
WSTR s_sd_f3, "삭제"
WSTR h_sd_act, "작업"
WSTR h_sd_path, "경로"
WSTR h_sd_size, "크기"
WSTR f_sd_sum, "신규 %llu · 덮어쓰기 %llu · 삭제 %llu  (총 %llu 작업)  — 삭제는 휴지통으로 이동합니다"
WSTR a_new_r, "복사 → (신규)"
WSTR a_ovr_r, "복사 → (덮어쓰기)"
WSTR a_new_l, "복사 ← (신규)"
WSTR a_ovr_l, "복사 ← (덮어쓰기)"
WSTR a_mk_r, "폴더 생성 →"
WSTR a_mk_l, "폴더 생성 ←"
WSTR a_del_r, "삭제 (오른쪽)"
WSTR a_rd_r, "폴더 삭제 (오른쪽)"
align 8
sd_act: dq 0, a_new_r, a_ovr_r, a_new_l, a_ovr_l, a_mk_r, a_mk_l, a_del_r, a_rd_r

section .bss
alignb 8
g_sd_result: resq 1

section .text

; sd_category(fold, op index) -> eax 1 new / 2 overwrite / 3 delete ; edx = action text index (1..8)
sd_category:
    mov rax, [rcx+F_PLAN]
    lea rax, [rax+rdx*8]
    mov r8d, [rax]                   ; type
    mov r9d, [rax+4]                 ; entry
    mov rax, r9
    shl rax, 6
    add rax, [rcx+F_ENTS]
    cmp r8d, OP_COPYLR
    je .clr
    cmp r8d, OP_COPYRL
    je .crl
    cmp r8d, OP_MKDIRR
    je .mkr
    cmp r8d, OP_MKDIRL
    je .mkl
    cmp r8d, OP_DELR
    je .del
    mov edx, 8
    mov eax, 3
    ret
.clr:
    mov edx, 1
    mov ecx, 1
    cmp dword [rax+E_STATUS], ST_DIFF
    jne .r
    mov edx, 2
    mov ecx, 2
.r:
    mov eax, ecx
    ret
.crl:
    mov edx, 3
    mov ecx, 1
    cmp dword [rax+E_STATUS], ST_DIFF
    jne .r
    mov edx, 4
    mov ecx, 2
    jmp .r
.mkr:
    mov edx, 5
    mov eax, 1
    ret
.mkl:
    mov edx, 6
    mov eax, 1
    ret
.del:
    mov edx, 7
    mov eax, 3
    ret

; sd_fill(hwnd, fold, filter 0..3)
sd_fill:
    PROLOG 400
    mov rsi, rcx
    mov rbx, rdx
    mov r12d, r8d
    invoke GetDlgItem, rsi, SD_LIST
    mov r13, rax
    invoke SendMessageW, r13, LVM_DELETEALLITEMS, 0, 0
    invoke SendMessageW, r13, WM_SETREDRAW, 0, 0
    xor r14d, r14d                   ; op
    xor r15d, r15d                   ; list row
.l:
    cmp r14, [rbx+F_NPLAN]
    jae .done
    invoke sd_category, rbx, r14
    mov edi, eax                     ; category
    mov ebp, edx                     ; action index
    test r12d, r12d
    jz .add
    cmp edi, r12d
    jne .next
.add:
    mov rax, r14
    shl rax, 3
    add rax, [rbx+F_PLAN]
    mov eax, [rax+4]
    shl rax, 6
    add rax, [rbx+F_ENTS]
    mov [rsp+192], rax               ; entry
    ; LVITEMW at [rsp+96]
    invoke memset, &rsp+96, 0, 88
    mov dword [rsp+96], LVIF_TEXT|LVIF_PARAM
    mov [rsp+100], r15d
    lea rcx, [sd_act]
    mov rax, [rcx+rbp*8]
    mov [rsp+96+24], rax
    mov [rsp+96+40], rdi
    invoke SendMessageW, r13, LVM_INSERTITEMW, 0, &rsp+96
    ; sub item 1: path
    invoke memset, &rsp+96, 0, 88
    mov dword [rsp+96+8], 1
    mov rax, [rsp+192]
    mov rax, [rax+E_NAME]
    mov [rsp+96+24], rax
    invoke SendMessageW, r13, LVM_SETITEMTEXTW, r15, &rsp+96
    ; sub item 2: size of the source
    mov rax, [rsp+192]
    mov rdx, [rax+E_SIZEA]
    cmp ebp, 3
    je .sb
    cmp ebp, 4
    jne .sz
.sb:
    mov rdx, [rax+E_SIZEB]
.sz:
    test dword [rax+E_FLAGS], EF_DIRA|EF_DIRB
    jz .fmt
    xor edx, edx
.fmt:
    invoke fmt_size, &rsp+240, rdx
    invoke memset, &rsp+96, 0, 88
    mov dword [rsp+96+8], 2
    lea rax, [rsp+240]
    mov [rsp+96+24], rax
    invoke SendMessageW, r13, LVM_SETITEMTEXTW, r15, &rsp+96
    inc r15d
.next:
    inc r14
    jmp .l
.done:
    invoke SendMessageW, r13, WM_SETREDRAW, 1, 0
    invoke InvalidateRect, r13, 0, 1
    EPILOG 400

; sd_summary(hwnd, fold)
sd_summary:
    PROLOG 400
    mov rsi, rcx
    mov rbx, rdx
    xor r12d, r12d
    xor r13d, r13d
    xor r14d, r14d
    xor r15d, r15d
.l:
    cmp r15, [rbx+F_NPLAN]
    jae .fmt
    invoke sd_category, rbx, r15
    cmp eax, 1
    jne .c2
    inc r12d
    jmp .n
.c2:
    cmp eax, 2
    jne .c3
    inc r13d
    jmp .n
.c3:
    inc r14d
.n:
    inc r15
    jmp .l
.fmt:
    mov rax, [rbx+F_NPLAN]
    mov [rsp+32], rax
    lea rcx, [rsp+96]
    mov edx, 140
    lea r8, [f_sd_sum]
    mov r9d, r12d
    mov [rsp+40], r14
    ; _snwprintf(buf, n, fmt, new, overwrite, delete, total): arguments in order
    mov [rsp+32], r13
    mov [rsp+40], r14
    mov rax, [rbx+F_NPLAN]
    mov [rsp+48], rax
    call _snwprintf
    invoke GetDlgItem, rsi, SD_SUM
    invoke SetWindowTextW, rax, &rsp+96
    EPILOG 400

; sd_layout(hwnd)
sd_layout:
    PROLOG 192
    mov rsi, rcx
    invoke GetClientRect, rsi, &rsp+96
    mov r12d, [rsp+104]              ; width
    mov r13d, [rsp+108]              ; height
    mov ecx, 8
    call scl
    mov r14d, eax                    ; margin
    mov ecx, 30
    call scl
    mov r15d, eax                    ; row height
    mov ebx, r12d
    sub ebx, r14d
    sub ebx, 200
    sub ebx, r14d
    MVID rsi, SD_SUM, r14, r14, rbx, r15
    mov eax, r12d
    sub eax, 190
    sub eax, r14d
    mov ebx, eax
    mov ecx, 190
    call scl
    mov ebp, eax
    MVID rsi, SD_COMBO, rbx, r14, rbp, r15
    mov eax, r15d
    shl eax, 1
    add eax, r14d
    mov edi, eax                     ; list top
    mov eax, r13d
    sub eax, edi
    sub eax, r15d
    sub eax, r14d
    sub eax, r14d
    mov ebp, eax                     ; list height
    mov ebx, r12d
    sub ebx, r14d
    sub ebx, r14d
    MVID rsi, SD_LIST, r14, rdi, rbx, rbp
    ; buttons
    mov eax, r13d
    sub eax, r15d
    sub eax, r14d
    mov edi, eax                     ; button y
    mov ecx, 120
    call scl
    mov ebp, eax                     ; button width
    mov eax, r12d
    sub eax, r14d
    sub eax, ebp
    mov ebx, eax                     ; cancel x
    MVID rsi, SD_CANCEL, rbx, rdi, rbp, r15
    mov eax, ebx
    sub eax, ebp
    sub eax, r14d
    mov ebx, eax
    MVID rsi, SD_OK, rbx, rdi, rbp, r15
    EPILOG 192

sd_proc:
    PROLOG 320
    mov rsi, rcx
    mov edi, edx
    mov r12, r8
    mov r13, r9
    cmp edi, WM_CREATE
    je .create
    cmp edi, WM_SIZE
    je .size
    cmp edi, WM_COMMAND
    je .command
    cmp edi, WM_NOTIFY
    je .notify
    cmp edi, WM_CLOSE
    je .close
    cmp edi, WM_ERASEBKGND
    je .erase
    cmp edi, WM_CTLCOLORSTATIC
    je .cstatic
.def:
    invoke DefWindowProcW, rsi, rdi, r12, r13
    EPILOG 320
.create:
    mov rax, [r13]
    mov r14, [rax]                   ; lpCreateParams = fold
    invoke SetWindowLongPtrW, rsi, GWLP_USERDATA, r14
    invoke mk_lbl, rsi, &s_empty, SD_SUM
    invoke mk, rsi, &cn_combo, 0, CBS_DROPDOWNLIST|WS_VSCROLL|WS_TABSTOP, SD_COMBO
    mov rbx, rax
    invoke SendMessageW, rbx, CB_ADDSTRING, 0, &s_sd_f0
    invoke SendMessageW, rbx, CB_ADDSTRING, 0, &s_sd_f1
    invoke SendMessageW, rbx, CB_ADDSTRING, 0, &s_sd_f2
    invoke SendMessageW, rbx, CB_ADDSTRING, 0, &s_sd_f3
    invoke SendMessageW, rbx, CB_SETCURSEL, 0, 0
    invoke mk, rsi, &cn_list, 0, LVS_REPORT|LVS_SHOWSELALWAYS|WS_TABSTOP|WS_BORDER, SD_LIST
    mov rbx, rax
    invoke SendMessageW, rbx, LVM_SETEXTENDEDLISTVIEWSTYLE, 0, LVS_EX_FULLROWSELECT|LVS_EX_DOUBLEBUFFER
    invoke lv_dark_header, rbx
    ; columns
    xor ebp, ebp
.col:
    cmp ebp, 3
    jae .cd
    invoke memset, &rsp+96, 0, 40
    mov dword [rsp+96], LVCF_FMT|LVCF_WIDTH|LVCF_TEXT
    lea rax, [h_sd_act]
    mov ecx, 190
    cmp ebp, 0
    je .ct
    lea rax, [h_sd_path]
    mov ecx, 470
    cmp ebp, 1
    je .ct
    lea rax, [h_sd_size]
    mov ecx, 110
    mov dword [rsp+100], 1           ; right aligned
.ct:
    mov [rsp+112], rax
    mov r15, rcx
    mov ecx, r15d
    call scl
    mov [rsp+104], eax
    invoke SendMessageW, rbx, LVM_INSERTCOLUMNW, rbp, &rsp+96
    inc ebp
    jmp .col
.cd:
    invoke GetDlgItem, rsi, SD_LIST
    invoke SendMessageW, rax, LVM_SETBKCOLOR, 0, #[th_bg]
    invoke GetDlgItem, rsi, SD_LIST
    invoke SendMessageW, rax, LVM_SETTEXTCOLOR, 0, #[th_fg]
    invoke GetDlgItem, rsi, SD_LIST
    invoke SendMessageW, rax, LVM_SETTEXTBKCOLOR, 0, #[th_bg]
    invoke mk_btn, rsi, &s_sd_ok, SD_OK
    invoke mk_btn, rsi, &s_sd_cancel, SD_CANCEL
    invoke sd_layout, rsi
    invoke sd_summary, rsi, r14
    invoke sd_fill, rsi, r14, 0
    xor eax, eax
    EPILOG 320
.size:
    invoke sd_layout, rsi
    jmp .zero
.command:
    movzx eax, r12w
    cmp eax, SD_OK
    je .ok
    cmp eax, SD_CANCEL
    je .close
    cmp eax, SD_COMBO
    jne .zero
    mov eax, r12d
    shr eax, 16
    cmp eax, CBN_SELCHANGE
    jne .zero
    invoke GetWindowLongPtrW, rsi, GWLP_USERDATA
    mov r14, rax
    invoke GetDlgItem, rsi, SD_COMBO
    invoke SendMessageW, rax, CB_GETCURSEL, 0, 0
    movsxd r8, eax
    invoke sd_fill, rsi, r14, r8
    jmp .zero
.ok:
    mov qword [g_sd_result], 1
    jmp .zero
.close:
    mov qword [g_sd_result], 0
    jmp .zero
.erase:
    invoke GetClientRect, rsi, &rsp+96
    invoke FillRect, r12, &rsp+96, [th_panelbrush]
    mov eax, 1
    EPILOG 320
.cstatic:
    invoke ctl_color, r12, 1
    EPILOG 320
.notify:
    cmp dword [r13+NMH_CODE], NM_CUSTOMDRAW
    jne .def
    mov eax, [r13+CD_STAGE]
    cmp eax, CDDS_PREPAINT
    jne .cd2
    mov eax, CDRF_NOTIFYITEMDRAW
    EPILOG 320
.cd2:
    cmp eax, CDDS_ITEMPREPAINT
    jne .zero
    mov rax, [r13+72]                ; item lParam = category
    mov edx, [th_bg]
    cmp eax, 3
    jne .c2
    mov edx, [th_diff]
.c2:
    cmp eax, 2
    jne .set
    mov edx, [th_type]
.set:
    mov [r13+CD_CLRTEXTBK], edx
    mov eax, [th_fg]
    mov [r13+CD_CLRTEXT], eax
.zero:
    xor eax, eax
    EPILOG 320

; sync_preview(owner, fold) -> eax 1 = run it
sync_preview:
    PROLOG 256
    mov rbx, rcx
    mov rsi, rdx
    cmp qword [g_sd_wc], 0
    jne .have
    invoke reg_class, &cn_sd, &sd_proc, [th_panelbrush]
    mov qword [g_sd_wc], 1
.have:
    invoke GetWindowRect, rbx, &rsp+96
    mov eax, [rsp+104]
    sub eax, [rsp+96]
    mov ecx, 900
    mov r12d, ecx
    sub eax, ecx
    sar eax, 1
    add eax, [rsp+96]
    mov r13d, eax                    ; x
    mov eax, [rsp+108]
    sub eax, [rsp+100]
    mov ecx, 620
    mov r14d, ecx
    sub eax, ecx
    sar eax, 1
    add eax, [rsp+100]
    mov r15d, eax                    ; y
    mov qword [g_sd_result], -1
    mov [rsp+192], rsi               ; lpParam block: pointer to fold
    mov ecx, 900
    call scl
    mov r12d, eax
    mov ecx, 620
    call scl
    mov r14d, eax
    invoke CreateWindowExW, 1, &cn_sd, &s_sd_title, WS_POPUP|WS_CAPTION|WS_SYSMENU|WS_THICKFRAME|WS_VISIBLE|WS_CLIPCHILDREN, r13, r15, r12, r14, rbx, 0, [g_hinst], &rsp+192
    mov rdi, rax
    test rax, rax
    jz .fail
    invoke EnableWindow, rbx, 0
.loop:
    cmp qword [g_sd_result], -1
    jne .done
    invoke GetMessageW, &rsp+96, 0, 0, 0
    test eax, eax
    jle .quit
    invoke TranslateMessage, &rsp+96
    invoke DispatchMessageW, &rsp+96
    jmp .loop
.quit:
    mov qword [g_sd_result], 0
    invoke PostQuitMessage, 0
.done:
    invoke EnableWindow, rbx, 1
    invoke DestroyWindow, rdi
    invoke SetFocus, rbx
    mov rax, [g_sd_result]
    EPILOG 256
.fail:
    xor eax, eax
    EPILOG 256

section .bss
alignb 8
g_sd_wc: resq 1
section .text

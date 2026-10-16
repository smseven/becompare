; shell.asm - IN-02 Explorer context menu integration (per-user registry verbs)
;   "BeCompare: 왼쪽으로 선택"  -> bcgui /shellleft "%1"    (remembers the path)
;   "BeCompare: 비교"           -> bcgui /shellcompare "%1" (compares with the remembered path)
%include "inc/macros.inc"
%include "inc/win.inc"

extern RegCreateKeyExW, RegSetValueExW, RegCloseKey, RegDeleteTreeW
extern GetCommandLineW, CommandLineToArgvW, LocalFree, GetModuleFileNameW
extern WritePrivateProfileStringW, GetPrivateProfileStringW
extern wcslen, wcscpy, wcscat, _wcsicmp, _snwprintf, wcsncpy
extern g_ini, ini_path_init, msgbox, s_appname

global shell_install, shell_early, shell_pending

section .rdata
WSTR k_star_l, "Software\Classes\*\shell\BeCompareAsmLeft"
WSTR k_star_c, "Software\Classes\*\shell\BeCompareAsmCompare"
WSTR k_dir_l, "Software\Classes\Directory\shell\BeCompareAsmLeft"
WSTR k_dir_c, "Software\Classes\Directory\shell\BeCompareAsmCompare"
WSTR s_cmd, "\command"
WSTR t_left, "BeCompare: 왼쪽으로 선택"
WSTR t_cmp, "BeCompare: 선택한 항목과 비교"
WSTR f_cmd_left, '"%s" /shellleft "%%1"'
WSTR f_cmd_cmp, '"%s" /shellcompare "%%1"'
WSTR sw_install, "/shellinstall"
WSTR sw_uninstall, "/shelluninstall"
WSTR sw_left, "/shellleft"
WSTR sec_shell, "Shell"
WSTR k_left, "Left"
WSTR s_empty, ""
WSTR s_on_done, "탐색기 오른쪽 클릭 메뉴에 등록했습니다 (현재 사용자)."
WSTR s_off_done, "탐색기 오른쪽 클릭 메뉴 등록을 해제했습니다."

section .text

; sh_put(key path, menu text, command) : create key (default = text) and key\command (default = command)
sh_put:
    PROLOG 1424
    mov rsi, rcx
    mov rdi, rdx
    mov r12, r8
    invoke RegCreateKeyExW, 0xFFFFFFFF80000001, rsi, 0, 0, 0, 0xF003F, 0, &rsp+96, 0
    test eax, eax
    jnz .d
    invoke wcslen, rdi
    lea r13d, [rax*2+2]
    invoke RegSetValueExW, [rsp+96], 0, 0, 1, rdi, r13
    invoke RegCloseKey, [rsp+96]
    invoke wcscpy, &rsp+200, rsi
    invoke wcscat, &rsp+200, &s_cmd
    invoke RegCreateKeyExW, 0xFFFFFFFF80000001, &rsp+200, 0, 0, 0, 0xF003F, 0, &rsp+96, 0
    test eax, eax
    jnz .d
    invoke wcslen, r12
    lea r13d, [rax*2+2]
    invoke RegSetValueExW, [rsp+96], 0, 0, 1, r12, r13
    invoke RegCloseKey, [rsp+96]
.d:
    EPILOG 1424

; shell_install(on 1 / 0)
shell_install:
    PROLOG 3440
    mov r12d, ecx
    test r12d, r12d
    jz .off
    invoke GetModuleFileNameW, 0, &rsp+96, 520
    invoke _snwprintf, &rsp+1200, 520, &f_cmd_left, &rsp+96
    invoke _snwprintf, &rsp+2304, 520, &f_cmd_cmp, &rsp+96
    invoke sh_put, &k_star_l, &t_left, &rsp+1200
    invoke sh_put, &k_dir_l, &t_left, &rsp+1200
    invoke sh_put, &k_star_c, &t_cmp, &rsp+2304
    invoke sh_put, &k_dir_c, &t_cmp, &rsp+2304
    EPILOG 3440
.off:
    invoke RegDeleteTreeW, 0xFFFFFFFF80000001, &k_star_l
    invoke RegDeleteTreeW, 0xFFFFFFFF80000001, &k_star_c
    invoke RegDeleteTreeW, 0xFFFFFFFF80000001, &k_dir_l
    invoke RegDeleteTreeW, 0xFFFFFFFF80000001, &k_dir_c
    EPILOG 3440

; shell_pending(out wchar[520]) -> eax 1 when a left path is remembered
shell_pending:
    PROLOG 64
    mov rbx, rcx
    invoke GetPrivateProfileStringW, &sec_shell, &k_left, &s_empty, rbx, 519, &g_ini
    xor eax, eax
    cmp word [rbx], 0
    je .d
    mov eax, 1
.d:
    EPILOG 64

; shell_early() -> eax 1 when the command line was a shell maintenance switch (nothing else to do)
shell_early:
    PROLOG 160
    invoke GetCommandLineW
    invoke CommandLineToArgvW, rax, &rsp+96
    test rax, rax
    jz .no
    mov rbx, rax
    cmp dword [rsp+96], 2
    jl .free
    invoke _wcsicmp, [rbx+8], &sw_install
    test eax, eax
    jnz .u
    mov ecx, 1
    call shell_install
    jmp .yes
.u:
    invoke _wcsicmp, [rbx+8], &sw_uninstall
    test eax, eax
    jnz .l
    xor ecx, ecx
    call shell_install
    jmp .yes
.l:
    invoke _wcsicmp, [rbx+8], &sw_left
    test eax, eax
    jnz .free
    cmp dword [rsp+96], 3
    jl .free
    call ini_path_init
    invoke WritePrivateProfileStringW, &sec_shell, &k_left, [rbx+16], &g_ini
.yes:
    invoke LocalFree, rbx
    mov eax, 1
    EPILOG 160
.free:
    invoke LocalFree, rbx
.no:
    xor eax, eax
    EPILOG 160

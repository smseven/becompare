; bc.asm - file/folder compare CLI in x64 NASM (Windows, Win64 ABI)
;
;   bc dir  [-c] [-a] A B   folder compare (recursive)   FC-01..03
;   bc text [-i] [-w] [-a] A B   line diff (LCS)         TC-01,02
;   bc hex  [-a] A B        byte diff                    HX-01
;   bc sync [-n] [-c] A B   mirror folder A into B       SY-01..04
;
; exit code: 0 identical, 1 differences, 2 error
;
; build: see build.ps1   (nasm -f win64, link with gcc for the C runtime)

default rel
bits 64

extern printf, snprintf, strcmp, memcmp, memcpy
extern fopen, fseek, ftell, fread, fclose, malloc, calloc, atoi, atof, strtod, fprintf
extern DeleteFileA, RemoveDirectoryA, SetFileAttributesA
extern FindFirstFileA, FindNextFileA, FindClose
extern GetFileAttributesExA, CopyFileA, CreateDirectoryA

global main

; WIN32_FIND_DATAA / WIN32_FILE_ATTRIBUTE_DATA offsets (shared prefix)
%define O_ATTR   0
%define O_MTIME  20
%define O_SZHI   28
%define O_SZLO   32
%define O_NAME   44

; walk() frame layout (locals start after 32 shadow + 2 stack-arg slots)
%define L_FD     64          ; WIN32_FIND_DATAA   320
%define L_ATTR   384         ; attr data           48
%define L_PA     432         ; path A             528
%define L_PB     960         ; path B             528
%define L_REL    1488        ; child relative     528
%define WALK_FRAME 2032

%define MAXPATH_BUF 520
%define MTIME_TOL   20000000 ; 2 seconds in 100ns units
%define LCS_LIMIT   30000000 ; max DP cells
%define HEX_LIMIT   256
%define MAXCOL      32

%macro LOWER 1
    cmp %1, 'A'
    jb %%s
    cmp %1, 'Z'
    ja %%s
    add %1, 32
%%s:
%endmacro

%macro PROLOG 1
    push rbx
    push rbp
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    sub rsp, %1+8
%endmacro

%macro EPILOG 1
    add rsp, %1+8
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbp
    pop rbx
    ret
%endmacro

; print "<status> <rel><name>" ; expects r12=rel, rbx=name
%macro ENTRY 1
    lea rcx, [fmt_ent]
    lea rdx, [%1]
    mov r8, r12
    mov r9, rbx
    call printf
    mov rcx, [outfp]
    test rcx, rcx
    jz %%n
    lea rdx, [%1]
    mov r8, r12
    mov r9, rbx
    call html_row
%%n:
%endmacro

section .rdata
fmt_ent:    db '%-7s %s%s', 10, 0
fmt_path:   db '%s\%s', 0
fmt_star:   db '%s\*', 0
fmt_rel:    db '%s%s\', 0
fmt_line:   db '%c %6llu: %s', 10, 0
fmt_hex:    db '%08llX: %02X %02X', 10, 0
fmt_sum:    db 10, '%s: same=%llu diff=%llu A-only=%llu B-only=%llu errors=%llu', 10, 0
fmt_tsum:   db 10, 'text: %llu removed(-), %llu added(+)', 10, 0
fmt_hsum:   db 10, 'hex: %llu differing byte(s)', 10, 0
fmt_hsize:  db 'size differs: A=%llu B=%llu bytes', 10, 0
fmt_hmore:  db '(first 256 shown; use -a for all)', 10, 0
fmt_cant:   db 'error: cannot read %s', 10, 0
fmt_nodir:  db 'error: not a usable folder: %s', 10, 0
fmt_badopt: db 'error: unknown option -%c', 10, 0
fmt_big:    db 'error: files too large/different for the LCS table', 10, 0
fmt_bak:    db '%s.bak', 0
fmt_cell:   db '~ A:%llu B:%llu col %llu: "%s" -> "%s"', 10, 0
fmt_row:    db '%c row %llu:', 0
fmt_fld:    db '%s%s', 0
fmt_tbsum:  db 10, 'table: %llu changed cell(s), %llu row(s) only in A(-), %llu only in B(+)', 10, 0
s_sp:       db ' ', 0
s_comma:    db ',', 0
s_nl:       db 10, 0
s_table:    db 'table', 0
fmt_hrow:   db '<tr class="%s"><td>%s</td><td>%s</td></tr>', 10, 0
fmt_hhead:  db '<!doctype html><html><head><meta charset="utf-8"><title>bc folder report</title><style>'
            db 'body{font-family:sans-serif}table{border-collapse:collapse}td,th{padding:2px 10px;border-bottom:1px solid #ddd;text-align:left}'
            db '.DIFF{background:#fdd}.A-only{background:#dfd}.B-only{background:#ddf}.TYPE,.FAILED{background:#fc8}.same{color:#888}'
            db '</style></head><body><h2>Folder compare</h2><p>A: %s<br>B: %s</p><table><tr><th>status</th><th>path</th></tr>', 10, 0
fmt_hfoot:  db '</table><p>same=%llu diff=%llu A-only=%llu B-only=%llu errors=%llu</p></body></html>', 10, 0
fmt_cantw:  db 'error: cannot write %s', 10, 0
e_amp:      db '&amp;', 0
e_lt:       db '&lt;', 0
e_gt:       db '&gt;', 0
e_quot:     db '&quot;', 0
s_w:        db 'w', 0
S_delete:   db 'delete', 0
fmt_dry:    db '(dry run: nothing will be changed)', 10, 0
s_usage:    db 'bc - compare tool (x64 NASM)', 10
            db 'usage: bc <command> [options] <A> <B>', 10
            db '  dir   recursive folder compare   -c compare content  -a show identical', 10
            db '  text  line diff of text files    -i ignore case  -w ignore whitespace  -a show identical', 10
            db '  hex   byte diff of binary files  -a list all differences', 10
            db '  table CSV compare                -k N match rows by key column N  -t X numeric tolerance', 10
            db '  sync  mirror folder A into B     -n dry run  -c compare content  -b keep .bak of overwritten files', 10
            db 'dir/sync: -x PATTERN excludes names (* and ?, repeatable up to 8)  -o FILE.html writes an HTML report', 10
            db 'sync -d deletes items that exist only in B (with -b, *.bak files are kept; use -n first!)', 10
            db 'exit code: 0 identical, 1 differences, 2 error', 10, 0
s_dir:      db 'dir', 0
s_text:     db 'text', 0
s_hex:      db 'hex', 0
s_sync:     db 'sync', 0
s_rb:       db 'rb', 0
s_empty:    db 0
s_lcmp:     db 'compare', 0
s_lsync:    db 'sync', 0
S_aonly:    db 'A-only', 0
S_bonly:    db 'B-only', 0
S_diff:     db 'DIFF', 0
S_same:     db 'same', 0
S_type:     db 'TYPE', 0
S_link:     db 'LINK', 0
S_copy:     db 'copy', 0
S_update:   db 'update', 0
S_mkdir:    db 'mkdir', 0
S_fail:     db 'FAILED', 0

section .bss
alignb 8
f_c:        resb 1
f_a:        resb 1
f_i:        resb 1
f_w:        resb 1
f_n:        resb 1
mode:       resb 1          ; 0 compare, 1 sync
f_b:        resb 1
f_t:        resb 1
f_d:        resb 1
alignb 8
tolv:       resq 1
outpath:    resq 1
outfp:      resq 1
hbuf:       resb 8192
hbuf2:      resb 1100
keycol:     resq 1
xcount:     resq 1
xpat:       resq 8
tbA:        resq 3          ; fields*, counts*, n
tbB:        resq 3
cnt_same:   resq 1
cnt_diff:   resq 1
cnt_a:      resq 1
cnt_b:      resq 1
cnt_err:    resq 1
fsA:        resq 4          ; lines*, keys*, n, buf
fsB:        resq 4
cmpbufA:    resb 65536
cmpbufB:    resb 65536

section .text

; ---------------------------------------------------------------- helpers

; eax = 1 if rcx is "." or ".."
is_dots:
    cmp byte [rcx], '.'
    jne .no
    mov al, [rcx+1]
    test al, al
    je .yes
    cmp al, '.'
    jne .no
    cmp byte [rcx+2], 0
    jne .no
.yes:
    mov eax, 1
    ret
.no:
    xor eax, eax
    ret

; eax = 1 if path rcx exists and is a directory
isdir:
    PROLOG 112
    xor edx, edx
    lea r8, [rsp+48]
    call GetFileAttributesExA
    test eax, eax
    jz .no
    mov eax, [rsp+48]
    shr eax, 4
    and eax, 1
    EPILOG 112
.no:
    xor eax, eax
    EPILOG 112

; eax: 0 identical, 1 differ, 2 error     (rcx=pathA, rdx=pathB)
contentcmp:
    PROLOG 64
    mov r14, rdx
    lea rdx, [s_rb]
    call fopen
    test rax, rax
    jz .err
    mov rsi, rax
    mov rcx, r14
    lea rdx, [s_rb]
    call fopen
    test rax, rax
    jz .err1
    mov rdi, rax
    xor r12d, r12d
.rd:
    lea rcx, [cmpbufA]
    mov edx, 1
    mov r8d, 65536
    mov r9, rsi
    call fread
    mov r13, rax
    lea rcx, [cmpbufB]
    mov edx, 1
    mov r8d, 65536
    mov r9, rdi
    call fread
    cmp rax, r13
    jne .differ
    test r13, r13
    jz .done
    lea rcx, [cmpbufA]
    lea rdx, [cmpbufB]
    mov r8, r13
    call memcmp
    test eax, eax
    jnz .differ
    jmp .rd
.differ:
    mov r12d, 1
.done:
    mov rcx, rsi
    call fclose
    mov rcx, rdi
    call fclose
    mov eax, r12d
    EPILOG 64
.err1:
    mov rcx, rsi
    call fclose
.err:
    mov eax, 2
    EPILOG 64

; eax: 0 same, 1 differ, 2 error
; rcx=&findData(A) rdx=&attrData(B) r8=pathA r9=pathB
filesdiffer:
    PROLOG 64
    mov rsi, r8
    mov rdi, r9
    mov eax, [rcx+O_SZHI]
    cmp eax, [rdx+O_SZHI]
    jne .diff
    mov eax, [rcx+O_SZLO]
    cmp eax, [rdx+O_SZLO]
    jne .diff
    cmp byte [f_c], 0
    jne .content
    mov rax, [rcx+O_MTIME]
    sub rax, [rdx+O_MTIME]
    jns .abs
    neg rax
.abs:
    mov r8, MTIME_TOL
    cmp rax, r8
    ja .diff
    xor eax, eax
    EPILOG 64
.content:
    mov rcx, rsi
    mov rdx, rdi
    call contentcmp
    EPILOG 64
.diff:
    mov eax, 1
    EPILOG 64

; ---------------------------------------------------------------- folder walk
; walk(rcx=pathA, rdx=pathB, r8=rel prefix with trailing '\' or "")
walk:
    PROLOG WALK_FRAME
    mov rsi, rcx
    mov rdi, rdx
    mov r12, r8
    lea rbx, [rsp+L_FD+O_NAME]

    ; ---- pass 1: every entry of A
    lea rcx, [rsp+L_PA]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_star]
    mov r9, rsi
    call snprintf
    lea rcx, [rsp+L_PA]
    lea rdx, [rsp+L_FD]
    call FindFirstFileA
    cmp rax, -1
    je .pass2
    mov r13, rax
.loop1:
    mov rcx, rbx
    call is_dots
    test eax, eax
    jnz .next1
    mov rcx, rbx
    call excluded
    test eax, eax
    jnz .next1

    lea rcx, [rsp+L_PA]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_path]
    mov r9, rsi
    mov [rsp+32], rbx
    call snprintf
    lea rcx, [rsp+L_PB]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_path]
    mov r9, rdi
    mov [rsp+32], rbx
    call snprintf

    mov r14d, [rsp+L_FD+O_ATTR]
    shr r14d, 4
    and r14d, 1                     ; r14d = A is dir
    test r14d, r14d
    jz .nolink
    test dword [rsp+L_FD+O_ATTR], 0x400
    jnz .link
.nolink:
    lea rcx, [rsp+L_PB]
    xor edx, edx
    lea r8, [rsp+L_ATTR]
    call GetFileAttributesExA
    test eax, eax
    jz .aonly
    mov r15d, [rsp+L_ATTR+O_ATTR]
    shr r15d, 4
    and r15d, 1                     ; r15d = B is dir
    cmp r14d, r15d
    jne .type
    test r14d, r14d
    jnz .bothdirs

    lea rcx, [rsp+L_FD]
    lea rdx, [rsp+L_ATTR]
    lea r8, [rsp+L_PA]
    lea r9, [rsp+L_PB]
    call filesdiffer
    cmp eax, 2
    je .copyfail
    test eax, eax
    jnz .differs
    inc qword [cnt_same]
    cmp byte [f_a], 0
    je .next1
    ENTRY S_same
    jmp .next1
.differs:
    inc qword [cnt_diff]
    cmp byte [mode], 0
    jne .sync_upd
    ENTRY S_diff
    jmp .next1
.sync_upd:
    ENTRY S_update
    cmp byte [f_n], 0
    jne .next1
    cmp byte [f_b], 0
    je .do_copy
    lea rcx, [rsp+L_REL]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_bak]
    lea r9, [rsp+L_PB]
    call snprintf
    lea rcx, [rsp+L_PB]
    lea rdx, [rsp+L_REL]
    xor r8d, r8d
    call CopyFileA
    test eax, eax
    jz .copyfail
    jmp .do_copy

.bothdirs:
    test dword [rsp+L_ATTR+O_ATTR], 0x400
    jnz .link
    jmp .recurse

.aonly:
    inc qword [cnt_a]
    cmp byte [mode], 0
    jne .sync_new
    ENTRY S_aonly
    jmp .next1
.sync_new:
    test r14d, r14d
    jnz .sync_mkdir
    ENTRY S_copy
    jmp .do_copy
.sync_mkdir:
    ENTRY S_mkdir
    cmp byte [f_n], 0
    jne .next1
    lea rcx, [rsp+L_PB]
    xor edx, edx
    call CreateDirectoryA
    test eax, eax
    jz .copyfail
    jmp .recurse

.do_copy:
    cmp byte [f_n], 0
    jne .next1
    lea rcx, [rsp+L_PA]
    lea rdx, [rsp+L_PB]
    xor r8d, r8d
    call CopyFileA
    test eax, eax
    jnz .next1
.copyfail:
    inc qword [cnt_err]
    ENTRY S_fail
    jmp .next1

.type:
    inc qword [cnt_diff]
    ENTRY S_type
    jmp .next1
.link:
    ENTRY S_link
    jmp .next1

.recurse:
    lea rcx, [rsp+L_REL]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_rel]
    mov r9, r12
    mov [rsp+32], rbx
    call snprintf
    lea rcx, [rsp+L_PA]
    lea rdx, [rsp+L_PB]
    lea r8, [rsp+L_REL]
    call walk

.next1:
    mov rcx, r13
    lea rdx, [rsp+L_FD]
    call FindNextFileA
    test eax, eax
    jnz .loop1
    mov rcx, r13
    call FindClose

    ; ---- pass 2: entries that exist only in B
.pass2:
    lea rcx, [rsp+L_PA]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_star]
    mov r9, rdi
    call snprintf
    lea rcx, [rsp+L_PA]
    lea rdx, [rsp+L_FD]
    call FindFirstFileA
    cmp rax, -1
    je .out
    mov r13, rax
.loop2:
    mov rcx, rbx
    call is_dots
    test eax, eax
    jnz .next2
    mov rcx, rbx
    call excluded
    test eax, eax
    jnz .next2
    lea rcx, [rsp+L_PA]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_path]
    mov r9, rsi
    mov [rsp+32], rbx
    call snprintf
    lea rcx, [rsp+L_PA]
    xor edx, edx
    lea r8, [rsp+L_ATTR]
    call GetFileAttributesExA
    test eax, eax
    jnz .next2
    inc qword [cnt_b]
    cmp byte [mode], 1
    jne .bo_report
    cmp byte [f_d], 0
    je .bo_report
    cmp byte [f_b], 0
    je .bo_del
    mov rcx, rbx
    call endsbak
    test eax, eax
    jnz .bo_report
.bo_del:
    ENTRY S_delete
    cmp byte [f_n], 0
    jne .next2
    lea rcx, [rsp+L_PB]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_path]
    mov r9, rdi
    mov [rsp+32], rbx
    call snprintf
    lea rcx, [rsp+L_PB]
    xor edx, edx
    lea r8, [rsp+L_ATTR]
    call GetFileAttributesExA
    test eax, eax
    jz .next2
    lea rcx, [rsp+L_PB]
    mov eax, [rsp+L_ATTR+O_ATTR]
    test eax, 0x10
    jz .delfile
    test eax, 0x400
    jnz .dellink
    call rmtree
    jmp .delres
.dellink:
    call RemoveDirectoryA
    jmp .delres
.delfile:
    mov edx, 0x80
    call SetFileAttributesA
    lea rcx, [rsp+L_PB]
    call DeleteFileA
.delres:
    test eax, eax
    jnz .next2
    inc qword [cnt_err]
    ENTRY S_fail
    jmp .next2
.bo_report:
    ENTRY S_bonly
.next2:
    mov rcx, r13
    lea rdx, [rsp+L_FD]
    call FindNextFileA
    test eax, eax
    jnz .loop2
    mov rcx, r13
    call FindClose
.out:
    EPILOG WALK_FRAME

; cmd_dir(rcx=A, rdx=B) -> eax exit code. uses [mode]
cmd_dir:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
    mov rcx, rsi
    call isdir
    test eax, eax
    jz .bad_a
    mov rcx, rdi
    call isdir
    test eax, eax
    jnz .ok
    cmp byte [mode], 1
    jne .bad_b
    cmp byte [f_n], 0
    jne .ok
    mov rcx, rdi
    xor edx, edx
    call CreateDirectoryA
    test eax, eax
    jz .bad_b
.ok:
    cmp byte [mode], 1
    jne .go
    cmp byte [f_n], 0
    je .go
    lea rcx, [fmt_dry]
    call printf
.go:
    cmp qword [outpath], 0
    je .walkit
    mov rcx, [outpath]
    lea rdx, [s_w]
    call fopen
    mov [outfp], rax
    test rax, rax
    jnz .hdr
    lea rcx, [fmt_cantw]
    mov rdx, [outpath]
    call printf
    jmp .walkit
.hdr:
    lea rcx, [hbuf]
    mov rdx, rsi
    call html_esc
    lea rcx, [hbuf+4096]
    mov rdx, rdi
    call html_esc
    mov rcx, [outfp]
    lea rdx, [fmt_hhead]
    lea r8, [hbuf]
    lea r9, [hbuf+4096]
    call fprintf
.walkit:
    mov rcx, rsi
    mov rdx, rdi
    lea r8, [s_empty]
    call walk
    mov rcx, [outfp]
    test rcx, rcx
    jz .nofoot
    lea rdx, [fmt_hfoot]
    mov r8, [cnt_same]
    mov r9, [cnt_diff]
    mov rax, [cnt_a]
    mov [rsp+32], rax
    mov rax, [cnt_b]
    mov [rsp+40], rax
    mov rax, [cnt_err]
    mov [rsp+48], rax
    call fprintf
    mov rcx, [outfp]
    call fclose
.nofoot:

    lea rcx, [fmt_sum]
    lea rdx, [s_lcmp]
    cmp byte [mode], 1
    jne .lbl
    lea rdx, [s_lsync]
.lbl:
    mov r8, [cnt_same]
    mov r9, [cnt_diff]
    mov rax, [cnt_a]
    mov [rsp+32], rax
    mov rax, [cnt_b]
    mov [rsp+40], rax
    mov rax, [cnt_err]
    mov [rsp+48], rax
    call printf

    cmp qword [cnt_err], 0
    jne .e2
    mov rax, [cnt_diff]
    or rax, [cnt_a]
    or rax, [cnt_b]
    jnz .e1
    xor eax, eax
    EPILOG 64
.e1:
    mov eax, 1
    EPILOG 64
.e2:
    mov eax, 2
    EPILOG 64
.bad_a:
    mov rdx, rsi
    jmp .bad
.bad_b:
    mov rdx, rdi
.bad:
    lea rcx, [fmt_nodir]
    call printf
    mov eax, 2
    EPILOG 64

; ---------------------------------------------------------------- file I/O

; readfile(rcx=path) -> rax=buffer (NUL terminated, 0 on failure), rdx=size
readfile:
    PROLOG 64
    lea rdx, [s_rb]
    call fopen
    test rax, rax
    jz .fail
    mov rsi, rax
    mov rcx, rsi
    xor edx, edx
    mov r8d, 2                      ; SEEK_END
    call fseek
    mov rcx, rsi
    call ftell
    movsxd r12, eax
    test r12, r12
    js .failclose
    mov rcx, rsi
    xor edx, edx
    xor r8d, r8d
    call fseek
    lea rcx, [r12+1]
    call malloc
    test rax, rax
    jz .failclose
    mov rdi, rax
    mov rcx, rdi
    mov edx, 1
    mov r8, r12
    mov r9, rsi
    call fread
    mov r13, rax
    mov byte [rdi+r13], 0
    mov rcx, rsi
    call fclose
    mov rax, rdi
    mov rdx, r13
    EPILOG 64
.failclose:
    mov rcx, rsi
    call fclose
.fail:
    xor eax, eax
    xor edx, edx
    EPILOG 64

; ---------------------------------------------------------------- text compare

; normkey(rcx=line): apply -i / -w in place
normkey:
    mov r8, rcx
    mov r9, rcx
.l:
    mov al, [r9]
    inc r9
    test al, al
    jz .end
    cmp byte [f_w], 0
    je .nw
    cmp al, ' '
    je .l
    cmp al, 9
    je .l
.nw:
    cmp byte [f_i], 0
    je .store
    cmp al, 'A'
    jb .store
    cmp al, 'Z'
    ja .store
    add al, 32
.store:
    mov [r8], al
    inc r8
    jmp .l
.end:
    mov [r8], al
    ret

; load_lines(rcx=path, rdx=fs*) -> eax 1 ok / 0 fail (prints error)
; fs: [0]=lines* [8]=keys* [16]=n [24]=buf
load_lines:
    PROLOG 64
    mov [rsp+40], rcx
    mov r12, rdx
    call readfile
    test rax, rax
    jz .fail
    mov rsi, rax
    mov r13, rdx
    mov [r12+24], rax

    ; upper bound of line count = newlines + 1
    mov rdi, rsi
    lea r8, [rsi+r13]
    mov r14d, 1
.cnt:
    cmp rdi, r8
    jae .cdone
    cmp byte [rdi], 10
    jne .cn
    inc r14
.cn:
    inc rdi
    jmp .cnt
.cdone:
    lea rcx, [r14*8+8]
    call malloc
    test rax, rax
    jz .fail
    mov [r12], rax

    ; split in place on LF, strip CR
    mov rdi, rsi
    lea r8, [rsi+r13]
    mov r9, rax
    xor ebx, ebx
.sp:
    cmp rdi, r8
    jae .spdone
    mov [r9+rbx*8], rdi
    inc rbx
.fnd:
    cmp rdi, r8
    jae .spdone
    cmp byte [rdi], 10
    je .eol
    inc rdi
    jmp .fnd
.eol:
    mov byte [rdi], 0
    mov rax, [r9+rbx*8-8]
    cmp rdi, rax
    je .eolnext
    cmp byte [rdi-1], 13
    jne .eolnext
    mov byte [rdi-1], 0
.eolnext:
    inc rdi
    jmp .sp
.spdone:
    mov [r12+16], rbx
    mov r14, rbx

    cmp byte [f_i], 0
    jne .need
    cmp byte [f_w], 0
    jne .need
    mov rax, [r12]
    mov [r12+8], rax
    mov eax, 1
    EPILOG 64
.need:
    lea rcx, [r14*8+8]
    call malloc
    test rax, rax
    jz .fail
    mov r15, rax                    ; keys array
    lea rcx, [r13+1]
    call malloc
    test rax, rax
    jz .fail
    mov rbp, rax                    ; key text copy
    mov rcx, rbp
    mov rdx, rsi
    lea r8, [r13+1]
    call memcpy
    mov [r12+8], r15
    xor ebx, ebx
.kl:
    cmp rbx, r14
    jae .kdone
    mov rax, [r12]
    mov rax, [rax+rbx*8]
    sub rax, rsi
    add rax, rbp
    mov [r15+rbx*8], rax
    mov rcx, rax
    call normkey
    inc rbx
    jmp .kl
.kdone:
    mov eax, 1
    EPILOG 64
.fail:
    lea rcx, [fmt_cant]
    mov rdx, [rsp+40]
    call printf
    xor eax, eax
    EPILOG 64

; show(ecx=tag char, rdx=line number, r8=text)
show:
    PROLOG 64
    mov r9, r8
    mov r8, rdx
    mov rdx, rcx
    lea rcx, [fmt_line]
    call printf
    EPILOG 64

; show_common(rcx=first index, rdx=count): print lines of A as unchanged
show_common:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
.l:
    test rdi, rdi
    jz .d
    mov rax, [fsA]
    mov r8, [rax+rsi*8]
    lea rdx, [rsi+1]
    mov ecx, ' '
    call show
    inc rsi
    dec rdi
    jmp .l
.d:
    EPILOG 64

; cmd_text(rcx=A, rdx=B) -> eax exit code
; frame: 64 p, 72 s, 80 n1, 88 m1, 96 L*, 104 W, 112 removed, 120 added
cmd_text:
    PROLOG 128
    mov r14, rcx
    mov r15, rdx
    mov rcx, r14
    lea rdx, [fsA]
    call load_lines
    test eax, eax
    jz .err
    mov rcx, r15
    lea rdx, [fsB]
    call load_lines
    test eax, eax
    jz .err
    mov rsi, [fsA+8]
    mov rdi, [fsB+8]
    mov r12, [fsA+16]
    mov r13, [fsB+16]

    ; common prefix
    xor ebx, ebx
.pre:
    cmp rbx, r12
    jae .predone
    cmp rbx, r13
    jae .predone
    mov rcx, [rsi+rbx*8]
    mov rdx, [rdi+rbx*8]
    call strcmp
    test eax, eax
    jnz .predone
    inc rbx
    jmp .pre
.predone:
    mov [rsp+64], rbx
    mov rax, r12
    sub rax, rbx
    mov [rsp+80], rax
    mov rax, r13
    sub rax, rbx
    mov [rsp+88], rax

    ; common suffix (not overlapping the prefix)
    xor ebp, ebp
.suf:
    cmp rbp, [rsp+80]
    jae .sufdone
    cmp rbp, [rsp+88]
    jae .sufdone
    mov rax, r12
    sub rax, rbp
    dec rax
    mov rcx, [rsi+rax*8]
    mov rax, r13
    sub rax, rbp
    dec rax
    mov rdx, [rdi+rax*8]
    call strcmp
    test eax, eax
    jnz .sufdone
    inc rbp
    jmp .suf
.sufdone:
    mov [rsp+72], rbp
    mov rax, [rsp+80]
    sub rax, rbp
    mov [rsp+80], rax
    mov rax, [rsp+88]
    sub rax, rbp
    mov [rsp+88], rax
    mov qword [rsp+112], 0
    mov qword [rsp+120], 0

    cmp byte [f_a], 0
    je .noprefix
    xor ecx, ecx
    mov rdx, [rsp+64]
    call show_common
.noprefix:
    ; DP table over the middle part
    mov rax, [rsp+80]
    inc rax
    mov rcx, [rsp+88]
    inc rcx
    mov [rsp+104], rcx
    mul rcx
    test rdx, rdx
    jnz .big
    cmp rax, LCS_LIMIT
    ja .big
    lea rcx, [rax*4]
    call malloc
    test rax, rax
    jz .big
    mov [rsp+96], rax
    mov r14, rax
    mov rbx, [rsp+64]
    lea rsi, [rsi+rbx*8]            ; keys A shifted by prefix
    lea rdi, [rdi+rbx*8]
    mov rbp, [rsp+104]
    mov r12, [rsp+80]               ; i
.irow:
    mov r13, [rsp+88]               ; j
.jcol:
    mov rax, r12
    imul rax, rbp
    add rax, r13
    cmp r12, [rsp+80]
    je .zero
    cmp r13, [rsp+88]
    je .zero
    mov rcx, [rsi+r12*8]
    mov rdx, [rdi+r13*8]
    call strcmp
    mov rcx, r12
    imul rcx, rbp
    add rcx, r13
    test eax, eax
    jnz .neq
    lea rdx, [rcx+rbp+1]
    mov eax, [r14+rdx*4]
    inc eax
    mov [r14+rcx*4], eax
    jmp .jnext
.neq:
    lea rdx, [rcx+rbp]
    mov eax, [r14+rdx*4]
    mov r8d, [r14+rcx*4+4]
    cmp eax, r8d
    jae .mx
    mov eax, r8d
.mx:
    mov [r14+rcx*4], eax
    jmp .jnext
.zero:
    mov dword [r14+rax*4], 0
.jnext:
    test r13, r13
    jz .rowdone
    dec r13
    jmp .jcol
.rowdone:
    test r12, r12
    jz .dpdone
    dec r12
    jmp .irow
.dpdone:

    ; walk the table forward emitting the edit script
    xor r12d, r12d
    xor r13d, r13d
.walk:
    cmp r12, [rsp+80]
    jb .ihas
    cmp r13, [rsp+88]
    jae .walkdone
    jmp .plus
.ihas:
    cmp r13, [rsp+88]
    jae .minus
    mov rcx, [rsi+r12*8]
    mov rdx, [rdi+r13*8]
    call strcmp
    test eax, eax
    jnz .differ
    cmp byte [f_a], 0
    je .cskip
    mov rax, [rsp+64]
    add rax, r12
    lea rdx, [rax+1]
    mov rcx, [fsA]
    mov r8, [rcx+rax*8]
    mov ecx, ' '
    call show
.cskip:
    inc r12
    inc r13
    jmp .walk
.differ:
    mov rax, r12
    inc rax
    imul rax, rbp
    add rax, r13
    mov ecx, [r14+rax*4]            ; L[i+1][j]
    mov rax, r12
    imul rax, rbp
    add rax, r13
    inc rax
    mov edx, [r14+rax*4]            ; L[i][j+1]
    cmp ecx, edx
    jb .plus
.minus:
    mov rax, [rsp+64]
    add rax, r12
    lea rdx, [rax+1]
    mov rcx, [fsA]
    mov r8, [rcx+rax*8]
    mov ecx, '-'
    call show
    inc qword [rsp+112]
    inc r12
    jmp .walk
.plus:
    mov rax, [rsp+64]
    add rax, r13
    lea rdx, [rax+1]
    mov rcx, [fsB]
    mov r8, [rcx+rax*8]
    mov ecx, '+'
    call show
    inc qword [rsp+120]
    inc r13
    jmp .walk
.walkdone:
    cmp byte [f_a], 0
    je .nosuffix
    mov rcx, [fsA+16]
    sub rcx, [rsp+72]
    mov rdx, [rsp+72]
    call show_common
.nosuffix:
    lea rcx, [fmt_tsum]
    mov rdx, [rsp+112]
    mov r8, [rsp+120]
    call printf
    mov rax, [rsp+112]
    or rax, [rsp+120]
    jnz .e1
    xor eax, eax
    EPILOG 128
.e1:
    mov eax, 1
    EPILOG 128
.big:
    lea rcx, [fmt_big]
    call printf
.err:
    mov eax, 2
    EPILOG 128

; ---------------------------------------------------------------- hex compare

; cmd_hex(rcx=A, rdx=B) -> eax exit code
cmd_hex:
    PROLOG 64
    mov r14, rcx
    mov r15, rdx
    mov rcx, r14
    call readfile
    test rax, rax
    jz .errA
    mov rsi, rax
    mov r12, rdx
    mov rcx, r15
    call readfile
    test rax, rax
    jz .errB
    mov rdi, rax
    mov r13, rdx

    mov r14, r12
    cmp r14, r13
    jbe .minok
    mov r14, r13
.minok:
    xor ebx, ebx
    xor ebp, ebp
.l:
    cmp rbx, r14
    jae .done
    movzx eax, byte [rsi+rbx]
    movzx edx, byte [rdi+rbx]
    cmp eax, edx
    je .nx
    inc rbp
    cmp rbp, HEX_LIMIT
    jbe .pr
    cmp byte [f_a], 0
    je .nx
.pr:
    mov r9d, edx
    mov r8d, eax
    mov rdx, rbx
    lea rcx, [fmt_hex]
    call printf
.nx:
    inc rbx
    jmp .l
.done:
    cmp r12, r13
    je .samesize
    lea rcx, [fmt_hsize]
    mov rdx, r12
    mov r8, r13
    call printf
.samesize:
    cmp rbp, HEX_LIMIT
    jbe .sum
    cmp byte [f_a], 0
    jne .sum
    lea rcx, [fmt_hmore]
    call printf
.sum:
    lea rcx, [fmt_hsum]
    mov rdx, rbp
    call printf
    cmp r12, r13
    jne .e1
    test rbp, rbp
    jnz .e1
    xor eax, eax
    EPILOG 64
.e1:
    mov eax, 1
    EPILOG 64
.errB:
    mov rdx, r15
    jmp .err
.errA:
    mov rdx, r14
.err:
    lea rcx, [fmt_cant]
    call printf
    mov eax, 2
    EPILOG 64

; ---------------------------------------------------------------- html / numeric / delete helpers

; html_esc(rcx=dst, rdx=src): copy with & < > " escaped
html_esc:
.l:
    mov al, [rdx]
    inc rdx
    test al, al
    jz .end
    cmp al, '&'
    jne .c1
    lea r8, [e_amp]
    jmp .cp
.c1:
    cmp al, '<'
    jne .c2
    lea r8, [e_lt]
    jmp .cp
.c2:
    cmp al, '>'
    jne .c3
    lea r8, [e_gt]
    jmp .cp
.c3:
    cmp al, '"'
    jne .st
    lea r8, [e_quot]
    jmp .cp
.st:
    mov [rcx], al
    inc rcx
    jmp .l
.cp:
    mov r9b, [r8]
    test r9b, r9b
    jz .l
    mov [rcx], r9b
    inc rcx
    inc r8
    jmp .cp
.end:
    mov byte [rcx], 0
    ret

; html_row(rcx=FILE*, rdx=status, r8=rel, r9=name)
html_row:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
    mov r12, r8
    mov r13, r9
    lea rcx, [hbuf2]
    mov edx, 1100
    lea r8, [fmt_fld]
    mov r9, r12
    mov [rsp+32], r13
    call snprintf
    lea rcx, [hbuf]
    lea rdx, [hbuf2]
    call html_esc
    mov rcx, rsi
    lea rdx, [fmt_hrow]
    mov r8, rdi
    mov r9, rdi
    lea rax, [hbuf]
    mov [rsp+32], rax
    call fprintf
    EPILOG 64

; eax = 1 if name rcx ends in ".bak"
endsbak:
    mov rax, rcx
.len:
    cmp byte [rax], 0
    je .e
    inc rax
    jmp .len
.e:
    sub rax, rcx
    cmp rax, 4
    jb .no
    lea rdx, [rcx+rax-4]
    cmp byte [rdx], '.'
    jne .no
    mov r8b, [rdx+1]
    or r8b, 0x20
    cmp r8b, 'b'
    jne .no
    mov r8b, [rdx+2]
    or r8b, 0x20
    cmp r8b, 'a'
    jne .no
    mov r8b, [rdx+3]
    or r8b, 0x20
    cmp r8b, 'k'
    jne .no
    mov eax, 1
    ret
.no:
    xor eax, eax
    ret

; eax = 1 if both strings are fully numeric and |a-b| <= tolerance
numeq:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
    mov rcx, rsi
    lea rdx, [rsp+32]
    call strtod
    movsd [rsp+48], xmm0
    mov rax, [rsp+32]
    cmp rax, rsi
    je .no
    cmp byte [rax], 0
    jne .no
    mov rcx, rdi
    lea rdx, [rsp+40]
    call strtod
    mov rax, [rsp+40]
    cmp rax, rdi
    je .no
    cmp byte [rax], 0
    jne .no
    movsd xmm1, [rsp+48]
    subsd xmm1, xmm0
    movq rax, xmm1
    btr rax, 63
    movq xmm1, rax
    ucomisd xmm1, [tolv]
    jp .no
    ja .no
    mov eax, 1
    EPILOG 64
.no:
    xor eax, eax
    EPILOG 64

; rmtree(rcx=dir) -> eax 1 if everything was removed (links are not followed)
rmtree:
    PROLOG 928
    mov rsi, rcx
    mov r15d, 1
    lea rcx, [rsp+384]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_star]
    mov r9, rsi
    call snprintf
    lea rcx, [rsp+384]
    lea rdx, [rsp+64]
    call FindFirstFileA
    cmp rax, -1
    je .rmdir
    mov r13, rax
    lea rbx, [rsp+64+O_NAME]
.l:
    mov rcx, rbx
    call is_dots
    test eax, eax
    jnz .nx
    lea rcx, [rsp+384]
    mov edx, MAXPATH_BUF
    lea r8, [fmt_path]
    mov r9, rsi
    mov [rsp+32], rbx
    call snprintf
    mov eax, [rsp+64]
    test eax, 0x10
    jz .file
    test eax, 0x400
    jnz .linkdir
    lea rcx, [rsp+384]
    call rmtree
    jmp .chk
.linkdir:
    lea rcx, [rsp+384]
    call RemoveDirectoryA
    jmp .chk
.file:
    lea rcx, [rsp+384]
    mov edx, 0x80
    call SetFileAttributesA
    lea rcx, [rsp+384]
    call DeleteFileA
.chk:
    test eax, eax
    jnz .nx
    xor r15d, r15d
.nx:
    mov rcx, r13
    lea rdx, [rsp+64]
    call FindNextFileA
    test eax, eax
    jnz .l
    mov rcx, r13
    call FindClose
.rmdir:
    mov rcx, rsi
    call RemoveDirectoryA
    test eax, eax
    jnz .done
    xor r15d, r15d
.done:
    mov eax, r15d
    EPILOG 928

; ---------------------------------------------------------------- exclude filter

; eax = 1 if string rdx matches wildcard pattern rcx (* and ?, case-insensitive)
wild:
    xor r8d, r8d
    xor r9d, r9d
.loop:
    mov al, [rdx]
    mov r10b, [rcx]
    cmp r10b, '*'
    jne .ns
    inc rcx
    cmp byte [rcx], 0
    je .yes
    mov r8, rcx
    mov r9, rdx
    jmp .loop
.ns:
    test al, al
    jz .strend
    cmp r10b, '?'
    je .adv
    LOWER al
    LOWER r10b
    cmp al, r10b
    jne .mis
.adv:
    inc rcx
    inc rdx
    jmp .loop
.mis:
    test r8, r8
    jz .no
    cmp byte [r9], 0
    je .no
    inc r9
    mov rdx, r9
    mov rcx, r8
    jmp .loop
.strend:
    cmp byte [rcx], '*'
    jne .chk
    inc rcx
    jmp .strend
.chk:
    cmp byte [rcx], 0
    jne .no
.yes:
    mov eax, 1
    ret
.no:
    xor eax, eax
    ret

; eax = 1 if name rcx matches any -x pattern
excluded:
    PROLOG 64
    mov rsi, rcx
    xor ebx, ebx
.l:
    cmp rbx, [xcount]
    jae .no
    lea rax, [xpat]
    mov rcx, [rax+rbx*8]
    mov rdx, rsi
    call wild
    test eax, eax
    jnz .yes
    inc rbx
    jmp .l
.no:
    xor eax, eax
    EPILOG 64
.yes:
    mov eax, 1
    EPILOG 64

; ---------------------------------------------------------------- table (CSV) compare

; split_row(rcx=line (modified in place), rdx=out ptr array) -> eax = field count (<= MAXCOL)
split_row:
    xor eax, eax
    mov r8, rcx
    mov r9, rcx
.field:
    cmp eax, MAXCOL
    jae .cap
    mov [rdx+rax*8], r9
    inc eax
    cmp byte [r8], '"'
    jne .plain
    inc r8
.q:
    mov r10b, [r8]
    test r10b, r10b
    jz .eol
    inc r8
    cmp r10b, '"'
    jne .qstore
    cmp byte [r8], '"'
    jne .junk
    inc r8
.qstore:
    mov [r9], r10b
    inc r9
    jmp .q
.junk:
    mov r10b, [r8]
    test r10b, r10b
    jz .eol
    inc r8
    cmp r10b, ','
    je .comma
    jmp .junk
.plain:
    mov r10b, [r8]
    test r10b, r10b
    jz .eol
    inc r8
    cmp r10b, ','
    je .comma
    mov [r9], r10b
    inc r9
    jmp .plain
.comma:
    mov byte [r9], 0
    inc r9
    jmp .field
.eol:
    mov byte [r9], 0
.cap:
    ret

; rax = pointer to field rcx=tb* rdx=row r8=col  ("" if the row is shorter)
getfield:
    mov r9, [rcx+8]
    cmp r8d, [r9+rdx*4]
    jae .empty
    mov r9, rdx
    shl r9, 5
    add r9, r8
    mov rax, [rcx]
    mov rax, [rax+r9*8]
    ret
.empty:
    lea rax, [s_empty]
    ret

; table_load(rcx=path, rdx=fs*, r8=tb*) -> eax 1 ok / 0 fail
table_load:
    PROLOG 64
    mov rsi, rdx
    mov r14, r8
    call load_lines
    test eax, eax
    jz .fail
    mov rbx, [rsi+16]
    mov rcx, rbx
    shl rcx, 8
    add rcx, 8
    call malloc
    test rax, rax
    jz .fail
    mov [r14], rax
    lea rcx, [rbx*4+8]
    call malloc
    test rax, rax
    jz .fail
    mov [r14+8], rax
    mov [r14+16], rbx
    xor r12d, r12d
.l:
    cmp r12, rbx
    jae .done
    mov rax, [rsi]
    mov rcx, [rax+r12*8]
    mov rdx, r12
    shl rdx, 8
    add rdx, [r14]
    call split_row
    mov rcx, [r14+8]
    mov [rcx+r12*4], eax
    inc r12
    jmp .l
.done:
    mov eax, 1
    EPILOG 64
.fail:
    xor eax, eax
    EPILOG 64

; print_row(ecx=tag, rdx=tb*, r8=row)
print_row:
    PROLOG 64
    mov rsi, rdx
    mov rdi, r8
    mov rdx, rcx
    lea r8, [rdi+1]
    lea rcx, [fmt_row]
    call printf
    mov rax, [rsi+8]
    mov r12d, [rax+rdi*4]
    xor ebx, ebx
.l:
    cmp ebx, r12d
    jae .d
    mov rcx, rsi
    mov rdx, rdi
    mov r8, rbx
    call getfield
    mov r8, rax
    lea rdx, [s_sp]
    test ebx, ebx
    jz .first
    lea rdx, [s_comma]
.first:
    lea rcx, [fmt_fld]
    call printf
    inc ebx
    jmp .l
.d:
    lea rcx, [s_nl]
    call printf
    EPILOG 64

; cmp_rows(rcx=row in A, rdx=row in B): print differing cells, count in cnt_diff
cmp_rows:
    PROLOG 64
    mov r14, rcx
    mov r15, rdx
    mov rax, [tbA+8]
    mov r12d, [rax+r14*4]
    mov rax, [tbB+8]
    mov r13d, [rax+r15*4]
    cmp r12d, r13d
    jae .mx
    mov r12d, r13d
.mx:
    xor ebx, ebx
.c:
    cmp ebx, r12d
    jae .d
    lea rcx, [tbA]
    mov rdx, r14
    mov r8, rbx
    call getfield
    mov rsi, rax
    lea rcx, [tbB]
    mov rdx, r15
    mov r8, rbx
    call getfield
    mov rdi, rax
    mov rcx, rsi
    mov rdx, rdi
    call strcmp
    test eax, eax
    jz .nx
    cmp byte [f_t], 0
    je .report
    mov rcx, rsi
    mov rdx, rdi
    call numeq
    test eax, eax
    jnz .nx
.report:
    inc qword [cnt_diff]
    lea rcx, [fmt_cell]
    lea rdx, [r14+1]
    lea r8, [r15+1]
    lea r9, [rbx+1]
    mov [rsp+32], rsi
    mov [rsp+40], rdi
    call printf
.nx:
    inc ebx
    jmp .c
.d:
    EPILOG 64

; cmd_table(rcx=A, rdx=B) -> eax exit code
cmd_table:
    PROLOG 64
    mov r14, rcx
    mov r15, rdx
    mov rcx, r14
    lea rdx, [fsA]
    lea r8, [tbA]
    call table_load
    test eax, eax
    jz .err
    mov rcx, r15
    lea rdx, [fsB]
    lea r8, [tbB]
    call table_load
    test eax, eax
    jz .err
    mov r12, [tbA+16]
    mov r13, [tbB+16]
    lea rcx, [r13+1]
    mov edx, 1
    call calloc
    test rax, rax
    jz .err
    mov rbp, rax                    ; used[] flags for B rows
    xor ebx, ebx
.i:
    cmp rbx, r12
    jae .bpass
    mov r14, [keycol]
    test r14, r14
    jnz .bykey
    cmp rbx, r13
    jae .onlya
    mov rsi, rbx
    jmp .matched
.bykey:
    lea rcx, [tbA]
    mov rdx, rbx
    lea r8, [r14-1]
    call getfield
    mov rdi, rax
    xor esi, esi
.scan:
    cmp rsi, r13
    jae .onlya
    cmp byte [rbp+rsi], 0
    jne .scn
    lea rcx, [tbB]
    mov rdx, rsi
    lea r8, [r14-1]
    call getfield
    mov rcx, rdi
    mov rdx, rax
    call strcmp
    test eax, eax
    jz .matched
.scn:
    inc rsi
    jmp .scan
.matched:
    mov byte [rbp+rsi], 1
    mov rcx, rbx
    mov rdx, rsi
    call cmp_rows
    jmp .inext
.onlya:
    inc qword [cnt_a]
    mov ecx, '-'
    lea rdx, [tbA]
    mov r8, rbx
    call print_row
.inext:
    inc rbx
    jmp .i
.bpass:
    xor ebx, ebx
.b:
    cmp rbx, r13
    jae .sum
    cmp byte [rbp+rbx], 0
    jne .bn
    inc qword [cnt_b]
    mov ecx, '+'
    lea rdx, [tbB]
    mov r8, rbx
    call print_row
.bn:
    inc rbx
    jmp .b
.sum:
    lea rcx, [fmt_tbsum]
    mov rdx, [cnt_diff]
    mov r8, [cnt_a]
    mov r9, [cnt_b]
    call printf
    mov rax, [cnt_diff]
    or rax, [cnt_a]
    or rax, [cnt_b]
    jnz .e1
    xor eax, eax
    EPILOG 64
.e1:
    mov eax, 1
    EPILOG 64
.err:
    mov eax, 2
    EPILOG 64

; ---------------------------------------------------------------- entry

usage:
    PROLOG 64
    lea rcx, [s_usage]
    call printf
    mov eax, 2
    EPILOG 64

main:
    PROLOG 64
    mov r12d, ecx                   ; argc
    mov r13, rdx                    ; argv
    cmp r12d, 4
    jl .usage
    mov r14, [r13+8]                ; command
    xor esi, esi
    xor edi, edi
    mov ebx, 2
.argloop:
    cmp ebx, r12d
    jge .argdone
    mov rcx, [r13+rbx*8]
    cmp byte [rcx], '-'
    jne .pos
    cmp byte [rcx+1], 0
    je .pos
    lea rdx, [rcx+1]
.fl:
    mov al, [rdx]
    test al, al
    jz .nextarg
    cmp al, 'c'
    jne .f1
    mov byte [f_c], 1
    jmp .fn
.f1:
    cmp al, 'a'
    jne .f2
    mov byte [f_a], 1
    jmp .fn
.f2:
    cmp al, 'i'
    jne .f3
    mov byte [f_i], 1
    jmp .fn
.f3:
    cmp al, 'w'
    jne .f4
    mov byte [f_w], 1
    jmp .fn
.f4:
    cmp al, 'n'
    jne .f6
    mov byte [f_n], 1
    jmp .fn
.f6:
    cmp al, 'b'
    jne .f7
    mov byte [f_b], 1
    jmp .fn
.f7:
    cmp al, 'x'
    jne .f8
    inc ebx
    cmp ebx, r12d
    jge .usage
    mov rcx, [r13+rbx*8]
    mov rax, [xcount]
    cmp rax, 8
    jae .nextarg
    lea rdx, [xpat]
    mov [rdx+rax*8], rcx
    inc rax
    mov [xcount], rax
    jmp .nextarg
.f8:
    cmp al, 'k'
    jne .f9
    inc ebx
    cmp ebx, r12d
    jge .usage
    mov rcx, [r13+rbx*8]
    call atoi
    test eax, eax
    jns .kok
    xor eax, eax
.kok:
    mov eax, eax
    mov [keycol], rax
    jmp .nextarg
.f9:
    cmp al, 'd'
    jne .f10
    mov byte [f_d], 1
    jmp .fn
.f10:
    cmp al, 'o'
    jne .f11
    inc ebx
    cmp ebx, r12d
    jge .usage
    mov rcx, [r13+rbx*8]
    mov [outpath], rcx
    jmp .nextarg
.f11:
    cmp al, 't'
    jne .f5
    inc ebx
    cmp ebx, r12d
    jge .usage
    mov rcx, [r13+rbx*8]
    call atof
    movsd [tolv], xmm0
    mov byte [f_t], 1
    jmp .nextarg
.f5:
    movzx edx, al
    lea rcx, [fmt_badopt]
    call printf
    mov eax, 2
    EPILOG 64
.fn:
    inc rdx
    jmp .fl
.pos:
    test rsi, rsi
    jnz .pos2
    mov rsi, rcx
    jmp .nextarg
.pos2:
    test rdi, rdi
    jnz .usage
    mov rdi, rcx
.nextarg:
    inc ebx
    jmp .argloop
.argdone:
    test rsi, rsi
    jz .usage
    test rdi, rdi
    jz .usage

    mov rcx, r14
    lea rdx, [s_dir]
    call strcmp
    test eax, eax
    jz .c_dir
    mov rcx, r14
    lea rdx, [s_sync]
    call strcmp
    test eax, eax
    jz .c_sync
    mov rcx, r14
    lea rdx, [s_text]
    call strcmp
    test eax, eax
    jz .c_text
    mov rcx, r14
    lea rdx, [s_table]
    call strcmp
    test eax, eax
    jz .c_table
    mov rcx, r14
    lea rdx, [s_hex]
    call strcmp
    test eax, eax
    jz .c_hex
.usage:
    lea rcx, [s_usage]
    call printf
    mov eax, 2
    EPILOG 64
.c_dir:
    mov byte [mode], 0
    mov rcx, rsi
    mov rdx, rdi
    call cmd_dir
    EPILOG 64
.c_sync:
    mov byte [mode], 1
    mov rcx, rsi
    mov rdx, rdi
    call cmd_dir
    EPILOG 64
.c_text:
    mov rcx, rsi
    mov rdx, rdi
    call cmd_text
    EPILOG 64
.c_table:
    mov rcx, rsi
    mov rdx, rdi
    call cmd_table
    EPILOG 64
.c_hex:
    mov rcx, rsi
    mov rdx, rdi
    call cmd_hex
    EPILOG 64

import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
exec(open('../tools/ph.py', encoding='utf-8').read())

# ---- fix ftp.inc issues
f = open('ftp.inc', encoding='utf-8').read()
def repf(a, b, cnt=1):
    global f
    assert f.count(a) == cnt, (a[:60], f.count(a))
    f = f.replace(a, b)
repf("%define FT_PATH  1656            ; wchar[520]", "%define FT_PATH  1656            ; wchar[520]\n%define FT_PORT  2700")
f = f.replace("[rsp+FT_PATH-8]", "[rsp+FT_PORT]")
# authority end lives in rdi (callee saved)
repf("    mov r8, rdi                      ; authority end\n", "")
repf("""    cmp rcx, r8
    jae .atd""", """    cmp rcx, rdi
    jae .atd""")
repf("""    cmp rcx, r8
    jae .hld""", """    cmp rcx, rdi
    jae .hld""")
repf("""    cmp rcx, r8
    jae .pld""", """    cmp rcx, rdi
    jae .pld""")
repf("""    cmp word [r8], 0
    je .pathd
    invoke wcscpy, r13, r8""", """    cmp word [rdi], 0
    je .pathd
    invoke wcscpy, r13, rdi""")
repf("""    mov ecx, [rsp+FT_PORT]
    invoke InternetConnectW, [rbx+F_INET], r15, rcx, &rsp+FT_USER, &rsp+FT_PASS, 1, 0x08000000, 0""",
     """    mov r14d, [rsp+FT_PORT]
    invoke InternetConnectW, [rbx+F_INET], r15, r14, &rsp+FT_USER, &rsp+FT_PASS, 1, 0x08000000, 0""")
repf("""    mov rbx, rcx
    mov rsi, r8
    mov rdi, r9
    lea rcx, [rbx+F_FTPP]
    test edx, edx
    jz .b
    lea rcx, [rbx+F_FTPP+1040]
.b:
    cmp word [rsi], 0
    jne .rel
    invoke _snwprintf, rdi, 1099, &f_ftp_root, rcx
    jmp .conv
.rel:
    invoke _snwprintf, rdi, 1099, &f_ftp_rel, rcx, rsi""", """    mov rbx, rcx
    mov rsi, r8
    mov rdi, r9
    lea rbp, [rbx+F_FTPP]
    test edx, edx
    jz .b
    lea rbp, [rbx+F_FTPP+1040]
.b:
    cmp word [rsi], 0
    jne .rel
    invoke _snwprintf, rdi, 1099, &f_ftp_root, rbp
    jmp .conv
.rel:
    invoke _snwprintf, rdi, 1099, &f_ftp_rel, rbp, rsi""")
open('ftp.inc', 'w', encoding='utf-8', newline='\n').write(f)

# ---- folder.asm
s = open('folder.asm', encoding='utf-8').read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:60], s.count(a))
    s = s.replace(a, b)
rep("%define F_SIZE    3008\n", "%define F_INET    3008\n%define F_FTPC    3016\n%define F_FTPP    3032\n%define F_SIZE    5120\n")
rep("extern CreateDirectoryW\n", "extern CreateDirectoryW, _wcsnicmp\nextern InternetOpenW, InternetConnectW, FtpFindFirstFileW, InternetFindNextFileW, InternetCloseHandle, FtpGetFileW\n")
rep('WSTR s_bak, ".bak"\n', '''WSTR s_bak, ".bak"
WSTR s_ftp_scheme, "ftp://"
WSTR s_anon, "anonymous"
WSTR s_anonpw, "becompare@asm"
WSTR s_agent, "BeCompareAsm"
WSTR f_ftp_root, "%s"
WSTR f_ftp_rel, "%s/%s"
''')
rep("""    cmp qword [r12+F_KIND+rbp*8], 1
    je .virt
    cmp word [r14], 0
    jne .rel""", """    cmp qword [r12+F_KIND+rbp*8], 1
    je .virt
    cmp qword [r12+F_KIND+rbp*8], 2
    je .ftp
    cmp word [r14], 0
    jne .rel""")
rep(""".virt:
    lea rcx, [r12+F_VTA]
    test ebp, ebp
    jz .vt""", """.ftp:
    invoke ftp_enum, r12, rbp, r14, r15
    EPILOG 2896
.virt:
    lea rcx, [r12+F_VTA]
    test ebp, ebp
    jz .vt""")
rep('%include "folder_vfs.inc"\n', '%include "folder_vfs.inc"\n%include "ftp.inc"\n')
open('folder.asm', 'w', encoding='utf-8', newline='\n').write(s)

# ---- folder_vfs.inc
v = open('folder_vfs.inc', encoding='utf-8').read()
def repv(a, b, cnt=1):
    global v
    assert v.count(a) == cnt, (a[:60], v.count(a))
    v = v.replace(a, b)
repv("""    mov rax, [r12+F_KIND+r13*8]
    test rax, rax
    jz .disk
    test dword [r14+8], HAS_CRC""", """    mov rax, [r12+F_KIND+r13*8]
    test rax, rax
    jz .disk
    cmp rax, 2
    je .remote
    test dword [r14+8], HAS_CRC""")
repv(""".unknown:
    mov rax, -1
    EPILOG 2400
.disk:""", """.unknown:
    mov rax, -1
    EPILOG 2400
.remote:
    invoke fold_side_path, r12, r13, r15, &rsp+96
    test eax, eax
    jz .unknown
    invoke file_crc, r12, &rsp+96
    EPILOG 2400
.disk:""")
repv("""fold_free_vt:
    PROLOG 64
    mov rbx, rcx""", """fold_free_vt:
    PROLOG 64
    mov rbx, rcx
    invoke ftp_close, rbx""")
repv("""fold_open_root:
    PROLOG 128
    mov rbx, rcx
    mov r12d, edx
    mov r13, r8
    invoke GetFileAttributesW, r13""", """fold_open_root:
    PROLOG 128
    mov rbx, rcx
    mov r12d, edx
    mov r13, r8
    invoke ftp_is_url, r13
    test eax, eax
    jz .local
    invoke ftp_open, rbx, r12, r13
    EPILOG 128
.local:
    invoke GetFileAttributesW, r13""")
# side path: remote files are downloaded
repv(""".virt:
    lea rsi, [rbx+F_VTA]
    test r12d, r12d
    jz .have
    lea rsi, [rbx+F_VTB]
.have:
    cmp qword [rsi+VT_KIND_], 0
    jne .nosnap                      ; a snapshot has no contents
    invoke vt_find, rsi, r13
    test rax, rax
    jz .fail
    mov rdi, rax
    invoke GetTempPathW, 400, &rsp+96""", """.virt:
    mov [rsp+1560], r13              ; the original relative name
    cmp qword [rbx+F_KIND+r12*8], 2
    je .tmp
    lea rsi, [rbx+F_VTA]
    test r12d, r12d
    jz .have
    lea rsi, [rbx+F_VTB]
.have:
    cmp qword [rsi+VT_KIND_], 0
    jne .nosnap                      ; a snapshot has no contents
    invoke vt_find, rsi, r13
    test rax, rax
    jz .fail
    mov rdi, rax
.tmp:
    invoke GetTempPathW, 400, &rsp+96""")
repv("""    invoke wcscpy, &r15+2, r13
    invoke zip_extract, rsi, rdi, r14
    EPILOG 1600""", """    invoke wcscpy, &r15+2, r13
    cmp qword [rbx+F_KIND+r12*8], 2
    je .dl
    invoke zip_extract, rsi, rdi, r14
    EPILOG 1600
.dl:
    invoke ftp_download, rbx, r12, [rsp+1560], r14
    EPILOG 1600""")
open('folder_vfs.inc', 'w', encoding='utf-8', newline='\n').write(v)
b = open('../build-gui.ps1', encoding='utf-8').read().replace("-ldwmapi", "-ldwmapi -lwininet")
open('../build-gui.ps1', 'w', encoding='utf-8', newline='\n').write(b)
print('ftp patched')

; props_media.inc - MD-01 audio tag compare: MP3 (ID3v2.2/2.3/2.4, ID3v1) and FLAC (Vorbis comments)
; slots: 0 format, 1 size, 2 title, 3 artist, 4 album, 5 year, 6 track, 7 genre, 8 album artist,
;        9 comment, 10 tag kind, 11 audio info, 12 audio data CRC32, 13 tag bytes, 14 cover art

extern MultiByteToWideChar, _stricmp, read_file_bytes

section .rdata
WSTR ml0, "형식"
WSTR ml1, "파일 크기 (바이트)"
WSTR ml2, "제목"
WSTR ml3, "아티스트"
WSTR ml4, "앨범"
WSTR ml5, "연도"
WSTR ml6, "트랙"
WSTR ml7, "장르"
WSTR ml8, "앨범 아티스트"
WSTR ml9, "코멘트"
WSTR ml10, "태그 종류"
WSTR ml11, "오디오 정보"
WSTR ml12, "오디오 데이터 CRC32 (태그 제외)"
WSTR ml13, "태그 크기 (바이트)"
WSTR ml14, "표지 이미지"
WSTR ml15, "(예약)"
WSTR mf_mp3, "MP3"
WSTR mf_flac, "FLAC"
WSTR mf_unk, "알 수 없음 (지원하지 않는 형식)"
WSTR mk_id3v1, "ID3v1"
WSTR mk_id3v2x, "ID3v2.%u"
WSTR mk_id3both, "ID3v2.%u + ID3v1"
WSTR mk_vorbis, "Vorbis 주석"
WSTR mf_u, "%u"
WSTR mf_crc, "%08X"
WSTR mf_cover, "있음 (%u 바이트)"
WSTR mf_mp3info, "%s %s · %u kbps · %u Hz · %s"
WSTR mf_flacinfo, "%u Hz · %u채널 · %u비트 · %u:%02u"
WSTR mv_1, "MPEG1"
WSTR mv_2, "MPEG2"
WSTR mv_25, "MPEG2.5"
WSTR mly_1, "Layer I"
WSTR mly_2, "Layer II"
WSTR mly_3, "Layer III"
WSTR mch_0, "스테레오"
WSTR mch_1, "조인트 스테레오"
WSTR mch_2, "듀얼 채널"
WSTR mch_3, "모노"

align 8
media_labels: dq ml0, ml1, ml2, ml3, ml4, ml5, ml6, ml7, ml8, ml9, ml10, ml11, ml12, ml13, ml14, ml15
mv_names:  dq mv_25, 0, mv_2, mv_1
mly_names: dq 0, mly_3, mly_2, mly_1
mch_names: dq mch_0, mch_1, mch_2, mch_3

br_v1l3: dw 0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0
br_v2l3: dw 0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0
align 4
sr_tbl: dd 11025, 12000, 8000, 0, 0, 0, 0, 0, 0, 22050, 24000, 16000, 44100, 48000, 32000

; id3 frame id tables: dd id, dd slot, dd kind (0 text, 1 comment, 2 picture)
id3_t4: dd 'TIT2', 2, 0
        dd 'TPE1', 3, 0
        dd 'TALB', 4, 0
        dd 'TYER', 5, 0
        dd 'TDRC', 5, 0
        dd 'TRCK', 6, 0
        dd 'TCON', 7, 0
        dd 'TPE2', 8, 0
        dd 'COMM', 9, 1
        dd 'APIC', 14, 2
        dd 0, 0, 0
id3_t3: dd 'TT2', 2, 0
        dd 'TP1', 3, 0
        dd 'TAL', 4, 0
        dd 'TYE', 5, 0
        dd 'TRK', 6, 0
        dd 'TCO', 7, 0
        dd 'TP2', 8, 0
        dd 'COM', 9, 1
        dd 'PIC', 14, 2
        dd 0, 0, 0

fk_title: db "TITLE", 0
fk_artist: db "ARTIST", 0
fk_album: db "ALBUM", 0
fk_date: db "DATE", 0
fk_year: db "YEAR", 0
fk_track: db "TRACKNUMBER", 0
fk_genre: db "GENRE", 0
fk_aart: db "ALBUMARTIST", 0
fk_comment: db "COMMENT", 0
fk_desc: db "DESCRIPTION", 0
align 8
flac_keys: dq fk_title, 2, fk_artist, 3, fk_album, 4, fk_date, 5, fk_year, 5, fk_track, 6, fk_genre, 7, fk_aart, 8, fk_comment, 9, fk_desc, 9, 0, 0

section .text

; mt_put(slots, idx, src): fill a slot unless it already has a value
mt_put:
    PROLOG 64
    imul eax, edx, VF_SLOTB
    lea rbx, [rcx+rax]
    cmp word [rbx], 0
    jne .d
    invoke wcsncpy, rbx, r8, 128
    mov word [rbx+256], 0
.d:
    EPILOG 64

; mt_conv(enc, data, len, out): text frame payload -> wide string (out holds 130 wchar)
mt_conv:
    PROLOG 64
    mov r12d, ecx
    mov r13, rdx
    mov r14, r8
    mov r15, r9
    mov word [r15], 0
    test r14, r14
    jle .d
    cmp r12d, 1
    je .u16
    cmp r12d, 2
    je .u16
    mov ebx, 28591
    cmp r12d, 3
    jne .mb
    mov ebx, 65001
.mb:
    cmp r14, 126
    jbe .len
    mov r14d, 126
.len:
    invoke MultiByteToWideChar, rbx, 0, r13, r14, r15, 128
    test eax, eax
    jle .d
    mov word [r15+rax*2], 0
    jmp .d
.u16:
    shr r14, 1
    xor ebp, ebp
    test r14, r14
    jz .d
    movzx eax, word [r13]
    cmp ax, 0xFEFF
    jne .nle
    add r13, 2
    dec r14
    jmp .go
.nle:
    cmp ax, 0xFFFE
    jne .nbe
    add r13, 2
    dec r14
    mov ebp, 1
    jmp .go
.nbe:
    cmp r12d, 2
    jne .go
    mov ebp, 1
.go:
    xor esi, esi
.l:
    cmp rsi, r14
    jae .e
    cmp esi, 127
    jae .e
    movzx eax, word [r13+rsi*2]
    test ebp, ebp
    jz .nb
    rol ax, 8
.nb:
    test ax, ax
    jz .e
    mov [r15+rsi*2], ax
    inc esi
    jmp .l
.e:
    mov word [r15+rsi*2], 0
.d:
    EPILOG 64

; mt_ss28(ecx = value read big-endian) -> eax: ID3 synchsafe integer (clobbers ecx, edx)
mt_ss28:
    mov eax, ecx
    and eax, 0x7F
    mov edx, ecx
    shr edx, 8
    and edx, 0x7F
    shl edx, 7
    or eax, edx
    mov edx, ecx
    shr edx, 16
    and edx, 0x7F
    shl edx, 14
    or eax, edx
    shr ecx, 24
    and ecx, 0x7F
    shl ecx, 21
    or eax, ecx
    ret

; mt_id3v2(buf, size, slots) -> eax: offset where the audio starts (0 if no ID3v2 tag), edx: major version
%define T_END   380
%define T_AUD   384
%define T_FSZ   388
%define T_HDR   392
%define T_DAT   396
mt_id3v2:
    PROLOG 448
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    cmp r13, 10
    jb .none
    cmp word [r12], 'ID'
    jne .none
    cmp byte [r12+2], '3'
    jne .none
    movzx r15d, byte [r12+3]          ; major
    mov ecx, [r12+6]
    bswap ecx
    call mt_ss28
    lea ebp, [rax+10]
    test byte [r12+5], 0x10
    jz .nofoot
    add ebp, 10
.nofoot:
    mov [rsp+T_AUD], ebp
    lea rbx, [rax+10]
    cmp rbx, r13
    jbe .endok
    mov rbx, r13
.endok:
    mov [rsp+T_END], ebx
    mov esi, 10                       ; pos
    test byte [r12+5], 0x40
    jz .frames
    cmp r15d, 3
    jb .frames
    mov ecx, [r12+10]
    bswap ecx
    cmp r15d, 4
    jne .v23ext
    call mt_ss28
    add esi, eax
    jmp .frames
.v23ext:
    lea esi, [rsi+rcx+4]
.frames:
    mov edi, [rsp+T_END]
    cmp r15d, 2
    jne .hdr10
    lea eax, [rsi+6]
    cmp eax, edi
    ja .fin
    cmp byte [r12+rsi], 0
    je .fin
    mov eax, [r12+rsi]
    and eax, 0x00FFFFFF
    movzx ecx, byte [r12+rsi+3]
    shl ecx, 16
    movzx edx, byte [r12+rsi+4]
    shl edx, 8
    or ecx, edx
    movzx edx, byte [r12+rsi+5]
    or ecx, edx
    mov [rsp+T_FSZ], ecx
    mov dword [rsp+T_HDR], 6
    lea r8, [id3_t3]
    jmp .lookup
.hdr10:
    lea eax, [rsi+10]
    cmp eax, edi
    ja .fin
    cmp byte [r12+rsi], 0
    je .fin
    mov ecx, [r12+rsi+4]
    bswap ecx
    cmp r15d, 4
    jne .szok
    call mt_ss28
    mov ecx, eax
.szok:
    mov [rsp+T_FSZ], ecx
    mov dword [rsp+T_HDR], 10
    mov eax, [r12+rsi]
    lea r8, [id3_t4]
.lookup:
    mov ecx, [rsp+T_FSZ]
    mov edx, [rsp+T_HDR]
    lea r9d, [rsi+rdx]                ; data offset
    mov [rsp+T_DAT], r9d
    lea r10, [r9+rcx]                 ; data end
    cmp r10, rdi
    ja .fin
.tl:
    mov edx, [r8]
    test edx, edx
    jz .nextframe
    cmp edx, eax
    je .hit
    add r8, 12
    jmp .tl
.hit:
    mov ebx, [r8+4]                   ; slot
    mov edx, [r8+8]                   ; kind
    mov r9d, [rsp+T_DAT]
    mov ecx, [rsp+T_FSZ]
    test ecx, ecx
    jz .nextframe
    cmp edx, 2
    je .pic
    movzx r10d, byte [r12+r9]         ; encoding
    inc r9d
    dec ecx
    test edx, edx
    jz .conv
    add r9d, 3                        ; comment: skip language + short description
    sub ecx, 3
    jle .nextframe
    cmp r10d, 1
    je .w16
    cmp r10d, 2
    je .w16
.s8:
    test ecx, ecx
    jle .nextframe
    cmp byte [r12+r9], 0
    je .s8end
    inc r9d
    dec ecx
    jmp .s8
.s8end:
    inc r9d
    dec ecx
    jmp .conv
.w16:
    cmp ecx, 2
    jl .nextframe
    cmp word [r12+r9], 0
    je .w16end
    add r9d, 2
    sub ecx, 2
    jmp .w16
.w16end:
    add r9d, 2
    sub ecx, 2
.conv:
    movsxd r8, ecx
    lea rdx, [r12+r9]
    mov ecx, r10d
    lea r9, [rsp+96]
    call mt_conv
    invoke mt_put, r14, rbx, &rsp+96
    jmp .nextframe
.pic:
    mov eax, ecx
    invoke _snwprintf, &rsp+96, 60, &mf_cover, rax
    invoke mt_put, r14, rbx, &rsp+96
.nextframe:
    mov eax, [rsp+T_FSZ]
    add eax, [rsp+T_HDR]
    add esi, eax
    jmp .frames
.fin:
    mov eax, [rsp+T_AUD]
    mov edx, r15d
    EPILOG 448
.none:
    xor eax, eax
    xor edx, edx
    EPILOG 448

; mt_id3v1(buf, size, slots) -> eax 1 when a v1 tag is present
mt_id3v1:
    PROLOG 400
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    cmp r13, 128
    jb .no
    lea r15, [r12+r13-128]
    cmp word [r15], 'TA'
    jne .no
    cmp byte [r15+2], 'G'
    jne .no
    xor ebp, ebp
.f:
    ; (offset, length, slot) triples
    lea rax, [id3v1_fields]
    lea rax, [rax+rbp*4]
    lea rax, [rax+rbp*8]
    movzx edx, byte [rax]
    movzx r8d, byte [rax+1]
    movzx ebx, byte [rax+2]
    lea rdx, [r15+rdx]
    xor ecx, ecx
    lea r9, [rsp+96]
    call mt_conv
    ; trim trailing spaces
    lea rdi, [rsp+96]
    invoke wcslen, rdi
.trim:
    test rax, rax
    jz .put
    cmp word [rdi+rax*2-2], ' '
    jne .put
    mov word [rdi+rax*2-2], 0
    dec rax
    jmp .trim
.put:
    invoke mt_put, r14, rbx, &rsp+96
    inc ebp
    cmp ebp, 4
    jb .f
    ; track (v1.1) and genre number
    cmp byte [r15+125], 0
    jne .genre
    movzx eax, byte [r15+126]
    test eax, eax
    jz .genre
    invoke _snwprintf, &rsp+96, 20, &mf_u, rax
    invoke mt_put, r14, 6, &rsp+96
.genre:
    movzx eax, byte [r15+127]
    cmp eax, 255
    je .yes
    invoke _snwprintf, &rsp+96, 20, &mf_u, rax
    invoke mt_put, r14, 7, &rsp+96
.yes:
    mov eax, 1
    EPILOG 400
.no:
    xor eax, eax
    EPILOG 400

section .rdata
; id3v1 fields: offset, length, slot (3 bytes each, padded to 3 per entry via 12-byte stride trick avoided: 4 entries)
id3v1_fields: db 3, 30, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0
              db 33, 30, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0
              db 63, 30, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0
              db 93, 4, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0
section .text

; mt_mp3hdr(buf, start, end, slot) -> eax 1 when a frame header was found; writes the audio info string
mt_mp3hdr:
    PROLOG 192
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    mov r15, r9
    lea rax, [r13+65536]
    cmp rax, r14
    jbe .lim
    mov rax, r14
.lim:
    sub rax, 4
    jbe .no
    mov rbp, rax                      ; last scan position
.scan:
    cmp r13, rbp
    ja .no
    cmp byte [r12+r13], 0xFF
    jne .nx
    movzx eax, byte [r12+r13+1]
    and eax, 0xE0
    cmp eax, 0xE0
    jne .nx
    movzx ebx, byte [r12+r13+1]
    shr ebx, 3
    and ebx, 3                        ; version
    cmp ebx, 1
    je .nx
    movzx esi, byte [r12+r13+1]
    shr esi, 1
    and esi, 3                        ; layer
    test esi, esi
    jz .nx
    movzx edi, byte [r12+r13+2]
    mov eax, edi
    shr eax, 4                        ; bitrate index
    cmp eax, 15
    je .nx
    shr edi, 2
    and edi, 3                        ; sample rate index
    cmp edi, 3
    je .nx
    jmp .found
.nx:
    inc r13
    jmp .scan
.found:
    xor ecx, ecx                      ; kbps
    cmp esi, 1
    jne .nobr
    lea rdx, [br_v2l3]
    cmp ebx, 3
    jne .tb
    lea rdx, [br_v1l3]
.tb:
    movzx ecx, word [rdx+rax*2]
.nobr:
    mov r8d, 12
    cmp ebx, 3
    je .sb
    mov r8d, 9
    cmp ebx, 2
    je .sb
    xor r8d, r8d
.sb:
    add r8d, edi
    lea rdx, [sr_tbl]
    mov r9d, [rdx+r8*4]               ; sample rate
    movzx edx, byte [r12+r13+3]
    shr edx, 6
    lea rax, [mch_names]
    mov rbp, [rax+rdx*8]              ; channel mode text
    lea rax, [mv_names]
    mov rdi, [rax+rbx*8]
    lea rax, [mly_names]
    mov rsi, [rax+rsi*8]
    mov ebx, ecx                      ; kbps
    mov r13d, r9d                     ; Hz
    invoke _snwprintf, r15, 120, &mf_mp3info, rdi, rsi, rbx, r13, rbp
    mov eax, 1
    EPILOG 192
.no:
    xor eax, eax
    EPILOG 192

; mt_vorbis(ptr, len, slots): FLAC / Vorbis comment block
mt_vorbis:
    PROLOG 560
    mov r12, rcx
    lea r13, [rcx+rdx]                ; end
    mov r14, r8
    cmp rdx, 8
    jb .d
    mov eax, [r12]
    lea r12, [r12+rax+4]
    lea rax, [r12+4]
    cmp rax, r13
    ja .d
    mov ebx, [r12]                    ; comment count
    add r12, 4
    cmp ebx, 500
    jbe .cnt
    mov ebx, 500
.cnt:
.next:
    test ebx, ebx
    jz .d
    dec ebx
    lea rax, [r12+4]
    cmp rax, r13
    ja .d
    mov r15d, [r12]
    add r12, 4
    lea rax, [r12+r15]
    cmp rax, r13
    ja .d
    ; find '='
    xor esi, esi
.eq:
    cmp esi, r15d
    jae .skip
    cmp byte [r12+rsi], '='
    je .gotkey
    inc esi
    jmp .eq
.gotkey:
    cmp esi, 31
    ja .skip
    lea rdi, [rsp+400]
    xor ecx, ecx
.kc:
    cmp ecx, esi
    jae .kd
    mov al, [r12+rcx]
    mov [rdi+rcx], al
    inc ecx
    jmp .kc
.kd:
    mov byte [rdi+rcx], 0
    lea rbp, [flac_keys]
.kl:
    mov rax, [rbp]
    test rax, rax
    jz .skip
    invoke _stricmp, rdi, rax
    test eax, eax
    jz .hit
    add rbp, 16
    jmp .kl
.hit:
    mov ecx, 3
    lea rdx, [r12+rsi+1]
    mov r8d, r15d
    sub r8d, esi
    dec r8d
    lea r9, [rsp+96]
    call mt_conv
    mov rdx, [rbp+8]
    invoke mt_put, r14, rdx, &rsp+96
.skip:
    add r12, r15
    jmp .next
.d:
    EPILOG 560

; mt_flacinfo(streaminfo, out)
mt_flacinfo:
    PROLOG 192
    mov r12, rcx
    mov r13, rdx
    movzx eax, byte [r12+10]
    shl eax, 8
    movzx ecx, byte [r12+11]
    or eax, ecx
    shl eax, 4
    movzx ecx, byte [r12+12]
    shr ecx, 4
    or eax, ecx
    mov r14d, eax                      ; sample rate
    movzx eax, byte [r12+12]
    shr eax, 1
    and eax, 7
    inc eax
    mov r15d, eax                      ; channels
    movzx eax, byte [r12+12]
    and eax, 1
    shl eax, 4
    movzx ecx, byte [r12+13]
    shr ecx, 4
    or eax, ecx
    inc eax
    mov ebp, eax                       ; bits per sample
    movzx eax, byte [r12+13]
    and eax, 0x0F
    movzx ecx, byte [r12+14]
    shl rax, 8
    or rax, rcx
    movzx ecx, byte [r12+15]
    shl rax, 8
    or rax, rcx
    movzx ecx, byte [r12+16]
    shl rax, 8
    or rax, rcx
    movzx ecx, byte [r12+17]
    shl rax, 8
    or rax, rcx                        ; total samples
    xor ebx, ebx
    test r14d, r14d
    jz .nodur
    xor edx, edx
    mov ecx, r14d
    div rcx
    mov rbx, rax                       ; seconds
.nodur:
    mov rax, rbx
    xor edx, edx
    mov ecx, 60
    div rcx
    mov rsi, rax
    mov rdi, rdx
    invoke _snwprintf, r13, 100, &mf_flacinfo, r14, r15, rbp, rsi, rdi
    EPILOG 192

; mt_flac(buf, size, slots) -> eax audio start (0 when this is not FLAC)
mt_flac:
    PROLOG 256
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    cmp r13, 8
    jb .no
    cmp dword [r12], 'fLaC'
    jne .no
    mov esi, 4
.blk:
    lea rax, [rsi+4]
    cmp rax, r13
    ja .end
    movzx ebx, byte [r12+rsi]          ; header
    movzx eax, byte [r12+rsi+1]
    shl eax, 8
    movzx ecx, byte [r12+rsi+2]
    or eax, ecx
    shl eax, 8
    movzx ecx, byte [r12+rsi+3]
    or eax, ecx
    mov edi, eax                       ; length
    lea r15, [rsi+4]                   ; data offset
    lea rax, [r15+rdi]
    cmp rax, r13
    ja .end
    mov eax, ebx
    and eax, 0x7F
    test eax, eax
    jz .info
    cmp eax, 4
    je .vorbis
    cmp eax, 6
    je .pic
    jmp .adv
.info:
    cmp edi, 18
    jb .adv
    lea rcx, [r12+r15]
    lea rdx, [r14+VF_SLOTB*11]
    call mt_flacinfo
    jmp .adv
.vorbis:
    invoke mt_vorbis, &r12+r15, rdi, r14
    invoke mt_put, r14, 10, &mk_vorbis
    jmp .adv
.pic:
    invoke _snwprintf, &rsp+96, 60, &mf_cover, rdi
    invoke mt_put, r14, 14, &rsp+96
.adv:
    lea esi, [r15+rdi]
    test bl, 0x80
    jnz .end
    jmp .blk
.end:
    mov eax, esi
    EPILOG 256
.no:
    xor eax, eax
    EPILOG 256


; mt_side(path, slots) -> eax 1 when the file could be read
mt_side:
    PROLOG 256
    mov r12, rcx
    mov r13, rdx
    invoke read_file_bytes, r12, &rsp+96
    test rax, rax
    jz .fail
    mov rbx, rax                       ; buffer
    mov r14, [rsp+96]                  ; size
    invoke fmt_size, &r13+VF_SLOTB, r14
    xor r15d, r15d                     ; audio start
    mov rbp, r14                       ; audio end
    cmp dword [rbx], 'fLaC'
    jne .mp3
    invoke mt_flac, rbx, r14, r13
    mov r15d, eax
    invoke mt_put, r13, 0, &mf_flac
    jmp .crc
.mp3:
    invoke mt_id3v2, rbx, r14, r13
    mov r15d, eax
    mov esi, edx                       ; major (0 = none)
    invoke mt_id3v1, rbx, r14, r13
    mov edi, eax                       ; v1 present
    test edi, edi
    jz .end
    sub rbp, 128
.end:
    cmp r15, rbp
    jbe .rng
    mov r15, rbp
.rng:
    lea rax, [rsp+160]
    mov word [rax], 0
    lea r10, [rsp+160]
    test esi, esi
    jz .nov2
    test edi, edi
    jz .only2
    invoke _snwprintf, &rsp+160, 30, &mk_id3both, rsi
    jmp .kind
.only2:
    invoke _snwprintf, &rsp+160, 30, &mk_id3v2x, rsi
    jmp .kind
.nov2:
    test edi, edi
    jz .nokind
    invoke wcscpy, &rsp+160, &mk_id3v1
.kind:
    invoke mt_put, r13, 10, &rsp+160
.nokind:
    lea rcx, [rbx]
    mov rdx, r15
    mov r8, rbp
    lea r9, [r13+VF_SLOTB*11]
    call mt_mp3hdr
    test eax, eax
    jnz .ismp3
    test esi, esi
    jnz .ismp3
    test edi, edi
    jz .unk
.ismp3:
    invoke mt_put, r13, 0, &mf_mp3
    jmp .crc
.unk:
    invoke mt_put, r13, 0, &mf_unk
.crc:
    mov rax, rbp
    sub rax, r15
    jbe .nocrc
    lea rdx, [rbx+r15]
    mov r8, rax
    xor ecx, ecx
    call crc32_update
    invoke _snwprintf, &r13+VF_SLOTB*12, 30, &mf_crc, rax
.nocrc:
    mov rax, r15
    test edi, edi
    jz .tb
    add rax, 128
.tb:
    cmp dword [rbx], 'fLaC'
    jne .tbw
.tbw:
    invoke _snwprintf, &r13+VF_SLOTB*13, 30, &mf_u, rax
    invoke free, rbx
    mov eax, 1
    EPILOG 256
.fail:
    xor eax, eax
    EPILOG 256

; pr_media(P, pathA, pathB) -> eax 1 ok
pr_media:
    PROLOG 64
    mov rbx, rcx
    mov r12, rdx
    mov r13, r8
    invoke calloc, 2*VF_NSLOT, VF_SLOTB
    mov r14, rax
    test rax, rax
    jz .fail
    invoke mt_side, r12, r14
    test eax, eax
    jz .free
    lea rdx, [r14+VF_NSLOT*VF_SLOTB]
    invoke mt_side, r13, rdx
    test eax, eax
    jz .free
    invoke pr_emit, rbx, r14, &media_labels
    invoke free, r14
    mov eax, 1
    EPILOG 64
.free:
    invoke free, r14
.fail:
    xor eax, eax
    EPILOG 64

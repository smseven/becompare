import re
p = r'C:\Users\charles\workspace\becompare\README.md'
s = open(p, encoding='utf-8').read().replace('\r\n', '\n')

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:50]
    s = s.replace(a, b)

rep("| FC-02 | 🟡 | 크기·수정 시각·내용(바이트). CRC32, 속성, 실행 파일 버전 ❌ |",
    "| FC-02 | 🟡 | 크기·수정 시각·내용(바이트)·CRC32·속성 ✅. 실행 파일 버전 ❌ |")
rep("| SY-01 SY-02 SY-03 SY-05 | ✅ | SY-02는 디스크↔디스크(UNC 포함). FTP·압축 파일 ❌ |",
    "| SY-01 SY-02 SY-03 SY-05 | ✅ | 디스크↔디스크(UNC 포함). 실행 전 동기화 미리보기 대화상자(작업 목록·필터·요약) 포함. ZIP/스냅샷/FTP는 읽기 전용 |")
rep("| VF-02~06 AR-01~02 SN-01 | ❌ | FTP/SFTP/클라우드/SVN/휴대 장치/압축 파일/스냅샷 |",
    "| VF-02 | 🟡 | 평문 FTP(WinInet, `ftp://user:pass@host:port/path`) 목록·다운로드 비교 ✅. SFTP/FTPS ❌ |\n"
    "| AR-01 SN-01 | ✅ | .zip(자체 DEFLATE+CRC32) 및 스냅샷(.bcss) 읽기 전용 비교, 스냅샷 저장 버튼·`/snapshot` |\n"
    "| VF-03~06 AR-02 | ❌ | 클라우드(OAuth/서명)/SVN/휴대 장치(MTP)/기타 압축 형식 |")
rep("| **공통** |",
    "| **UI/UX** | 경로 막대 ⇄ 교체 버튼, 아이콘 글꼴·툴팁 헬퍼, 다크 리스트 머리글, 텍스트 줄 번호 거터·차이 막대·인라인 복사 글리프(→/←), 차이 미니맵, 폴더 '방향' 열, 상태 표시줄에 인코딩·줄바꿈 |\n| **공통** |")
rep("- 다크 모드에서 탭 컨트롤 머리글과 리스트 머리글은 시스템 테마(밝은색)를 따릅니다.",
    "- 다크 모드에서 탭 컨트롤 머리글은 시스템 테마(밝은색)를 따릅니다. 리스트 머리글은 직접 그립니다.\n"
    "- UI/UX 제언 중 홈 대시보드 카드 재설계, 3분할 상태 표시줄, 분할 필터 버튼, 모든 버튼의 아이콘 전환은 부분 적용/미적용입니다.\n"
    "- SFTP/FTPS, 클라우드, Subversion, MTP, MSSCCI, 자동 업데이트, macOS/Linux 포팅은 이 환경에서 구현·검증할 수 없어 제외했습니다.\n"
    "- 버전/레지스트리/미디어 비교, 폴더 병합(FM), 텍스트 편집 세션, 스크립트 언어, 셸 확장, 사용자 정의 설정 대화상자, xlsx 표 비교는 미구현입니다.")
rep("  pic.asm    + pic_ui.inc/ui2  이미지 비교",
    "  pic.asm    + pic_ui.inc/ui2  이미지 비교\n  inflate.asm   DEFLATE + CRC32\n  vtab.asm      ZIP 디렉터리·스냅샷 읽기, 추출\n  folder: ftp.inc, folder_vfs.inc, sync_dlg.inc   FTP·가상 측·동기화 미리보기\n  text_gutter.inc   줄 번호 거터·미니맵")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')

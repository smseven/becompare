import os
os.chdir(r'C:\Users\charles\workspace\becompare')
s = open('README.md', encoding='utf-8').read().replace('\r\n', '\n')

# ---- build section
a = s.index("## 빌드와 실행")
b = s.index("```\nbcgui.exe  ")
build = """## 빌드

### 준비물

| 도구 | 용도 | 확인 |
| --- | --- | --- |
| Windows 10 이상 (x64) | 실행·빌드 환경 | |
| NASM 2.16 이상 | 어셈블 (`nasm -f win64`) | `nasm -v` |
| MinGW-w64 (`gcc`, `windres`) | 링크·리소스 컴파일 (UCRT 빌드 권장) | `gcc --version` |
| PowerShell 5.1 이상 | 빌드 스크립트 실행 | |
| Python 3 (선택) | 정적 검사·회귀 검사 | `python --version` |

NASM과 MinGW-w64는 `PATH`에 있어야 합니다. 예: `winget install NASM.NASM`, `winget install BrechtSanders.WinLibs.POSIX.UCRT`.

### 빌드 순서

```powershell
git clone https://github.com/smseven/demo.git BeCompare
cd BeCompare

powershell -File build-gui.ps1      # gui/*.asm -> build/*.obj -> bcgui.exe (GUI, 메인 프로그램)
powershell -File build.ps1          # src/bc.asm -> bc.exe (이전 단계의 콘솔 도구, 선택)
```

- 성공하면 마지막 줄에 `built bcgui.exe`(또는 `built bc.exe`)가 출력되고 실행 파일이 저장소 루트에 만들어집니다. 중간 산출물은 `build/`에 쌓입니다.
- `build-gui.ps1`은 `gui/`의 모듈을 하나씩 `nasm -f win64`로 어셈블하고, 리소스(`gui/res/app.rc`, 매니페스트)를 `windres`로 컴파일한 뒤 `gcc -mwindows`로 링크합니다. 링크 라이브러리: user32, gdi32, comctl32, comdlg32, shell32, ole32, dwmapi, wininet, gdiplus, uxtheme, shlwapi, version, advapi32.
- 새 모듈을 추가하면 `build-gui.ps1`의 `$optional` 목록에 이름을 넣어야 링크됩니다.

### 검사 (빌드 후)

```powershell
python tools/hazard.py              # invoke 인자 덮어쓰기 / 스택 프레임 16바이트 정렬 정적 검사 -> "hazards: 0" 이어야 함
python tools/test_regressions.py    # 격리된 경로에서 재빌드 + 저장 오류·상태·명령줄 회귀 검사 57개
powershell -File tools/t_smoke.ps1  # 세션 유형 14가지가 3초 이상 살아 있는지 확인 (실제 창을 띄움)
```

### 자주 막히는 곳

- `nasm`/`gcc`/`windres`를 찾지 못함: 설치 후 새 터미널을 열어 `PATH`를 다시 읽게 합니다.
- `cannot open output file ..\\bcgui.exe: Permission denied`: 실행 중인 `bcgui.exe`를 종료한 뒤 다시 빌드합니다.
- `symbol ... not defined` (NASM): 새 상수·문자열을 추가한 파일에서 `extern`/`%define`을 확인합니다.
- 화면 캡처형 시험 스크립트(`tools/t_*.ps1`)는 개발 PC의 임시 경로를 가정하므로 그대로 쓰지 말고 참고용으로 보세요.

## 실행

"""
s = s[:a] + build + s[b:]

# ---- PRD table
a = s.index("## PRD 대비 구현 현황")
b = s.index("## 측정한 성능")
prd = """## PRD 대비 구현 현황

구현 ✅ / 일부 🟡 / 미구현 ❌. 영역 코드: FC 폴더 비교, TC 텍스트 비교, TB 표 비교, HX 헥스 비교, PC 이미지 비교, MD 미디어 비교, VR 버전 비교, RG 레지스트리 비교, EX 외부 도구, TM 텍스트 병합, FM 폴더 병합, SY 동기화, VF 가상 파일 시스템(원격·특수 저장소), AR 압축 파일, SN 스냅샷, AU 자동화, IN 통합, CU 사용자 정의.

| 영역 | 대상 | 상태 | 비고 |
| --- | --- | --- | --- |
| FC-01 FC-02 FC-03 FC-07 | 폴더 비교 세션: 트리 스캔, 비교 기준, 필터, 결과 처리 | ✅ | 기준: 크기·시각·내용·CRC32·속성 (실행 파일 버전 값은 버전 비교 세션에서 확인). 이름 제외 + 크기/날짜 필터 |
| FC-04 FC-06 | 폴더 비교 부가 기능 | ❌ | 이번 구현 범위에 포함하지 않음 |
| FC-05 | 폴더 비교 보고서 | 🟡 | HTML 보고서 + 파일별 상세 보고서 링크 ✅. 인쇄용 레이아웃 ❌ |
| TC-01 TC-03 TC-04 | 텍스트 비교: 줄 비교·정렬, 수동 정렬, 구문 강조 | ✅ | 키워드 목록 기반의 단순 토크나이저 |
| TC-02 | 텍스트 비교 규칙(무시 옵션) | 🟡 | 대소문자·공백·주석·줄 종결 ✅. 정규식, 페이지 머리글, 열, 수동 선택 ❌ |
| TC-05 TC-06 TC-07 | 텍스트 문서 변환, 클립보드·북마크, 식별자 이름 변경 인식 | ❌ | Word/PDF 변환, 클립보드·북마크, 이름 변경 식별자. (찾기/바꾸기는 텍스트 편집 세션에서 ✅) |
| TB-01 TB-02 TB-03 TB-04 | 표 비교: 파일 형식, 키 매칭, 셀 허용 오차, 열·행 옵션 | 🟡 | CSV/TSV/XLSX ✅, 복합 키, 숫자·날짜 허용 오차 ✅. HTML 표, 열 순서 변경, 여러 시트 선택 ❌ |
| HX-01 | 헥스 비교·편집 | ✅ | 바꾸기는 덮어쓰기(같은 길이)만 지원 |
| PC-01 | 이미지 비교(차이 지도·겹치기 등) | 🟡 | 교체된 색 무시, 썸네일 확대 ❌ |
| MD-01 | 미디어 비교: 오디오 태그·정보 | 🟡 | MP3(ID3v1/v2)·FLAC(Vorbis 주석)만. MP4/OGG 태그 ❌ |
| VR-01 RG-01 | 파일 버전 리소스 비교, 레지스트리 키 비교 | ✅ | 버전: 고정 정보·문자열 리소스. 레지스트리: 키·값 재귀 비교 |
| EX-01 | 외부 도구 위임 | ✅ | 확장자별 명령줄(`%1`·`%2`), 폴더 비교에서 더블클릭/Enter |
| TM-01~05 | 텍스트 병합: 3-way/2-way, 충돌 해결, 전체 우선 채택 | ✅ | |
| TM-06 | 텍스트 병합 부가 기능 | ❌ | 이번 구현 범위에 포함하지 않음 |
| FM-01 FM-02 FM-03 | 폴더 병합: 3개 폴더 판정·해결·출력 | ✅ | 충돌은 텍스트 병합 세션으로 해결. 이진 파일 충돌은 채택 방향을 직접 선택 |
| SY-01 SY-02 SY-03 SY-04 SY-05 | 동기화: 방식, 미리보기, 실행, 파일 작업, 안전장치 | ✅ | SY-04: 복사·삭제·이동·이름 변경·일시중지 ✅, 속성/시각 설정 ❌. 스캔이 불완전하면 동기화를 막음 |
| SY-06 | 파일 시스템 메타데이터 동기화 | ❌ | NTFS ACL, 8.3 별칭 |
| VF-01 | 로컬·네트워크 경로 | ✅ | 로컬·네트워크 드라이브·UNC |
| VF-02 | FTP 서버 비교 | 🟡 | 평문 FTP(WinInet) ✅. SFTP/FTPS ❌ |
| AR-01 SN-01 | 압축 파일·스냅샷 비교 | ✅ | .zip, .bcss 읽기 전용 비교 |
| VF-03~06 AR-02 | 클라우드·SVN·휴대 장치, 기타 압축 형식 | ❌ | 이 환경에서 만들거나 검증할 수 없어 제외 |
| AU-01~05 | 자동화: 세션·워크스페이스 저장, 명령줄, 스크립트 | ✅ | 스크립트 언어: set/echo/run/if/goto/exit |
| IN-01 IN-02 IN-03 | 통합: VCS 도구 연동, 탐색기 메뉴, 끌어놓기 | ✅ | IN-02는 레지스트리 동사 방식(IContextMenu 셸 확장 DLL은 아님) |
| IN-04 IN-05 | 변환 규칙, 소스 제어 통합 | ❌ | 변환 규칙, MSSCCI |
| CU-01 CU-02 | 설정 대화상자, 관리자 정책 | ✅ | 글꼴·색·단축키·외부 도구 / 레지스트리 정책(읽기 코드만, HKLM 실제 차단은 미검증) |
| CU-03 | 사용자 정의 부가 기능 | ❌ | 이번 구현 범위에 포함하지 않음 |
| 비기능 | 성능·안정성·접근성 | 🟡 | 스레드 스캔·동기화, 삭제 전 확인(휴지통), 자동 백업, 유니코드, DPI ✅. 10만 파일 이상 규모는 미측정 |

"""
s = s[:a] + prd + s[b:]
open('README.md', 'w', encoding='utf-8', newline='\n').write(s)
print('ok')

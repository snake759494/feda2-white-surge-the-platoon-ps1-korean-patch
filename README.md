# FEDA 2 화이트 서지 더 플래툰 PS1 한글패치

PS1 일본판 **FEDA2 WHITE SURGE the PLATOON (SLPS-00723)**용 비공식 한국어 패치입니다. 이벤트·캠프·전투 대사와 메뉴, 명령, 병종·특수기·아이템 이름, 미션 조건, 전투 메시지를 모두 한국어로 바꿨습니다. **나레이션과 게임 오버 문장, 타이틀·파일 메뉴, 캠프 이름표, 작전명** 같은 그림 글자도 한글로 다시 그렸습니다. 현재 배포판은 **v1.2 (2026-11-21)**입니다.

[패치 다운로드](https://github.com/snake759494/feda2-white-surge-the-platoon-ps1-korean-patch/releases/latest) · [기술 설명](docs/TECHNICAL.md) · [재빌드](docs/BUILD.md) · [변경 기록](CHANGELOG.md) · [권리 안내](RIGHTS.md)

릴리즈 첨부 파일은 한글패치 **FEDA2_White_Surge_the_Platoon_PS1_KO_v1.2.xdelta**뿐입니다. 저장소에는 제작 소스와 한국어 번역만 공개합니다. 원본·완성 디스크 이미지, 추출한 게임 파일, 일본어 원문, 글꼴 파일, 외부 실행 파일은 포함하지 않습니다. GitHub가 자동으로 만드는 Source code ZIP/TAR는 저장소 소스를 압축한 것이며 게임 파일이 아닙니다.

## 게임 소개 및 대상 버전

『FEDA2 WHITE SURGE the PLATOON』은 야노만이 1997년에 PS1으로 낸 시뮬레이션 RPG로, 맥스 엔터테인먼트가 개발했습니다. 슈퍼 패미컴 『FEDA THE EMBLEM OF JUSTICE』의 후속작입니다. 공국군 혼성 소대 「화이트 서지」를 이끌고 제국과의 전쟁 속 특수 임무에 나섭니다. 캠프에서 동료와 대화하고 HQ의 브리핑을 받은 뒤 출격해, 쿼터뷰 맵에서 소대를 움직이며 싸웁니다. 오프닝에는 실사 영상이 들어 있습니다.

이 패치는 **PS1 일본판 SLPS-00723의 BIN/CUE 이미지(데이터 1트랙)**에 적용합니다. 파일 이름보다 아래 표의 크기와 해시가 일치하는지가 중요합니다.

## 적용할 원본

| 항목 | 값 |
| --- | --- |
| 게임 ID | SLPS-00723 |
| 원본 형식 | 수정되지 않은 일본판 BIN/CUE (트랙 1개, MODE2/2352) |
| 원본 BIN 크기 | 749,227,248 바이트 |
| **원본 BIN MD5** | `ba534cd2e7acaabbfbe5ec917110001e` |
| 원본 BIN SHA-1 | `d0cfd504823cb0ec347a15a9640b802cc573e02e` |
| 원본 BIN SHA-256 | `c5028c3150e05c37dc36f55903936f79dc193180f18442407a5380ad42a878fc` |
| xdelta 파일 크기 | 1,562,847 바이트 |
| xdelta SHA-256 | `dc5d496160b46265fd23495330d3694512079c3f84c8b7546272c9ecb51c5f54` |
| 적용 결과 BIN 크기 | 749,227,248 바이트 (원본과 같음) |
| 적용 결과 BIN SHA-1 | `769d6814d97f7785a9b4b272e2e01baec2e8fc3c` |
| 적용 결과 BIN SHA-256 | `c0182028e0e23b3197dd26a959fa6cb0d1a6240b894d1940ccffecf49c843e2b` |

원본 게임 파일은 사용자가 직접 준비해야 합니다.

## 패치 적용 방법

### Windows에서 원본 확인

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath '.\FEDA 2 - White Surge the Platoon (Japan).bin'
```

위 표와 다르면 적용을 중단하세요. CHD, PBP, ECM, 압축 이미지에는 적용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `FEDA2_White_Surge_the_Platoon_PS1_KO_v1.2.xdelta`를 받습니다.
2. xdelta3 패치를 지원하는 도구에서 **Apply Patch** 기능을 엽니다.
3. **Patch**에는 xdelta 파일을, **Source File**에는 해시가 일치하는 원본 `.bin`을 선택합니다.
4. **Output File**에는 새 파일 이름을 지정합니다(예: `FEDA 2 - White Surge the Platoon (Korean).bin`).
5. 원본 `.cue`를 복사해 이름을 바꾸고, `FILE "..."` 줄을 결과 BIN 파일 이름으로 고칩니다.

```
FILE "FEDA 2 - White Surge the Platoon (Korean).bin" BINARY
  TRACK 01 MODE2/2352
    INDEX 01 00:00:00
```

xdelta 자체는 [공식 프로젝트](https://github.com/jmacd/xdelta)를 참고하세요.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s '.\FEDA 2 - White Surge the Platoon (Japan).bin' '.\FEDA2_White_Surge_the_Platoon_PS1_KO_v1.2.xdelta' '.\FEDA 2 - White Surge the Platoon (Korean).bin'
```

해시를 자동으로 검사하고 CUE까지 만들어 주는 도구도 있습니다. Python 3과 xdelta3가 필요하며, 같은 이름의 출력 파일이 이미 있으면 덮어쓰지 않습니다.

```powershell
python tools/apply_release.py --xdelta '.\xdelta3.exe' --source '.\FEDA 2 - White Surge the Platoon (Japan).bin' --patch '.\FEDA2_White_Surge_the_Platoon_PS1_KO_v1.2.xdelta' --output '.\FEDA 2 - White Surge the Platoon (Korean).bin'
```

### 실행

에뮬레이터에서 결과 `.cue`를 여세요. 원본판의 세이브 스테이트는 불러오지 마세요(실행 파일과 글꼴 배치가 다릅니다). 메모리 카드 세이브는 형식을 바꾸지 않았습니다. 게임 자체 글꼴에 한글을 넣었으므로 BIOS 종류와 관계없이 한글이 나옵니다.

## 작업 내용과 범위

| 구분 | 작업량 및 내용 |
| --- | --- |
| 이벤트·막간 대사 | TXTDATA 대본 73블록, 2,912줄 |
| 캠프 대화 | 캠프 대본 8블록의 고유 문장 2,751줄 |
| 전투 대사 | BATMSG 대본 8블록, 581줄 |
| 실행 파일 문자열 | 401종 — 메뉴·명령(공격·대기·특수기·아이템), 병종·특수기·아이템 이름, 미션 조건, 상태 표시(경상·중상), 시스템 메시지 |
| 글꼴 | 번역에 쓰인 한글 963자. 메뉴용 고정 글꼴 + 장면별 글꼴에 나눔스퀘어 네오로 그림 |
| 그림 글자 | 나레이션·게임 오버 문장 33장, 엔딩 크레딧 역할명, 타이틀·파일 메뉴 문구, 캠프 장소·인물 이름표 25종, 작전명 14종(결과 화면 포함), 상태창 「무장」 라벨 |

게임 글꼴은 Shift-JIS 한자 코드를 글리프 표로 찾아 그리는 구조라서, 한글 글자마다 한자 코드를 하나씩 배정하고 그 칸의 글리프를 바꿨습니다. 출력 루틴은 고치지 않았습니다. 자세한 내용은 [docs/TECHNICAL.md](docs/TECHNICAL.md)를 참고하세요.

### 번역 원칙

- 기계 번역 없이 문맥을 보고 직접 번역했습니다.
- 대사창 폭(한 줄 20자)과 한 창 3줄 안에 들어가게 줄을 나눴습니다. 실행 파일 문자열은 원문 자리 크기 안에 넣었습니다.
- 그림 글자의 문장은 갈무리 글꼴을 늘리거나 줄이지 않은 원래 크기로 쓰고, 굵게 하기 같은 효과를 넣지 않았습니다. 이름표·작전명은 원본의 외곽선·기울임에 맞춰 그렸습니다.

### 번역하지 않은 것

- 음성, 오프닝 실사 영상
- 원래 영문인 그림 글자(PUSH START BUTTON, NOW LOADING, MISSION END, GAME OVER, SECTION/BATTLE, MISSION CONDITION, OPM, HP/MP 등)
- 화면에 나오지 않는 대본 속 화자 주석, 개발용 낙서 그림

## 알려진 한계

- 모든 대사를 화면으로 직접 확인하지는 못했습니다. 타이틀, 기록 불러오기, 캠프(HQ·병원·막사·모닥불·타이탄II 대화), HQ 브리핑, 첫 두 전투(대사·미션 조건·명령 메뉴·상태창·전투 연출·아이템), 결과 화면, 게임 오버 나레이션은 DuckStation에서 확인했습니다. 결과 화면은 메모리를 고쳐 전투를 빨리 끝내고 확인했습니다.
- 출격 전 편성·무장·창고 화면은 초반에 나오지 않아 게임 화면으로 확인하지 못했습니다(문자열은 번역함). 엔딩도 게임 안에서는 보지 못했습니다.
- 실기에서의 동작은 확인하지 못했습니다. 칸을 넘치거나 일본어가 남은 곳이 있으면 이슈로 알려 주세요.

## 저장소 구성

| 경로 | 내용 |
| --- | --- |
| `tools/build.py` | 전체 빌드(글꼴 배정, 대본·실행 파일 문자열·그림 글자 교체, 디스크에 다시 씀) |
| `tools/` | `script.py`·`check.py`·`camp.py` 대본 형식과 검사, `hg.py`·`fonts.py` 한글 코드와 글리프, `narr.py`·`narrband.py`·`title.py`·`labels.py`·`tim.py` 그림 글자, `iso.py`·`disc.py`·`cdsec.py` 디스크 읽기·쓰기(EDC/ECC), `extract.py` 디스크 파일 추출, `apply_release.py` 해시 검사 후 적용, `emu.py`·`ctl.py` 에뮬레이터 조작 |
| `text/ko/` | 대사 번역 (`txtNN` 이벤트, `batNN` 전투, `camp` 캠프, `narr` 그림 문장) |
| `text/exe_ko.tsv` | 실행 파일 문자열 번역(위치·원문 바이트 수) |
| `docs/` | 기술 설명, 재빌드 방법, 글꼴 출처 |

권리 관련 내용은 [RIGHTS.md](RIGHTS.md)를 참고하세요.

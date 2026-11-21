# 재빌드

## 준비물

```
<이 저장소>/
  fonts/NanumSquareNeo-cBd.ttf  fonts/NanumSquareNeo-eHv.ttf
  fonts/Galmuri9.ttf  fonts/Galmuri11.ttf  fonts/Galmuri14.ttf
```

- Python 3.13, `Pillow`, `numpy`, `scipy`
- 글꼴 출처는 `docs/FONT_CREDITS.md`
- xdelta3 (배포 파일을 만들 때만)

## 빌드

저장소 폴더에서 실행합니다. 원본 BIN은 어디에 두어도 됩니다.

```powershell
python tools/build.py "..\FEDA 2 - White Surge the Platoon (Japan).bin" "..\FEDA 2 - White Surge the Platoon (Korean).bin"
```

`build.py`는 원본 BIN을 결과 경로로 복사한 뒤 바뀐 파일의 섹터를 다시 씁니다(EDC/ECC 재계산). 결과 BIN의 SHA-256이 `release_manifest.json`의 `output_bin_sha256`과 같아야 합니다. CUE는 원본 CUE를 복사해 `FILE` 줄만 고치면 됩니다.

## 배포 파일

```powershell
xdelta3 -e -f -s "FEDA 2 - White Surge the Platoon (Japan).bin" "FEDA 2 - White Surge the Platoon (Korean).bin" FEDA2_White_Surge_the_Platoon_PS1_KO_v1.2.xdelta
```

## 번역 수정

- 대사: `text/ko/txtNN.txt`(이벤트·막간, TXTDATA 블록 NN), `batNN.txt`(전투, BATMSG 블록 NN), `camp.txt`(캠프 대화). 원본 블록에서 화면에 나오는 문장을 순서대로 하나씩 대응시킵니다. `/`는 줄바꿈, `$` 로 시작하는 코드는 원문의 제어 코드입니다. 한 줄 20자, 한 창 3줄까지입니다.
  - `@이름` 줄은 화자 표시라 무시합니다. `=` 은 화면에 나오지 않는 주석 줄이라 원문 그대로 둔다는 뜻입니다.
  - `camp.txt`는 캠프 블록 8개에서 같은 문장을 한 번만 번역합니다(첫 등장 순서).
- 실행 파일 문자열: `text/exe_ko.tsv`의 `오프셋(16진, 쉼표로 여러 곳)<TAB>원문 바이트 수<TAB>번역`. 번역은 원문 자리(4바이트 정렬 여유 포함)에 들어가야 합니다. `/`는 줄바꿈입니다.
- 나레이션 그림: `text/ko/narr.txt` (`#그림번호 모드` 뒤에 줄 단위 번역).
- 그림 글자: 캠프 이름표·작전명 `tools/labels.py`, 타이틀·파일 메뉴 `tools/title.py`.

## 화면 확인

`tools/emu.py`는 DuckStation을 창 밖에 띄우고 GDB 서버(포트 2353)로 메모리를 읽고 쓰며, 창 메시지로 키를 보내고 스크린샷을 찍습니다. 실행 파일 경로는 `duck/feda_emu.exe`(DuckStation 포터블 폴더, GDB 서버를 켠 설정)입니다. `tools/ctl.py "wait 3; press o; eshot a.png"`처럼 실행 중인 에뮬레이터에 명령을 보냅니다.

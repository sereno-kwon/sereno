# SERENO

개인 홈페이지. 정적 사이트(index.html 하나)이며 Vercel 또는 GitHub Pages로 배포합니다.

- `index.html` 페이지 본문
- `photos/` 갤러리 이미지와 `photos.json` (자동 생성, 직접 편집하지 않음)
- `scripts/sync_photos.py` 구글 드라이브 "SERENO Photography" 폴더에서 받은 원본을 리사이즈하고 목록을 만듭니다

사진 추가: 구글 드라이브의 SERENO Photography 폴더에 파일을 넣으면 예약 작업이 주기적으로 반영합니다.
파일 이름이 캡션이 됩니다. 예: `2026-09 남양성모성지.jpg` → 캡션 "남양성모성지", 날짜순 정렬.

## Writing

원고는 노션 데이터베이스 **Writing**에서 씁니다. 속성 "상태"를 **발행**으로 바꾸면 예약 작업이 가져옵니다.
가져온 글은 `writing/src/<슬러그>.md`로 저장되고, `scripts/build_writing.py`가 `writing/index.json`과 글 페이지(`writing/<슬러그>.html`)를 만듭니다.
본문 이미지는 구글 드라이브 **SERENO Writing** 폴더에 `<슬러그>-<번호>.jpg` 이름으로 넣습니다 (예: `north-europe-1.jpg`). 동기화 때 `scripts/sync_writing_images.py`가 `writing/img/`로 옮기고, 글 본문의 같은 이름 자리에 들어가거나(노션에서 가져온 이미지 자리) 자리가 없으면 글 끝에 순서대로 붙습니다. `writing/src/`와 `writing/img/` 외의 `writing/` 파일은 자동 생성됩니다.

## 언어

홈은 KO / EN / JA 전환이 되며, 글도 세 언어로 제공됩니다.
- 한국어 원문: `writing/src/<슬러그>.md`
- 영어 / 일본어: `writing/src/en/<슬러그>.md`, `writing/src/ja/<슬러그>.md`. 앞머리 `translated: auto`는 동기화 때 자동 번역된 것, `manual`은 노션에서 직접 쓴 번역입니다.
- 직접 번역을 올리려면 노션 Writing에 페이지를 만들고 "언어"를 EN 또는 JA로, "원문 슬러그"에 원문 글의 슬러그를 적고 상태를 발행으로 바꿉니다. 자동 번역을 대체합니다.
- 생성 결과: `writing/<슬러그>.html`, `writing/en/…`, `writing/ja/…`, 언어별 목록 `writing/index.html`, `writing/en/index.html`, `writing/ja/index.html`

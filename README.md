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
본문 이미지는 `writing/img/`에 저장됩니다. `writing/src/`와 `writing/img/` 외의 `writing/` 파일은 자동 생성됩니다.

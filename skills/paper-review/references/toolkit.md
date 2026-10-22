# 로컬 실행 도구

이 스킬과 함께 공개된 Paper Review Kit 저장소를 사용한다. 설치 위치를 추정하지 말고 사용자가 제공한 저장소나 현재 작업 공간의 README.md를 확인한다. Python 도구는 스킬 폴더가 아닌 저장소 루트에 있다.

1. 공개 PDF의 페이지 텍스트는 `reviewkit.py extract PDF OUTPUT`으로 추출한다. OCR·그림 해석 기능이 아니다.
2. 저장소의 `schema.json`에 맞는 evidence.json과 review.md를 작성한다. 핵심 주장에 `[claim:C1]` 형식을 붙인다.
3. `reviewkit.py check REVIEW_FOLDER`로 구조를 검사한다. 원문 대조는 별도로 수행한다.
4. `reviewkit.py bibliography REVIEW_FOLDER`는 중복 후보를 출력하며 버전을 합치지 않는다.
5. `reviewkit.py export REVIEW_FOLDER --format html obsidian graph`로 선택한 결과만 출력한다. 기존 결과 교체는 명시적인 `--force`가 필요하다.
6. `mark`와 `resume`은 진행 기록용이다. 파일 존재나 상태값은 과학 검증 증거가 아니다. 입력이 바뀌면 stale 항목을 다시 확인한다.

HTML 렌더러는 신뢰하는 로컬 Markdown과 demo.html을 대상으로 한다. 원문 문서의 HTML·스크립트를 그대로 저작 파일에 옮기지 않는다. LoRA build_example.py와 build_slides.py는 특정 예제의 재생성 코드다. 다른 논문 내용을 자동 생성하는 것으로 설명하지 않는다.

별도 paper-review-site 또는 interactive-slides가 설치돼 있으면 추가 출력에 사용한다. 없어도 기본 HTML 출력은 가능하다. 훅은 수동 실행 가능한 읽기 전용 어댑터이며 호스트에 자동 등록되어 있지 않다.

# jira-to-md-downloader 스펙

jira.cubrid.org의 이슈를 조회해 로컬에 Markdown 파일로 저장하는 CLI 도구.
[md-to-jira-uploader](https://github.com/vimkim/md-to-jira-uploader)에서 아이디어를 얻어 반대로 download 도구를 개발.
## 1. 목표

- 하나 이상의 Jira 이슈 ID를 입력받아, 각 이슈당 한 개의 `.md` 파일을 생성한다.
- 변환 대상은 **summary**, **description**, **comments** 세 필드로 한정한다.
- 파일명은 이슈 ID와 동일하게 한다 (`{ID}.md`).

## 2. 비목표 (이번 범위 외)

- Assignee / Reporter / Status / Labels 등 기타 필드
- 첨부파일·인라인 이미지 다운로드 및 경로 재작성
- Jira Cloud (ADF 포맷) 대응
- 병렬 처리, rate-limit 핸들링 등 고급 기능

## 3. 스택

- **언어**: Python 3.x
- **패키지 매니저**: `uv`
- **HTTP 클라이언트**: `requests`
- **마크업 변환**: `pandoc` (subprocess 호출, `-f jira -t gfm`)

## 4. 인증

환경변수 기반 basic auth. 참고 repo와 동일.

| 변수명          | 설명                                          |
| --------------- | --------------------------------------------- |
| `JIRA_URL`      | Jira base URL (예: `https://jira.cubrid.org`) |
| `JIRA_USER`     | 사용자명                                      |
| `JIRA_PASSWORD` | 비밀번호                                      |

셋 중 하나라도 누락 시 즉시 에러로 종료한다.

## 5. CLI 인터페이스

```
jira-to-md-download [ISSUE_ID...] [-f FILE] [-o OUTPUT_DIR]
```

| 옵션 / 인자      | 기본값         | 설명                                        |
| ---------------- | -------------- | ------------------------------------------- |
| `ISSUE_ID...`    | —              | 1개 이상의 이슈 ID를 위치 인자로 직접 지정  |
| `-f`, `--file`   | `./issues.txt` | 이슈 ID 목록 파일 (위치 인자 없을 때만 사용) |
| `-o`, `--output` | `./out/`       | 출력 디렉토리 (없으면 자동 생성)            |

**우선순위**: 위치 인자가 하나라도 있으면 `-f`는 무시한다.

## 6. 입력 파일 포맷 (`issues.txt`)

- UTF-8 텍스트.
- 줄 단위로 이슈 ID 하나씩.
- 각 줄은 `strip()` 후 처리.
- 다음은 **무시**한다:
  - 빈 줄
  - `#`으로 시작하는 줄 (주석)
- ID 형식은 고정된 정규식으로 검증하지 않는다. 비어있지 않은 토큰이면 그대로 API에 전달한다.
  (예: `TOOLS-4888`, `APIS-1079`, `CUBRID-26725` 등 모두 허용)

**예시**
```
# 릴리스 노트용 이슈들
TOOLS-4888
APIS-1079

CUBRID-26725
```

## 7. 처리 흐름

이슈 ID 한 개당:

1. `GET {JIRA_URL}/rest/api/2/issue/{ID}` 호출 (basic auth). `fields` 파라미터는 붙이지 않는다: jira.cubrid.org의 http/https 리다이렉트가 쿼리를 다시 인코딩해 쉼표가 깨진다.
2. 응답 파싱:
   - `fields.summary` (문자열, 필수)
   - `fields.description` (문자열 또는 `null`)
   - `fields.comment.comments` (작성자 `author.displayName`, 작성 시각 `created`, 본문 `body`, 공개 범위 `visibility.value`)
3. description이 `null` 이거나 빈 문자열이면 빈 본문으로 처리.
4. description(Jira wiki markup)을 pandoc으로 변환:
   `pandoc -f jira -t gfm` (stdin → stdout). 댓글 본문도 같은 방식으로 변환하되, 댓글 머리글 아래에 놓이도록 `--shift-heading-level-by=3`으로 제목을 세 단계 낮춘다.
5. 아래 구조로 `{OUTPUT_DIR}/{ID}.md` 에 저장 (이미 존재하면 **덮어쓰기**):

   ```markdown
   # {summary}

   {pandoc으로 변환된 description}

   ## Comments

   ### {작성자} · {작성 시각 YYYY-MM-DD HH:MM}[ · restricted to {공개 범위}]

   {pandoc으로 변환된 댓글 본문}
   ```

   댓글이 없으면 Comments 절을 쓰지 않는다. 응답에 실린 댓글이 전체 수보다 적으면 빠진 개수를 끝에 적는다.

6. 성공 로그 출력.

## 8. 에러 처리

다음 상황은 **경고 출력 후 다음 ID로 계속 진행**:

- HTTP 404 (이슈 없음 / 권한 없음)
- HTTP 401 / 403
- HTTP 5xx
- 네트워크 타임아웃
- pandoc 변환 실패
- description 파싱 실패

다음 상황은 **즉시 종료**:

- 필수 env 변수 누락
- pandoc 바이너리를 찾을 수 없음
- 입력 파일(`-f` 지정 또는 기본 `issues.txt`) 없음 & 위치 인자도 없음
- 출력 디렉토리 생성 실패

## 9. 출력 정책

- 파일명: `{ID}.md` (ID 원본 그대로, 대소문자 변경 없음)
- 인코딩: UTF-8, LF 개행
- 기존 파일: 무조건 덮어쓰기 (플래그 없음)

## 10. 실행 종료 요약

stdout에 처리 결과 요약 출력:

```
✓ TOOLS-4888  → ./out/TOOLS-4888.md
✓ APIS-1079   → ./out/APIS-1079.md
✗ CUBRID-9999 → 404 Not Found (skipped)

2 succeeded, 1 failed.
```

exit code:
- `0`: 모두 성공
- `1`: 하나 이상 실패했지만 일부는 성공
- `2`: 치명적 오류로 조기 종료 (env 누락, pandoc 없음 등)

## 11. 프로젝트 구조 (예정)

```
jira-to-md-downloader/
├── SPEC.md              # 본 문서
├── README.md
├── pyproject.toml       # uv 프로젝트 설정
├── .envrc.example
├── issues.txt.example
└── src/
    └── jira_to_md_downloader/
        ├── __init__.py
        ├── __main__.py  # CLI 엔트리
        ├── cli.py       # 인자 파싱
        ├── jira.py      # API 호출
        ├── convert.py   # pandoc 래퍼
        └── io.py        # 입력 파일 파싱 / 출력 파일 쓰기
```

## 12. 향후 확장 아이디어

- 첨부파일·인라인 이미지 다운로드 및 경로 재작성
- labels 등 추가 필드 옵션
- Jira Cloud (ADF) 대응
- JQL 기반 배치 다운로드 (`--jql "project = TOOLS AND ..."`)
- 병렬 처리 (`--concurrency N`)

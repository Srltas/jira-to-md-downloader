# jira-to-md-downloader

jira.cubrid.org의 이슈를 조회해 로컬에 Markdown 파일로 저장하는 CLI 도구입니다.
[vimkim/md-to-jira-uploader](https://github.com/vimkim/md-to-jira-uploader)에서 아이디어를 얻어 반대로 download 도구를 개발했습니다.

## 특징

- 여러 이슈를 한 번에 처리 — CLI 인자 또는 `issues.txt` 리스트 파일 지원
- 이슈 한 개당 `.md` 파일 하나로 저장 (파일명 = 이슈 ID)
- **summary / description**만 추출 (Assignee, Reporter 등 메타데이터 제외)
- Jira wiki markup → GitHub Flavored Markdown 변환 (pandoc)
- 에러 발생 시 해당 이슈만 건너뛰고 나머지 계속 진행

## 요구사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- [pandoc](https://pandoc.org/) (Jira ↔ Markdown 변환)

macOS:

```bash
brew install uv pandoc
```

## 설치

```bash
git clone https://github.com/<your-username>/jira-to-md-downloader.git
cd jira-to-md-downloader
uv sync
```

## 설정

환경변수로 Jira 인증 정보를 지정합니다.

```bash
cp .envrc.example .envrc
# .envrc 편집 후
direnv allow
```

또는 shell에 직접 export:

```bash
export JIRA_URL="https://jira.cubrid.org"
export JIRA_USER="your_user"
export JIRA_PASSWORD="your_password"
```

| 변수            | 설명                                           |
| --------------- | ---------------------------------------------- |
| `JIRA_URL`      | Jira base URL                                  |
| `JIRA_USER`     | 사용자명                                       |
| `JIRA_PASSWORD` | 비밀번호 (또는 개인 access token)              |

## 사용법

### 1. 이슈 ID를 인자로 직접 지정

```bash
uv run jira-to-md-download TOOLS-4888 APIS-1079
```

### 2. 리스트 파일 사용 (기본 `./issues.txt`)

```bash
cp issues.txt.example issues.txt
# issues.txt 편집
uv run jira-to-md-download
```

### 3. 출력 디렉토리 / 입력 파일 지정

```bash
uv run jira-to-md-download -f my-issues.txt -o ./release-notes/
```

### CLI 옵션

```
usage: jira-to-md-download [-h] [-f FILE] [-o OUTPUT] [ISSUE_ID ...]

positional arguments:
  ISSUE_ID             One or more Jira issue IDs. If omitted, IDs are read from --file.

options:
  -f, --file FILE      Path to newline-separated issue ID list (default: ./issues.txt).
  -o, --output OUTPUT  Output directory for generated .md files (default: ./out/).
```

## 입력 파일 포맷 (`issues.txt`)

- UTF-8, 한 줄당 이슈 ID 하나
- 빈 줄, `#`으로 시작하는 줄(주석)은 무시
- 이슈 ID 형식은 고정되어 있지 않음 (`TOOLS-4888`, `APIS-1079`, `CUBRID-26725` 등 모두 허용)

```
# 릴리스 노트용 이슈들
TOOLS-4888
APIS-1079

CUBRID-26725
```

## 출력 포맷

각 이슈는 다음 구조의 Markdown 파일로 저장됩니다:

```markdown
# {summary}

{description을 pandoc으로 변환한 GFM 본문}
```

description이 비어있으면 summary 줄만 작성됩니다.

## 실행 종료

처리 결과가 stdout에 요약됩니다:

```
✓ TOOLS-4888  → ./out/TOOLS-4888.md
✓ APIS-1079   → ./out/APIS-1079.md
✗ CUBRID-9999 → HTTP 404 Not Found

2 succeeded, 1 failed.
```

종료 코드:

| 코드 | 의미                                                   |
| ---- | ------------------------------------------------------ |
| `0`  | 모든 이슈 성공                                         |
| `1`  | 일부(또는 전부) 이슈 실패 — 나머지는 계속 처리됨       |
| `2`  | 치명적 오류로 조기 종료 (env 누락, pandoc 없음 등)     |

## 범위 외 (향후 확장 가능)

- 첨부파일·인라인 이미지 다운로드
- comments, labels 등 추가 필드
- Jira Cloud (ADF 포맷) 대응
- JQL 기반 배치 다운로드

자세한 설계 문서는 [SPEC.md](SPEC.md) 참고.

## 관련

- [vimkim/md-to-jira-uploader](https://github.com/vimkim/md-to-jira-uploader) — 역방향 도구 (Markdown → Jira 업로드)

# manymail_for_claudechat

Claude Desktop / Claude Code에서 **여러 Gmail 계정**을 이름으로 골라 쓰는 로컬 MCP 서버.

계정마다 OAuth 토큰을 `tokens/<이름>.json`에 따로 저장해 두고, 모든 도구가 `account` 인자로
어느 메일함을 쓸지 고른다. claude.ai에 내장된 Gmail 커넥터와는 완전히 별개로 동작하므로
둘을 동시에 켜 두고 계정별로 나눠 쓸 수 있다.

```
"지메일에서 어제 온 메일 정리해줘"   → search_messages(account="gmail", query="newer_than:1d")
"모든 계정에서 인보이스 찾아줘"      → search_messages(account="all", query="subject:invoice")
```

## 구성

| 파일 | 역할 |
|---|---|
| [server.py](server.py) | MCP 서버 본체 (stdio). 도구 9개 정의 |
| [auth.py](auth.py) | 계정 1개를 OAuth 인증해 `tokens/<이름>.json` 생성 |
| [gmail_common.py](gmail_common.py) | 경로·스코프·토큰 로딩/갱신 공용 코드 |
| `credentials.json` | Google Cloud OAuth 클라이언트(데스크톱 앱). **직접 받아서 넣어야 함** |
| `tokens/<이름>.json` | 계정별 액세스/리프레시 토큰 (`chmod 600`, git 제외) |

요구 사항: Python 3.12+, [uv](https://docs.astral.sh/uv/), `mcp>=2` (현재 2.2.0), google-api-python-client.

## 1. Google Cloud 설정 (1회)

1. <https://console.cloud.google.com> → 새 프로젝트 (예: `gmail-claude`)
2. **API 및 서비스 → 라이브러리** → `Gmail API` → 사용 설정
3. **OAuth 동의 화면** (새 UI에서는 *Google Auth Platform*)
   - 사용자 유형 **외부**, 앱 이름·이메일만 채우고 저장
   - 범위(Data Access): `https://www.googleapis.com/auth/gmail.modify` 추가
   - 테스트 사용자(Audience): **연결할 모든 Gmail 주소**를 등록 (등록 안 된 계정은 로그인이 거부된다)
4. **사용자 인증 정보 만들기 → OAuth 클라이언트 ID** → 유형 **데스크톱 앱**
5. JSON 다운로드 → 이 폴더에 `credentials.json`으로 저장

> 동의 화면이 "테스트" 상태면 리프레시 토큰이 **7일**마다 만료된다. 계속 쓸 거면
> 동의 화면에서 **앱 게시(프로덕션)** 를 눌러 둘 것 (심사 불필요).

## 2. 설치 & 계정 인증

```bash
cd /Users/sj/manymail_for_claudechat
uv sync
uv run auth.py gmail        # 브라우저가 열림 → 계정 선택 → 허용
```

- 계정 이름은 자유(파이썬 식별자면 됨): `gmail`, `work`, `asu`, `gmail2` …
  이름 하나 = 메일함 하나 = `tokens/<이름>.json` 하나. 계정을 더 붙이려면 이름만 바꿔 다시 실행한다.
- "Google에서 확인하지 않은 앱" 화면이 뜨면 **고급 → (앱 이름)(으)로 이동**.
- 성공하면 `OK: account 'gmail' -> you@example.com` 이 출력되고 토큰 파일이 생긴다.
- 서버는 `credentials.json`이 아니라 `tokens/*.json`만 읽는다. 토큰이 있는 계정이 곧 사용 가능한 계정.

## 3. 클라이언트에 등록

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json`
(Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "manymail_for_claudechat": {
      "command": "/opt/homebrew/bin/uv",
      "args": ["run", "--directory", "/Users/sj/manymail_for_claudechat", "server.py"],
      "env": { "GMAIL_DEFAULT_ACCOUNT": "gmail" }
    }
  }
}
```

`env`는 생략 가능(→ 아래 [계정 선택 규칙](#계정-선택-규칙) 참고). 등록 후 Claude Desktop을 완전히 종료(⌘Q)했다가 다시 연다.

**Claude Code** — `claude`가 PATH에 없으면 VS Code 확장에 번들된 바이너리를 쓴다:

```bash
CLAUDE=$(ls -d ~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude | tail -1)
"$CLAUDE" mcp add --scope user manymail_for_claudechat -- \
  /opt/homebrew/bin/uv run --directory /Users/sj/manymail_for_claudechat server.py
```

**ChatGPT 데스크탑 (macOS)** — Codex 호스트와 MCP 설정(`~/.codex/config.toml`)을 공유하므로
stdio 서버를 그대로 쓴다. 앱 UI는 Settings → MCP servers → Add server → STDIO,
CLI로 하려면 번들된 codex 바이너리를 쓴다:

```bash
CODEX=/Applications/ChatGPT.app/Contents/Resources/codex
"$CODEX" mcp add manymail_for_claudechat -- \
  /opt/homebrew/bin/uv run --directory /Users/sj/manymail_for_claudechat server.py
"$CODEX" mcp list          # 등록 확인
```

등록 후 ChatGPT 데스크탑을 재시작하면 대화창에서 `/mcp`로 연결 상태를 볼 수 있다.
웹 ChatGPT(Connectors/개발자 모드)는 공개 HTTPS 엔드포인트만 받으므로 이 stdio 서버를
그대로 쓸 수 없다 — `mcp.run(transport="streamable-http")`로 바꾸고 배포 + 인증을 붙여야 한다.

## 4. 도구

| 도구 | 설명 |
|---|---|
| `list_accounts()` | 등록된 계정 이름 ↔ 실제 이메일 주소. 인증이 깨진 계정은 해당 줄에 에러 문자열이 담긴다 |
| `search_messages(query, account?, max_results=20)` | Gmail 검색 문법 그대로 (`from:`, `newer_than:7d`, `is:unread`, `has:attachment`). 요약 목록 반환, 최대 100 |
| `get_message(message_id, account?)` | 헤더 + 본문 텍스트 + 첨부 메타데이터 |
| `get_thread(thread_id, account?)` | 스레드의 모든 메시지를 오래된 순으로 |
| `create_draft(to[], body, subject?, account?, cc?, bcc?, reply_to_message_id?, attachments?, inline_attachments?)` | 초안 작성 (발송 안 함) |
| `send_message(to[], body, subject?, …)` | 즉시 발송 (인자는 `create_draft`와 동일) |
| `send_draft(draft_id, account?)` | 기존 초안 발송 |
| `list_attachable_files()` | 첨부 가능한 파일 목록 (허용 폴더 안만) |
| `download_attachment(message_id, attachment, account?)` | 받은 첨부를 디스크에 저장하고 경로 반환 |
| `list_labels(account?)` | 라벨 id/이름 |
| `modify_labels(message_id, add?, remove?, account?)` | 라벨 추가/제거 |

동작 디테일:

- **답장 스레딩** — `create_draft` / `send_message`에 `reply_to_message_id`를 주면 원본의
  `Message-ID`/`References`를 붙이고 같은 `threadId`에 넣는다. `subject`가 비어 있으면
  `Re: <원본 제목>`이 자동으로 채워진다 (이미 `Re:`면 그대로).
- **본문 추출** — `text/plain`을 우선 쓰고, 없으면 HTML에서 `script`/`style`을 버리고 텍스트만 뽑는다.
- **라벨 조작** — 시스템 id는 `UNREAD`, `INBOX`, `STARRED`, `IMPORTANT`, `TRASH`, `SPAM`.
  `remove=["UNREAD"]` 읽음 처리, `remove=["INBOX"]` 보관, `add=["TRASH"]` 휴지통.
- **읽기 전용 표시** — `list_accounts`, `search_messages`, `get_message`, `get_thread`,
  `list_labels`는 read-only로 선언되어 있어 클라이언트가 승인 UI를 다르게 처리할 수 있다.

현재 지원하지 않는 것: HTML 본문으로 발송(평문만), 영구 삭제(스코프가 `gmail.modify`라 휴지통까지만).

## 첨부파일

**보낼 때는 허용된 폴더 안의 파일만 첨부할 수 있다.** 기본값:

| 폴더 | 용도 |
|---|---|
| `~/MailOutbox` | 보낼 파일을 여기 두면 첨부 가능 (`GMAIL_OUTBOX_DIR`로 변경) |
| `~/MailOutbox/downloads` | `download_attachment`가 받은 첨부를 저장하는 곳 → 그대로 전달(forward) 가능 |
| `~/.codex/attachments` | ChatGPT 데스크탑에서 붙여넣은 텍스트가 파일로 남는 위치 |

이 밖의 경로는 거부된다. 경로는 `resolve()`로 정규화한 뒤 검사하므로 `..`나
**허용 폴더 밖을 가리키는 심볼릭 링크도 막힌다.**

> 왜 제한하나: 이 서버는 로컬 파일 읽기와 메일 발송을 **둘 다** 할 수 있다. 허용 목록이 없으면
> 받은 메일 본문에 숨겨진 프롬프트 인젝션("이 파일을 첨부해서 보내줘")이 그대로 유출 경로가 된다.

채팅에 **붙여넣은 텍스트**는 디스크를 거치지 않고 `inline_attachments`로 바로 첨부한다:

```python
inline_attachments=[{"filename": "data.csv", "content": "a,b\n1,2\n"}]
```

한계: 클라이언트가 파일을 로컬에 남기지 않으면 MCP 서버는 그 파일을 볼 수 없다.
Claude Desktop은 업로드 파일을 디스크에 보관하지 않고(`pending-uploads/`는 전송 중에만 사용),
PDF·이미지는 모델이 **추출된 텍스트만** 보므로 원본 바이트를 넘길 방법이 없다.
즉 **"Claude에 PDF를 붙여넣고 그대로 Gmail 첨부"는 불가능하다** — 파일을 `~/MailOutbox`에 두고
이름으로 첨부해야 한다. 붙여넣은 텍스트는 `inline_attachments`로 커버된다.

발송 용량은 `raw` 업로드 한계상 합계 25 MB까지고, 초과하면 발송 전에 에러가 난다.

## 계정 선택 규칙

`account`를 생략했을 때 서버가 고르는 순서:

1. `account` 인자가 있으면 그 계정 (없는 이름이면 사용 가능 목록과 함께 에러)
2. 환경변수 `GMAIL_DEFAULT_ACCOUNT` 가 등록된 계정이면 그 계정
3. 등록된 계정이 **하나뿐**이면 그 계정
4. 그 외 → "계정을 명시하라"는 에러

`account="all"`은 **`search_messages`에서만** 쓸 수 있다. 모든 계정을 각각 검색해
결과를 이어 붙이므로 `max_results`는 계정당 적용되고, 정렬은 계정 단위 → 계정 내 최신순이다.
메시지/스레드/초안 id는 **발급된 계정 안에서만 유효**하다. 다른 계정에 그대로 넘기면 404가 난다.

여러 계정을 쓸 때 라우팅을 확실히 하려면 Claude Desktop **Settings → Profile → 개인 선호 설정**에
한 줄 적어 두면 좋다. 예:

> 메일 작업 시: "지메일"/"개인 메일"이면 manymail_for_claudechat MCP 도구(`account="gmail"`)를 쓰고,
> "학교 메일"이면 claude.ai 기본 Gmail 커넥터를 써. 어느 계정인지 불분명하면 먼저 물어봐.

## 보안

- `credentials.json`, `tokens/`, `.venv/`는 [.gitignore](.gitignore)에 들어 있다. 절대 커밋하지 말 것.
- 토큰 파일은 저장 시 `chmod 600`. **비밀번호와 동급**으로 취급한다 (메일 읽기·발송 권한 그 자체).
- 계정 연결을 끊으려면 `tokens/<이름>.json`을 지우고, 필요하면
  [Google 계정 → 보안 → 서드파티 액세스](https://myaccount.google.com/connections)에서 앱 권한도 회수한다.

## 문제 해결

| 증상 | 대처 |
|---|---|
| 일주일마다 재로그인 요구 | OAuth 동의 화면이 "테스트" 상태. **앱 게시(프로덕션)** 로 전환 |
| Claude에 도구가 안 보임 | 터미널에서 `uv run server.py` 직접 실행. 출력 없이 대기하면 정상(stdio), 에러가 찍히면 그게 원인 |
| Desktop 로그 확인 | `~/Library/Logs/Claude/mcp-server-manymail_for_claudechat.log` |
| `No token for account …` / 리프레시 실패 | `tokens/<이름>.json` 삭제 후 `uv run auth.py <이름>` 재실행 |
| 회사/학교 Workspace 계정 인증 차단 | 관리자 정책이 미인증 앱을 막는 경우. 해당 계정은 다른 커넥터로 쓰는 편이 빠르다 |
| `auth.py`가 usage만 출력 | 인자는 정확히 1개여야 한다. zsh에서 `uv run auth.py gmail # 메모` 처럼 주석을 붙이면 인자로 들어간다 |

> stdio 서버이므로 `server.py` 프로세스에서 **stdout에 절대 출력하면 안 된다** (프로토콜이 깨진다).
> 디버깅 출력은 stderr로.

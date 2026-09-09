# Mini Git 시스템 기능 및 기술 명세서 (Specification)

이 문서는 현재 구현의 설계 선택을 기록합니다. 과제 원문은 `subject.md`이며,
원문에서 해시 길이나 SHA-1 사용을 강제하지는 않습니다.

---

## 1. 시스템 개요 및 개발 환경

- **시스템명**: Mini Git CLI
- **목적**: 커밋 이력을 DAG(방향성 비순환 그래프) 구조로 관리하고, 직접 구현한 그래프 탐색, 자체 정렬 알고리즘, 역색인(Inverted Index)을 검증하는 분산 버전 관리 시스템 모형 구현.
- **개발 환경**: Python 3.10 이상
- **제약 사항**:
  - Python 내장 정렬 API (`sorted()`, `list.sort()`) 사용 금지.
  - 외부 그래프 라이브러리(NetworkX 등) 사용 금지.
  - 모든 커밋 메타데이터 및 인덱스는 메모리 상에서 관리.

---

## 2. 핵심 데이터 구조 명세

### 2.1 커밋 노드 (`Commit`)
각 커밋은 불변(Immutable) 객체로 다루어지며 다음 필드를 갖습니다.

| 필드명 | 타입 | 설명 |
| :--- | :--- | :--- |
| `hash` | `str` | 커밋 메타데이터와 내부 순번 기반 SHA-1 전체 해시(40자리 16진수). 화면에서만 기본 6자리의 유일한 접두어로 축약. |
| `message` | `str` | 커밋 메시지 (공백 포함 가능) |
| `author` | `str` | 작성자 이름 |
| `timestamp` | `str` | 커밋 생성 시각 (형식: `YYYY-MM-DD HH:MM:SS`) |
| `parents` | `tuple[str, ...]` | 부모 커밋 해시 목록 (`0개`: 최초 커밋, `1개`: 일반 커밋, `2개`: 병합 커밋) |

### 2.2 저장소 및 브랜치 관리 (`Repository`)
- **`commits`**: `dict[str, Commit]` - 커밋 해시를 키로 하는 커밋 노드 저장소.
- **`branches`**: `dict[str, str | None]` - 브랜치 이름을 키로 하고, 해당 브랜치가 가리키는 커밋 해시를 값으로 갖는 해시맵.
- **`head_branch`**: `str` - 현재 활성화된 브랜치 이름 (기본값: `main`).
- **`current_user`**: `str` - 현재 활성화된 작성자 이름.

`Commit.hash`, `parents`, `commits`의 키, `branches`의 값과 역색인에는 전체
해시를 저장한다. 전체 해시가 중복될 때만 내부 순번을 바꿔 재시도한다.
표시용 접두어가 겹치면 표시 길이만 늘리고 저장된 해시는 변경하지 않는다.
정렬 및 PATH의 사전순 동률 처리는 전체 해시를 기준으로 한다.

### 2.3 역색인 데이터 구조 (`InvertedIndex`)
빠른 커밋 검색을 위해 두 가지 인덱스 테이블을 `dict[str, set[str]]` 구조로 유지합니다.

1. **`keyword_index`**: `dict[str, set[str]]`
   - 키: 커밋 메시지를 공백 기준 split 후 `lower()` 정규화한 토큰.
   - 값: 해당 토큰을 포함하는 커밋 해시의 `set`.
2. **`author_index`**: `dict[str, set[str]]`
   - 키: 작성자 이름 (`lower()` 정규화).
   - 값: 해당 작성자가 생성한 커밋 해시의 `set`.

---

## 3. CLI 규칙 및 에러 처리 명세

### 3.1 명령어 문법 및 파싱
- **대소문자 미구분**: 입력된 명령어 키워드는 대소문자를 구분하지 않음 (`init`, `INIT`, `Init` 모두 동등 처리).
- **공백 및 따옴표 처리**: 큰따옴표(`"..."`)로 감싸진 문자열은 하나의 인자로 파싱 (`shlex.split` 방식 구현).
- **옵션 형식**: `--author=<name>`, `--sort-by=date|author` 형태 파싱.
- **옵션 종료**: `SEARCH -- "--author=Bob"`처럼 `--` 뒤의 인자 하나는 옵션이 아닌 메시지 검색어로 처리.
- **커밋 참조**: `PATH`, `ANCESTORS`는 전체 해시 또는 비어 있지 않은 유일한 접두어를 받는다. 해시 문자는 소문자를 사용한다.
- **해시 표시**: COMMIT, LOG, PATH, ANCESTORS, SEARCH에서 저장소 전체 커밋과 구분되는 최소 6자리 접두어를 표시한다. 새 커밋 추가 후 표시 길이가 늘어날 수 있다.
- **조회·표시 비용**: 전체 해시 조회는 평균 O(1), 접두어 조회는 O(V). 표시표 생성은 병합 정렬과 이웃 접두어 비교로 O(V log V), 공간 O(V) (해시 길이 40을 상수로 간주).

### 3.2 에러 메시지 표준
- 잘못된 인자 개수/형식: `Invalid args`
- 존재하지 않는 브랜치: `Unknown branch: <name>`
- 존재하지 않는 커밋 해시: `Unknown commit: <hash>`
- 여러 커밋에 해당하는 접두어: `Ambiguous commit: <hash>`
- 미초기화 저장소 접근: `Repository not initialized`

---

## 4. 명령어 상세 기능 명세

| 명령어 | 형식 | 설명 및 출력 명세 |
| :--- | :--- | :--- |
| `INIT` | `INIT <user_name>` | 저장소를 초기화하고 `main` 브랜치를 생성하며 `current_user`를 설정. |
| `BRANCH` | `BRANCH <branch_name>` | 현재 HEAD 커밋을 가리키는 새 브랜치를 생성. |
| `SWITCH` | `SWITCH <branch_name>` | HEAD를 지정한 브랜치로 이동. |
| `COMMIT` | `COMMIT <message>` | 현재 HEAD를 부모로 하는 새 커밋 노드를 생성하고 역색인을 갱신. |
| `LOG` | `LOG` | 부모 커밋이 자식 커밋보다 먼저 출력되도록 **위상 정렬(Topological Sort)**하여 출력. |
| `LOG` (정렬) | `LOG --sort-by=date\|author` | 타임스탬프 또는 작성자 기준으로 지정한 정렬 알고리즘(Merge Sort)으로 정렬하여 출력. |
| `PATH` | `PATH <commit1> <commit2>` | 무방향 간선 그래프 기준 두 커밋 간 **BFS 최단 경로**를 탐색. (없을 시 `No path`, 동률 시 사전순 최소 경로 선택) |
| `ANCESTORS` | `ANCESTORS <commit_hash>` | 해당 커밋에서 도달 가능한 모든 부모/조상 커밋 목록 탐색 및 출력. |
| `SEARCH` | `SEARCH <keyword>` / `SEARCH --author=<name>` | 역색인 룩업을 활용하여 O(1) 후보 검색 후 결과 출력. |
| `DIFF` *(보너스)* | `DIFF <file1> <file2>` | 두 텍스트 파일 간 줄 단위 추가/삭제/공통 변경사항 비교 출력. |
| `MERGE` *(보너스)* | `MERGE <branch_name>` | 현재 브랜치 HEAD와 대상 브랜치 HEAD 2개를 부모로 하는 Merge Commit 생성. |

---

## 5. 핵심 알고리즘 설계 명세

### 5.1 최단 경로 탐색 알고리즘 (`PATH`)
- **기반 알고리즘**: 너비 우선 탐색 (BFS)
- **그래프 모델**: 커밋 간 `parents` 관계를 양방향(무방향) 간선으로 간주하여 인접 리스트 구축.
- **사전순 Tie-breaking**:
  - 최단 경로의 길이(간선 수)가 동일한 복수의 경로가 발견될 경우, 경로 문자열(`hash1->hash2->...->hashN`)을 비교하여 **사전순으로 가장 작은 경로**를 최종 반환.

### 5.2 커밋 로그 위상 정렬 알고리즘 (`LOG`)
- **요구 조건**: 부모 커밋이 자식 커밋보다 반드시 먼저 출력되어야 함.
- **기반 알고리즘**: Kahn's Algorithm (진입 차수 Indegree 기반 위상 정렬)
- **동률 처리**: 진입 차수가 0인 노드가 여러 개일 경우 생성 타임스탬프(또는 커밋 해시) 오름차순으로 정렬하여 일관된 출력을 보장.

### 5.3 자체 정렬 알고리즘 (`Merge Sort` & `Quick Sort`)
- **제약**: Python 내장 `sorted()`, `list.sort()` 일절 사용 금지.
- **구현 정렬 알고리즘**:
  1. **Merge Sort (병합 정렬)**:
     - 복잡도: $O(N \log N)$ (최악/평균/최선)
     - 특징: **안정 정렬(Stable Sort)**로 비교 키 전체가 같은 원소의 기존 순서를 보장. 날짜 정렬 키는 `(timestamp, hash)`, 작성자 정렬 키는 `(author.lower(), timestamp, hash)`이므로 날짜나 작성자만 같으면 추가 키로 순서를 결정.
  2. **Quick Sort (퀵 정렬)**:
     - 복잡도: 평균 $O(N \log N)$, 최악 $O(N^2)$
     - 특징: 피벗 선택 전략(Median-of-three)을 적용하여 정렬 수행.
- **정렬 성능 비교 모듈** *(보너스)*:
  - 대량의 가상 커밋 데이터를 생성한 후 Merge Sort와 Quick Sort의 수행 시간을 `time.perf_counter()`로 측정하여 비교 분석 리포트 출력.

### 5.4 역색인(Inverted Index) 검색 알고리즘
- **인덱싱**: `COMMIT` 실행 시 커밋 메시지를 소문자로 토큰화하여 `keyword_index`에 등록, 작성자를 `author_index`에 등록.
- **검색**: `SEARCH <keyword>` 요청 시 인덱스 해시맵 룩업 $O(1)$을 수행하여 해당 커밋 해시 집합을 즉시 반환.

### 5.5 Diff 알고리즘 *(보너스)*
- **기반 알고리즘**: LCS(Longest Common Subsequence) 또는 줄 단위 차이 비교 알고리즘.
- **출력 서식**:
  - 공통 줄: `  <line>`
  - 삭제된 줄: `- <line>`
  - 추가된 줄: `+ <line>`

---

## 6. 권장 모듈 및 파일 아키텍처

```text
.
├── main.py                  # CLI 엔트리 포인트 (REPL 실행 루프)
├── subject.md               # 과제 설명 문서
├── SPECIFICATION.md         # (본 문서) 기술 구현 명세서
├── README.md                # 실행 방법 및 구조 설명 문서
│
├── minigit/
│   ├── __init__.py
│   ├── models.py            # Commit 노드 클래스 정의
│   ├── repository.py        # Repository, Branch, HEAD 및 InvertedIndex 관리
│   ├── parser.py            # REPL 인자 파싱 및 따옴표/옵션 처리기
│   │
│   └── algorithms/
│       ├── __init__.py
│       ├── sort.py          # Merge Sort 및 Quick Sort 직접 구현 (표준 API 사용 금지)
│       ├── graph.py         # BFS 최단경로, Kahn 위상정렬, 조상 탐색 알고리즘
│       ├── index.py         # 역색인 구축 및 검색 알고리즘
│       └── diff.py          # 줄 단위 Diff 알고리즘
```

---

## 7. 결과 예시 동기화

실행 인터랙션 예시는 [subject.md](subject.md)의 8번 결과 예시 표준 서식을 완벽하게 준수합니다.

```text
mini-git> init "Alice"
Initialized repository.
Current branch: main
Current user: Alice

mini-git> commit "Initial commit"
[main a1b2c3] Initial commit

mini-git> branch feature
Created branch: feature

mini-git> switch feature
Switched to branch: feature

mini-git> commit "Add login feature"
[feature d4e5f6] Add login feature

mini-git> switch main
Switched to branch: main

mini-git> commit "Add payment feature"
[main g7h8i9] Add payment feature

mini-git> log
commit a1b2c3 (Alice, 2024-01-15 09:00:00) [main]
Initial commit
commit d4e5f6 (Alice, 2024-01-15 09:15:00) [feature]
Add login feature
commit g7h8i9 (Alice, 2024-01-15 09:30:00) [main]
Add payment feature

mini-git> path a1b2c3 g7h8i9
Path: a1b2c3 -> g7h8i9

mini-git> search "login"
Found 1 commit:

- d4e5f6: Add login feature

mini-git> log --sort-by=author
commit a1b2c3 (Alice, 2024-01-15 09:00:00)
Initial commit
commit d4e5f6 (Alice, 2024-01-15 09:15:00)
Add login feature
commit g7h8i9 (Alice, 2024-01-15 09:30:00)
Add payment feature
```

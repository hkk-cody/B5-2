# Mini Git CLI

커밋 메타데이터를 메모리에서 관리하며 Git의 핵심 원리를 연습하는 학습용
프로그램입니다. 파일 내용은 저장하지 않지만, 커밋 그래프와 브랜치, 검색,
정렬을 직접 구현해 실제 Git 내부 구조의 기초를 확인할 수 있습니다.

## 실행 방법

- Python 3.10 이상이 필요합니다.
- 외부 패키지는 사용하지 않습니다.

프로젝트 최상위 폴더에서 다음 명령을 실행합니다.

```bash
python main.py
```

`mini-git>` 프롬프트가 나타나면 명령을 입력합니다. `exit`, `quit`, Ctrl-D로
종료할 수 있습니다. 모든 데이터는 메모리에만 있으므로 프로그램을 종료하면
커밋 기록도 사라집니다.

## 처음 코드를 읽는다면

[실습형 학습 노트](docs/STUDY_WORKBOOK.md)에서 단계별 학습 순서, 실행 가능한
예제, 예상 결과와 해설을 따라가세요. 최신 검색 문법과 성능 개선 원리도 다룹니다.

[Mini Git 초보자용 코드 분석 가이드](docs/CODE_ANALYSIS_GUIDE.md)에서 이
프로젝트에 사용된 Python 문법, 파일별 책임, 명령 실행 흐름, 상태 변화,
알고리즘과 테스트 분석 방법을 실제 코드와 함께 설명합니다.

처음에는 `models → algorithms → repository → parser → main → tests` 순서로
읽는 것을 권장합니다. 각 단계에서 무엇을 확인해야 하는지도 가이드에 정리되어
있습니다.

## 지원 명령

| 명령 | 설명 |
| --- | --- |
| `INIT <user_name>` | 저장소와 `main` 브랜치를 만들고 작성자를 설정합니다. |
| `COMMIT <message>` | 현재 브랜치에 새 커밋을 만듭니다. |
| `BRANCH <branch_name>` | 현재 커밋에서 새 브랜치를 만듭니다. |
| `SWITCH <branch_name>` | 작업할 브랜치를 바꿉니다. |
| `LOG` | 모든 부모가 자식보다 먼저 나오는 전체 로그를 봅니다. |
| `LOG --sort-by=date` | 전체 커밋을 생성 시각 오름차순으로 봅니다. |
| `LOG --sort-by=author` | 전체 커밋을 작성자 오름차순으로 봅니다. |
| `PATH <commit1> <commit2>` | 두 커밋 사이의 최단 경로를 찾습니다. |
| `ANCESTORS <commit_hash>` | 커밋의 모든 부모와 조상을 봅니다. |
| `SEARCH <keyword>` | 메시지의 단어를 역색인으로 검색합니다. |
| `SEARCH --author=<name>` | 작성자를 대소문자 구분 없이 검색합니다. |

명령어와 옵션 이름은 대소문자를 구분하지 않습니다. 공백이 들어간 사용자명,
메시지, 검색어는 큰따옴표로 감쌉니다.

커밋은 내부적으로 전체 SHA-1 해시(40자리)로 식별합니다. 화면에서는 기본
6자리로 줄여 보여 주고, 다른 커밋과 겹치면 구분될 때까지 표시 길이를 늘립니다.
`PATH`, `ANCESTORS`에는 전체 해시 또는 유일하게 구분되는 접두어를 입력할 수
있습니다. 여러 커밋에 해당하면 `Ambiguous commit: <hash>`를 출력합니다.
새 커밋이 추가되어 예전 접두어가 겹치게 되면 `LOG`에서 늘어난 표시를 확인하세요.
축약은 표시 규칙이며 정렬·최단 경로의 동률 비교에는 항상 전체 해시를 사용합니다.

```text
mini-git> init "Alice Kim"
Initialized repository.
Current branch: main
Current user: Alice Kim

mini-git> commit "Initial commit"
[main 3f17a2] Initial commit

mini-git> branch feature
Created branch: feature

mini-git> switch feature
Switched to branch: feature

mini-git> commit "Add login feature"
[feature 92a3c1] Add login feature

mini-git> search "login feature"
Found 1 commit:

- 92a3c1: Add login feature
```

예시 해시는 실행 시각과 커밋 정보에 따라 달라집니다. 여러 단어를 검색하면
모든 단어를 포함한 커밋만 반환합니다. 예를 들어 `SEARCH "login feature"`는
`login`과 `feature`가 모두 있는 메시지를 찾습니다.

옵션처럼 생긴 단어는 `SEARCH -- "--author"` 또는
`SEARCH -- "--author=Bob"`처럼 `--` 뒤에 입력하면 메시지에서 검색합니다.
`SEARCH --author=Bob`은 기존처럼 작성자 검색입니다.

## 과제 평가용 실행 예시

평가자가 CLI 환경에서 주요 기능과 예외 처리를 한눈에 검증할 수 있는 실행 시나리오입니다.

### 1. 빠른 전체 실행 (터미널 일괄 입력)

터미널에서 아래 명령을 그대로 복사해 붙여넣으면 기본 REPL 흐름을 한 번에 실행할 수 있습니다.

```bash
python main.py << 'EOF'
init "Alice Kim"
commit "Initial commit"
branch feature
switch feature
commit "Add login feature"
switch main
commit "Add payment feature"
log
log --sort-by=date
log --sort-by=author
search "login"
search --author="Alice Kim"
exit
EOF
```

---

### 2. 단계별 대화형 평가 시나리오

터미널에서 `python main.py`를 실행한 후 `mini-git>` 프롬프트에 순서대로 입력하며 동작을 확인합니다.  
*(※ 커밋 해시는 실행 시각에 따라 동적으로 생성되므로, `PATH`나 `ANCESTORS` 명령에는 앞서 화면에 출력된 실제 해시를 입력하세요.)*

#### Step 1: 저장소 초기화 및 브랜치 분기 작업
```text
mini-git> init "Alice Kim"
Initialized repository.
Current branch: main
Current user: Alice Kim

mini-git> commit "Initial commit"
[main 3f17a2] Initial commit

mini-git> branch feature
Created branch: feature

mini-git> switch feature
Switched to branch: feature

mini-git> commit "Add login feature"
[feature 92a3c1] Add login feature

mini-git> switch main
Switched to branch: main

mini-git> commit "Add payment feature"
[main 7b4e10] Add payment feature
```

#### Step 2: 커밋 로그 및 정렬 검증
- **기본 `LOG` (위상 정렬)**: 부모 커밋(`Initial commit`)이 항상 자식 커밋들보다 먼저 출력되며, 브랜치 최신 커밋에 `[main]`, `[feature]` 라벨이 표시됩니다.
- **`LOG --sort-by=date`**: 커밋 생성 시각(timestamp) 오름차순으로 정렬됩니다.
- **`LOG --sort-by=author`**: 작성자 이름(대소문자 무관) 오름차순으로 정렬됩니다.

```text
mini-git> log
commit 3f17a2 (Alice Kim, 2026-09-15 02:30:00)
Initial commit

commit 7b4e10 (Alice Kim, 2026-09-15 02:30:02) [main]
Add payment feature

commit 92a3c1 (Alice Kim, 2026-09-15 02:30:01) [feature]
Add login feature

mini-git> log --sort-by=date
(생성 시각 순으로 전체 커밋 출력)

mini-git> log --sort-by=author
(작성자 이름 사전순으로 전체 커밋 출력)
```

#### Step 3: 커밋 그래프 탐색 (PATH, ANCESTORS)
- 앞서 생성된 커밋들의 해시(예: root=`3f17a2`, feature=`92a3c1`, main=`7b4e10`)를 활용해 테스트합니다.

```text
mini-git> ancestors 92a3c1
Ancestors of 92a3c1:
- 3f17a2: Initial commit

mini-git> ancestors 3f17a2
No ancestors

mini-git> path 92a3c1 7b4e10
Path: 92a3c1 -> 3f17a2 -> 7b4e10

mini-git> path 3f17a2 3f17a2
Path: 3f17a2
```

#### Step 4: 역색인 검색 (SEARCH)
- 메시지 단어 분리(소문자 정규화) 및 작성자 역색인을 통해 순회 없이 즉시 결과를 반환합니다.

```text
mini-git> search "login"
Found 1 commit:

- 92a3c1: Add login feature

mini-git> search "login feature"
Found 1 commit:

- 92a3c1: Add login feature

mini-git> search --author="alice kim"
Found 3 commits:

- 3f17a2: Initial commit
- 7b4e10: Add payment feature
- 92a3c1: Add login feature

mini-git> search "nonexistent"
Found 0 commits.
```

#### Step 5: 예외 처리 및 에러 메시지 검증
과제 요구 명세에 맞춘 에러 메시지 표준화 여부를 확인합니다.

```text
# 잘못된 인자 개수 또는 문법 오류
mini-git> init Alice Bob
Invalid args

mini-git> commit "unclosed quote
Invalid args

# 중복 초기화 방지
mini-git> init "Another User"
Repository already initialized

# 존재하지 않는 대상 조회
mini-git> switch nonexistent
Unknown branch: nonexistent

mini-git> ancestors 999999
Unknown commit: 999999

# 알 수 없는 명령어
mini-git> foobar
Unknown command: foobar

# REPL 종료
mini-git> exit
```

---

### 3. 과제 제약사항 및 단위 테스트 자동 검증

과제 요구사항인 **"Python 표준 정렬 API(`sorted()`, `list.sort()`) 및 외부 그래프 라이브러리 사용 금지"** 제약과 전체 알고리즘 정합성은 단위 테스트를 통해 자동으로 검증할 수 있습니다.

```bash
python -m unittest discover -s tests -v
```

- `test_constraints.py`: AST(추상 구문 트리) 정적 분석으로 `sorted`, `list.sort`, `networkx` 등의 금지된 API 미사용 보장
- `test_algorithms.py`: 직접 구현한 Kahn 위상 정렬, BFS 최단 경로, 조상 탐색, Merge Sort, Quick Sort, 역색인 검증
- `test_repository.py` & `test_cli.py`: 저장소 상태 관리 및 REPL 통합 동작 검증 (총 43개 테스트 전체 통과)

## 프로젝트 구조

```text
.
├── main.py                 # REPL 실행 진입점
├── minigit/
│   ├── models.py           # 변경할 수 없는 Commit 데이터
│   ├── repository.py       # 커밋, 브랜치, HEAD 관리
│   ├── parser.py           # 명령 파싱, 검증, 출력 생성
│   └── algorithms/
│       ├── common.py       # 공용 타입과 비교 함수
│       ├── merge_sort.py   # 병합 정렬
│       ├── quick_sort.py   # 퀵 정렬
│       ├── topological_sort.py # Kahn 위상 정렬
│       ├── bfs.py          # BFS 최단 경로와 무방향 그래프 생성
│       ├── dfs.py          # DFS 조상 탐색
│       ├── min_heap.py     # 최소 힙 삽입·삭제
│       ├── inverted_index.py # 키워드와 작성자 역색인
│       └── sort.py / graph.py / index.py # 기존 import 호환 모듈
├── tests/                  # 단위 테스트와 REPL 통합 테스트
└── docs/
    ├── subject.md          # 과제 설명 원문
    ├── SPECIFICATION.md    # 현재 구현의 기술 명세
    └── CODE_ANALYSIS_GUIDE.md  # 초보자용 코드 분석 가이드
```

## 핵심 원리

### 커밋 그래프가 DAG인 이유

커밋은 자신보다 먼저 생성된 부모 커밋만 가리킵니다. 과거의 부모가 아직 없는
미래의 자식을 다시 가리키지 않으므로 방향을 따라가다 출발점으로 돌아오는
순환이 생기지 않습니다. 이런 방향성 비순환 그래프를 DAG라고 합니다.

커밋은 SHA-1 결과 40자리 전체를 `dict`의 키로 저장합니다. `Commit.hash`,
`parents`, 브랜치와 역색인도 전체 해시를 보관합니다. 앞부분만 같으면 각각
저장하고, 전체 해시까지 중복될 때만 내부 순번을 바꿔 다시 계산합니다.
커밋 객체는 생성 후 수정할 수 없습니다.

`subject.md`의 요구는 세션 내 유일성입니다. 전체 해시 저장과 화면 축약은
이 프로젝트의 설계 선택이며 과제 원문에서 해시 길이를 지정한 것은 아닙니다.

### 부모 우선 LOG: Kahn 위상 정렬

각 커밋에 아직 처리되지 않은 부모가 몇 개인지 진입 차수로 기록합니다. 부모가
없는 커밋부터 출력하고, 해당 커밋의 자식 진입 차수를 하나 줄입니다. 진입 차수가
0이 된 자식만 다음 후보가 되므로 부모가 자식보다 먼저 나온다는 규칙이 지켜집니다.
후보는 직접 구현한 최소 힙으로 관리하며, 커밋 수를 V, 연결 수를 E라고 할 때
전체 시간복잡도는 O((V + E) log V)입니다.

### PATH와 ANCESTORS

`PATH`는 부모-자식 연결을 양방향 간선으로 보고 BFS를 수행합니다. BFS는 간선
수가 적은 경로부터 탐색하므로 최단 경로를 찾습니다. 시작점과 끝점에서 계산한
거리를 이용해 최단 거리를 유지하는 이웃 중 해시가 가장 작은 커밋을 선택하므로,
같은 길이 중 사전순으로 가장 작은 경로를 반환합니다. 시간복잡도는 O(V + E)입니다.

`ANCESTORS`는 부모 방향으로만 스택을 이용해 탐색합니다. 방문한 해시는 set에
기록해 여러 경로에서 같은 조상을 만나도 한 번만 처리합니다.

### 역색인

커밋을 만들 때 메시지를 공백으로 나누고 소문자로 바꾼 뒤 다음 표에 등록합니다.

```text
login -> {a1b2c3, d4e5f6}
alice -> {a1b2c3}
```

위 표의 해시는 설명용 축약입니다. 실제 인덱스에는 40자리 전체 해시가 들어갑니다.

검색할 때 모든 커밋 메시지를 다시 읽지 않고 dict에서 검색어의 해시 집합을
바로 가져옵니다. dict 키 조회의 평균 시간복잡도는 O(1)입니다. 여러 단어를
검색할 때의 set 복사·교집합은 후보 수에 비례하고, R개의 최종 결과를 출력 순서로
정렬하는 데에는 Merge Sort의 O(R log R)이 추가로 필요합니다.

화면용 해시 표시표는 출력할 때 저장소 전체 해시를 병합 정렬한 뒤 이웃끼리
공통 접두어를 비교해 만듭니다. 전체 커밋 수 V에 대해 O(V log V)의 표시 비용이
추가되며, 커밋 메시지 본문을 다시 검색하지는 않습니다. 전체 해시 조회는 평균
O(1), 짧은 접두어 조회는 현재 구현에서 O(V)입니다(해시 길이를 상수로 간주).

### 직접 구현한 정렬

프로그램 구현부에서는 Python 표준 정렬 API인 `sorted()`와 `list.sort()`를
사용하지 않습니다.

| 알고리즘 | 평균 | 최악 | 추가 메모리 | 안정 정렬 |
| --- | --- | --- | --- | --- |
| Merge Sort | O(N log N) | O(N log N) | O(N) | 예 |
| Quick Sort | O(N log N) | O(N²) | O(N) 복사본 + O(log N) 호출 스택 | 아니요 |

날짜 정렬은 `(timestamp, hash)`, 작성자 정렬은
`(author.lower(), timestamp, hash)` 순서로 비교합니다. 날짜나 작성자가 같아도
추가 비교 기준에 따라 순서가 달라질 수 있습니다.

LOG의 날짜·작성자 정렬에는 결과가 예측 가능하고 안정적인 Merge Sort를
사용합니다. Quick Sort는 첫 값, 가운데 값, 마지막 값 중 중간값을 피벗으로
선택하는 median-of-three 방식과 중복 값에 유리한 3구역 분할을 사용합니다.
작은 파티션만 재귀 처리해 불균형한 입력에서도 재귀 한도를 넘지 않게 합니다.

## 오류 처리와 설계 선택

- `INIT` 이전에 저장소 명령을 실행하면 `Repository not initialized`를 출력합니다.
- 최초 커밋 전에는 새 브랜치가 가리킬 커밋이 없어 `No commits yet`을 출력합니다.
- 같은 세션에서 다시 `INIT`하면 기록 손실을 막기 위해 거부합니다.
- 존재하지 않는 브랜치와 커밋은 각각 `Unknown branch: <name>`,
  `Unknown commit: <hash>`로 표시합니다.
- 잘못된 인자 개수, 옵션, 닫히지 않은 따옴표는 `Invalid args`로 처리하며 REPL은
  계속 실행됩니다.
- `LOG`는 현재 브랜치뿐 아니라 저장소의 모든 브랜치에서 만든 커밋을 보여 줍니다.

## 테스트 실행

외부 테스트 도구 없이 표준 라이브러리의 `unittest`로 실행할 수 있습니다.

```bash
python -m unittest discover -s tests -v
```

테스트는 정렬과 안정성, 역색인, 분기된 DAG의 위상 순서, 모든 조상 탐색,
최단 경로의 사전순 동률 처리, 큰 입력, 오류 메시지, 실제 REPL 세션을 확인합니다.
또한 AST 검사로 금지된 정렬 API와 그래프 라이브러리 사용을 방지합니다.

## 구현하지 않은 선택 보너스

과제에서 선택 사항으로 제시한 `DIFF`, `MERGE`, 정렬 성능 비교 명령은 현재
범위에 포함하지 않았습니다. 다만 기술 명세에 포함된 Quick Sort 알고리즘은
학습할 수 있도록 구현하고 자동 테스트합니다.

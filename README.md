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

## 프로젝트 구조

```text
.
├── main.py                 # REPL 실행 진입점
├── minigit/
│   ├── models.py           # 변경할 수 없는 Commit 데이터
│   ├── repository.py       # 커밋, 브랜치, HEAD 관리
│   ├── parser.py           # 명령 파싱, 검증, 출력 생성
│   └── algorithms/
│       ├── graph.py        # 위상 정렬, BFS 경로, 조상 탐색
│       ├── index.py        # 키워드와 작성자 역색인
│       └── sort.py         # Merge Sort와 Quick Sort
├── tests/                  # 단위 테스트와 REPL 통합 테스트
└── docs/                   # 과제와 기술 명세 원문
```

## 핵심 원리

### 커밋 그래프가 DAG인 이유

커밋은 자신보다 먼저 생성된 부모 커밋만 가리킵니다. 과거의 부모가 아직 없는
미래의 자식을 다시 가리키지 않으므로 방향을 따라가다 출발점으로 돌아오는
순환이 생기지 않습니다. 이런 방향성 비순환 그래프를 DAG라고 합니다.

커밋은 SHA-1 결과의 앞 6자리 해시로 `dict`에 저장합니다. 같은 6자리가 나오는
충돌에 대비해 내부 순번을 바꿔 다시 계산하므로 한 세션 안에서 해시가
중복되지 않습니다. 커밋 객체는 생성 후 수정할 수 없습니다.

### 부모 우선 LOG: Kahn 위상 정렬

각 커밋에 아직 처리되지 않은 부모가 몇 개인지 진입 차수로 기록합니다. 부모가
없는 커밋부터 출력하고, 해당 커밋의 자식 진입 차수를 하나 줄입니다. 진입 차수가
0이 된 자식만 다음 후보가 되므로 부모가 자식보다 먼저 나온다는 규칙이 지켜집니다.
시간복잡도는 커밋 수를 V, 연결 수를 E라고 할 때 기본 탐색이 O(V + E)입니다.

### PATH와 ANCESTORS

`PATH`는 부모-자식 연결을 양방향 간선으로 보고 BFS를 수행합니다. BFS는 간선
수가 적은 경로부터 탐색하므로 최단 경로를 찾습니다. 같은 길이의 후보끼리는
`hash1->hash2` 형태의 전체 문자열을 비교해 사전순으로 가장 작은 경로를
선택합니다. 시간복잡도는 O(V + E)입니다.

`ANCESTORS`는 부모 방향으로만 스택을 이용해 탐색합니다. 방문한 해시는 set에
기록해 여러 경로에서 같은 조상을 만나도 한 번만 처리합니다.

### 역색인

커밋을 만들 때 메시지를 공백으로 나누고 소문자로 바꾼 뒤 다음 표에 등록합니다.

```text
login -> {a1b2c3, d4e5f6}
alice -> {a1b2c3}
```

검색할 때 모든 커밋 메시지를 다시 읽지 않고 dict에서 검색어의 해시 집합을
바로 가져옵니다. dict 키 조회의 평균 시간복잡도는 O(1)이며, 그 뒤에는 실제
결과 수에 비례하는 작업만 수행합니다.

### 직접 구현한 정렬

프로그램 구현부에서는 Python 표준 정렬 API인 `sorted()`와 `list.sort()`를
사용하지 않습니다.

| 알고리즘 | 평균 | 최악 | 추가 메모리 | 안정 정렬 |
| --- | --- | --- | --- | --- |
| Merge Sort | O(N log N) | O(N log N) | O(N) | 예 |
| Quick Sort | O(N log N) | O(N²) | 재귀 스택 | 아니요 |

LOG의 날짜·작성자 정렬에는 결과가 예측 가능하고 안정적인 Merge Sort를
사용합니다. Quick Sort는 첫 값, 가운데 값, 마지막 값 중 중간값을 피벗으로
선택하는 median-of-three 방식과 중복 값에 유리한 3구역 분할을 사용합니다.

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
최단 경로의 사전순 동률 처리, 오류 메시지, 실제 REPL 세션을 확인합니다.

## 구현하지 않은 선택 보너스

과제에서 선택 사항으로 제시한 `DIFF`, `MERGE`, 정렬 성능 비교 명령은 현재
범위에 포함하지 않았습니다. 다만 기술 명세에 포함된 Quick Sort 알고리즘은
학습할 수 있도록 구현하고 자동 테스트합니다.

"""커밋, 브랜치, HEAD와 검색 인덱스를 한곳에서 관리합니다."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime

from minigit.algorithms.graph import find_ancestors, find_shortest_path, topological_sort
from minigit.algorithms.index import InvertedIndex
from minigit.algorithms.sort import merge_sort
from minigit.models import Commit


class RepositoryError(Exception):
    """사용자 명령을 실행할 수 없을 때 보여 줄 오류입니다."""


class Repository:
    """메모리 안에서 Mini Git 저장소의 전체 상태를 관리합니다.

    ``commits``는 해시를 키로 사용하므로 특정 커밋을 평균 O(1)에 찾을 수
    있습니다. ``branches``의 값은 각 브랜치가 가리키는 최신 커밋 해시입니다.
    저장소를 막 초기화했을 때는 아직 커밋이 없으므로 값이 ``None``입니다.

    ``clock``은 테스트에서 원하는 시간을 주입하기 위한 선택 인자입니다.
    일반 실행에서는 현재 시각을 반환하는 ``datetime.now``를 사용합니다.
    """

    HASH_LENGTH = 6
    HASH_SPACE_SIZE = 16**HASH_LENGTH

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, str | None] = {}
        self.head_branch: str | None = None
        self.current_user: str | None = None
        self.index = InvertedIndex()

        self._clock = clock if clock is not None else datetime.now
        self._hash_nonce = 0

    @property
    def initialized(self) -> bool:
        """INIT 명령이 성공했는지 알려 줍니다."""

        return self.current_user is not None and self.head_branch is not None

    @property
    def head_hash(self) -> str | None:
        """현재 브랜치가 가리키는 커밋 해시를 반환합니다."""

        self._require_initialized()
        # 초기화가 끝났다면 head_branch는 반드시 branches에 존재합니다.
        assert self.head_branch is not None
        return self.branches[self.head_branch]

    def initialize(self, user_name: str) -> None:
        """저장소를 초기화하고 비어 있는 main 브랜치를 만듭니다."""

        if self.initialized:
            raise RepositoryError("Repository already initialized")
        if not user_name.strip():
            raise RepositoryError("Invalid args")

        self.current_user = user_name
        self.head_branch = "main"
        self.branches["main"] = None

    def create_branch(self, branch_name: str) -> None:
        """현재 커밋을 가리키는 새 브랜치를 만듭니다."""

        self._require_initialized()
        if not branch_name.strip():
            raise RepositoryError("Invalid args")
        if branch_name in self.branches:
            raise RepositoryError(f"Branch already exists: {branch_name}")

        current_hash = self.head_hash
        if current_hash is None:
            raise RepositoryError("No commits yet")

        self.branches[branch_name] = current_hash

    def switch_branch(self, branch_name: str) -> None:
        """HEAD를 기존 브랜치로 옮깁니다. 커밋 자체는 변경하지 않습니다."""

        self._require_initialized()
        if branch_name not in self.branches:
            raise RepositoryError(f"Unknown branch: {branch_name}")
        self.head_branch = branch_name

    def create_commit(self, message: str) -> Commit:
        """현재 HEAD를 부모로 하는 새 커밋을 만들고 색인을 갱신합니다."""

        self._require_initialized()
        if not message.strip():
            raise RepositoryError("Invalid args")

        assert self.current_user is not None
        assert self.head_branch is not None

        current_hash = self.branches[self.head_branch]
        parents = () if current_hash is None else (current_hash,)
        timestamp = self._clock().strftime("%Y-%m-%d %H:%M:%S")
        commit_hash = self._make_unique_hash(
            message=message,
            author=self.current_user,
            timestamp=timestamp,
            parents=parents,
        )

        commit = Commit(
            hash=commit_hash,
            message=message,
            author=self.current_user,
            timestamp=timestamp,
            parents=parents,
        )
        self.commits[commit_hash] = commit
        self.branches[self.head_branch] = commit_hash
        self.index.add(commit)
        return commit

    def get_commit(self, commit_hash: str) -> Commit:
        """해시로 커밋을 찾고, 없으면 표준 오류를 발생시킵니다."""

        self._require_initialized()
        if commit_hash not in self.commits:
            raise RepositoryError(f"Unknown commit: {commit_hash}")
        return self.commits[commit_hash]

    def get_log(self, sort_by: str | None = None) -> list[Commit]:
        """위상 순서 또는 요청한 비교 기준으로 전체 커밋을 반환합니다."""

        self._require_initialized()

        if sort_by is None:
            return topological_sort(self.commits)
        if sort_by == "date":
            return merge_sort(
                list(self.commits.values()),
                key=lambda commit: (commit.timestamp, commit.hash),
            )
        if sort_by == "author":
            return merge_sort(
                list(self.commits.values()),
                key=lambda commit: (
                    commit.author.lower(),
                    commit.timestamp,
                    commit.hash,
                ),
            )
        raise RepositoryError("Invalid args")

    def get_path(self, start_hash: str, end_hash: str) -> list[str] | None:
        """두 해시를 검증한 뒤 무방향 그래프의 최단 경로를 반환합니다."""

        self.get_commit(start_hash)
        self.get_commit(end_hash)
        return find_shortest_path(self.commits, start_hash, end_hash)

    def get_ancestors(self, commit_hash: str) -> list[Commit]:
        """모든 조상을 부모가 자식보다 먼저 오는 순서로 반환합니다."""

        self.get_commit(commit_hash)
        ancestor_hashes = find_ancestors(self.commits, commit_hash)
        ancestor_commits: dict[str, Commit] = {}

        for ancestor_hash in ancestor_hashes:
            ancestor_commits[ancestor_hash] = self.commits[ancestor_hash]

        return topological_sort(ancestor_commits)

    def search_keyword(self, query: str) -> list[Commit]:
        """역색인에서 키워드를 찾아 결정적인 시간순으로 반환합니다."""

        self._require_initialized()
        hashes = self.index.search_keywords(query)
        return self._commits_in_date_order(hashes)

    def search_author(self, author: str) -> list[Commit]:
        """역색인에서 작성자를 찾아 결정적인 시간순으로 반환합니다."""

        self._require_initialized()
        hashes = self.index.search_author(author)
        return self._commits_in_date_order(hashes)

    def branches_for_commit(self, commit_hash: str) -> list[str]:
        """현재 해당 커밋을 직접 가리키는 브랜치 이름을 반환합니다."""

        branch_names: list[str] = []
        for branch_name, branch_hash in self.branches.items():
            if branch_hash == commit_hash:
                branch_names.append(branch_name)
        return merge_sort(branch_names)

    def _commits_in_date_order(self, hashes: set[str]) -> list[Commit]:
        """해시 집합을 실제 커밋 목록으로 바꾸고 시간순으로 정렬합니다."""

        commits: list[Commit] = []
        for commit_hash in hashes:
            # 색인은 저장소가 커밋과 함께 갱신하므로 해시가 항상 존재합니다.
            commits.append(self.commits[commit_hash])

        return merge_sort(
            commits, key=lambda commit: (commit.timestamp, commit.hash)
        )

    def _make_unique_hash(
        self,
        message: str,
        author: str,
        timestamp: str,
        parents: tuple[str, ...],
    ) -> str:
        """커밋 메타데이터로 세션에서 유일한 6자리 SHA-1 해시를 만듭니다.

        SHA-1 전체값의 앞 6자리만 사용하면 아주 드물게 기존 해시와 충돌할 수
        있습니다. 내부 순번(nonce)을 입력에 함께 넣고 충돌 시 다음 순번으로
        다시 계산하여, 사용 가능한 해시 공간 안에서는 중복을 허용하지 않습니다.
        """

        if len(self.commits) >= self.HASH_SPACE_SIZE:
            raise RepositoryError("Commit hash space exhausted")

        while True:
            nonce = self._hash_nonce
            self._hash_nonce += 1
            parent_text = ",".join(parents)
            payload = "\x1f".join(
                (message, author, timestamp, parent_text, str(nonce))
            )
            candidate = hashlib.sha1(payload.encode("utf-8")).hexdigest()[
                : self.HASH_LENGTH
            ]

            if candidate not in self.commits:
                return candidate

    def _require_initialized(self) -> None:
        """INIT 이전 명령이 저장소 상태에 접근하지 못하게 막습니다."""

        if not self.initialized:
            raise RepositoryError("Repository not initialized")

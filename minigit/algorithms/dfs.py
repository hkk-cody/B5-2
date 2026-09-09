"""커밋 그래프 알고리즘입니다."""

from __future__ import annotations

from collections.abc import Mapping

from minigit.models import Commit


def find_ancestors(commits: Mapping[str, Commit], commit_hash: str) -> set[str]:
    """주어진 커밋에서 부모 방향으로 도달할 수 있는 모든 해시를 반환합니다.

    ``visited`` 집합 덕분에 여러 갈래에서 같은 조상을 만나도 한 번만 처리합니다.
    요청한 커밋 자신은 결과에 포함하지 않습니다.
    """

    if commit_hash not in commits:
        return set()

    ancestors: set[str] = set()
    stack = list(commits[commit_hash].parents)

    while stack:
        current_hash = stack.pop()
        if current_hash in ancestors or current_hash not in commits:
            continue

        ancestors.add(current_hash)
        stack.extend(commits[current_hash].parents)

    return ancestors

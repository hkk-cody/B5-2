"""커밋 그래프 알고리즘입니다."""

from __future__ import annotations

from collections.abc import Mapping

from minigit.models import Commit
from minigit.algorithms.min_heap import heap_pop, heap_push


def topological_sort(commits: Mapping[str, Commit]) -> list[Commit]:
    """부모 커밋이 자식보다 먼저 오도록 Kahn 알고리즘으로 정렬합니다.

    ``indegree``는 한 커밋보다 먼저 처리해야 할 부모의 수입니다. 이 값이
    0인 커밋부터 출력하고, 그 커밋을 부모로 둔 자식의 값을 하나씩 줄입니다.
    모든 부모가 처리된 자식은 다음 출력 후보가 됩니다.

    후보가 여러 개라면 timestamp와 hash 순으로 선택하여 실행할 때마다 같은
    결과를 만듭니다. 그래프에 순환이 있으면 모든 노드를 처리할 수 없으므로
    ``ValueError``를 발생시킵니다.
    """

    indegree: dict[str, int] = {}
    children: dict[str, set[str]] = {}

    for commit_hash in commits:
        indegree[commit_hash] = 0
        children[commit_hash] = set()

    for commit in commits.values():
        for parent_hash in commit.parents:
            # 저장소 밖의 부모는 잘못된 데이터이므로 간선으로 계산하지 않습니다.
            if parent_hash not in commits:
                continue
            if commit.hash not in children[parent_hash]:
                children[parent_hash].add(commit.hash)
                indegree[commit.hash] += 1

    ready: list[Commit] = []
    for commit_hash, degree in indegree.items():
        if degree == 0:
            heap_push(ready, commits[commit_hash])

    result: list[Commit] = []

    while ready:
        current = heap_pop(ready)
        result.append(current)

        for child_hash in children[current.hash]:
            indegree[child_hash] -= 1
            if indegree[child_hash] == 0:
                heap_push(ready, commits[child_hash])

    if len(result) != len(commits):
        raise ValueError("Commit graph contains a cycle")

    return result

"""커밋 DAG에서 사용하는 그래프 탐색 알고리즘입니다."""

from __future__ import annotations

from collections.abc import Mapping

from minigit.algorithms.sort import merge_sort
from minigit.models import Commit


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
            ready.append(commits[commit_hash])

    result: list[Commit] = []

    while ready:
        ready = merge_sort(ready, key=lambda commit: (commit.timestamp, commit.hash))
        current = ready.pop(0)
        result.append(current)

        for child_hash in children[current.hash]:
            indegree[child_hash] -= 1
            if indegree[child_hash] == 0:
                ready.append(commits[child_hash])

    if len(result) != len(commits):
        raise ValueError("Commit graph contains a cycle")

    return result


def build_undirected_graph(commits: Mapping[str, Commit]) -> dict[str, set[str]]:
    """부모-자식 연결을 양방향으로 이동 가능한 인접 리스트로 바꿉니다."""

    graph: dict[str, set[str]] = {}
    for commit_hash in commits:
        graph[commit_hash] = set()

    for commit in commits.values():
        for parent_hash in commit.parents:
            if parent_hash not in commits:
                continue
            graph[commit.hash].add(parent_hash)
            graph[parent_hash].add(commit.hash)

    return graph


def find_shortest_path(
    commits: Mapping[str, Commit], start_hash: str, end_hash: str
) -> list[str] | None:
    """두 커밋 사이의 최단 경로를 BFS로 찾아 해시 목록으로 반환합니다.

    BFS는 시작점에서 간선 하나 거리, 두 개 거리 순으로 층을 넓혀 갑니다.
    같은 층에서 한 커밋에 도달하는 경로가 여러 개면 ``->``로 연결한 문자열이
    가장 작은 경로만 남깁니다. 따라서 목적지가 처음 등장한 층의 경로가
    '가장 짧고, 동률 중 사전순 최소'라는 두 조건을 모두 만족합니다.
    """

    if start_hash not in commits or end_hash not in commits:
        return None
    if start_hash == end_hash:
        return [start_hash]

    graph = build_undirected_graph(commits)
    frontier: dict[str, list[str]] = {start_hash: [start_hash]}
    visited = {start_hash}

    while frontier:
        next_frontier: dict[str, list[str]] = {}
        next_path_text: dict[str, str] = {}

        for current_hash, current_path in frontier.items():
            for neighbor_hash in graph[current_hash]:
                if neighbor_hash in visited:
                    continue

                candidate = current_path + [neighbor_hash]
                candidate_text = "->".join(candidate)

                if (
                    neighbor_hash not in next_frontier
                    or candidate_text < next_path_text[neighbor_hash]
                ):
                    next_frontier[neighbor_hash] = candidate
                    next_path_text[neighbor_hash] = candidate_text

        if end_hash in next_frontier:
            return next_frontier[end_hash]

        visited.update(next_frontier)
        frontier = next_frontier

    return None


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

"""커밋 그래프 알고리즘입니다."""

from __future__ import annotations

from collections.abc import Mapping

from minigit.models import Commit
from collections import deque


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

    시작점과 끝점에서 각각 BFS를 수행해 모든 커밋까지의 거리를 구합니다.
    이후 최단 거리를 유지하는 이웃 중 해시가 가장 작은 커밋을 하나씩 고르면,
    전체 경로를 매번 복사하지 않고도 사전순으로 가장 작은 최단 경로가 됩니다.
    """

    if start_hash not in commits or end_hash not in commits:
        return None
    if start_hash == end_hash:
        return [start_hash]

    graph = build_undirected_graph(commits)
    distance_from_start = _bfs_distances(graph, start_hash)
    if end_hash not in distance_from_start:
        return None

    distance_to_end = _bfs_distances(graph, end_hash)
    shortest_distance = distance_from_start[end_hash]
    path = [start_hash]
    current_hash = start_hash

    while current_hash != end_hash:
        next_hash: str | None = None

        for neighbor_hash in graph[current_hash]:
            # 시작점에서 한 칸 앞으로 가면서도, 끝점까지의 남은 거리를 더했을 때
            # 전체 최단 거리와 같아야 최단 경로 위의 이웃입니다.
            if distance_from_start.get(neighbor_hash) != len(path):
                continue
            if (
                distance_from_start[neighbor_hash]
                + distance_to_end[neighbor_hash]
                != shortest_distance
            ):
                continue
            if next_hash is None or neighbor_hash < next_hash:
                next_hash = neighbor_hash

        # 거리 조건상 반드시 하나 이상의 다음 커밋이 존재합니다.
        if next_hash is None:
            raise ValueError("Could not reconstruct shortest path")

        path.append(next_hash)
        current_hash = next_hash

    return path


def _bfs_distances(graph: Mapping[str, set[str]], start_hash: str) -> dict[str, int]:
    """시작 커밋에서 도달 가능한 각 커밋까지의 최단 거리를 계산합니다."""

    distances = {start_hash: 0}
    queue = deque([start_hash])

    while queue:
        current_hash = queue.popleft()
        next_distance = distances[current_hash] + 1

        for neighbor_hash in graph[current_hash]:
            if neighbor_hash in distances:
                continue
            distances[neighbor_hash] = next_distance
            queue.append(neighbor_hash)

    return distances

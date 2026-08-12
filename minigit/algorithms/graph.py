"""커밋 DAG에서 사용하는 그래프 탐색 알고리즘입니다."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping

from minigit.models import Commit


def _commit_order_key(commit: Commit) -> tuple[str, str]:
    """위상 정렬 후보의 우선순위인 생성 시각과 해시를 반환합니다."""

    return commit.timestamp, commit.hash


def _heap_push(heap: list[Commit], commit: Commit) -> None:
    """직접 구현한 최소 힙에 커밋을 O(log N)으로 추가합니다.

    과제에서 금지한 내장 정렬 API를 사용하지 않으면서도, 매번 후보 전체를
    다시 정렬하지 않기 위해 이진 최소 힙을 사용합니다. 부모 위치의 값이
    자식보다 항상 작도록 새 값을 위로 올립니다.
    """

    heap.append(commit)
    child_index = len(heap) - 1

    while child_index > 0:
        parent_index = (child_index - 1) // 2
        if _commit_order_key(heap[parent_index]) <= _commit_order_key(
            heap[child_index]
        ):
            break

        heap[parent_index], heap[child_index] = heap[child_index], heap[parent_index]
        child_index = parent_index


def _heap_pop(heap: list[Commit]) -> Commit:
    """최소 힙에서 가장 이른 커밋을 O(log N)으로 꺼냅니다."""

    first = heap[0]
    last = heap.pop()
    if not heap:
        return first

    heap[0] = last
    parent_index = 0

    while True:
        left_index = parent_index * 2 + 1
        right_index = left_index + 1
        smallest_index = parent_index

        if (
            left_index < len(heap)
            and _commit_order_key(heap[left_index])
            < _commit_order_key(heap[smallest_index])
        ):
            smallest_index = left_index
        if (
            right_index < len(heap)
            and _commit_order_key(heap[right_index])
            < _commit_order_key(heap[smallest_index])
        ):
            smallest_index = right_index

        if smallest_index == parent_index:
            break

        heap[parent_index], heap[smallest_index] = (
            heap[smallest_index],
            heap[parent_index],
        )
        parent_index = smallest_index

    return first


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
            _heap_push(ready, commits[commit_hash])

    result: list[Commit] = []

    while ready:
        current = _heap_pop(ready)
        result.append(current)

        for child_hash in children[current.hash]:
            indegree[child_hash] -= 1
            if indegree[child_hash] == 0:
                _heap_push(ready, commits[child_hash])

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

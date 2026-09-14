"""위상 정렬 후보를 관리하는 최소 힙의 삽입과 삭제입니다."""

from __future__ import annotations

from minigit.models import Commit
from minigit.algorithms.common import commit_order_key


def heap_push(heap: list[Commit], commit: Commit) -> None:
    """직접 구현한 최소 힙에 커밋을 O(log N)으로 추가합니다.

    과제에서 금지한 내장 정렬 API를 사용하지 않으면서도, 매번 후보 전체를
    다시 정렬하지 않기 위해 이진 최소 힙을 사용합니다. 부모 위치의 값이
    자식보다 항상 작도록 새 값을 위로 올립니다.
    """

    heap.append(commit)
    child_index = len(heap) - 1

    while child_index > 0:
        parent_index = (child_index - 1) // 2
        if commit_order_key(heap[parent_index]) <= commit_order_key(heap[child_index]):
            break

        heap[parent_index], heap[child_index] = heap[child_index], heap[parent_index]
        child_index = parent_index


def heap_pop(heap: list[Commit]) -> Commit:
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
            left_index < len(heap) and
            commit_order_key(heap[left_index]) < commit_order_key(heap[smallest_index])
        ):
            smallest_index = left_index
        if (
            right_index < len(heap) and
            commit_order_key(heap[right_index]) < commit_order_key(heap[smallest_index])
        ):
            smallest_index = right_index

        if smallest_index == parent_index:
            break

        heap[parent_index], heap[smallest_index] = heap[smallest_index], heap[parent_index]
        parent_index = smallest_index

    return first

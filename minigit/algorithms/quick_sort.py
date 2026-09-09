"""퀵 정렬: 피벗 기준의 세 구역으로 나누어 정렬합니다."""

from __future__ import annotations

from collections.abc import Sequence

from minigit.algorithms.common import KeyFunction, T, identity


def quick_sort(items: Sequence[T], key: KeyFunction[T] | None = None) -> list[T]:
    """퀵 정렬로 ``items``를 오름차순 정렬한 새 list를 반환합니다.

    세 후보 중 중간값을 피벗으로 고르는 median-of-three 전략을 사용합니다.
    피벗보다 작은 값, 같은 값, 큰 값의 세 구역으로 나누기 때문에 중복 값이
    많아도 불필요하게 깊은 재귀가 생기는 일을 줄일 수 있습니다.

    평균 시간복잡도는 O(N log N), 최악은 O(N²)입니다. 원소 교환이 일어나므로
    같은 값의 기존 순서를 보장하지 않는 불안정 정렬입니다.
    """

    key_function = key if key is not None else identity
    values = list(items)
    _quick_sort_range(values, 0, len(values) - 1, key_function)
    return values


def _quick_sort_range(
    values: list[T], low: int, high: int, key: KeyFunction[T]
) -> None:
    """``low``부터 ``high``까지 정렬하며 재귀 호출 깊이를 제한합니다.

    두 파티션을 모두 재귀 호출하면 매우 불균형한 입력에서 Python의 재귀 한도를
    넘을 수 있습니다. 작은 파티션만 재귀로 처리하고 큰 파티션은 while 문으로
    계속 처리하면 호출 스택은 최악의 경우에도 O(log N) 크기로 제한됩니다.
    """

    while low < high:
        pivot_index = _median_of_three_index(values, low, high, key)
        pivot_key = key(values[pivot_index])

        # [low, smaller)는 피벗보다 작은 구역, (larger, high]는 큰 구역입니다.
        # cursor가 가운데를 훑으며 각 값을 맞는 구역으로 이동시킵니다.
        smaller = low
        cursor = low
        larger = high

        while cursor <= larger:
            current_key = key(values[cursor])
            if current_key < pivot_key:
                values[smaller], values[cursor] = values[cursor], values[smaller]
                smaller += 1
                cursor += 1
            elif pivot_key < current_key:
                values[cursor], values[larger] = values[larger], values[cursor]
                larger -= 1
            else:
                cursor += 1

        left_size = smaller - low
        right_size = high - larger

        if left_size < right_size:
            _quick_sort_range(values, low, smaller - 1, key)
            low = larger + 1
        else:
            _quick_sort_range(values, larger + 1, high, key)
            high = smaller - 1


def _median_of_three_index(
    values: list[T], low: int, high: int, key: KeyFunction[T]
) -> int:
    """첫 값, 가운데 값, 마지막 값 중 중간 크기인 원소의 위치를 반환합니다."""

    middle = (low + high) // 2
    low_key = key(values[low])
    middle_key = key(values[middle])
    high_key = key(values[high])

    if low_key < middle_key:
        if middle_key < high_key:
            return middle
        if low_key < high_key:
            return high
        return low

    if low_key < high_key:
        return low
    if middle_key < high_key:
        return high
    return middle

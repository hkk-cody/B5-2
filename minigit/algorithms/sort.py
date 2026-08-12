"""Python의 내장 정렬 기능에 의존하지 않는 정렬 알고리즘입니다."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar


T = TypeVar("T")
KeyFunction = Callable[[T], Any]


def _identity(value: T) -> T:
    """별도 비교 기준이 없을 때 값 자체를 비교 기준으로 사용합니다."""

    return value


def merge_sort(items: Sequence[T], key: KeyFunction[T] | None = None) -> list[T]:
    """병합 정렬로 ``items``를 오름차순 정렬한 새 list를 반환합니다.

    병합 정렬은 목록을 절반씩 나눈 뒤, 정렬된 두 목록을 다시 합칩니다.
    원소가 같은 경우 왼쪽 목록의 원소를 먼저 선택하므로 입력에서의 상대적
    순서가 유지됩니다. 이런 성질을 '안정 정렬'이라고 합니다.

    시간복잡도는 입력 모양과 관계없이 O(N log N)이고, 합치는 과정에서
    O(N)의 추가 메모리를 사용합니다. 원본 목록은 변경하지 않습니다.
    """

    key_function = key if key is not None else _identity
    values = list(items)

    if len(values) <= 1:
        return values

    middle = len(values) // 2
    left = merge_sort(values[:middle], key_function)
    right = merge_sort(values[middle:], key_function)
    return _merge(left, right, key_function)


def _merge(left: list[T], right: list[T], key: KeyFunction[T]) -> list[T]:
    """이미 정렬된 두 목록을 하나의 정렬된 목록으로 합칩니다."""

    merged: list[T] = []
    left_index = 0
    right_index = 0

    while left_index < len(left) and right_index < len(right):
        left_key = key(left[left_index])
        right_key = key(right[right_index])

        # right가 left보다 작지 않다면 left가 먼저입니다. 같은 값일 때도
        # left를 택하는 것이 병합 정렬의 안정성을 지키는 핵심입니다.
        if not right_key < left_key:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    # 한쪽 목록을 모두 사용했다면 다른 쪽의 남은 부분은 이미 정렬되어 있습니다.
    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return merged


def quick_sort(items: Sequence[T], key: KeyFunction[T] | None = None) -> list[T]:
    """퀵 정렬로 ``items``를 오름차순 정렬한 새 list를 반환합니다.

    세 후보 중 중간값을 피벗으로 고르는 median-of-three 전략을 사용합니다.
    피벗보다 작은 값, 같은 값, 큰 값의 세 구역으로 나누기 때문에 중복 값이
    많아도 불필요하게 깊은 재귀가 생기는 일을 줄일 수 있습니다.

    평균 시간복잡도는 O(N log N), 최악은 O(N²)입니다. 원소 교환이 일어나므로
    같은 값의 기존 순서를 보장하지 않는 불안정 정렬입니다.
    """

    key_function = key if key is not None else _identity
    values = list(items)
    _quick_sort_range(values, 0, len(values) - 1, key_function)
    return values


def _quick_sort_range(
    values: list[T], low: int, high: int, key: KeyFunction[T]
) -> None:
    """``low``부터 ``high``까지를 제자리에서 퀵 정렬합니다."""

    if low >= high:
        return

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

    _quick_sort_range(values, low, smaller - 1, key)
    _quick_sort_range(values, larger + 1, high, key)


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

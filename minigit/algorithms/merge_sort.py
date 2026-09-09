"""병합 정렬: 목록을 나눈 뒤 안정적으로 합칩니다."""

from __future__ import annotations

from collections.abc import Sequence

from minigit.algorithms.common import KeyFunction, T, identity


def merge_sort(items: Sequence[T], key: KeyFunction[T] | None = None) -> list[T]:
    """병합 정렬로 ``items``를 오름차순 정렬한 새 list를 반환합니다.

    병합 정렬은 목록을 절반씩 나눈 뒤, 정렬된 두 목록을 다시 합칩니다.
    원소가 같은 경우 왼쪽 목록의 원소를 먼저 선택하므로 입력에서의 상대적
    순서가 유지됩니다. 이런 성질을 '안정 정렬'이라고 합니다.

    시간복잡도는 입력 모양과 관계없이 O(N log N)이고, 합치는 과정에서
    O(N)의 추가 메모리를 사용합니다. 원본 목록은 변경하지 않습니다.
    """

    key_function = key if key is not None else identity
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

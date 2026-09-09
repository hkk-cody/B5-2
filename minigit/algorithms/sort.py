"""기존 정렬 import 경로를 유지하는 호환 모듈입니다. 구현은 개별 파일에 있습니다."""

from minigit.algorithms.merge_sort import merge_sort
from minigit.algorithms.quick_sort import quick_sort

__all__ = ["merge_sort", "quick_sort"]

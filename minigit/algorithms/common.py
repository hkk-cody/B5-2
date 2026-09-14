"""알고리즘에서 공유하는 타입과 기본 비교 함수입니다."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from minigit.models import Commit

T = TypeVar("T")
KeyFunction = Callable[[T], Any] # T타입의 값을 받아서 비교가능한 값을 반환하는 함수


def identity(value: T) -> T:
    """별도 비교 기준이 없을 때 값 자체를 비교 기준으로 사용합니다."""

    return value


def commit_order_key(commit: Commit) -> tuple[str, str]:
    """위상 정렬 후보의 우선순위인 생성 시각과 해시를 반환합니다."""

    return commit.timestamp, commit.hash

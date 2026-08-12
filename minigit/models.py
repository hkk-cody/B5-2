"""Mini Git에서 사용하는 핵심 데이터 모델을 정의합니다."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Commit:
    """한 번 생성된 뒤에는 바뀌지 않는 커밋 한 개를 나타냅니다.

    실제 Git의 커밋도 생성 후 내용을 수정하지 않습니다. 내용을 바꾸고 싶다면
    기존 커밋을 고치는 대신 새로운 커밋을 만들기 때문입니다. ``frozen=True``는
    이 규칙을 Python 객체에도 적용합니다.

    ``parents``는 부모 커밋의 해시를 담습니다. 일반 커밋은 부모가 하나이고,
    저장소의 첫 커밋은 부모가 없습니다. tuple을 사용한 이유는 list와 달리
    객체 생성 후 원소를 추가하거나 삭제할 수 없어 불변성이 유지되기 때문입니다.
    """

    hash: str
    message: str
    author: str
    timestamp: str
    parents: tuple[str, ...]

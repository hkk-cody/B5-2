"""커밋을 빠르게 검색하기 위한 역색인을 구현합니다."""

from __future__ import annotations

from minigit.models import Commit


class InvertedIndex:
    """단어와 작성자에서 관련 커밋 해시로 이어지는 표를 관리합니다.

    모든 커밋을 매번 처음부터 읽는 대신, 책 뒤의 색인처럼 검색어를 먼저
    찾아 관련 커밋 해시만 가져옵니다. dict에서 키 하나를 찾는 평균 비용은
    O(1)이므로 커밋 수가 많아질수록 전체 순회보다 유리합니다.
    """

    def __init__(self) -> None:
        self.keyword_index: dict[str, set[str]] = {}
        self.author_index: dict[str, set[str]] = {}

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """명세에 따라 공백으로 나눈 뒤 소문자로 정규화합니다."""

        return text.lower().split()

    def add(self, commit: Commit) -> None:
        """새 커밋을 키워드 색인과 작성자 색인에 등록합니다."""

        for token in self.tokenize(commit.message):
            if token not in self.keyword_index:
                self.keyword_index[token] = set()
            self.keyword_index[token].add(commit.hash)

        author_key = commit.author.lower()
        if author_key not in self.author_index:
            self.author_index[author_key] = set()
        self.author_index[author_key].add(commit.hash)

    def search_keywords(self, query: str) -> set[str]:
        """질문의 모든 단어를 포함하는 커밋 해시 집합을 반환합니다.

        여러 단어를 검색하면 각 단어의 결과에 공통으로 들어 있는 해시만
        남깁니다. 즉, ``login feature``는 두 단어가 모두 있는 커밋을 찾습니다.
        이 과정에서도 커밋 본문 전체를 다시 순회하지 않습니다.
        """

        tokens = self.tokenize(query)
        if not tokens:
            return set()

        # 없는 단어는 즉시 종료하고, 가장 작은 후보 집합만 복사합니다.
        candidates: list[set[str]] = []
        for token in set(tokens):
            candidate = self.keyword_index.get(token)
            if not candidate:
                return set()
            candidates.append(candidate)

        smallest = min(candidates, key=len) # 가장 적은 수의 해시를 가진 후보를 선택
        matches = set(smallest)
        for candidate in candidates:
            if candidate is smallest:
                continue
            matches.intersection_update(candidate) # 교집합
            if not matches:
                break

        return matches

    def search_author(self, author: str) -> set[str]:
        """대소문자와 관계없이 작성자가 정확히 일치하는 해시를 반환합니다."""

        return set(self.author_index.get(author.lower(), set()))

"""정렬, 그래프 탐색, 역색인 알고리즘의 단위 테스트입니다."""

from __future__ import annotations

import unittest

from minigit.algorithms.graph import (
    find_ancestors,
    find_shortest_path,
    topological_sort,
)
from minigit.algorithms.index import InvertedIndex
from minigit.algorithms.sort import merge_sort, quick_sort
from minigit.models import Commit


def make_commit(
    commit_hash: str,
    message: str = "message",
    author: str = "Alice",
    timestamp: str = "2024-01-01 09:00:00",
    parents: tuple[str, ...] = (),
) -> Commit:
    """테스트용 커밋을 짧게 만드는 보조 함수입니다."""

    return Commit(commit_hash, message, author, timestamp, parents)


class SortAlgorithmTests(unittest.TestCase):
    def test_merge_sort_orders_values_without_changing_original(self) -> None:
        original = [5, 1, 4, 2, 3]

        result = merge_sort(original)

        self.assertEqual(result, [1, 2, 3, 4, 5])
        self.assertEqual(original, [5, 1, 4, 2, 3])

    def test_merge_sort_is_stable_for_equal_keys(self) -> None:
        records = [("first", 2), ("second", 1), ("third", 2)]

        result = merge_sort(records, key=lambda record: record[1])

        self.assertEqual(
            result,
            [("second", 1), ("first", 2), ("third", 2)],
        )

    def test_quick_sort_handles_duplicates_and_custom_key(self) -> None:
        records = [("c", 3), ("a", 1), ("b", 2), ("b2", 2), ("a2", 1)]

        result = quick_sort(records, key=lambda record: record[1])

        self.assertEqual([record[1] for record in result], [1, 1, 2, 2, 3])
        self.assertEqual(records[0], ("c", 3))

    def test_both_algorithms_accept_empty_and_single_value_lists(self) -> None:
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(quick_sort([]), [])
        self.assertEqual(merge_sort([1]), [1])
        self.assertEqual(quick_sort([1]), [1])


class GraphAlgorithmTests(unittest.TestCase):
    def setUp(self) -> None:
        root = make_commit("111111", timestamp="2024-01-01 09:00:00")
        left = make_commit(
            "aaaaaa",
            timestamp="2024-01-01 09:02:00",
            parents=(root.hash,),
        )
        right = make_commit(
            "dddddd",
            timestamp="2024-01-01 09:01:00",
            parents=(root.hash,),
        )
        merge = make_commit(
            "eeeeee",
            timestamp="2024-01-01 09:03:00",
            parents=(left.hash, right.hash),
        )
        isolated = make_commit("ffffff", timestamp="2024-01-01 09:04:00")
        self.commits = {
            root.hash: root,
            left.hash: left,
            right.hash: right,
            merge.hash: merge,
            isolated.hash: isolated,
        }

    def test_topological_sort_always_places_parents_first(self) -> None:
        result = topological_sort(self.commits)
        positions = {commit.hash: index for index, commit in enumerate(result)}

        self.assertLess(positions["111111"], positions["aaaaaa"])
        self.assertLess(positions["111111"], positions["dddddd"])
        self.assertLess(positions["aaaaaa"], positions["eeeeee"])
        self.assertLess(positions["dddddd"], positions["eeeeee"])
        # 두 자식이 동시에 준비되면 더 이른 timestamp가 먼저입니다.
        self.assertLess(positions["dddddd"], positions["aaaaaa"])

    def test_topological_sort_detects_cycle(self) -> None:
        first = make_commit("aaaaaa", parents=("bbbbbb",))
        second = make_commit("bbbbbb", parents=("aaaaaa",))

        with self.assertRaisesRegex(ValueError, "cycle"):
            topological_sort({first.hash: first, second.hash: second})

    def test_shortest_path_uses_lexicographically_smallest_tie(self) -> None:
        # 111111 -> aaaaaa -> eeeeee와
        # 111111 -> dddddd -> eeeeee는 길이가 같습니다.
        result = find_shortest_path(self.commits, "111111", "eeeeee")

        self.assertEqual(result, ["111111", "aaaaaa", "eeeeee"])

    def test_shortest_path_handles_same_commit_and_disconnected_graph(self) -> None:
        self.assertEqual(
            find_shortest_path(self.commits, "111111", "111111"),
            ["111111"],
        )
        self.assertIsNone(find_shortest_path(self.commits, "111111", "ffffff"))

    def test_find_ancestors_returns_every_parent_without_self(self) -> None:
        result = find_ancestors(self.commits, "eeeeee")

        self.assertEqual(result, {"111111", "aaaaaa", "dddddd"})
        self.assertNotIn("eeeeee", result)


class InvertedIndexTests(unittest.TestCase):
    def test_keyword_and_author_indexes_are_case_insensitive(self) -> None:
        index = InvertedIndex()
        commit = make_commit(
            "abc123",
            message="Add Login Feature login",
            author="Alice Kim",
        )

        index.add(commit)

        self.assertEqual(index.search_keywords("LOGIN"), {"abc123"})
        self.assertEqual(index.search_author("alice kim"), {"abc123"})
        # 같은 단어가 메시지에 두 번 있어도 set에는 해시가 한 번만 들어갑니다.
        self.assertEqual(index.keyword_index["login"], {"abc123"})

    def test_multiword_search_intersects_each_token_result(self) -> None:
        index = InvertedIndex()
        index.add(make_commit("aaaaaa", message="Add login feature"))
        index.add(make_commit("bbbbbb", message="Add payment feature"))

        self.assertEqual(index.search_keywords("add feature"), {"aaaaaa", "bbbbbb"})
        self.assertEqual(index.search_keywords("login feature"), {"aaaaaa"})
        self.assertEqual(index.search_keywords("login missing"), set())


if __name__ == "__main__":
    unittest.main()

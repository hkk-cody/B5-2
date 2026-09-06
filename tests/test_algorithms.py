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

    def test_quick_sort_limits_recursion_for_unbalanced_partitions(self) -> None:
        # 이 형태는 median-of-three 퀵 정렬에 불균형한 파티션을 반복해서 만들 수
        # 있습니다. 큰 파티션까지 재귀 호출하면 Python 재귀 한도를 넘습니다.
        values = list(range(1, 5001)) + list(range(5000, 0, -1))
        expected = [value for value in range(1, 5001) for _ in range(2)]

        result = quick_sort(values)

        self.assertEqual(result, expected)

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

    def test_topological_sort_handles_many_ready_commits_in_key_order(self) -> None:
        root = make_commit("000000", timestamp="2024-01-01 09:00:00")
        children = [
            make_commit(
                f"{number:06x}",
                timestamp="2024-01-01 09:01:00",
                parents=(root.hash,),
            )
            for number in range(1, 2001)
        ]
        # 일부러 역순으로 넣어 dict 삽입 순서가 결과를 좌우하지 않는지 확인합니다.
        commits = {root.hash: root}
        for child in reversed(children):
            commits[child.hash] = child

        result = topological_sort(commits)

        self.assertEqual(
            [commit.hash for commit in result],
            [root.hash] + [child.hash for child in children],
        )

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

    def test_shortest_path_uses_full_path_order_in_both_directions(self) -> None:
        start = make_commit("111111")
        first_left = make_commit("100000", parents=(start.hash,))
        first_right = make_commit("200000", parents=(start.hash,))
        second_left = make_commit("ffffff", parents=(first_left.hash,))
        second_right = make_commit("000001", parents=(first_right.hash,))
        shared = make_commit(
            "aaaaaa", parents=(second_left.hash, second_right.hash)
        )
        target = make_commit("eeeeee", parents=(shared.hash,))
        commits = {
            commit.hash: commit
            for commit in (
                target,
                shared,
                second_right,
                second_left,
                first_right,
                first_left,
                start,
            )
        }

        forward = find_shortest_path(commits, start.hash, target.hash)
        backward = find_shortest_path(commits, target.hash, start.hash)

        self.assertEqual(
            forward,
            ["111111", "100000", "ffffff", "aaaaaa", "eeeeee"],
        )
        self.assertEqual(
            backward,
            ["eeeeee", "aaaaaa", "000001", "200000", "111111"],
        )

    def test_find_ancestors_returns_every_parent_without_self(self) -> None:
        result = find_ancestors(self.commits, "eeeeee")

        self.assertEqual(result, {"111111", "aaaaaa", "dddddd"})
        self.assertNotIn("eeeeee", result)


class InvertedIndexTests(unittest.TestCase):
    def test_intersection_preserves_index_and_ignores_query_order(self) -> None:
        index = InvertedIndex()
        index.add(make_commit("aaaaaa", message="common rare"))
        index.add(make_commit("bbbbbb", message="common"))
        for query in ("common rare", "rare common", "common common rare"):
            self.assertEqual(index.search_keywords(query), {"aaaaaa"})
        self.assertEqual(index.search_keywords("common missing"), set())
        matches = index.search_keywords("common")
        matches.clear()
        self.assertEqual(index.search_keywords("common"), {"aaaaaa", "bbbbbb"})

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

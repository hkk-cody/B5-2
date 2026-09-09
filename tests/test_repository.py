"""저장소 상태와 브랜치 동작의 단위 테스트입니다."""

from __future__ import annotations

import re
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from unittest.mock import patch

from minigit.models import Commit
from minigit.repository import Repository, RepositoryError


class SequenceClock:
    """호출할 때마다 미리 준비한 시각을 하나씩 돌려주는 테스트 시계입니다."""

    def __init__(self, values: list[datetime]) -> None:
        self.values = values
        self.index = 0

    def __call__(self) -> datetime:
        value = self.values[self.index]
        if self.index < len(self.values) - 1:
            self.index += 1
        return value


class RepositoryTests(unittest.TestCase):
    def test_hash_collision_retries_without_overwriting_existing_commit(self) -> None:
        repository = Repository()
        repository.initialize("Alice")
        with patch("minigit.repository.hashlib.sha1") as sha1:
            sha1.return_value.hexdigest.side_effect = [
                "aaaaaa" + "0" * 34,
                "aaaaaa" + "0" * 34,
                "bbbbbb" + "0" * 34,
            ]
            first = repository.create_commit("first")
            second = repository.create_commit("second")
        self.assertEqual(len(repository.commits), 2)
        self.assertEqual(repository.get_commit(first.hash), first)
        self.assertEqual(sha1.call_count, 3)
        self.assertEqual(second.hash, "bbbbbb" + "0" * 34)
        self.assertEqual(second.parents, (first.hash,))
        self.assertEqual(repository.head_hash, second.hash)
        self.assertEqual(repository.search_keyword("first"), [first])
        self.assertEqual(repository.search_keyword("second"), [second])

    def test_full_hash_storage_and_unique_prefix_lookup(self) -> None:
        repository = Repository()
        repository.initialize("Alice")
        self.assertEqual(repository.abbreviated_hashes(), {})
        first_hash = "abcdef0" + "1" * 33
        second_hash = "abcdef1" + "2" * 33
        with patch("minigit.repository.hashlib.sha1") as sha1:
            sha1.return_value.hexdigest.side_effect = [first_hash, second_hash]
            first = repository.create_commit("first")
            self.assertEqual(repository.abbreviated_hashes(), {first_hash: "abcdef"})
            repository.create_branch("feature")
            second = repository.create_commit("second")
        # 앞부분만 같다면 재계산 없이 서로 다른 전체 해시로 저장합니다.
        self.assertEqual(sha1.call_count, 2)
        self.assertEqual(set(repository.commits), {first_hash, second_hash})
        self.assertEqual(repository.branches, {"main": second_hash, "feature": first_hash})
        self.assertEqual(repository.head_hash, second_hash)
        self.assertEqual(second.parents, (first_hash,))
        self.assertEqual(repository.index.keyword_index["first"], {first_hash})
        self.assertEqual(repository.index.author_index["alice"], {first_hash, second_hash})
        self.assertEqual(repository.abbreviated_hashes(), {
            first_hash: "abcdef0", second_hash: "abcdef1",
        })
        for reference in (first_hash, "abcdef0", first_hash[:-1]):
            self.assertIs(repository.get_commit(reference), first)
        self.assertEqual(repository.get_path("abcdef0", "abcdef1"), [first_hash, second_hash])
        self.assertEqual(repository.get_path("abcdef1", second_hash), [second_hash])
        self.assertEqual(repository.get_ancestors("abcdef1"), [first])
        with self.assertRaisesRegex(RepositoryError, "Ambiguous commit: abcdef"):
            repository.get_commit("abcdef")
        for reference in ("", "ffffff", first_hash + "0"):
            with self.assertRaisesRegex(RepositoryError, "Unknown commit:"):
                repository.get_commit(reference)

    def test_abbreviations_expand_as_far_as_needed(self) -> None:
        repository = Repository()
        repository.initialize("Alice")
        hashes = ["a" * 39 + "0", "a" * 39 + "1", "a" * 38 + "20", "b" * 40]
        with patch("minigit.repository.hashlib.sha1") as sha1:
            sha1.return_value.hexdigest.side_effect = hashes
            for value in hashes:
                repository.create_commit(value)
        abbreviated = repository.abbreviated_hashes()
        self.assertEqual(abbreviated, {
            hashes[0]: hashes[0], hashes[1]: hashes[1],
            hashes[2]: hashes[2][:39], hashes[3]: "bbbbbb",
        })
        for full_hash, prefix in abbreviated.items():
            self.assertEqual(repository.get_commit(prefix).hash, full_hash)

    def test_commands_require_initialization(self) -> None:
        repository = Repository()

        with self.assertRaisesRegex(RepositoryError, "Repository not initialized"):
            repository.create_commit("message")

    def test_initialize_creates_empty_main_and_rejects_second_init(self) -> None:
        repository = Repository()

        repository.initialize("Alice")

        self.assertTrue(repository.initialized)
        self.assertEqual(repository.head_branch, "main")
        self.assertIsNone(repository.head_hash)
        with self.assertRaisesRegex(RepositoryError, "already initialized"):
            repository.initialize("Bob")

    def test_branch_cannot_be_created_before_first_commit(self) -> None:
        repository = Repository()
        repository.initialize("Alice")

        with self.assertRaisesRegex(RepositoryError, "No commits yet"):
            repository.create_branch("feature")

    def test_commit_is_immutable_and_has_full_sha1_hash(self) -> None:
        repository = Repository(
            clock=lambda: datetime(2024, 1, 15, 9, 0, 0)
        )
        repository.initialize("Alice")

        commit = repository.create_commit("Initial commit")

        self.assertIsNotNone(re.fullmatch(r"[0-9a-f]{40}", commit.hash))
        self.assertEqual(commit.parents, ())
        with self.assertRaises(FrozenInstanceError):
            commit.message = "changed"  # type: ignore[misc]

    def test_branch_commits_share_parent_but_keep_unique_hashes(self) -> None:
        fixed_time = lambda: datetime(2024, 1, 15, 9, 0, 0)
        repository = Repository(clock=fixed_time)
        repository.initialize("Alice")
        root = repository.create_commit("Initial commit")
        repository.create_branch("feature")
        repository.create_branch("experiment")

        repository.switch_branch("feature")
        feature_commit = repository.create_commit("Same message")
        repository.switch_branch("experiment")
        experiment_commit = repository.create_commit("Same message")

        self.assertEqual(feature_commit.parents, (root.hash,))
        self.assertEqual(experiment_commit.parents, (root.hash,))
        self.assertNotEqual(feature_commit.hash, experiment_commit.hash)
        self.assertEqual(len(repository.commits), 3)

    def test_commit_updates_branch_and_both_indexes(self) -> None:
        repository = Repository()
        repository.initialize("Alice Kim")

        commit = repository.create_commit("Add Login Feature")

        self.assertEqual(repository.head_hash, commit.hash)
        self.assertEqual(repository.search_keyword("login feature"), [commit])
        self.assertEqual(repository.search_author("alice kim"), [commit])

    def test_log_is_topological_across_branches(self) -> None:
        clock = SequenceClock(
            [
                datetime(2024, 1, 15, 9, 0, 0),
                datetime(2024, 1, 15, 9, 2, 0),
                datetime(2024, 1, 15, 9, 1, 0),
            ]
        )
        repository = Repository(clock=clock)
        repository.initialize("Alice")
        root = repository.create_commit("Initial")
        repository.create_branch("feature")
        feature = repository.create_commit("On main")
        repository.switch_branch("feature")
        branch_commit = repository.create_commit("On feature")

        log = repository.get_log()
        positions = {commit.hash: index for index, commit in enumerate(log)}

        self.assertLess(positions[root.hash], positions[feature.hash])
        self.assertLess(positions[root.hash], positions[branch_commit.hash])
        self.assertEqual(len(log), 3)

    def test_date_and_author_log_use_requested_keys(self) -> None:
        repository = Repository()
        repository.initialize("Owner")
        alice = Commit("aaaaaa", "A", "alice", "2024-01-01 10:00:00", ())
        bob = Commit("bbbbbb", "B", "Bob", "2024-01-01 09:00:00", ())
        repository.commits = {alice.hash: alice, bob.hash: bob}

        by_date = repository.get_log("date")
        by_author = repository.get_log("author")

        self.assertEqual([commit.hash for commit in by_date], ["bbbbbb", "aaaaaa"])
        self.assertEqual([commit.hash for commit in by_author], ["aaaaaa", "bbbbbb"])

    def test_unknown_branch_and_commit_use_standard_errors(self) -> None:
        repository = Repository()
        repository.initialize("Alice")

        with self.assertRaisesRegex(RepositoryError, "Unknown branch: missing"):
            repository.switch_branch("missing")
        with self.assertRaisesRegex(RepositoryError, "Unknown commit: abcdef"):
            repository.get_commit("abcdef")


if __name__ == "__main__":
    unittest.main()

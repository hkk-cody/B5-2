"""명령 파싱과 실제 REPL 입출력의 통합 테스트입니다."""

from __future__ import annotations

import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from minigit.models import Commit
from minigit.parser import CommandProcessor
from minigit.repository import Repository


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CommandProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = CommandProcessor()

    def test_commands_ignore_case_and_support_quoted_arguments(self) -> None:
        init_result = self.processor.execute('InIt "Alice Kim"')
        commit_result = self.processor.execute('CoMmIt "Add login feature"')

        self.assertIn("Current user: Alice Kim", init_result.output)
        self.assertRegex(commit_result.output, r"\[main [0-9a-f]{6}\] Add login feature")

    def test_invalid_syntax_does_not_crash_processor(self) -> None:
        self.assertEqual(self.processor.execute('commit "not closed').output, "Invalid args")
        self.assertEqual(self.processor.execute("init Alice Bob").output, "Invalid args")
        self.assertEqual(self.processor.execute("exit now").output, "Invalid args")
        self.assertEqual(self.processor.execute("unknown").output, "Unknown command: unknown")

    def test_uninitialized_and_unknown_values_return_standard_errors(self) -> None:
        self.assertEqual(
            self.processor.execute('commit "message"').output,
            "Repository not initialized",
        )

        self.processor.execute("init Alice")
        self.processor.execute('commit "Initial"')
        self.assertEqual(
            self.processor.execute("switch missing").output,
            "Unknown branch: missing",
        )
        self.assertEqual(
            self.processor.execute("ancestors abcdef").output,
            "Unknown commit: abcdef",
        )

    def test_branch_log_search_path_and_ancestors_work_together(self) -> None:
        self.processor.execute('init "Alice Kim"')
        self.processor.execute('commit "Initial commit"')
        root_hash = self.processor.repository.head_hash
        assert root_hash is not None

        self.processor.execute("branch feature")
        self.processor.execute("switch feature")
        self.processor.execute('commit "Add login feature"')
        feature_hash = self.processor.repository.head_hash
        assert feature_hash is not None

        self.processor.execute("switch main")
        self.processor.execute('commit "Add payment feature"')
        main_hash = self.processor.repository.head_hash
        assert main_hash is not None

        log_output = self.processor.execute("LOG").output
        search_output = self.processor.execute('SEARCH "login feature"').output
        author_output = self.processor.execute('SEARCH --author="alice kim"').output
        path_output = self.processor.execute(f"PATH {feature_hash} {main_hash}").output
        ancestor_output = self.processor.execute(f"ANCESTORS {feature_hash}").output

        short = self.processor.repository.abbreviated_hashes()
        self.assertLess(log_output.index(short[root_hash]), log_output.index(short[feature_hash]))
        self.assertLess(log_output.index(short[root_hash]), log_output.index(short[main_hash]))
        self.assertIn(f"- {short[feature_hash]}: Add login feature", search_output)
        self.assertIn("Found 3 commits:", author_output)
        self.assertEqual(
            path_output,
            f"Path: {short[feature_hash]} -> {short[root_hash]} -> {short[main_hash]}",
        )
        self.assertIn(f"- {short[root_hash]}: Initial commit", ancestor_output)

    def test_short_hashes_are_unambiguous_across_all_outputs_and_inputs(self) -> None:
        self.processor.execute("init Alice")
        first_hash = "abcdef0" + "1" * 33
        second_hash = "abcdef1" + "2" * 33
        with patch("minigit.repository.hashlib.sha1") as sha1:
            sha1.return_value.hexdigest.side_effect = [first_hash, second_hash]
            self.assertEqual(self.processor.execute("commit root").output, "[main abcdef] root")
            self.assertEqual(self.processor.execute("commit child").output, "[main abcdef1] child")

        for command in ("log", "log --sort-by=date", "log --sort-by=author", "search --author=Alice"):
            with self.subTest(command=command):
                output = self.processor.execute(command).output
                self.assertIn("abcdef0", output)
                self.assertIn("abcdef1", output)
                self.assertNotIn(first_hash, output)
                self.assertNotIn(second_hash, output)
        # 검색 결과가 하나여도 저장소의 다른 커밋과 구분되는 길이로 표시합니다.
        self.assertIn("- abcdef0: root", self.processor.execute("search root").output)
        for reference in ("abcdef1", second_hash):
            self.assertEqual(self.processor.execute(f"ancestors {reference}").output,
                             "Ancestors of abcdef1:\n- abcdef0: root")
            self.assertEqual(self.processor.execute(f"path abcdef0 {reference}").output,
                             "Path: abcdef0 -> abcdef1")
        self.assertEqual(self.processor.execute("path abcdef0 abcdef0").output, "Path: abcdef0")
        self.assertEqual(self.processor.execute("ancestors abcdef0").output, "No ancestors")
        for command in ("ancestors abcdef", "path abcdef abcdef1", "path abcdef0 abcdef"):
            self.assertEqual(self.processor.execute(command).output, "Ambiguous commit: abcdef")
        self.assertEqual(self.processor.execute("ancestors ffffff").output, "Unknown commit: ffffff")
        self.assertIn("abcdef0", self.processor.execute("log").output)

    def test_log_options_and_unknown_option(self) -> None:
        self.processor.execute("init Alice")
        self.processor.execute('commit "Initial"')

        self.assertIn("commit ", self.processor.execute("LOG --SORT-BY=DATE").output)
        self.assertIn("commit ", self.processor.execute("log --sort-by=AUTHOR").output)
        self.assertEqual(
            self.processor.execute("log --sort-by=message").output,
            "Invalid args",
        )

    def test_log_contains_every_required_commit_field(self) -> None:
        repository = Repository(clock=lambda: datetime(2024, 1, 15, 9, 0, 0))
        processor = CommandProcessor(repository)
        processor.execute('init "Alice Kim"')
        processor.execute('commit "Initial commit"')
        commit_hash = repository.head_hash
        assert commit_hash is not None
        commit = repository.commits[commit_hash]

        output = processor.execute("log").output

        self.assertIn(commit.hash[:6], output)
        self.assertNotIn(commit.hash, output)
        self.assertIn(commit.author, output)
        self.assertIn(commit.timestamp, output)
        self.assertIn(commit.message, output)

    def test_search_accepts_keyword_that_starts_with_dashes(self) -> None:
        self.processor.execute("init Alice")
        self.processor.execute('commit "--fix parser"')
        commit_hash = self.processor.repository.head_hash
        assert commit_hash is not None

        output = self.processor.execute('search "--fix"').output

        self.assertIn("Found 1 commit:", output)
        self.assertIn(f"- {commit_hash[:6]}: --fix parser", output)
        self.assertEqual(
            self.processor.execute("search --author").output,
            "Invalid args",
        )

    def test_no_results_and_root_ancestors_have_clear_output(self) -> None:
        self.processor.execute("init Alice")
        self.processor.execute('commit "Initial"')
        root_hash = self.processor.repository.head_hash
        assert root_hash is not None

        self.assertEqual(self.processor.execute("search missing").output, "Found 0 commits.")
        self.assertEqual(
            self.processor.execute(f"ancestors {root_hash}").output,
            "No ancestors",
        )

    def test_search_option_terminator_searches_literal_keywords(self) -> None:
        self.processor.execute("init Alice")
        self.processor.execute('commit "Fix --author flag and --author=Bob parsing"')
        for keyword in ("--author", "--author=Bob"):
            with self.subTest(keyword=keyword):
                output = self.processor.execute(f'search -- "{keyword}"').output
                self.assertIn("Found 1 commit:", output)
        self.assertEqual(
            self.processor.execute("search --author=Bob").output, "Found 0 commits."
        )
        for command in ('search --', 'search -- ""', 'search -- " "', 'search -- a b'):
            with self.subTest(command=command):
                self.assertEqual(self.processor.execute(command).output, "Invalid args")

    def test_log_branch_labels_follow_branch_heads(self) -> None:
        self.processor.execute("init Alice")
        self.processor.execute("commit root")
        for name in ("zeta", "alpha"):
            self.processor.execute(f"branch {name}")
        self.assertIn("[alpha, main, zeta]", self.processor.execute("log").output)
        self.processor.execute("switch alpha")
        self.processor.execute("commit child")
        for command in ("log", "log --sort-by=date", "log --sort-by=author"):
            with self.subTest(command=command):
                output = self.processor.execute(command).output
                self.assertIn("[main, zeta]\nroot", output)
                self.assertIn("[alpha]\nchild", output)

    def test_no_path_is_reported_for_disconnected_commits(self) -> None:
        self.processor.execute("init Alice")
        first = Commit("aaaaaa", "first", "Alice", "2024-01-01 09:00:00", ())
        second = Commit("bbbbbb", "second", "Alice", "2024-01-01 09:01:00", ())
        self.processor.repository.commits = {first.hash: first, second.hash: second}

        result = self.processor.execute("path aaaaaa bbbbbb")

        self.assertEqual(result.output, "No path")

    def test_exit_and_quit_request_repl_shutdown(self) -> None:
        self.assertTrue(self.processor.execute("exit").should_exit)
        self.assertTrue(self.processor.execute("QUIT").should_exit)


class ReplIntegrationTests(unittest.TestCase):
    def test_main_program_runs_complete_session(self) -> None:
        session = '\n'.join(
            [
                'init "Alice"',
                'commit "Initial commit"',
                'search "initial"',
                'quit',
                '',
            ]
        )

        completed = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py")],
            input=session,
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("mini-git> ", completed.stdout)
        self.assertIn("Initialized repository.", completed.stdout)
        self.assertIn("Found 1 commit:", completed.stdout)
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()

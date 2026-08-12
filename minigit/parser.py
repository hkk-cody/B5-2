"""한 줄짜리 CLI 입력을 해석하고 저장소 명령으로 연결합니다."""

from __future__ import annotations

import shlex
from dataclasses import dataclass

from minigit.models import Commit
from minigit.repository import Repository, RepositoryError


@dataclass(frozen=True, slots=True)
class CommandResult:
    """명령 실행 뒤 REPL이 출력하고 종료할 정보를 함께 담습니다."""

    output: str = ""
    should_exit: bool = False


class CommandProcessor:
    """문자열 명령의 문법을 검사하고 알맞은 Repository 메서드를 호출합니다."""

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository if repository is not None else Repository()

    def execute(self, line: str) -> CommandResult:
        """입력 한 줄을 실행합니다. 사용자 입력 오류는 결과 문자열로 돌려줍니다."""

        try:
            parts = shlex.split(line)
        except ValueError:
            # 닫히지 않은 따옴표처럼 shlex가 해석할 수 없는 입력입니다.
            return CommandResult("Invalid args")

        if not parts:
            return CommandResult()

        command = parts[0].lower()
        args = parts[1:]

        if command in ("exit", "quit"):
            if args:
                return CommandResult("Invalid args")
            return CommandResult(should_exit=True)

        try:
            return self._dispatch(command, args)
        except RepositoryError as error:
            # 저장소가 알려 준 표준 오류만 사용자 화면에 간단히 표시합니다.
            return CommandResult(str(error))

    def _dispatch(self, command: str, args: list[str]) -> CommandResult:
        """검증된 명령 이름을 실제 기능별 처리 메서드로 분배합니다."""

        if command == "init":
            return self._handle_init(args)
        if command == "branch":
            return self._handle_branch(args)
        if command == "switch":
            return self._handle_switch(args)
        if command == "commit":
            return self._handle_commit(args)
        if command == "log":
            return self._handle_log(args)
        if command == "path":
            return self._handle_path(args)
        if command == "ancestors":
            return self._handle_ancestors(args)
        if command == "search":
            return self._handle_search(args)

        return CommandResult(f"Unknown command: {command}")

    @staticmethod
    def _has_one_nonempty_arg(args: list[str]) -> bool:
        """공백뿐인 값이 아닌 인자가 정확히 하나인지 확인합니다."""

        return len(args) == 1 and bool(args[0].strip())

    def _handle_init(self, args: list[str]) -> CommandResult:
        if not self._has_one_nonempty_arg(args):
            return CommandResult("Invalid args")

        self.repository.initialize(args[0])
        output = (
            "Initialized repository.\n"
            "Current branch: main\n"
            f"Current user: {args[0]}"
        )
        return CommandResult(output)

    def _handle_branch(self, args: list[str]) -> CommandResult:
        if not self._has_one_nonempty_arg(args):
            return CommandResult("Invalid args")

        self.repository.create_branch(args[0])
        return CommandResult(f"Created branch: {args[0]}")

    def _handle_switch(self, args: list[str]) -> CommandResult:
        if not self._has_one_nonempty_arg(args):
            return CommandResult("Invalid args")

        self.repository.switch_branch(args[0])
        return CommandResult(f"Switched to branch: {args[0]}")

    def _handle_commit(self, args: list[str]) -> CommandResult:
        if not self._has_one_nonempty_arg(args):
            return CommandResult("Invalid args")

        commit = self.repository.create_commit(args[0])
        assert self.repository.head_branch is not None
        return CommandResult(
            f"[{self.repository.head_branch} {commit.hash}] {commit.message}"
        )

    def _handle_log(self, args: list[str]) -> CommandResult:
        sort_by: str | None = None

        if args:
            if len(args) != 1:
                return CommandResult("Invalid args")
            option = args[0].lower()
            if option == "--sort-by=date":
                sort_by = "date"
            elif option == "--sort-by=author":
                sort_by = "author"
            else:
                return CommandResult("Invalid args")

        commits = self.repository.get_log(sort_by)
        if not commits:
            return CommandResult("No commits")

        blocks = [self._format_log_commit(commit) for commit in commits]
        return CommandResult("\n\n".join(blocks))

    def _handle_path(self, args: list[str]) -> CommandResult:
        if len(args) != 2 or not args[0].strip() or not args[1].strip():
            return CommandResult("Invalid args")

        path = self.repository.get_path(args[0], args[1])
        if path is None:
            return CommandResult("No path")
        return CommandResult(f"Path: {' -> '.join(path)}")

    def _handle_ancestors(self, args: list[str]) -> CommandResult:
        if not self._has_one_nonempty_arg(args):
            return CommandResult("Invalid args")

        ancestors = self.repository.get_ancestors(args[0])
        if not ancestors:
            return CommandResult("No ancestors")

        lines = [f"Ancestors of {args[0]}:"]
        for commit in ancestors:
            lines.append(f"- {commit.hash}: {commit.message}")
        return CommandResult("\n".join(lines))

    def _handle_search(self, args: list[str]) -> CommandResult:
        if not self._has_one_nonempty_arg(args):
            return CommandResult("Invalid args")

        argument = args[0]
        lower_argument = argument.lower()
        author_prefix = "--author="

        if lower_argument.startswith(author_prefix):
            author = argument[len(author_prefix) :]
            if not author.strip():
                return CommandResult("Invalid args")
            commits = self.repository.search_author(author)
        elif argument.startswith("--"):
            return CommandResult("Invalid args")
        else:
            commits = self.repository.search_keyword(argument)

        return CommandResult(self._format_search_results(commits))

    def _format_log_commit(self, commit: Commit) -> str:
        """로그에 필요한 해시, 작성자, 시각, 메시지를 읽기 좋게 만듭니다."""

        branch_names = self.repository.branches_for_commit(commit.hash)
        branch_label = ""
        if branch_names:
            branch_label = f" [{', '.join(branch_names)}]"

        return (
            f"commit {commit.hash} ({commit.author}, {commit.timestamp})"
            f"{branch_label}\n{commit.message}"
        )

    @staticmethod
    def _format_search_results(commits: list[Commit]) -> str:
        """검색 개수와 커밋 요약을 과제 예시와 같은 형태로 만듭니다."""

        count = len(commits)
        if count == 0:
            return "Found 0 commits."

        noun = "commit" if count == 1 else "commits"
        lines = [f"Found {count} {noun}:", ""]
        for commit in commits:
            lines.append(f"- {commit.hash}: {commit.message}")
        return "\n".join(lines)

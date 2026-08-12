"""Mini Git CLI의 실행 진입점입니다.

터미널에서 ``python main.py``를 실행하면 ``mini-git>`` 프롬프트가 나타납니다.
"""

from __future__ import annotations

from minigit.parser import CommandProcessor


def run_repl(processor: CommandProcessor | None = None) -> None:
    """사용자가 종료 명령을 입력할 때까지 읽기-실행-출력을 반복합니다."""

    command_processor = processor if processor is not None else CommandProcessor()

    while True:
        try:
            line = input("mini-git> ")
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D(입력 종료)나 Ctrl-C를 눌러도 traceback 없이 깔끔히 끝냅니다.
            print()
            break

        result = command_processor.execute(line)
        if result.output:
            print(result.output)
        if result.should_exit:
            break


def main() -> None:
    """프로그램 실행 시 REPL을 시작합니다."""

    run_repl()


if __name__ == "__main__":
    main()

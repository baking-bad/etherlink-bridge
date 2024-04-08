from contextlib import suppress
from typing import Any

import click
from tabulate import tabulate


def echo(message: str, err: bool = False, **styles: Any) -> None:
    with suppress(BrokenPipeError):
        click.secho(message, err=err, **styles)


def notice_echo(message: str) -> None:
    echo(f'\n{message}\n', fg='yellow')


def green_echo(message: str) -> None:
    echo(message, fg='green')


def red_echo(message: str) -> None:
    echo(message, err=True, fg='red')


def prompt_anyof(
    question: str,
    options: list[str],
    comments: list[str],
    default: int,
) -> tuple[int, str]:
    """Ask user to choose one of options; returns index and value"""
    import survey  # type: ignore[import-untyped]

    table = tabulate(
        zip(options, comments, strict=True),
        tablefmt='plain',
    )
    index = survey.routines.select(
        question + '\n',
        options=table.split('\n'),
        index=default,
    )
    return index, options[index]

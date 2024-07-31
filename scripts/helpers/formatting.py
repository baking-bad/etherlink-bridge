import click


def accent(msg: str) -> str:
    return click.style(msg, fg='bright_cyan')


def wrap(msg: str, symbol: str = '`') -> str:
    return '`' + msg + '`'


def echo_variable(prefix: str, name: str, value: str) -> None:
    click.echo(prefix + name + ': ' + wrap(accent(value)))


def format_int(number: int) -> str:
    return f'{number:0,d}'.replace(',', '_')

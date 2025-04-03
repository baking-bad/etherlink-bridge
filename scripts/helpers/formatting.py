import click
from scripts.helpers.contracts.tokens.token import TokenHelper


def accent(msg: str) -> str:
    return click.style(msg, fg='bright_cyan')


def wrap(msg: str, symbol: str = '`') -> str:
    return symbol + msg + symbol


def echo_variable(prefix: str, name: str, value: str) -> None:
    click.echo(prefix + name + ': ' + wrap(accent(value)))


def format_int(number: int) -> str:
    return f'{number:0,d}'.replace(',', '_')


def format_token_info(token: TokenHelper) -> str:
    # TODO: consider moving this logic to the Token?
    token_dict = token.as_dict()
    if 'fa2' in token_dict:
        return (
            accent('FA2')
            + ' token, address: '
            + wrap(accent(token.address))
            + ', id: '
            + wrap(accent(str(token.token_id)))
        )
    elif 'fa12' in token_dict:
        return accent('FA1.2') + 'token, address' + wrap(accent(token.address))
    else:
        return (
            'Undefined token type, address: '
            + wrap(accent(token.address))
            + ', id: '
            + wrap(accent(str(token.token_id)))
        )

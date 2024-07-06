import click
from typing import Optional
from scripts.helpers.contracts import Ticketer, TokenHelper
from scripts.helpers.utility import (
    accent,
    get_tezos_client,
    echo_variable,
    wrap,
)
from scripts import cli_options


# TODO: consider moving this to helpers?
def make_extra_metadata(
    name: Optional[str],
    symbol: Optional[str],
    decimals: Optional[int],
) -> dict[str, str]:
    """Creates extra metadata for ticketer content with name, symbol and decimals"""

    extra_metadata = {}
    if name:
        extra_metadata['name'] = name

    if symbol:
        extra_metadata['symbol'] = symbol

    if decimals:
        extra_metadata['decimals'] = str(decimals)

    return extra_metadata


@click.command()
@cli_options.token_address
@cli_options.token_type
@cli_options.token_id
@cli_options.token_decimals
@cli_options.token_symbol
@cli_options.token_name
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.skip_confirm
@cli_options.silent
def deploy_ticketer(
    token_address: str,
    token_type: str,
    token_id: int,
    token_decimals: int,
    token_symbol: str,
    token_name: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> Ticketer:
    """Deploys `ticketer` contract using provided key as a manager"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    Token = TokenHelper.get_cls(token_type)
    # TODO: consider changing Token.from_address implementation so it will
    #       return FA2 or FA1.2 token based on the token entrypoints
    token = Token.from_address(manager, token_address, token_id=token_id)
    extra_metadata = make_extra_metadata(token_name, token_symbol, token_decimals)

    if not silent:
        click.echo('Deploying Ticketer for ' + wrap(accent(token_symbol)) + ':')
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
        click.echo('  - Params:')
        echo_variable('      * ', 'Token type', token_type)
        echo_variable('      * ', 'Token address', token_address)
        if token_type == 'FA2':
            echo_variable('      * ', 'Token id', str(token_id))
        echo_variable('      * ', 'Token symbol', token_symbol)
        echo_variable('      * ', 'Token name', token_name)
        echo_variable('      * ', 'Token decimals', str(token_decimals))
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = Ticketer.originate(manager, token, extra_metadata).send()
    manager.wait(opg)
    ticketer = Ticketer.from_opg(manager, opg)
    if not silent:
        click.echo(
            'Successfully deployed Ticketer, address: ' + wrap(accent(ticketer.address))
        )

    return ticketer

import click
from scripts.helpers.contracts import TokenHelper
from scripts.helpers.utility import (
    get_tezos_client,
    accent,
    echo_variable,
    wrap,
)
from scripts.helpers.addressable import Addressable
from scripts import cli_options


# TODO: add logic from the bootstrap branch
@click.command()
@cli_options.token_type
@cli_options.token_id
@cli_options.total_supply
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.skip_confirm
@cli_options.silent
def deploy_token(
    token_type: str,
    token_id: int,
    total_supply: int,
    tezos_private_key: str,
    tezos_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> TokenHelper:
    """Deploys token contract using provided key as a manager"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    Token = TokenHelper.get_cls(token_type)
    balances: dict[Addressable, int] = {manager: total_supply}

    # TODO: add token_symbol, token_name, token_decimals to the options
    token_symbol = '!NO-TOKEN-SYMBOL'

    if not silent:
        click.echo('Deploying mock token contract ' + wrap(accent(token_symbol)) + ':')
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
        click.echo('  - Params:')
        # TODO: add params to the output
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = Token.originate(manager, balances, token_id).send()
    manager.wait(opg)
    token = Token.from_opg(manager, opg)
    if not silent:
        click.echo(
            'Successfully deployed '
            + wrap(accent(token_symbol))
            + ' '
            + wrap(accent(token_type))
            + ' Token, address: '
            + wrap(accent(token.address))
        )
    return token

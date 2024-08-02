import click
from scripts.helpers.contracts import Ticketer, TokenBridgeHelper
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.formatting import (
    accent,
    wrap,
    echo_variable,
)
from scripts import cli_options


@click.command()
@cli_options.ticketer_address
@cli_options.erc20_proxy_address
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.token_symbol
@cli_options.skip_confirm
@cli_options.silent
def deploy_token_bridge_helper(
    ticketer_address: str,
    erc20_proxy_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
    token_symbol: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> TokenBridgeHelper:
    """Deploys `token_bridge_helper` contract for provided ticketer"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    ticketer = Ticketer.from_address(manager, ticketer_address)
    erc20_proxy_bytes = bytes.fromhex(erc20_proxy_address.replace('0x', ''))

    if not silent:
        click.echo(
            'Deploying Token Bridge Helper for ' + wrap(accent(token_symbol)) + ':'
        )
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
        click.echo('  - Params:')
        echo_variable('      * ', 'Ticketer address', ticketer_address)
        echo_variable('      * ', 'ERC20 Proxy token address', erc20_proxy_address)
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = TokenBridgeHelper.originate(
        client=manager,
        ticketer=ticketer,
        erc_proxy=erc20_proxy_bytes,
        symbol=token_symbol,
    ).send()
    manager.wait(opg)
    token_bridge_helper = TokenBridgeHelper.from_opg(manager, opg)
    if not silent:
        click.echo(
            'Successfully deployed Token Bridge Helper, address: '
            + wrap(accent(token_bridge_helper.address))
        )

    return token_bridge_helper

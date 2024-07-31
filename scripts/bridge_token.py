import click
from scripts.tezos.deploy_ticketer import deploy_ticketer
from scripts.tezos.get_ticketer_params import get_ticketer_params
from scripts.tezos.deploy_token_bridge_helper import deploy_token_bridge_helper
from scripts.etherlink import deploy_erc20
from scripts import cli_options
from typing import Any, Dict
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
)


@click.command()
@cli_options.token_address
# TODO: consider auto-determine token type by token entrypoints
@cli_options.token_type
@cli_options.token_id
@cli_options.token_decimals
@cli_options.token_symbol
@cli_options.token_name
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.etherlink_private_key
@cli_options.etherlink_rpc_url
@cli_options.kernel_address
@cli_options.skip_confirm
def bridge_token(
    token_address: str,
    token_type: str,
    token_id: int,
    token_decimals: int,
    token_symbol: str,
    token_name: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
    etherlink_private_key: str,
    etherlink_rpc_url: str,
    kernel_address: str,
    skip_confirm: bool,
) -> Dict[str, Any]:
    """Deploys bridge contracts for a new token: Ticketer, ERC20 Proxy
    and Token Bridge Helper.
    """

    # TODO: consider require token_id to be provided if token_type is FA2
    # TODO: consider adding a TzKT API call to get token metadata if not provided
    click.echo('Deploying bridge contracts for ' + wrap(accent(token_symbol)) + ':')
    echo_variable('  - ', 'Token contract', token_address)
    if token_type == 'FA2':
        echo_variable('  - ', 'Token id', str(token_id))
    # TODO: echo token metadata
    # TODO: echo public keys, rpc node addresses
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)
    click.echo('')

    ticketer = deploy_ticketer.callback(
        token_address=token_address,
        token_type=token_type,
        token_id=token_id,
        token_decimals=token_decimals,
        token_symbol=token_symbol,
        token_name=token_name,
        tezos_private_key=tezos_private_key,
        tezos_rpc_url=tezos_rpc_url,
        skip_confirm=True,
        silent=False,
    )  # type: ignore
    click.echo('')

    ticketer_params = get_ticketer_params.callback(
        ticketer.address, tezos_private_key, tezos_rpc_url, silent=True
    )  # type: ignore

    erc20 = deploy_erc20.callback(
        ticketer_address_bytes=ticketer_params['address_bytes'],
        ticket_content_bytes=ticketer_params['content_bytes'],
        token_name=token_name,
        token_symbol=token_symbol,
        token_decimals=token_decimals,
        kernel_address=kernel_address,
        etherlink_private_key=etherlink_private_key,
        etherlink_rpc_url=etherlink_rpc_url,
        skip_confirm=True,
        silent=False,
    )  # type: ignore
    click.echo('')

    token_bridge_helper = deploy_token_bridge_helper.callback(
        ticketer_address=ticketer.address,
        erc20_proxy_address=erc20.address,
        tezos_private_key=tezos_private_key,
        tezos_rpc_url=tezos_rpc_url,
        token_symbol=token_symbol,
        skip_confirm=True,
        silent=False,
    )  # type: ignore
    click.echo('')

    click.echo('Successfully deployed FA Bridge contracts for ' + accent(token_symbol))
    return {
        'ticketer': ticketer,
        'erc20': erc20,
        'token_bridge_helper': token_bridge_helper,
    }

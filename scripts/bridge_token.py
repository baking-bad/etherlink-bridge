import click
from scripts.tezos.deploy_ticketer import deploy_ticketer
from scripts.tezos.get_ticketer_params import get_ticketer_params
from scripts.tezos.deploy_token_bridge_helper import deploy_token_bridge_helper
from scripts.etherlink import deploy_erc20
from scripts.environment import load_or_ask
from typing import Any, Dict, Optional


@click.command()
@click.option(
    '--token-address', required=True, help='The address of the token contract.'
)
# TODO: consider auto-determine token type by token entrypoints
@click.option(
    '--token-type', required=True, help='Token type, either `FA2` or `FA1.2`.'
)
@click.option(
    '--token-id',
    default=0,
    help='Identifier of the token in the contract (only for FA2), default: 0.',
)
@click.option(
    '--decimals',
    required=True,
    default=0,
    help='Token decimals added to the ERC20 token and ticketer metadata content.',
)
@click.option(
    '--symbol',
    required=True,
    help='Token symbol added to the ERC20 token and ticketer metadata content.',
)
@click.option(
    '--name',
    required=True,
    help='Token name added to the ERC20 token and ticketer metadata content.',
)
@click.option(
    '--tezos-private-key',
    default=None,
    help='Private key that would be used to deploy contracts on the Tezos network.',
)
@click.option('--tezos-rpc-url', default=None, help='Tezos RPC URL.')
@click.option(
    '--etherlink-private-key',
    default=None,
    help='Private key that would be used to deploy contract on the Etherlink network.',
)
@click.option('--etherlink-rpc-url', default=None, help='Etherlink RPC URL.')
@click.option(
    '--kernel-address',
    default='0x0000000000000000000000000000000000000000',
    help='The address of the Etherlink kernel which will be managing token. Default `0x0000000000000000000000000000000000000000`',
)
def bridge_token(
    token_address: str,
    token_type: str,
    token_id: int,
    decimals: int,
    symbol: str,
    name: str,
    tezos_private_key: Optional[str],
    tezos_rpc_url: Optional[str],
    etherlink_private_key: Optional[str],
    etherlink_rpc_url: Optional[str],
    kernel_address: str,
) -> Dict[str, Any]:
    """Deploys bridge contracts for a new token:
    - Ticketer
    - ERC20 Proxy
    - Token Bridge Helper
    """

    tezos_private_key = tezos_private_key or load_or_ask(
        'L1_PRIVATE_KEY', is_secret=True
    )
    tezos_rpc_url = tezos_rpc_url or load_or_ask('L1_RPC_URL')
    etherlink_private_key = etherlink_private_key or load_or_ask(
        'L2_PRIVATE_KEY', is_secret=True
    )
    etherlink_rpc_url = etherlink_rpc_url or load_or_ask('L2_RPC_URL')
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    # TODO: consider require token_id to be provided if token_type is FA2
    # TODO: consider adding a TzKT API call to get token metadata if not provided

    ticketer = deploy_ticketer.callback(
        token_address=token_address,
        token_type=token_type,
        token_id=token_id,
        decimals=decimals,
        symbol=symbol,
        name=name,
        private_key=tezos_private_key,
        rpc_url=tezos_rpc_url,
    )  # type: ignore

    ticketer_params = get_ticketer_params.callback(
        ticketer.address, tezos_private_key, tezos_rpc_url, silent=True
    )  # type: ignore

    erc_20_address = deploy_erc20.callback(
        ticketer_address_bytes=ticketer_params['address_bytes'],
        ticket_content_bytes=ticketer_params['content_bytes'],
        token_name=name,
        token_symbol=symbol,
        decimals=decimals,
        kernel_address=kernel_address,
        private_key=etherlink_private_key,
        rpc_url=etherlink_rpc_url,
    )  # type: ignore

    token_bridge_helper = deploy_token_bridge_helper.callback(
        ticketer_address=ticketer.address,
        proxy_address=erc_20_address,
        private_key=tezos_private_key,
        rpc_url=tezos_rpc_url,
        symbol=symbol,
    )  # type: ignore

    return {
        'ticketer': ticketer,
        'erc20': erc_20_address,
        'token_bridge_helper': token_bridge_helper,
    }

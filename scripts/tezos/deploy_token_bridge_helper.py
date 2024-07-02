import click
from typing import Optional
from scripts.helpers.contracts import TokenBridgeHelper
from scripts.environment import get_tezos_client
from scripts.helpers.contracts import Ticketer


@click.command()
@click.option(
    '--ticketer-address', required=True, help='The address of the ticketer contract.'
)
@click.option(
    '--proxy-address',
    required=True,
    help='The address of the ERC20Proxy on the Etherlink side in bytes form.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used to deploy contract on the Tezos network.',
)
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
@click.option(
    '--symbol',
    default=None,
    help='Optional symbol of the Token that would be added to the contract metadata if provided.',
)
def deploy_token_bridge_helper(
    ticketer_address: str,
    proxy_address: str,
    private_key: Optional[str],
    rpc_url: Optional[str],
    symbol: Optional[str] = None,
) -> TokenBridgeHelper:
    """Deploys `token_bridge_helper` contract for provided ticketer"""

    manager = get_tezos_client(rpc_url, private_key)
    ticketer = Ticketer.from_address(manager, ticketer_address)
    proxy_address = proxy_address.replace('0x', '')
    proxy_bytes = bytes.fromhex(proxy_address)
    opg = TokenBridgeHelper.originate(
        client=manager,
        ticketer=ticketer,
        erc_proxy=proxy_bytes,
        symbol=symbol,
    ).send()
    manager.wait(opg)
    token_bridge_helper = TokenBridgeHelper.from_opg(manager, opg)
    return token_bridge_helper

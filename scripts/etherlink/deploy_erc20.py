import click
from typing import Optional
from scripts.environment import (
    load_or_ask,
    get_etherlink_web3,
    get_etherlink_account,
)
from scripts.etherlink.erc20_helper import Erc20ProxyHelper


@click.command()
# TODO: consider simplify this command by using a single argument for the ticket
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticket-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
# TODO: consider extracting token name from the ticketer content bytes
@click.option(
    '--token-name', required=True, help='The name of the ERC20 token on Etherlink side.'
)
@click.option(
    '--token-symbol',
    required=True,
    help='The symbol of the ERC20 token on Etherlink side.',
)
@click.option(
    '--decimals',
    default=0,
    help='The number of decimals of the ERC20 token on Etherlink side.',
)
@click.option(
    '--kernel-address',
    default=None,
    help='The address of the Etherlink kernel that will be managing token.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used to deploy contract on the Etherlink side.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
# TODO: consider adding gas price and gas limit here as parameters?
def deploy_erc20(
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    token_name: str,
    token_symbol: str,
    decimals: int,
    kernel_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None | str:
    """Deploys ERC20 Proxy contract with given parameters"""

    web3 = get_etherlink_web3(rpc_url)
    account = get_etherlink_account(web3, private_key)
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    ticketer = bytes.fromhex(ticketer_address_bytes.replace('0x', ''))
    content = bytes.fromhex(ticket_content_bytes.replace('0x', ''))

    erc20 = Erc20ProxyHelper.originate(
        web3=web3,
        account=account,
        ticketer=ticketer,
        content=content,
        kernel=kernel_address,
        name=token_name,
        symbol=token_symbol,
        decimals=decimals,
    )

    print(f'Successfully deployed ERC20 contract: {erc20.address}')
    # TODO: consider returning the whole ERC20ProxyHelper object
    return erc20.address

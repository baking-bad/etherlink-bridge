import click
from typing import Optional
from scripts.helpers.contracts import Ticketer
from scripts.environment import get_tezos_client
from scripts.helpers.utility import make_address_bytes


@click.command()
@click.option('--ticketer', required=True, help='The address of the ticketer contract.')
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used in the Tezos network.',
)
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def get_ticketer_params(
    ticketer: str,
    private_key: Optional[str],
    rpc_url: Optional[str],
    silent: bool = False,
) -> dict[str, str]:
    """Founds ticketer in L1 and returns it params required for L2 ERC20 token deployment"""

    manager = get_tezos_client(rpc_url, private_key)
    # TODO: add ticketer validation by checking storage?
    ticketer_contract = Ticketer.from_address(manager, ticketer)
    content_bytes = ticketer_contract.get_content_bytes_hex()
    address_bytes = make_address_bytes(ticketer)
    ticket_hash = ticketer_contract.read_ticket().hash()
    print(f'address_bytes: {address_bytes}')
    print(f'content_bytes: {content_bytes}')
    print(f'ticket_hash: {ticket_hash}')
    return {
        'address_bytes': address_bytes,
        'content_bytes': content_bytes,
        'ticket_hash': str(ticket_hash),
    }

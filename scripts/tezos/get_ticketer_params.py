import click
from scripts.helpers.contracts import Ticketer
from scripts.helpers.utility import (
    get_tezos_client,
    make_address_bytes,
)
from scripts.helpers.formatting import accent
from scripts import cli_options


@click.command()
@cli_options.ticketer_address
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.silent
def get_ticketer_params(
    ticketer_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
    silent: bool = True,
) -> dict[str, str]:
    """Returns Ticketer params required for L2 ERC20 token deployment"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    # TODO: add ticketer validation by checking storage?
    ticketer = Ticketer.from_address(manager, ticketer_address)
    content_bytes = ticketer.get_content_bytes_hex()
    address_bytes = make_address_bytes(ticketer_address)
    ticket_hash = ticketer.read_ticket().hash()

    if not silent:
        click.echo('Ticketer params:')
        click.echo('  - Address bytes: `' + accent('0x' + address_bytes) + '`')
        click.echo('  - Content bytes: `' + accent('0x' + content_bytes) + '`')
        click.echo('  - Ticket hash: `' + accent('0x' + str(ticket_hash)) + '`')

    return {
        'address_bytes': address_bytes,
        'content_bytes': content_bytes,
        'ticket_hash': str(ticket_hash),
    }

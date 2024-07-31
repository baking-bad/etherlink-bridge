# Tools to simplify interactions in the different scenarios
# TODO: consider moving some of the functions to the CLI

import click
from pytezos.client import PyTezosClient
from scripts.helpers.formatting import (
    echo_variable,
    accent,
    wrap,
    format_int,
    format_token_info,
)
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from scripts.helpers.ticket import Ticket
from scripts.helpers.contracts import Ticketer


def transfer_ticket(ticket: Ticket, receiver: Addressable) -> str:
    # TODO: note that this code duplicated check in the ticket.py, but tezos_account
    # required to wait for transfer_opg:
    if isinstance(ticket.owner, PyTezosClient):
        tezos_account = ticket.owner
    else:
        raise ValueError('Transfer ticket owner should be a client')

    click.echo('Transfering ticket:')
    echo_variable('  - ', 'Owner', get_address(get_address(ticket.owner)))
    echo_variable('  - ', 'Ticketer address', ticket.ticketer)
    echo_variable('  - ', 'Ticket content', '0x' + ticket.content.to_bytes_hex())
    echo_variable('  - ', 'Amount', format_int(ticket.amount))
    echo_variable('  - ', 'Receiver', get_address(receiver))

    transfer_opg = ticket.transfer(receiver).send()

    tezos_account.wait(transfer_opg)
    opg_hash = transfer_opg.hash()
    click.echo('Successfully transfered, tx hash: ' + wrap(accent(opg_hash)))
    return opg_hash


def wrap_tokens_to_tickets(
    tezos_account: PyTezosClient, ticketer: Ticketer, amount: int
) -> str:
    click.echo(
        'Wrapping ' + format_token_info(ticketer.get_token()) + ' tokens to tickets:'
    )
    echo_variable('  - ', 'Token holder', tezos_account.key.public_key_hash())
    echo_variable('  - ', 'Ticketer', ticketer.address)
    echo_variable('  - ', 'Amount', format_int(amount))

    wrap_opg = tezos_account.bulk(
        ticketer.get_token().allow(tezos_account, ticketer),
        ticketer.deposit(amount),
    ).send()

    tezos_account.wait(wrap_opg)
    opg_hash = wrap_opg.hash()
    click.echo('Successfully wrapped, tx hash: ' + wrap(accent(opg_hash)))

    return opg_hash

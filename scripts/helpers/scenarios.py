# Tools to simplify interactions in the different scenarios
# TODO: consider moving some of the functions to the CLI

import click
from pytezos.client import PyTezosClient
from scripts.helpers.formatting import (
    echo_variable,
    accent,
    wrap,
    format_int,
)
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from scripts.helpers.ticket import Ticket


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

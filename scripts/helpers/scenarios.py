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
    EtherlinkAddressable,
    get_etherlink_address,
    make_deposit_routing_info,
)
from scripts.helpers.ticket import Ticket
from scripts.helpers.contracts import (
    Ticketer,
    TicketRouterTester,
)
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import TxParams
from web3.types import HexBytes  # type: ignore
from typing import Optional


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


def setup_ticket_router_tester_to_rollup_deposit(
    ticket_router_tester: TicketRouterTester,
    target: Addressable,
    receiver: EtherlinkAddressable,
    router: Optional[EtherlinkAddressable],
) -> str:

    deposit_info = make_deposit_routing_info(receiver, router)

    click.echo(
        'Setting up '
        + accent('TicketRouterTester')
        + ' to the '
        + accent('rollupDeposit')
        + ' mode:'
    )
    echo_variable('  - ', 'Target', get_address(target))
    echo_variable('  - ', 'Routing Info', '0x' + deposit_info.hex())

    set_deposit_opg = ticket_router_tester.set_rollup_deposit(
        target=target,
        routing_info=deposit_info,
    ).send()

    ticket_router_tester.client.wait(set_deposit_opg)
    opg_hash = set_deposit_opg.hash()

    click.echo('Successfully set, tx hash: ' + wrap(accent(opg_hash)))
    return opg_hash


def etherlink_legacy_transfer(
    web3: Web3,
    etherlink_account: LocalAccount,
    receiver: EtherlinkAddressable,
    value_wei: int,
) -> HexBytes:
    click.echo('Sending Ethernlink xtz:')
    receiever_address = get_etherlink_address(receiver)
    echo_variable('  - ', 'Sender', get_etherlink_address(etherlink_account))
    echo_variable('  - ', 'Receiver', receiever_address)
    echo_variable('  - ', 'Amount (wei)', format_int(value_wei))
    echo_variable('  - ', 'Amount (mutez)', format_int(value_wei // 10**12))

    transaction: TxParams = {
        'to': receiever_address,
        'gasPrice': web3.to_wei('1', 'gwei'),
        'value': web3.to_wei(value_wei, 'wei'),
        'nonce': web3.eth.get_transaction_count(etherlink_account.address),
    }

    transaction['gas'] = web3.eth.estimate_gas(transaction)
    signed_tx = etherlink_account.sign_transaction(transaction)  # type: ignore
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    click.echo('Successfully transfered, tx hash: ' + wrap(accent(tx_hash.hex())))
    return tx_hash


def deploy_ticket_router_tester(
    tezos_account: PyTezosClient,
    tezos_rpc_url: str,
    silent: bool = False,
) -> TicketRouterTester:
    # TODO: consider making CLI from this
    # TODO: provide setup tools for ticket-router-tester in CLI too? OR at least during deployment?

    if not silent:
        click.echo('Deploying TicketRouterTester:')
        echo_variable('  - ', 'Deployer', tezos_account.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)

    origination_opg = TicketRouterTester.originate(tezos_account).send()
    tezos_account.wait(origination_opg)
    ticket_router_tester = TicketRouterTester.from_opg(tezos_account, origination_opg)

    if not silent:
        click.echo(
            'Successfully deployed TicketRouterTester, address: '
            + wrap(accent(ticket_router_tester.address))
        )

    return ticket_router_tester
